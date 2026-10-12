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
| Actions per role | **20 counted actions.** At the twentieth, stop and record `gave_up` |
| What counts | One click, one key press, or **one whole form** (`fill_form` with every field at once is one action, not one per field) |
| What is free | Opening the app, signing in, signing out, and the one screenshot you take when you hit a defect. Those are the cost of being three people in one browser, not the product's fault |
| Page reads | One `take_snapshot` per action, and only when the action should have changed the page. Never re-read a page nothing happened to |
| Screenshots | **Only at a defect**, one per finding, saved to `.cs4602/evidence/`. Never as perception: the text read names the controls, a picture does not |
| Model turns | One action per turn. Never plan three ahead; the page will have moved |
| Isolation | **Every role runs in its own subagent.** Browser transcripts never enter the main conversation |

**Running out of budget is never a finding.** It goes in the run record as
`gave_up` with the count, and the report says so. If the product genuinely needs
more than twenty actions for one step, that is a `degraded` defect described in
product terms ("Publishing a course takes nine clicks across three screens"), not
a sentence about a budget.

## 3 — Run the roles: one subagent each, one after another

Read [`references/journey.md`](references/journey.md) for the roles, the four
steps and the hand-off between them.

```
Phase A   administrator (step 1)     ← one subagent
Phase B   instructor (step 2)        ← one subagent
Phase C   learner (step 3)           ← one subagent, briefed with A's and B's output
Phase D   instructor (step 4)        ← one short subagent, briefed with C's output
```

⚠️ **Roles run one at a time, even though steps 1 and 2 are independent.** All
roles share one browser, and the app's sign-in is a cookie on that browser: two
roles at once means the administrator's tab silently becomes the instructor
half-way through, and every finding after that is noise. Run them concurrently
only when each role has its **own browser profile** (a second `chrome-devtools`
MCP server started with `--isolated`), and say so in the report.

Dispatch each role as a **background subagent** and give it only: the app URL,
its role, its step, the hand-off facts it needs (below), and the path of this
skill. Do not wait inside the subagent call; wait for it to finish, read
`.cs4602/run.jsonl`, then start the next one. Each role **signs out** as its last
free action, so the next one starts clean.

| Harness | How to dispatch |
|---|---|
| **Antigravity** | Copy [`agents/simulated-user-role.agent.md`](agents/simulated-user-role.agent.md) to `.agents/agents/` once. Then `invoke_subagent` with `simulated-user-role`, one per role. It runs on the `flash` tier: a user clicking buttons does not need deep reasoning |
| **Claude Code** | `Agent` tool, one per role. Use the fastest model available (Haiku) |
| **Cursor** | One background agent per role, same brief |

Where the time goes, and what this design saves: the roles' browser transcripts
stay out of the main conversation, a form is one action instead of one per
field, sign-in is free, and the role model is the fast tier.

### Hand-off between phases

Each role appends **one line** to `.cs4602/run.jsonl` when it finishes. Append
with a shell command (`echo '<json>' >> .cs4602/run.jsonl`), never with a
write-file tool, which would replace the file:

```json
{"role":"administrator","status":"completed","actions":6,"findings":1,"created":{"learner_name":"Jane Doe","learner_email":"jane.doe@example.com","learner_password":null,"how_told":"the screen never showed or asked for one"}}
{"role":"instructor","status":"completed","actions":11,"findings":2,"created":{"course_title":"DevOps Engineering","course_id":"devops-engineering-2026-q4","quiz_title":"Foundations Quiz","questions":[{"text":"What does CI stand for?","options":{"A":"Continuous Integration","B":"Code Inspection","C":"Central Index"},"correct":"A"}]}}
{"role":"learner","status":"blocked","actions":2,"findings":0,"blocked_by":"administrator"}
```

`status` is `completed` · `blocked` · `gave_up`. `created` holds **only what the
product showed the role**, word for word; a password the screen never showed is
`null`, not a guess. The main conversation copies these facts into the next
phase's brief unchanged. The learner's brief must include the questions and
correct answers, because check 3.4 answers one wrong on purpose.

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
7. **When the step looks done, it is not done.** Open
   [`references/checks.md`](references/checks.md) and tick every check for your
   step, then run its probes. A check you cannot tick is a finding with the
   severity listed there. "I created the account" is not a result; "the account
   appears with the name I typed, the screen confirmed it, and I was told how
   the learner signs in" is.
8. Finish with the two free end-of-role reads in `checks.md` (phone width, sign
   out). At 20 counted actions, or when the checks are done, append your line to
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

### Completing cleanly is a real result, once every check is ticked

**If a role ticks every check in `checks.md`, survives the probes, and files
nothing, say so.** That is a real result. What is not a result is a role that
stopped at "it saved" without looking: a quiet run with the checks skipped is a
run that did not happen. And the opposite failure still holds: do not invent a
finding to have something to report. Every finding must fail a named check or a
probe, in "I did X, I expected Y, I got Z" form.

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
   - **Each issue is pre-approved:** the script comments `approve` on it, which
     is what the repository's issue loop waits for, so the fix starts on the
     loop's next tick. `--await-approval` if you want to read the plan first.
3. Report: **per role, its status and actions used; how many bugs were filed;
   how many sit inside the spine** (the three roles and four steps everyone was
   given). A bug in the spine is a requirement that was read and dropped.

## Red flags

| If you catch yourself… | Then |
|---|---|
| Running the roles in the main conversation | Stop. Dispatch subagents; the transcripts do not belong here |
| Starting two roles at once in one browser | They share the sign-in cookie. One at a time, unless each has its own browser profile |
| Filling a form one field per turn | `fill_form` takes every field at once. That is one action |
| Taking a screenshot to see the page | Don't. Read it as text. A screenshot is evidence of a defect, nothing else |
| Writing "budget exhausted" as a finding | It is not one. Record `gave_up` and move on |
| Recording `completed` the moment the form saved | Open `checks.md`. Tick every check for the step, run the probes, then record |
| Briefing the learner with a password the administrator was never shown | That is inside knowledge. `learner_password: null`; the failed sign-in is the administrator's finding |
| Answering every quiz question correctly | Check 3.4 answers one wrong on purpose. A perfect score proves nothing about the arithmetic |
| A learner reporting the course is missing when the instructor recorded `gave_up` | That is a consequence, not a defect. `blocked_by: instructor` |
| Tempted to `curl` the page instead | That is not a user. Stop and report the missing browser |
| Opening a source file to find the route | Stop. You have just stopped being a user |
| Filing a finding you cannot describe in "I did X, I expected Y, I got Z" | It is not a finding yet |
| Reporting success without a `findings.jsonl` on disk | Nothing ran. Say so |
| About to file more than 10 issues | The cap already stopped you. File the worst 10, not all 30 |
