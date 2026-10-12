# Findings — schema, severity, and the verify rubric

## One line of JSON, appended as it happens

Write to `.cs4602/findings.jsonl` **the moment you hit the problem.** Do not
collect findings in the conversation and write them at the end — that is how a
run with 9,000 tokens of context becomes a run with 40,000.

```json
{"role":"learner","step":"enrol and take the quiz","spine":true,"severity":"blocking",
 "title":"No way to enrol in a published course",
 "what_i_did":["signed in as the learner created in step 1","opened the course list","clicked the only course shown"],
 "what_i_expected":"a button or link to join the course",
 "what_happened":"the course page shows a title and description and nothing clickable"}
```

| Field | |
|---|---|
| `role` | `administrator` · `instructor` · `learner` |
| `step` | which of the four steps you were on |
| `spine` | `true` if this blocks or damages one of the four steps; `false` if it is outside them |
| `severity` | see below |
| `title` | one line, specific. *"No way to enrol in a published course"*, not *"enrolment is broken"* |
| `what_i_did` | the actions you actually took, in order. **The verify pass judges the claim against this** — if it does not support the title, the finding is marked suspect |
| `what_i_expected` | in user words |
| `what_happened` | what the page actually showed |

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

- *"the button does nothing"* — but the trail shows no snapshot after the click,
  so nothing was checked
- *"the form lost my data"* — but the trail never shows the data being typed
- *"there is no way to publish a course"* — but the trail shows three actions, none
  of which was looking at the course page

⭐ **Suspect findings stay in the report and get filed with the label.** They are
not deleted. A reader can disagree with the verdict, and the point of the rubric
is that the disagreement is about evidence rather than about tone.

## What goes in the issue

One issue per finding, labelled `gap` — plus `spine` when `spine: true`, and
`suspect` when the verify pass said so. Body is the schema rendered as prose:
what I tried, what I expected, what happened, and the verdict with its reason.

**The issue is addressed to the student, not to the agent that filed it.** It
should be actionable without reading this file.
