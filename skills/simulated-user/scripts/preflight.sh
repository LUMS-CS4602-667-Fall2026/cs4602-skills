#!/usr/bin/env bash
# Preflight for the simulated-user skill. No dependencies beyond curl, git and gh.
#
# Exits 0 only when all three prerequisites hold. Prints one line per check so the
# agent can report exactly which one failed rather than "setup problem".
#
#   bash preflight.sh http://localhost:3000

set -uo pipefail

URL="${1:-}"
fail=0

say() { printf '%-28s %s\n' "$1" "$2"; }
bad() { say "$1" "FAIL — $2"; fail=1; }

if [ -z "$URL" ]; then
  echo "usage: bash preflight.sh <the app's URL, e.g. http://localhost:3000>" >&2
  exit 2
fi

# 1 — the application answers on its port.
# --max-time keeps a hung server from eating the stage. Any HTTP status counts as
# alive: a 401 or a 404 at the root is a running app, and is itself worth a finding.
code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$URL" 2>/dev/null) || code=000
if [ "$code" = "000" ]; then
  bad "app on $URL" "nothing answered in 5s. Start it, and check the port"
else
  say "app on $URL" "ok — HTTP $code"
fi

# 2 — gh is authenticated, because the whole output of this skill is issues.
if ! command -v gh >/dev/null 2>&1; then
  bad "gh installed" "not on PATH — see cli.github.com"
elif ! gh auth status >/dev/null 2>&1; then
  bad "gh authenticated" "run: gh auth login"
else
  say "gh authenticated" "ok"
fi

# 3 — a GitHub origin to file against. Without it the findings have nowhere to go.
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  bad "git repo" "not inside a git repository"
else
  origin=$(git remote get-url origin 2>/dev/null || true)
  case "$origin" in
    *github.com*) repo=${origin##*/}; say "github origin" "ok — ${repo%.git}" ;;
    "")           bad "github origin" "no 'origin' remote" ;;
    *)            bad "github origin" "origin is not GitHub: $origin" ;;
  esac
fi

echo
if [ "$fail" -ne 0 ]; then
  echo "PREFLIGHT FAILED — fix the lines marked FAIL above. Do not run the journey." >&2
  exit 1
fi

# The fourth prerequisite cannot be checked from a shell: a browser is a tool surface
# in the agent's session, not a process here. It is a HARD blocker, so say so loudly.
echo "PREFLIGHT OK — three of four."
echo
echo "The fourth is yours to confirm: can you open a page, read it back as text,"
echo "and act on one element? Accepted: chrome-devtools-mcp, Claude in Chrome, or"
echo "Cursor's Browser tool. NOTHING ELSE — not curl, not fetch, not a test runner."
echo "If you have none of them, stop now and say so. Do not report a clean run."
