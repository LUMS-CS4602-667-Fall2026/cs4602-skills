---
name: simulated-user
license: MIT
description: >
  Use when a running web application needs checking against the requirements it
  was built from, and you need evidence of what it cannot do rather than a claim
  that it works. Also use when an application was written by an agent and nobody
  has read the code, when "is it finished?" has no trustworthy answer, or when a
  build needs to be exercised as a user rather than as a test suite.
---

# Simulated User

Three users walk one journey through a running application. Everything one of
them **could not do** becomes an issue in the repository, with the steps it took.

**You are the user the system was built for, and nothing more.**

## 1 — Preflight. Refuse rather than half-run

```bash
bash scripts/preflight.sh <the app's URL>
```

It checks the app answers on its port, `gh` is authenticated, and the repo has a
GitHub origin. **If it exits non-zero, stop and report why.**

Then the fourth prerequisite, which no script can check for you.

### 🔴 A real browser, driven by you. This one is a hard blocker

You must be able to **open a page, read it back as text, and act on one element.**
Exactly three tool surfaces are accepted:

| | Accepted because |
|---|---|
| **`chrome-devtools-mcp`** | the reference. Configured in Session 3 |
| **Claude in Chrome** | same capability, same text-first page read |
| **Cursor's Browser tool** | same capability, built in |

**Anything else: stop.** Do not substitute `curl`, `fetch`, `requests`, a test
runner, `evaluate_script`, or reading the source to work out what a page would
have shown. None of those is a user, and a run built on them reports a system
that works.

⚡ **A half-run that reports success is the failure this skill exists to catch.**
If you have none of the three, say so in one line and stop. That sentence is a
more useful result than anything you could produce without a browser.

## 2 — The budget. It is not advisory

| | |
|---|---|
| Actions per role | **10.** At the tenth, stop and record the outcome |
| Perception | **text only.** Never a screenshot — it costs twice as much and names nothing |
| Page reads | One per action, and only when the last action should have changed the page |
| Model turns | One action per turn. Never plan three ahead; the page will have moved |
| Isolation | **Run each role in its own subagent.** Three browser transcripts must not enter the main conversation |

## 3 — The loop, per role

Read [`references/journey.md`](references/journey.md) for the three roles and the
four steps. For each role, in its own subagent:

1. **Open** the app's URL — once.
2. **Read the page back as text.**
3. **Narrate one short first-person sentence** of what you expect. This narration
   is the record; never skip it.
4. Take **one** action.
5. **Read it back again.** Did it do what you expected?
6. Blocked, confused, or contradicted? Append a finding (§4) and continue if you
   can, abandon the step if you cannot.
7. At 10 actions, or when the journey is done, record
   `completed` · `blocked` · `gave_up`.

| Step | `chrome-devtools-mcp` | Claude in Chrome | Cursor |
|---|---|---|---|
| 1 open | `new_page(url)` — **note the `pageId` it reports back**; pages are not zero-indexed | `tabs_create_mcp`, then `navigate` | Browser: navigate |
| 2, 5 read | `take_snapshot(pageId)` | `read_page` | Browser: snapshot |
| 4 act | `click` · `fill_form` · `type_text` · `press_key` | `form_input`, or `computer` for a click | Browser: click, type |

⚠️ **Claude in Chrome drives the real browser with the real person's sessions.**
Point it at the local app and nothing else. Prefer `read_page` over screenshots.

### The one rule that makes the findings worth having

**Use only what the running application tells you.** Do not read the source. Do
not guess a URL. Do not infer that a control does something its label does not
say. Do not apply knowledge a user of this product would not have.

⚡ **If you cannot find a way to do your step, that is the finding — not a puzzle
to solve with developer knowledge.** An agent clever enough to work around a
missing feature reports a working system, which is worse than useless.

### Completing cleanly is a real result

**If a role finishes its journey without friction, say so and file nothing.** Do
not go looking for something to report. A quiet run is evidence; an invented
finding is noise in someone's issue tracker.

## 4 — Findings

One JSON object per line, appended to `.cs4602/findings.jsonl` as it happens —
never held in the conversation and summarised later. Schema and the severity
rules: [`references/finding.md`](references/finding.md).

## 5 — Verify, then file

Back in the main conversation, with only the findings file:

1. Re-read each finding against its own `what_i_did` trail. Mark it
   `confirmed` when the trail supports the claim, `suspect` when the trail
   contradicts it or the claim cannot be checked from the evidence.
   **Suspect findings are kept and labelled, never deleted.**
2. `python3 scripts/file_gaps.py .cs4602/findings.jsonl` to preview, then
   `--apply` to open one issue per finding, labelled `gap`.
3. Report two counts: **how many gaps, and how many fall inside the spine** —
   the three roles and the four steps everybody was given. A gap in the spine is
   a requirement that was read and dropped.

## Red flags

| If you catch yourself… | Then |
|---|---|
| Reaching for a screenshot | Don't. The text read gives you the labels, which is what you need |
| Tempted to `curl` the page instead | That is not a user. Stop and report the missing browser |
| Opening a source file to find the route | Stop. You have just stopped being a user |
| Past 10 actions on one role | Stop and record `gave_up`. The budget is the persona |
| Filing a finding you cannot describe in "I did X, I expected Y, I got Z" | It is not a finding yet |
| Reporting success without a `findings.jsonl` on disk | Nothing ran. Say so |
