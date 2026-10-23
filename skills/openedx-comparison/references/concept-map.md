# Concept map: a course LMS and Open edX

Open edX paths are pinned to commit `229f7e1a078f11406c47fa8487f8e1dab37f488b`
of `openedx/openedx-platform`. The left column is the **course reference build**
(paths under `lms/src/` in the instructor's demo repo). Your own app will differ:
map yours, then use these rows to find the Open edX side.
The reference-build paths are for the instructor. That repository is private, so
students cite their own code instead.

`openedx/envs/common.py` is outside the sparse checkout. Read it with
`git show HEAD:openedx/envs/common.py | sed -n '<from>,<to>p'`.

## The headline

| | Reference build | Open edX |
|---|---|---|
| Processes | One Node.js process, `node:http` | Two Django projects, LMS and CMS (Studio), plus Celery workers and React micro-frontends (MFEs). `README.rst:17-28`, `docs/decisions/0013-cms-vs-studio.rst:23-27` |
| Data | One SQLite file, 9 tables | MySQL for relational data, MongoDB for course content, Memcached for cache, a Celery broker, optional Elasticsearch. `openedx/envs/common.py:309-420,863-869,1849-1914`, `lms/envs/production.py:326-336` |
| Size | About 2,500 lines | 9,280 tracked files, 4,459 of them Python |
| Extension | Edit the source | Entry-point plugins: 33 built-in XBlocks, course tabs, LMS and CMS apps. `pyproject.toml:419-537` |

## People and access

| Concept | Reference build | Open edX | What changed and why |
|---|---|---|---|
| User | Two tables, `staff` and `learners`. `lms/src/db.js:27-83` | One Django `auth_user` for everyone, plus a 1:1 `UserProfile`. `common/djangoapps/student/models/user.py:411-443` | A role is something a person *has*, not something they *are*. One person can teach one course and take another |
| Role | A `role` column on `staff`. `lms/src/db.js:27-37` | Rows in `CourseAccessRole(user, org, course_id, role)`. `common/djangoapps/student/models/user.py:1083-1103`. Role classes: `common/djangoapps/student/roles.py:731-882` | Roles are scoped per course or per organization, so the same person holds different powers in different places |
| Client-scoped admin | `staff.client_id`, checked in each admin query. `lms/src/api.js:84-145` | The `org` column on the role row (`roles.py:404-414`). For API clients, ADR 0007 puts the org in the token: `openedx/core/djangoapps/oauth_dispatch/docs/decisions/0007-include-organizations-in-tokens.rst:64-100` | Scope moves from "who you are" to "what this grant allows" |
| Corporate client | `clients` table with seats. `lms/src/db.js:17-25` | Not in this repository. Organizations come from the external `edx-organizations` package, enterprise customers from the `enterprise` plugin. `lms/envs/common.py:2099-2100` | When a concern serves only some operators, it leaves the core. See ADR 0014 |
| Who taught when | `course_staff.assigned_on / unassigned_on`. `lms/src/db.js:51-58` | Removing a role deletes the row. `CourseAccessRoleHistory` keeps the audit trail. `user.py:1145-1172` | The live table stays small and fast. History lives beside it |

## Enrolment

| Concept | Reference build | Open edX | What changed and why |
|---|---|---|---|
| Enrolment row | `enrolments` with `withdrawn_on` and `outcome`. `lms/src/db.js:85-95` | `CourseEnrollment(user, course, mode, is_active)`, unique per user and course. `common/djangoapps/student/models/course_enrollment.py:298-354` | Withdrawal is `is_active=False` on the same row (`:853-879`). Outcome is not stored on the enrolment; it comes from grades |
| Enrolment history | None | django-simple-history table, every change. `course_enrollment.py:336-342` | Support staff must answer "what happened to this learner" years later |
| Who enrolled them | `enrolled_by` column | `ManualEnrollmentAudit` with reason and state transition. `course_enrollment.py:82-103` | |
| Paid tracks | None | Modes such as audit, verified, professional, credit, masters | The business model became part of the data model |

## Courses and content

| Concept | Reference build | Open edX | What changed and why |
|---|---|---|---|
| Course identity | A slug, `title-cohort`. `lms/src/api.js:230-250` | An opaque `CourseKey` such as `course-v1:Org+Course+Run`. `openedx/core/djangoapps/content/course_overviews/models.py:74`, `xmodule/docs/decisions/0002-remove-mongodb-dependency.rst:24` | Org, course and run are separate parts, so the same course can run many times |
| Course content | `course_pages` rows with text. `lms/src/db.js:107-114` | A tree of XBlocks in the modulestore: course, chapter, sequential, vertical, block. `xmodule/modulestore/xml_importer.py:1328-1341` | Content is freeform per block type, which is why it went to MongoDB. `xmodule/docs/decisions/0002-remove-mongodb-dependency.rst:7-11` |
| Course metadata for the LMS | Read straight from `courses` | `CourseOverview`, a MySQL cache of course metadata refreshed on publish. `openedx/core/djangoapps/content/course_overviews/__init__.py:1-20`, `openedx/core/djangoapps/content/course_overviews/signals.py:32-45` | Reading the content store for every dashboard was too slow. `docs/decisions/0011-limit-modulestore-use-in-lms.rst:14-58` |
| Draft and published | A `status` column on the course | Separate draft and published branches, each an immutable versioned structure. `xmodule/modulestore/docs/split-mongo.rst:52-119` | Authors edit while learners keep seeing the last published version |
| Due dates | `assessments.due_on` | Moved out of the content into database tables with per-learner overrides. `xmodule/docs/decisions/0001-move-due-dates-to-db.rst:12-59` | Reading dates from content meant walking the whole course tree |
| Bulk import | Stream 8 CSVs, one transaction per file, reject duplicates. `lms/src/import.js:54-264` | OLX tarball import and export as Celery tasks. `cms/djangoapps/contentstore/tasks.py:342-380,545-560` | Import is async and validated, and importing an existing key updates the course instead of failing. `xml_importer.py:622-653` |

## Assessment and grading

| Concept | Reference build | Open edX | What changed and why |
|---|---|---|---|
| Learner state per problem | One `attempts` row per submission. `lms/src/db.js:97-105` | One mutable `StudentModule` row per learner per block, with a JSON state blob. `lms/djangoapps/courseware/models.py:78-121` | Each block type keeps its own state shape. Attempt history lives inside the blob. `xmodule/capa_block.py:186-212` |
| Scoring | Inline, inside the HTTP request. `lms/src/api.js:418-468` | The block publishes a score event. Signal handlers queue a Celery task, which recomputes subsection and course grades. `lms/djangoapps/grades/signals/handlers.py:152-265`, `lms/djangoapps/grades/tasks.py:173-353` | Recomputing a course grade is too slow to do while the learner waits |
| Best attempt | `SELECT MAX(score)` on each request | `grading_method` on the problem: Last, First, Highest or Average. `xmodule/capa_block.py:198-212` | A course rule became a per-problem setting |
| Stored grades | None. Computed on read | `PersistentSubsectionGrade` and `PersistentCourseGrade`. `lms/djangoapps/grades/models.py:295-357,558-597`. ADR: `lms/djangoapps/grades/docs/decisions/0003-persistent-grades.rst` | Reads go straight to the stored row: `lms/djangoapps/grades/course_grade_factory.py:27-47`. ADR 0003's full rationale sits on an external wiki page, not in this repository |
| Grade changes after the fact | `UPDATE attempts SET score` | Overrides in their own table, applied on display, with history. `lms/djangoapps/grades/docs/decisions/0006-overrides-applied-separately.rst:16-39` | An override must never destroy the original score |
| Grade freeze | None | Grading stops 30 days after a course ends. `lms/djangoapps/grades/docs/decisions/0005-grade-freeze.rst:18-38` | Old courses must stop changing |

## Reports

| Concept | Reference build | Open edX | What changed and why |
|---|---|---|---|
| CSV report | One SQL query per request, CSV streamed back. `lms/src/api.js:471-535` | An `InstructorTask` row and a Celery task, batches of 100 learners, file uploaded to a report store. `lms/djangoapps/instructor_task/api_helper.py:442-469`, `lms/djangoapps/instructor_task/tasks_helper/grades.py:280-415` | The request returns at once. The report is downloaded later |
| Scheduled reports | None | Scheduled tasks kept in the database and queued by cron, not held in Celery. `lms/djangoapps/instructor_task/docs/decisions/001-scheduling-instructor-tasks.rst:17-54` | |

## Sessions and authentication

| Concept | Reference build | Open edX | What changed and why |
|---|---|---|---|
| Sessions | A `Map` in process memory. A restart signs everyone out. `lms/src/auth.js:3-46` | Django sessions in the shared cache, behind `SafeSessionMiddleware`. `openedx/envs/common.py:123-130`, `lms/envs/common.py:1241-1250` | Many server processes must share one session store |
| Passwords | Plain text, compared directly. `lms/src/auth.js:48-101` | Django's default password hashers and validators. `openedx/envs/common.py:178-201` | |
| API and frontend auth | The same session cookie | OAuth2 with signed JWTs. For MFEs the JWT travels in two cookies. `openedx/core/djangoapps/oauth_dispatch/docs/decisions/0003-use-jwt-as-oauth-tokens-remove-openid-connect.rst`, `.../0009-jwt-in-session-cookie.rst:41-80` | Separate frontends and mobile apps need a token they can carry |
