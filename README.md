# CS4602 skills

Skills for **CS4602 / CS667 — Coding for Careers**, LUMS, Fall 2026.

| Skill | What it is for |
|---|---|
| [`simulated-user`](skills/simulated-user/SKILL.md) | Three users walk one fixed journey through your running application. Everything they could not do becomes an issue in your repo |

## Install

**Any harness** — clone it beside your project and point your agent at it:

```bash
git clone https://github.com/LUMS-CS4602-667-Fall2026/cs4602-skills .cs4602
```

> *"Read `.cs4602/skills/simulated-user/SKILL.md` and follow it."*

**Claude Code** — as a plugin:

```
/plugin marketplace add LUMS-CS4602-667-Fall2026/cs4602-skills
/plugin install simulated-user@cs4602
```

**Read the skill before you run it.** It is three short Markdown files and two
scripts. Knowing what it is about to do to your repository is the point, and it
takes two minutes.

## What `simulated-user` needs

| | |
|---|---|
| Your app **running and reachable** | the one command from your README, on a port |
| 🔴 **A real browser you can drive** | `chrome-devtools-mcp` (configured in Session 3), **Claude in Chrome**, or **Cursor's Browser tool**. Nothing else — see below |
| `gh`, authenticated | the findings are filed as issues in your own repo |

### The browser is a hard blocker

The three accepted surfaces all do the same thing: open a page, read it back as
text, act on one element. **`curl`, `fetch`, a test runner, or reading the source
to work out what a page would have shown are not substitutes** — none of them is
a user, and a run built on one of them reports a system that works.

If you have none of the three, the skill stops and says so in one line. **That
sentence is a more useful result than anything it could produce without a
browser**, which is the whole reason it refuses instead of improvising.

`scripts/preflight.sh <your URL>` checks the first and third and refuses rather
than half-running; the browser is the one it cannot check for you, so the skill
asks you to confirm it before a single page is opened. **A clean report from a run
that never started is the exact failure this is built to catch.**

## What it costs

Designed to fit inside a normal Claude Code or Antigravity session — **no API
key, nothing metered separately.**

| | |
|---|---|
| Model turns | ~30 total, 10 per role, hard-capped |
| Perception | `take_snapshot` (~530 tokens of labelled page) — **never** `take_screenshot` (~1,230, and it tells you less) |
| Wall clock | 3–5 minutes |
| Your main context | almost nothing — each role runs in its own subagent and returns three lines |

For comparison, [Shoal](https://github.com/Raynan00/shoal) — the swarm-of-AI-users
tool this borrows its best ideas from — spends about **128,000 tokens per
agent-session** at 20–30 steps with screenshots. This is the same idea with the
journey fixed in advance, which is what makes it affordable in a classroom.

## What it borrows, and what it refuses

From Shoal, gratefully: the persona as a set of **knowledge limits** rather than a
personality; a **patience budget measured in actions**; narrating one first-person
sentence per action; and the **verify pass** that marks each finding `confirmed`
or `suspect` against the agent's own action trail, keeping the suspect ones
flagged rather than deleting them.

Not borrowed: Shoal's prompt tells the agent that *"a session with zero findings
on a flawed site is a failed session."* That is right for a site with planted
bugs and wrong when the output lands in a real issue tracker. **Here, finishing
the journey cleanly is a result**, and an invented finding is worse than none.

MIT. Issues and pull requests welcome from the cohort.
