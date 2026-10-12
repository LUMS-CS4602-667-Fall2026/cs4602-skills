#!/usr/bin/env python3
"""Turn .cs4602/findings.jsonl into one `bug` issue per confirmed finding.

FILES BY DEFAULT. These issues are the queue the factory works from, so the
default has to be the useful one. --dry-run previews without writing.

    python3 file_gaps.py .cs4602/findings.jsonl                    # files them
    python3 file_gaps.py .cs4602/findings.jsonl --dry-run          # preview only
    python3 file_gaps.py .cs4602/findings.jsonl --max 5            # tighter cap
    python3 file_gaps.py .cs4602/findings.jsonl --include-suspect  # file suspect ones too

Each issue is a bug report written in the voice of the user who hit it, with the
screenshot the role took at that moment attached (gh >= 2.99 `--attach`). Only
findings the verify pass marked `confirmed` (or never marked) are filed; `suspect`
ones are printed for a human to read. Anything that is really a run artefact (a
budget, a harness complaint) is refused here as a last line of defence.

Two guards, because the default writes:

  * MAX_ISSUES (default 10). Findings are triaged blocking > degraded > cosmetic,
    spine first, and anything past the cap is held back and named. One bad run
    cannot bury the tracker it exists to inform.
  * An append-only ledger beside the findings file, written BEFORE each create
    and checked before any API call.

⚠️ The ledger is not belt-and-braces. GitHub's issues-list endpoint lags a few
seconds behind a create, so a title check alone lets a fast re-run duplicate
everything (observed 2026-10-12 on the sibling post_project_brief.py). Re-running
after a fix round is this script's INTENDED workflow, so that path has to be safe.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

SEVERITIES = ("blocking", "degraded", "cosmetic")
ROLES = ("administrator", "instructor", "learner")
MAX_ISSUES = 10
LEDGER_NAME = "filed.jsonl"
# Words that mean the "finding" is about the run, not the product. finding.md
# forbids them; this catches the ones that slip through a tired role.
NOT_A_DEFECT = ("budget", "action limit", "actions limit", "subagent", "harness",
                "take_snapshot", "chrome-devtools", "mcp ")
STEP_NAMES = {
    "administrator": "create a learner's account",
    "instructor": "publish a course containing at least one quiz",
    "learner": "enrol and take the quiz",
}


def gh(*args, check=True):
    """Run gh and return stdout. gh's own stderr is left visible on failure."""
    out = subprocess.run(["gh", *args], capture_output=True, text=True)
    if check and out.returncode != 0:
        sys.exit(f"gh {' '.join(args[:2])} failed: {out.stderr.strip()}")
    return out.stdout


