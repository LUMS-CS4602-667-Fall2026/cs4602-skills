# The three roles and the four steps

This is the **spine**: the part of the brief that was fixed for everyone. It is
not negotiable and it is not to be adapted to what the application happens to
support. Where the application cannot support it, that is the finding.

## The roles

| Role | Who you are | What you know |
|---|---|---|
| **Administrator** | You manage people and access. You have never seen this product before today. | How to read a screen. Nothing about this application |
| **Instructor** | You create and publish learning content. | Your subject. Not this application's conventions |
| **Learner** | You take a course and are assessed. | How to use a website. ⚠️ **Not** that a cart icon opens a cart, that a logo goes home, or that underlined text is a link. You look for literal words matching your goal |

The Learner is the most valuable of the three, because the Learner is the only
one entitled to no inside knowledge at all.

## The journey, in order

1. **Administrator** creates a learner's account.
2. **Instructor** publishes a course containing at least one quiz.
3. **Learner** enrols and takes that quiz.
4. **Instructor** sees the result.

Four steps, three roles, one continuous thread: **step 3 must use the account
from step 1 and the course from step 2, and step 4 must show step 3's result.**
A system where each step works alone but the thread does not join is a finding,
and it is the most common one.

## Who runs when

One role at a time, each in its own subagent, each signing out when it is done.
Steps 1 and 2 do not depend on each other, but they share one browser and one
sign-in cookie, so they still run in turn (see `SKILL.md` §3 for the only
exception).

| Phase | Role and step | Needs from earlier phases |
|---|---|---|
| A | Administrator, step 1 | nothing |
| B | Instructor, step 2 | nothing |
| C | Learner, step 3 | the learner's sign-in details from step 1; the course title (and id if shown) and quiz title from step 2 |
| D | Instructor, step 4 | the course and quiz from step 2; the learner's name from step 1 |

Each role ends by appending one line to `.cs4602/run.jsonl` (format in
`SKILL.md` §3). The main conversation passes the `created` facts into the next
brief exactly as recorded, so the learner signs in with the real email and looks
for the real course title.

**Use what the product shows, not what you were told.** The brief says the course
is called "DevOps Engineering"; if the learner's page lists it as "DevOps
Engineering (2026-Q4)", that is the same course. If it lists nothing like it,
that is a finding, provided step 2 recorded `completed`.

## When an earlier step did not finish

If the instructor recorded `gave_up` or `blocked`, there is no published course.
The learner is told so in the brief, signs in, looks at what is offered, and
records `blocked_by: instructor` without filing anything about the missing
course. The same applies to step 4 when step 3 did not finish. **A consequence
of an earlier result is not a defect.**

## Sign-in, and what to do when there isn't any

Try to act as each role separately. Many builds have one kind of user, or none.
Signing in and out does not count against your actions.

**If you cannot become a role, file that as the first finding and carry on** as
whatever user you can be:

```
title:   I cannot sign in as an administrator; there is no way to become one
spine:   true
severity: blocking
```

Then continue the step. Do not stop, and do not quietly run all four steps as
one user without saying so. Role separation is in the spine, so its absence is
the single most valuable thing you can report.

## Where to stop

- **Fifteen counted actions per role**, then record `gave_up` with the count. A
  whole form is one action; sign-in, sign-out and the evidence screenshot are
  free. Four steps in fifteen actions is still tight on purpose; a product that
  needs more than that to publish one course is itself worth a `degraded`
  finding, written in product terms.
- **Do not explore.** No wandering, no clicking things that are not on the path.
  The step is the whole scope.
- **Do not fix anything.** You are a user. Users do not patch the product.
