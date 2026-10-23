# How Open edX changed shape

Sources: `git log` and release tags of `openedx/openedx-platform`, read on
2026-10-22 at commit `229f7e1a`. ADR paths are relative to the repository root.

## Activity

The first commit is dated 2011-12-07. There are 68,834 commits on `master` from
1,476 distinct author emails. 239 of those emails committed in 2025–2026.

| Year | Commits | Year | Commits |
|---|---|---|---|
| 2012 | 8,248 | 2019 | 4,587 |
| 2013 | 11,807 | 2020 | 4,086 |
| 2014 | 7,470 | 2021 | 3,834 |
| 2015 | 6,961 | 2022 | 1,752 |
| 2016 | 5,172 | 2023 | 1,957 |
| 2017 | 4,697 | 2024 | 1,880 |
| 2018 | 3,727 | 2025 | 1,476 |

2026 had 1,080 commits by 22 October. Ask yourself why activity in *this*
repository falls while the platform keeps growing. The ADRs below answer it.

## Named releases

A release every six months or so, alphabetical, named after trees. Dates are
the commit date of each release tag.

| Release | Date | Release | Date |
|---|---|---|---|
| Aspen | 2014-10-20 | Juniper | 2020-06-05 |
| Birch | 2015-02-19 | Koa | 2020-12-09 |
| Cypress | 2015-08-03 | Lilac | 2021-06-08 |
| Dogwood | 2016-02-09 | Maple | 2021-12-16 |
| Eucalyptus | 2016-08-26 | Nutmeg | 2022-06-08 |
| Ficus | 2017-02-15 | Olive | 2022-12-08 |
| Ginkgo | 2017-08-10 | Palm | 2023-06-12 |
| Hawthorn | 2018-08-03 | Quince | 2023-12-11 |
| Ironwood | 2019-03-16 | Redwood | 2024-06-17 |
| | | Sumac | 2024-12-13 |

Release tags in this repository stop at Sumac. The rename from `edx-platform` to
`openedx-platform` is reflected in commit `5a411c20b`, dated 2026-01-26.

## The decisions, by theme

There are 88 ADR files. These are the ones that explain the shape.

**1. Split the monolith by what it is for.**
LMS delivers learning; CMS (Studio) authors and publishes it. Data flows one
way, at an explicit publish step.
`docs/decisions/0005-studio-lms-subdomain-boundaries.rst`,
`docs/decisions/0013-cms-vs-studio.rst`.

**2. Stop reaching into other apps' tables.**
Apps talk through a Python `api.py`, never each other's models. New apps must
justify living in the core at all.
`docs/decisions/0002-inter-app-apis.rst`, `docs/decisions/0014-justifying-new-apps.rst`,
`docs/decisions/0010-extract-enrollment-python-api.rst`.

**3. Keep the LMS away from the content store.**
Read-optimised copies (course overviews, dates) are filled at publish time.
`docs/decisions/0001-courses-in-lms.rst`, `docs/decisions/0011-limit-modulestore-use-in-lms.rst`,
`xmodule/docs/decisions/0001-move-due-dates-to-db.rst`.

**4. Give XBlock a smaller job.**
Blocks keep the unit level and below. Navigation, grading and scheduling become
their own systems. `docs/decisions/0006-role-of-xblock.rst`.

**5. Move the frontend out.**
A 2017 plan to keep Python thin led to the MFE framework. The decision since is
that all frontend code leaves this repository.
`docs/decisions/0000-static-asset-plan.rst`,
`docs/decisions/0023-frontend-code-and-eslint-removal.rst`,
`docs/decisions/0035-canonical-mfe-configuration-endpoint.rst`.

**6. Persist what is expensive to compute.**
Grades are stored, overrides kept apart, old courses frozen.
`lms/djangoapps/grades/docs/decisions/0003-persistent-grades.rst` to `0006-…`.

**7. Tokens instead of sessions for machines.**
OAuth2 with signed JWTs, scopes and organization filters.
`openedx/core/djangoapps/oauth_dispatch/docs/decisions/0002-…` to `0017-…`,
`docs/decisions/0034-unify-auth-oauth2-dot-v2.rst`.

**8. Pay down the oldest choices.**
Remove the MongoDB dependency, dissolve sub-projects, simplify settings.
`xmodule/docs/decisions/0002-remove-mongodb-dependency.rst`,
`docs/decisions/0015-sub-project-dissolution.rst`,
`docs/decisions/0022-settings-simplification.rst`.

**9. Make the APIs consistent.**
A 2026 wave of ADRs standardises serializers, permissions, errors, pagination,
filtering, versioning and URLs for REST APIs. `docs/decisions/0025-…` to `0038-…`.
Two of the 0025–0027 files are about other topics; check the title first.
