# Findings: schema, screenshot, severity, and what the issue looks like

## One line of JSON, appended as it happens

Write to `.cs4602/findings.jsonl` **the moment you hit the problem.** Do not
collect findings in the conversation and write them at the end; that is how a
run with 9,000 tokens of context becomes a run with 40,000.

```json
{"role":"learner","step":"enrol and take the quiz","spine":true,"severity":"blocking",
 "title":"The course page has no way to join the course",
 "what_i_did":["signed in as jane.doe@example.com","opened Available Courses","clicked DevOps Engineering"],
 "what_i_expected":"a button or link that lets me join the course",
 "what_happened":"the course page shows a title and description and nothing I can click",
 "screenshot":".cs4602/evidence/learner-01.png"}
```

| Field | |
|---|---|
| `role` | `administrator` · `instructor` · `learner` |
| `step` | which of the four steps you were on |
| `spine` | `true` if this blocks or damages one of the four steps; `false` if it is outside them |
| `severity` | see below |
| `title` | **the symptom, as this user would say it**, naming the screen or control the product itself names. *"The course page has no way to join the course"*, not *"enrolment is broken"* and not *"No enrol button in CourseCard component"* |
| `what_i_did` | the actions you actually took, in order, including the sign-in. **The verify pass judges the claim against this.** If it does not support the title, the finding is marked suspect |
| `what_i_expected` | in user words |
| `what_happened` | what the page actually showed |
| `screenshot` | path of the one screenshot you took at this moment (below). Omit only if the browser surface cannot take one |
| `request` | optional: what you, the user, want the product to do instead, in one sentence. *"Let me join a course from its page."* When omitted, the issue asks for `what_i_expected` |

## The screenshot

Take **one** screenshot per finding, at the moment the page let you down, before
you move on. Save it under `.cs4602/evidence/` as `<role>-<nn>.png` where `nn`
is the finding number for that role (`learner-01.png`, `learner-02.png`).

```
take_screenshot(pageId, filePath=".cs4602/evidence/learner-01.png")
```

It does not count against your actions. It is also the **only** time you take a
screenshot: perception is the text read, always. The picture is for the student
reading the issue, who needs to see what you saw.

## What is not a finding

Write none of these down, in any wording:

| Not a finding | Where it goes instead |
|---|---|
| You ran out of actions | `run.jsonl`, `status: gave_up` |
| The thing you needed was never created because the earlier role did not finish | `run.jsonl`, `blocked_by: <role>` |
| The browser tool, the harness, the model, or this skill got in your way | your three-line return to the main conversation |
| Something you only know is wrong from reading the code | nothing; you were not supposed to read it |

## Severity

| | Means | Example |
|---|---|---|
| **`blocking`** | a step of the journey could not be completed at all | the learner cannot enrol |
| **`degraded`** | the step completed, but something was wrong, silent, or contradicted itself | the quiz submitted but showed no score, and the instructor's view showed none either |
| **`cosmetic`** | you noticed it, it cost you nothing | a heading says "Learners" on a page listing instructors |

⚠️ **Severity is about the journey, not about how annoyed you were.** Three
`cosmetic` findings and no `blocking` ones on a system that cannot enrol anyone
means the journey was not actually walked.

## The verify rubric

Run once, over the findings file, in the main conversation. For each finding ask
only this: **does `what_i_did` support `what_i_expected` → `what_happened`?**

| Verdict | When |
|---|---|
| `confirmed` | the trail is consistent with the claim |
| `suspect` | the trail contradicts the claim, the claim cannot be checked from the trail, or the action that would have proved it was never taken |

Typical `suspect` cases, all of which are the simulated user's fault rather than
the application's:

- *"the button does nothing"*, but the trail shows no page read after the click,
  so nothing was checked
- *"the form lost my data"*, but the trail never shows the data being typed
- *"there is no way to publish a course"*, but the trail shows three actions, none
  of which was looking at the course page

Also strike, at this point, anything that is really one of the non-findings
above. Those slip through when a role is tired.

**Suspect findings are not filed.** They are printed by `file_gaps.py` so you can
read them, and they stay in `findings.jsonl` with their verdict. If you disagree
with a verdict, fix the verdict and re-run; `--include-suspect` files them all,
labelled `suspect`.

## What goes in the issue

One issue per `confirmed` finding, labelled `bug`, plus the role, the severity,
and `spine` when `spine: true`. The title is the finding's title, unchanged.

The body is **a request from the user who hit it, to the student who built it**:
the same shape as any other issue a person would open, so the repository's issue
loop picks it up without special handling. It must be actionable without reading
this file.

```
I'm a learner. I signed in as jane.doe@example.com, then opened Available Courses.
I was trying to enrol and take the quiz.

**What I'd like:** let me join a course from its page.

**What happened instead:** the course page shows a title and description and
nothing I can click.

**How to see it yourself**
1. signed in as jane.doe@example.com
2. opened Available Courses
3. clicked DevOps Engineering

[screenshot]

Could you fix this? Reply here if you need anything else from me.

---
Severity `blocking`: I could not finish "enrol and take the quiz".
This step is one of the four every build was given.
```
