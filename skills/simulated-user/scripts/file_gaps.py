#!/usr/bin/env python3
"""Turn .cs4602/findings.jsonl into one labelled GitHub issue per finding.

Dry run by default — prints what it would create and stops. Add --apply to file.
Idempotent: an open or closed issue with the same title is skipped, so re-running
after a fix round adds only what is new.

    python3 file_gaps.py .cs4602/findings.jsonl
    python3 file_gaps.py .cs4602/findings.jsonl --apply
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

SEVERITIES = ("blocking", "degraded", "cosmetic")
ROLES = ("administrator", "instructor", "learner")
TITLE_PREFIX = "[gap]"


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("findings", help="path to findings.jsonl")
    ap.add_argument("--apply", action="store_true", help="actually create the issues")
    ap.add_argument("--repo", help="owner/name; defaults to the current repo")
    args = ap.parse_args()

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

    # One listing, not one lookup per finding: these runs are small but the stage is
    # 28 minutes long and 107 people are doing it at once against the same API.
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
        if title in existing or title in seen:
            print(f"  skip   {title}   (already filed)")
            continue
        seen.add(title)
        queued.append((title, f))

    if args.apply:
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
        if not args.apply:
            print(f"  would  {title}   [{', '.join(labs)}]")
            continue
        url = gh("issue", "create", "--title", title, "--body", body(f),
                 "--label", ",".join(labs), *repo).strip()
        print(f"  filed  {url}  {title}")

    spine = sum(1 for _, f in queued if f.get("spine"))
    print(f"\n{len(queued)} to file, {len(findings) - len(queued)} already there.")
    print(f"⭐ {spine} of {len(queued)} are inside the spine — that is the number to report.")
    if not args.apply:
        print("DRY RUN — add --apply to create the issues.")


if __name__ == "__main__":
    main()
