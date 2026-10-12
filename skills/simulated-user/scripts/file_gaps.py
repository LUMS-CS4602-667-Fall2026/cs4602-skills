#!/usr/bin/env python3
"""Turn .cs4602/findings.jsonl into one labelled GitHub issue per finding.

FILES BY DEFAULT. These issues are the queue the factory works from, so the
default has to be the useful one. --dry-run previews without writing.

    python3 file_gaps.py .cs4602/findings.jsonl              # files them
    python3 file_gaps.py .cs4602/findings.jsonl --dry-run    # preview only
    python3 file_gaps.py .cs4602/findings.jsonl --max 5      # tighter cap

Two guards, because the default writes:

  * MAX_ISSUES (default 10). Findings are triaged blocking > degraded > cosmetic,
    spine first, and anything past the cap is held back and named. One bad run
    cannot bury the tracker it exists to inform.
  * An append-only ledger beside the findings file, written BEFORE each create
    and checked before any API call.

⚠️ The ledger is not belt-and-braces. GitHub's issues-list endpoint lags a few
seconds behind a create, so a title check alone lets a fast re-run duplicate
everything — observed 2026-10-12 on the sibling post_project_brief.py. Re-running
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
TITLE_PREFIX = "[gap]"
MAX_ISSUES = 10
LEDGER_NAME = "filed.jsonl"


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


def body(f):
    did = "\n".join(f"{i}. {s}" for i, s in enumerate(f.get("what_i_did") or [], 1))
    verdict = f.get("verdict") or {}
    parts = [
        f"Filed by the **simulated user** walking the fixed journey as the "
        f"**{f.get('role', 'unknown')}**, on step *{f.get('step', 'unknown')}*.",
        f"## What I did\n{did or '_(no trail recorded — treat with suspicion)_'}",
        f"## What I expected\n{f.get('what_i_expected', '_(not recorded)_')}",
        f"## What happened\n{f['what_happened']}",
    ]
    if verdict.get("status"):
        note = verdict.get("note", "").strip() or "no reason given"
        parts.append(f"## Verify pass\n**{verdict['status']}** — {note}")
    if f.get("spine"):
        parts.append(
            "> ⚠️ **This is inside the spine** — the three roles and four steps "
            "every build was given. It is a requirement that was read and dropped, "
            "not a feature nobody asked for."
        )
    parts.append(
        "_Severity is about the journey, not about tone: `blocking` means a step "
        "could not be completed._"
    )
    return "\n\n".join(parts)


def labels_for(f):
    out = ["gap"]
    sev = f.get("severity")
    if sev in SEVERITIES:
        out.append(sev)
    if f.get("spine"):
        out.append("spine")
    if (f.get("verdict") or {}).get("status") == "suspect":
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
    layer one, because it lags behind a create — see the module docstring.
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
    """Worst first: blocking before cosmetic, spine before non-spine.

    Only matters when the cap bites, and that is exactly when it matters most —
    whatever gets held back should be the stuff nobody would have read anyway.
    """
    sev_rank = {s: i for i, s in enumerate(SEVERITIES)}
    return sorted(
        queued,
        key=lambda tf: (sev_rank.get(tf[1].get("severity"), len(SEVERITIES)),
                        0 if tf[1].get("spine") else 1,
                        tf[0]),
    )


def main():
    ap = argparse.ArgumentParser(
        description="File simulated-user findings as GitHub issues. Writes by default.")
    ap.add_argument("findings", help="path to findings.jsonl")
    ap.add_argument("--dry-run", action="store_true",
                    help="preview only; make no issues and no labels")
    ap.add_argument("--max", type=int, default=MAX_ISSUES, metavar="N",
                    help=f"most issues to create in one run (default {MAX_ISSUES})")
    ap.add_argument("--repo", help="owner/name; defaults to the current repo")
    args = ap.parse_args()
    apply = not args.dry_run
    if args.max < 1:
        sys.exit("--max must be at least 1")

    path = Path(args.findings)
    if not path.exists():
        sys.exit(
            f"no findings file at {path}.\n"
            "Nothing ran, or the run never wrote one. Do not report a clean result — "
            "a clean result is an empty file that exists."
        )

    findings, problems = load(path)
    if problems:
        print("skipped malformed lines:", *problems, sep="\n")
    if not findings:
        print(f"{path} holds no usable findings.")
        print("If the journey genuinely completed without friction, that is the result — "
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
    # One listing, not one lookup per finding — 107 people hit this at once.
    existing = {
        i["title"]
        for i in json.loads(
            gh("issue", "list", "--state", "all", "--limit", "200",
               "--json", "title", *repo) or "[]"
        )
    }

    seen, queued = set(), []
    for f in findings:
        title = f"{TITLE_PREFIX} {f['title']}".strip()
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
            ("gap", "B60205", "Something the simulated user could not do"),
            ("spine", "D93F0B", "Inside the three roles and four fixed steps"),
            ("suspect", "FBCA04", "The verify pass could not confirm this from the trail"),
            *[(s, "C5DEF5", "Severity") for s in SEVERITIES],
            *[(r, "BFD4F2", "Role") for r in ROLES],
        ]:
            gh("label", "create", name, "--color", colour, "--description", desc,
               "--force", *repo, check=False)

    for title, f in queued:
        labs = labels_for(f)
        if not apply:
            print(f"  would  {title}   [{', '.join(labs)}]")
            continue
        url = gh("issue", "create", "--title", title, "--body", body(f),
                 "--label", ",".join(labs), *repo).strip()
        record(args.findings, repo_key, title, url)
        print(f"  filed  {url}  {title}")

    verb = "filed" if apply else "to file"
    print(f"\n{len(queued)} {verb}, {len(findings) - len(queued) - len(held)} already there.")
    if queued:
        spine = sum(1 for _, f in queued if f.get("spine"))
        print(f"⭐ {spine} of {len(queued)} are inside the spine — that is the number to report.")

    if held:
        print(f"\n⚠️  CAPPED AT {args.max}. {len(held)} finding(s) held back, worst-last order:")
        for title, f in held:
            print(f"     - [{f.get('severity', '?')}] {title}")
        print("     Fix what was filed, re-run, and these come through — the ledger")
        print(f"     stops the filed ones repeating. Or raise it: --max {len(held) + args.max}.")

    if not apply:
        print("\nDRY RUN — nothing was created. Drop --dry-run to file.")


if __name__ == "__main__":
    main()
