# Checks: what "done" feels like to the user, step by step

Finishing a step is not the same as the product doing it right. A role that
creates an account and stops has checked nothing. **Each step below has checks
you tick before you record `completed`**, and one or two **probes**: things an
ordinary user does without thinking (typing the same person twice, leaving a
field blank, getting one answer wrong). A check you cannot tick is a finding,
with the severity shown. A probe the product handles well is nothing.

Two rules shape every line here:

- **Only what a user sees and feels.** The page, its words, its numbers, what
  happened after I clicked. Never the code, the data, the network, the console.
- **Written for the brief, not for one build.** Fifty students built fifty
  different products from the same four steps. The checks name the step's
  outcome ("I know how this person signs in"), never a screen or a button
  ("the Manage button"). Find the outcome wherever this product puts it.

## Step 1: Administrator creates a learner's account

| # | Check | If not |
|---|---|---|
| 1.1 | The person I created is now visible somewhere, with **exactly** the name and email I typed | `blocking` |
| 1.2 | The screen told me it worked (a message, or something visibly changed) | `degraded`: silence after saving |
| 1.3 | **I know how this person will sign in.** The screen showed me, or let me choose, their password or sign-in method. Record it word for word in `run.jsonl` | `blocking`: "I created an account but was never told how the learner signs in." Record `"learner_password": null` |

Probes (counted):
- **P1.a** Create the same person again. I expect to be stopped or warned. Two of them, and nothing said → `degraded`.
- **P1.b** Submit the form with the required fields empty. I expect to be told what is missing. A blank entry, or nothing happening at all → `degraded`.

## Step 2: Instructor publishes a course containing at least one quiz

| # | Check | If not |
|---|---|---|
| 2.1 | My course is visible with the title I typed, and the screen says, in words a learner would understand, that it is published or live | `blocking` |
| 2.2 | The quiz shows **my** question and **my** answer options. Any text I did not write that survived (pre-filled sample answers, an example question) | `degraded`: "The quiz shows answers I never wrote" |
| 2.3 | I could write the quiz I had in mind: mark the right answer, give as many options as I wanted, add more than one question | `degraded` for each thing I could not do, in my words ("I can only give two answers per question") |
| 2.4 | After publishing, the screen confirmed it | `degraded` |

Record in `run.jsonl` `created.questions`: each question's text, its options and which is correct, exactly as I entered them. The learner needs them.

Probe (counted):
- **P2.a** Make a second course with no quiz and try to publish it. I expect to be stopped or warned. It goes live silently → `degraded`: "I can publish an empty course." Leave it; do not use it in step 3.

## Step 3: Learner enrols and takes that quiz

| # | Check | If not |
|---|---|---|
| 3.1 | I sign in with **exactly** what the administrator recorded. Never a demo or sample account, never a password nobody gave me. If `learner_password` is `null`, try the email alone, then with an empty password | sign-in fails → `blocked_by: administrator`, no finding (step 1 already filed it) |
| 3.2 | I can find the course by the instructor's title, join it, and the screen confirms I am in | `blocking` |
| 3.3 | The quiz shows the instructor's questions and options word for word | `degraded` |
| 3.4 | **Answer all but one correctly, on purpose.** With *n* questions I expect to be told I scored round((n−1)/n × 100). The screen shows a score, and it is that number | no score shown → `blocking`; a different number → `degraded`: "I got 3 of 4 right and it told me 100%" |
| 3.5 | Retake with every answer correct. The screen tells me which attempt counts, and what it tells me now is the better one | `degraded` |
| 3.6 | Wherever this product shows me my courses or progress, this course now reflects what I just did, not blank or "not started" | `degraded` |

Probe (counted):
- **P3.a** Submit the quiz with one question unanswered. I expect to be told. Scored silently → `degraded`.

## Step 4: Instructor sees the result

| # | Check | If not |
|---|---|---|
| 4.1 | I can find the learner from step 1 **by name**, under this course, with the score step 3 was told counts, and when it happened | `blocking` |
| 4.2 | The learner's standing for this course reflects the quiz (passed, a grade, completed), not blank or pending | `degraded` |
| 4.3 | If there were two attempts, I can tell them apart | `cosmetic` |

## Every role, at the end, free

1. **Phone width.** `resize_page` to 390 px wide and read the page once. Text cut
   off, controls pushed off-screen, two things drawn over each other → one
   `cosmetic` finding per page, with a screenshot.
2. **Sign out.**

## When this product does not have the thing

Fifty builds, fifty shapes. Some have no sign-in, one kind of user, no list of
people, no retakes. The rule from `journey.md` holds: **if you cannot become the
role or reach the step at all, that is the finding** (`blocking`, `spine: true`),
and you carry on as whoever you can be. A check that assumes something this
product simply does not have (3.5 when retakes are not offered, 4.3 with one
attempt) is skipped, not failed; say so in your three-line return.

## How to count

Checks that only need the page you are already on cost nothing. A check or probe
that needs an action (open a list, submit a form, retake a quiz) costs that
action. The budget is 20 counted actions per role; the steps above fit in
about twelve. If you run out before the probes, skip the probes, not the checks.
