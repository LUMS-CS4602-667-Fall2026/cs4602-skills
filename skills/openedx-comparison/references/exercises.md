# Worksheet and questions

## Worksheet

Copy this table into your notes. Fill the left column from **your** code before
you look at Open edX.

| Concept | My app: file:line and one sentence | Open edX: file:line and one sentence | The pressure that explains the difference |
|---|---|---|---|
| A user | | | |
| A role, and where it is checked | | | |
| An enrolment, and how it ends | | | |
| A course, and how it is identified | | | |
| Course content | | | |
| Draft and published | | | |
| A quiz submission, until the score is stored | | | |
| A learner's final grade | | | |
| A CSV report on the full data | | | |
| A session | | | |
| Getting data in | | | |

## Questions

Answer each with citations from both repositories.

**1. One table or two.**
Your app may keep staff and learners apart. Open edX keeps one user table.
Find a real situation in your seed data or your journey where one person needs
two roles. What would your app have to change to support it?

**2. Where the score is computed.**
Trace a quiz submission in your app from the click to the stored score. Then
trace it in Open edX from `SCORE_PUBLISHED` to `PersistentCourseGrade`. Count
the processes involved in each. What does the learner wait for in each case?

**3. Computed or stored.**
Your app may compute "highest attempt counts" on every request. Open edX stores
grades. Time your own report on the full seed data. At what number of learners
or attempts would you start storing grades, and what new problem would that
create? (Hint: overrides and freezes.)

**4. The report that blocks.**
Your report runs inside the HTTP request. Open edX queues it. What happens in
your app if two administrators press "Download CSV" on the full data at once?
What does `InstructorTask` do about the same situation?

**5. History.**
Pick one table in your app that loses information when a row is updated or
deleted. Find how Open edX keeps that history. Who needs it, and when?

**6. Read an ADR.**
Choose one ADR from `evolution.md`. Summarise in three sentences: the problem,
the decision, the cost. Then write a one-paragraph ADR for a decision you made
in your own app without writing it down.

**7. The repository is shrinking.**
Commits to `openedx-platform` fell from about 11,800 in 2013 to about 1,500 in
2025. Using themes 2, 5 and 8 in `evolution.md`, explain where the work went.
Is that a sign of decline or of design?

**8. Your next ten years.**
Your client gets 100 times more learners and a second team joins. Name the
first three Open edX decisions you would adopt, in order, and the one you would
refuse. Justify each in one sentence.

## For instructors

The concept map's left column cites the course reference build. Use it to
check that a student's mapping is plausible, never as the student's answer.
A strong answer names a pressure and a cost. A weak answer says one system is
better.
