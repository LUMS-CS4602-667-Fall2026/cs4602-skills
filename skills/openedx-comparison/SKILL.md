---
name: openedx-comparison
license: MIT
description: >
  Use when studying software architecture by comparing the LMS you built in this
  course with Open edX, an LMS that has grown in public since 2011. Walks you
  through mapping every table, role and request path in your app to its Open edX
  counterpart, reading the decision records that explain why Open edX changed
  shape, and answering the session's questions with evidence from both codebases.
---

# Open edX comparison

You built a learning platform in a few hours: one process, one database file,
three dashboards. Open edX solves the same problem for millions of learners and
has 68,000+ commits behind it. **Every difference between the two is a decision
someone made under pressure.** This exercise is about finding those decisions
and saying when your app would need them too.

**You are a reader with a notebook, not a reviewer with an opinion.** "Open edX
is better" and "Open edX is bloated" are both non-answers. A good answer names
the pressure (scale, many teams, many operators, ten years of courses that must
still open) and the cost the design pays for it.

## 1 — Get Open edX at the pinned revision

Every citation in this skill is pinned to one commit so that the line numbers
match what you open.

```bash
git clone --filter=tree:0 --no-checkout --single-branch --branch master \
  https://github.com/openedx/openedx-platform .openedx
cd .openedx
git sparse-checkout set --cone common/djangoapps/student lms/djangoapps/grades \
  lms/djangoapps/instructor_task lms/djangoapps/courseware lms/envs cms/envs \
  openedx/core/djangoapps/content/course_overviews \
  openedx/core/djangoapps/oauth_dispatch cms/djangoapps/contentstore xmodule docs
git checkout 229f7e1a078f11406c47fa8487f8e1dab37f488b
```

Set the folders before the checkout. In the other order, git downloads the
whole tree.

The full repository is large and the download can drop half-way. If it fails
with `early EOF`, delete `.openedx` and run the clone again. Add `.openedx/` to
your `.gitignore`: you are reading it, not vendoring it.

The repository was called `openedx/edx-platform` until January 2026. Old links
and blog posts use that name; GitHub redirects them.

## 2 — Map your own app first

Before you open a single Open edX file, write down your own app's answers. Use
your own repository, not the one you remember:

- every table in your schema, and the one sentence that says what a row is
- every role, and where the code checks it
- what happens, in order, from "learner clicks Submit" to "the score is stored"
- how a report is produced, and how long it takes on the full seed data

Put it in the left column of the worksheet in
[`references/exercises.md`](references/exercises.md). **If you cannot cite the
file and line, you have not found it yet.**

## 3 — Walk the concept map

Open [`references/concept-map.md`](references/concept-map.md). For each row:

1. Open the Open edX file at the cited lines and read the surrounding code. The
   citation is a starting point, not the whole answer.
2. Write one sentence: *what does Open edX store or do here that my app does not,
   and what problem would make me need it?*
3. If the citation no longer matches what you see, say so. Do not invent a
   replacement.

## 4 — Read the history

Open [`references/evolution.md`](references/evolution.md). It dates the releases
and groups the architecture decision records (ADRs) by theme. **Read at least
three ADRs in full.** An ADR is the only place a codebase writes down *why*;
the code only shows *what*.

## 5 — Answer the questions

Work through the questions in [`references/exercises.md`](references/exercises.md).
Every answer cites `path:line` in **both** repositories, or states plainly that
one side has no equivalent.

## 6 — Draw it (optional)

If your agent has the archify skill (`npx skills add tt-a1i/archify`), ask it to
draw your app's architecture and then the same slice of Open edX, for example
"the path a quiz submission takes until a grade is stored". Two diagrams at the
same abstraction level make the difference visible in a way prose does not.

## Rules for the agent helping you

| If you catch yourself… | Then |
|---|---|
| Answering from memory about Open edX | Open the file. Ten years of history means your memory is probably of an older version |
| Citing a line you did not open | Open it, or write "not verified" |
| Calling one design good and the other bad | Name the pressure and the cost instead |
| Reading the whole Open edX repository | Stop. The concept map is the reading list. Wander only to answer a specific question |
| Changing the student's app to look like Open edX | Stop. This is a reading exercise. Nothing gets refactored |
| Using the course reference build's answers as the student's | The student's app is different. Map *their* code |
