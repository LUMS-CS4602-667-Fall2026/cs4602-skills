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

Three users walk one journey through a running application. Every **product
defect** one of them hits becomes an issue in the repository, written as that
user would write a request ("I'm a learner… What I'd like… What happened
instead…"), with a screenshot of the moment. It looks like any other issue a
person would open, so the repository's issue loop handles it the same way.

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
If you have none of the three, say so in one line and stop.

## 2 — The budget. It is not advisory

| | |
|---|---|
| Actions per role | **15 counted actions.** At the fifteenth, stop and record `gave_up` |
| What counts | One click, one key press, or **one whole form** (`fill_form` with every field at once is one action, not one per field) |
| What is free | Opening the app, signing in, signing out, and the one screenshot you take when you hit a defect. Those are the cost of being three people in one browser, not the product's fault |
| Page reads | One `take_snapshot` per action, and only when the action should have changed the page. Never re-read a page nothing happened to |
| Screenshots | **Only at a defect**, one per finding, saved to `.cs4602/evidence/`. Never as perception: the text read names the controls, a picture does not |
| Model turns | One action per turn. Never plan three ahead; the page will have moved |
| Isolation | **Every role runs in its own subagent.** Browser transcripts never enter the main conversation |

**Running out of budget is never a finding.** It goes in the run record as
`gave_up` with the count, and the report says so. If the product genuinely needs
more than fifteen actions for one step, that is a `degraded` defect described in
product terms ("Publishing a course takes nine clicks across three screens"), not
a sentence about a budget.

## 3 — Run the roles: two in parallel, then two in sequence

Read [`references/journey.md`](references/journey.md) for the roles, the four
steps and the hand-off between them. Steps 1 and 2 are independent, so they run
at the same time. Steps 3 and 4 depend on what came before.

```
Phase A   administrator (step 1)  ║  instructor (step 2)      ← two subagents, concurrently
Phase B   learner (step 3)                                     ← one subagent, briefed with A's output
Phase C   instructor (step 4)                                  ← one short subagent, briefed with B's output
```

Dispatch each role as a **background subagent** and give it only: the app URL,
its role, its step, the hand-off facts it needs (below), and the path of this
skill. Do not wait inside the subagent call; wait for the phase to finish, read
`.cs4602/run.jsonl`, then start the next phase.

| Harness | How to dispatch |
|---|---|
| **Antigravity** | Copy [`agents/simulated-user-role.agent.md`](agents/simulated-user-role.agent.md) to `.agents/agents/` once. Then `invoke_subagent` with `simulated-user-role`, one per role, Phase A's two in the same turn. It runs on the `flash` tier: a user clicking buttons does not need deep reasoning |
| **Claude Code** | `Agent` tool, one per role, Phase A's two in one message. Use the fastest model available (Haiku) |
| **Cursor** | One background agent per role, same brief |

### Hand-off between phases

Each role appends **one line** to `.cs4602/run.jsonl` when it finishes:

```json
{"role":"administrator","status":"completed","actions":4,"created":{"learner_email":"jane.doe@example.com","learner_password":"Welcome1!"}}
{"role":"instructor","status":"completed","actions":7,"created":{"course_id":"devops-engineering-2026-q4","course_title":"DevOps Engineering","quiz_title":"Foundations Quiz"}}
{"role":"learner","status":"blocked","actions":5,"blocked_by":"instructor"}
```

`status` is `completed` · `blocked` · `gave_up`. The main conversation copies the
`created` facts into the next phase's brief, word for word.

**If an upstream role did not finish, the downstream role does not look for its
output.** A learner briefed that the course was never published records
`blocked_by: instructor` and files nothing about the course being missing: that
is not a defect, it is the previous step's result arriving on time. The learner
still walks whatever it can (sign in, look around) so sign-in defects are caught.

## 4 — The loop, per role (inside the subagent)

1. **Open** the app's URL once. Note the `pageId` chrome-devtools reports back.
2. **Read the page back as text.**
3. **Narrate one short first-person sentence** of what you expect. This narration
   is the record; never skip it.
4. Take **one** action. A form is one action: fill every field, then submit.
5. **Read it back again.** Did it do what you expected?
6. Blocked, confused, or contradicted by the product? **Take one screenshot**,
   append a finding (§5) and continue if you can, abandon the step if you cannot.
7. At 15 counted actions, or when the step is done, append your line to
   `.cs4602/run.jsonl` and return **three lines**: status, actions used, findings
   count. Nothing else comes back to the main conversation.

| Step | `chrome-devtools-mcp` | Claude in Chrome | Cursor |
|---|---|---|---|
| 1 open | `new_page(url)` | `tabs_create_mcp`, then `navigate` | Browser: navigate |
| 2, 5 read | `take_snapshot(pageId)` | `read_page` | Browser: snapshot |
| 4 act | `click` · `fill_form` · `press_key` | `form_input`, or `computer` for a click | Browser: click, type |
| 6 evidence | `take_screenshot(pageId, filePath)` | `computer` screenshot | Browser: screenshot |

⚠️ **Claude in Chrome drives the real browser with the real person's sessions.**
Point it at the local app and nothing else.

### The one rule that makes the findings worth having

**Use only what the running application tells you.** Do not read the source. Do
not guess a URL. Do not infer that a control does something its label does not
say. Do not apply knowledge a user of this product would not have.

⚡ **If you cannot find a way to do your step, that is the finding, not a puzzle
to solve with developer knowledge.** An agent clever enough to work around a
missing feature reports a working system, which is worse than useless.

### Completing cleanly is a real result

**If a role finishes its step without friction, say so and file nothing.** Do not
go looking for something to report. A quiet run is evidence; an invented finding
is noise in someone's issue tracker.

## 5 — Findings are bug reports, written by the user who hit them

One JSON object per line, appended to `.cs4602/findings.jsonl` **the moment it
happens**, never held in the conversation and summarised later. Schema, the
screenshot rule, severity and the issue template:
[`references/finding.md`](references/finding.md).

A finding is a **defect in the product**: something the page let you believe you
could do and then did not do, a control that did nothing, a result that
contradicted an earlier screen, a step with no way to reach it. These are **not**
findings and must never be written down as one:

- the action budget running out (goes in `run.jsonl` as `gave_up`)
- a missing account or course because the role that creates it did not finish
  (goes in `run.jsonl` as `blocked_by`)
- anything about the browser tool, the harness, or this skill

## 6 — Verify, then file

Back in the main conversation, with only `findings.jsonl` and `run.jsonl`:

1. Re-read each finding against its own `what_i_did` trail. `confirmed` when the
   trail supports the claim; `suspect` when the trail contradicts it or the
   claim cannot be checked from the evidence. Drop any finding that is really
   one of the three non-findings above; they slip through.
2. `python3 scripts/file_gaps.py .cs4602/findings.jsonl`. **This files the
   issues.** Only `confirmed` findings become issues, labelled `bug`, with the
   screenshot attached and the body in the user's voice. `suspect` ones are
   listed in the output for you to read, not filed; `--include-suspect` overrides.
   - **At most 10 issues per run**, worst first. `--dry-run` previews;
     `--max N` tightens the cap.
   - A ledger beside the findings file stops a re-run duplicating what it
     already filed. ⚠️ **Do not delete it** to "start fresh".
3. Report: **per role, its status and actions used; how many bugs were filed;
   how many sit inside the spine** (the three roles and four steps everyone was
   given). A bug in the spine is a requirement that was read and dropped.

## Red flags

| If you catch yourself… | Then |
|---|---|
| Running the roles in the main conversation | Stop. Dispatch subagents; the transcripts do not belong here |
| Running administrator and instructor one after the other | They are independent. Start both, then wait |
| Filling a form one field per turn | `fill_form` takes every field at once. That is one action |
| Taking a screenshot to see the page | Don't. Read it as text. A screenshot is evidence of a defect, nothing else |
| Writing "budget exhausted" as a finding | It is not one. Record `gave_up` and move on |
| A learner reporting the course is missing when the instructor recorded `gave_up` | That is a consequence, not a defect. `blocked_by: instructor` |
| Tempted to `curl` the page instead | That is not a user. Stop and report the missing browser |
| Opening a source file to find the route | Stop. You have just stopped being a user |
| Filing a finding you cannot describe in "I did X, I expected Y, I got Z" | It is not a finding yet |
| Reporting success without a `findings.jsonl` on disk | Nothing ran. Say so |
| About to file more than 10 issues | The cap already stopped you. File the worst 10, not all 30 |
