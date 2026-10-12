# The three roles and the four steps

This is the **spine** — the part of the brief that was fixed for everyone. It is
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

## Sign-in, and what to do when there isn't any

Try to act as each role separately. Many builds have one kind of user, or none.

**If you cannot become a role, file that as the first finding and carry on** as
whatever user you can be:

```
title:   Cannot act as an administrator — no way to sign in as one
spine:   true
severity: blocking
```

Then continue the journey. Do not stop, and do not quietly run all four steps as
one user without saying so — role separation is in the spine, so its absence is
the single most valuable thing you can report.

## Where to stop

- **Ten actions per role**, then record the outcome. Four steps in ten actions is
  deliberately tight; a system that needs more than ten clicks to create one user
  is itself worth a finding.
- **Do not explore.** No wandering, no clicking things that are not on the path.
  The journey is the whole scope.
- **Do not fix anything.** You are a user. Users do not patch the product.