def load(path):
    """Parse the findings file, reporting the line number of anything malformed.

    A findings file is written one append at a time by an agent mid-run, so a
    truncated last line is a normal failure mode rather than a corrupt file.
    """
    findings, problems = [], []
    for n, line in enumerate(Path(path).read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            f = json.loads(line)
        except json.JSONDecodeError as e:
            problems.append(f"  line {n}: not valid JSON ({e.msg})")
            continue
        missing = [k for k in ("title", "what_i_did", "what_happened") if not f.get(k)]
        if missing:
            problems.append(f"  line {n}: missing {', '.join(missing)}")
            continue
        findings.append(f)
    return findings, problems


def not_a_defect(f):
    """Return the word that gives it away, or None."""
    text = " ".join([f.get("title", ""), f.get("what_happened", ""),
                     f.get("what_i_expected", "")]).lower()
    for w in NOT_A_DEFECT:
        if w in text:
            return w.strip()
    return None


def screenshot_for(f, findings_path):
    """Resolve the finding's screenshot to a real file, or None with a reason."""
    rel = f.get("screenshot")
    if not rel:
        return None, "no screenshot recorded"
    candidates = [Path(rel), Path(findings_path).resolve().parent.parent / rel,
                  Path(findings_path).resolve().parent / Path(rel).name]
    for c in candidates:
        if c.is_file():
            return c, None
    return None, f"screenshot not found: {rel}"


def body(f, shot):
    """The issue, in the voice of the user who hit it, for the student who built it."""
    role = f.get("role", "user")
    step = f.get("step") or STEP_NAMES.get(role, "my step")
    did = f.get("what_i_did") or []
    article = "an" if role[:1] in "aeiou" else "a"

    opening = f"I'm {article} {role}."
    if did:
        opening += f" I {did[0].strip().rstrip('.')}"
        if len(did) > 1:
            opening += f", then {did[1].strip().rstrip('.')}"
        opening += "."
    opening += f" I was trying to {step}."

    parts = [
        opening,
        f"**What I expected:** {f.get('what_i_expected') or '_(not recorded)_'}",
        f"**What happened:** {f['what_happened']}",
    ]
    if did:
        steps = "\n".join(f"{i}. {s}" for i, s in enumerate(did, 1))
        parts.append(f"**How to see it yourself**\n{steps}")
    if shot:
        parts.append(f"![What I saw]({shot.as_posix()})")

    sev = f.get("severity")
    tail = []
    if sev == "blocking":
        tail.append(f"Severity `blocking`: I could not finish \"{step}\".")
    elif sev == "degraded":
        tail.append(f"Severity `degraded`: I finished \"{step}\", but something was wrong along the way.")
    elif sev == "cosmetic":
        tail.append("Severity `cosmetic`: it did not stop me, but it is wrong.")
    if f.get("spine"):
        tail.append("This step is one of the four every build was given.")
    tail.append("_Filed by the simulated user, from a real browser session._")
    parts.append("---\n" + "\n".join(tail))
    return "\n\n".join(parts)


def labels_for(f, suspect):
    out = ["bug"]
    sev = f.get("severity")
    if sev in SEVERITIES:
        out.append(sev)
    if f.get("spine"):
        out.append("spine")
    if suspect:
        out.append("suspect")
    role = f.get("role")
    if role in ROLES:
        out.append(role)
    return out


def ledger_path(findings):
    """The ledger sits beside the findings file, so it travels with the run."""
    return Path(findings).resolve().parent / LEDGER_NAME


def already_filed(findings, repo_key):
    """Titles this machine has already filed into this repo, from the ledger.

    Checked before any API call. The issues-list endpoint is layer two, not
    layer one, because it lags behind a create (see the module docstring).
    """
    lp = ledger_path(findings)
    if not lp.exists():
        return set()
    done = set()
    for line in lp.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue            # a torn last line is normal; ignore it
        if rec.get("repo") == repo_key and rec.get("title"):
            done.add(rec["title"])
    return done


def record(findings, repo_key, title, url):
    """Append BEFORE the next create, so a crash cannot lose what we just made."""
    with ledger_path(findings).open("a") as fh:
        fh.write(json.dumps({"repo": repo_key, "title": title,
                             "url": url, "ts": time.time()}) + "\n")


def triage(queued):
    """Worst first: blocking before cosmetic, spine before non-spine."""
    sev_rank = {s: i for i, s in enumerate(SEVERITIES)}
    return sorted(
        queued,
        key=lambda tf: (sev_rank.get(tf[1].get("severity"), len(SEVERITIES)),
                        0 if tf[1].get("spine") else 1,
                        tf[0]),
    )


def main():
    ap = argparse.ArgumentParser(
        description="File simulated-user findings as bug issues. Writes by default.")
    ap.add_argument("findings", help="path to findings.jsonl")
    ap.add_argument("--dry-run", action="store_true",
                    help="preview only; make no issues and no labels")
    ap.add_argument("--max", type=int, default=MAX_ISSUES, metavar="N",
                    help=f"most issues to create in one run (default {MAX_ISSUES})")
    ap.add_argument("--include-suspect", action="store_true",
                    help="also file findings the verify pass marked suspect (labelled)")
    ap.add_argument("--repo", help="owner/name; defaults to the current repo")
    args = ap.parse_args()
    apply = not args.dry_run
    if args.max < 1:
        sys.exit("--max must be at least 1")

    path = Path(args.findings)
    if not path.exists():
        sys.exit(
            f"no findings file at {path}.\n"
            "Nothing ran, or the run never wrote one. Do not report a clean result; "
            "a clean result is an empty file that exists."
        )

    findings, problems = load(path)
    if problems:
        print("skipped malformed lines:", *problems, sep="\n")
    if not findings:
        print(f"{path} holds no usable findings.")
        print("If the journey genuinely completed without friction, that is the result: "
              "say so, and file nothing.")
        return

    repo = ["--repo", args.repo] if args.repo else []
    repo_key = args.repo or gh("repo", "view", "--json", "nameWithOwner",
                               "--jq", ".nameWithOwner").strip() or "(unknown)"
    print(f"repo:  {repo_key}")

    # Layer 1: the ledger. No API call, and authoritative for what we filed.
    filed = already_filed(args.findings, repo_key)
    if filed:
        print(f"ledger: {len(filed)} already filed into this repo from here")

    # Layer 2: the repo's own issues, for anything filed from somewhere else.
    existing = {
        i["title"]
        for i in json.loads(
            gh("issue", "list", "--state", "all", "--limit", "200",
               "--json", "title", *repo) or "[]"
        )
    }

    seen, queued, suspects = set(), [], []
    for f in findings:
        title = f["title"].strip()
        word = not_a_defect(f)
        if word:
            print(f"  refuse {title}   (about the run, not the product: \"{word}\")")
            continue
        status = (f.get("verdict") or {}).get("status")
        if status == "suspect" and not args.include_suspect:
            suspects.append((title, (f.get("verdict") or {}).get("note", "")))
            continue
        if not status:
            print(f"  note   {title}   (no verify verdict recorded; filing as confirmed)")
        if title in filed:
            print(f"  skip   {title}   (ledger)")
            continue
        if title in existing or title in seen:
            print(f"  skip   {title}   (already in the tracker)")
            continue
        seen.add(title)
        queued.append((title, f))

    queued = triage(queued)
    held = queued[args.max:]
    queued = queued[:args.max]

    if apply and queued:
        # --force so a re-run does not fail on labels that already exist.
        for name, colour, desc in [
            ("bug", "d73a4a", "Something isn't working"),
            ("spine", "D93F0B", "Inside the three roles and four fixed steps"),
            ("suspect", "FBCA04", "The verify pass could not confirm this from the trail"),
            *[(s, "C5DEF5", "Severity") for s in SEVERITIES],
            *[(r, "BFD4F2", "Role") for r in ROLES],
        ]:
            gh("label", "create", name, "--color", colour, "--description", desc,
               "--force", *repo, check=False)

    for title, f in queued:
        suspect = (f.get("verdict") or {}).get("status") == "suspect"
        labs = labels_for(f, suspect)
        shot, why = screenshot_for(f, args.findings)
        if not apply:
            extra = f"  +{shot.name}" if shot else f"  ({why})"
            print(f"  would  {title}   [{', '.join(labs)}]{extra}")
            continue
        cmd = ["issue", "create", "--title", title, "--body", body(f, shot),
               "--label", ",".join(labs), *repo]
        if shot:
            cmd += ["--attach", f"{shot.as_posix()}#What I saw"]
        else:
            print(f"  note   {title}   ({why}; filing without one)")
        url = gh(*cmd).strip()
        record(args.findings, repo_key, title, url)
        print(f"  filed  {url}  {title}")

    verb = "filed" if apply else "to file"
    print(f"\n{len(queued)} {verb}, "
          f"{len(findings) - len(queued) - len(held) - len(suspects)} already there or refused.")
    if queued:
        spine = sum(1 for _, f in queued if f.get("spine"))
        print(f"⭐ {spine} of {len(queued)} are inside the spine; that is the number to report.")

    if suspects:
        print(f"\n🔎 {len(suspects)} suspect finding(s) NOT filed. Read them; "
              "fix the verdict and re-run, or --include-suspect:")
        for title, note in suspects:
            print(f"     - {title}" + (f"  ({note})" if note else ""))

    if held:
        print(f"\n⚠️  CAPPED AT {args.max}. {len(held)} finding(s) held back, worst-last order:")
        for title, f in held:
            print(f"     - [{f.get('severity', '?')}] {title}")
        print("     Fix what was filed, re-run, and these come through; the ledger")
        print(f"     stops the filed ones repeating. Or raise it: --max {len(held) + args.max}.")

    if not apply:
        print("\nDRY RUN: nothing was created. Drop --dry-run to file.")


if __name__ == "__main__":
    main()
