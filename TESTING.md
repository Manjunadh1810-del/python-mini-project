# Testing Guide — SmartRecruit AI

## Running the tests

```bat
:: Run everything
python manage.py test

:: Run one app
python manage.py test matching

:: Run one test class
python manage.py test matching.tests.ComputeMatchIntegrationTests

:: Run one specific test
python manage.py test matching.tests.ComputeMatchIntegrationTests.test_strong_match_scores_reasonably_high
```

## Running with a coverage report

```bat
pip install coverage
coverage run --source=. --omit="*/migrations/*,manage.py,config/*,*/apps.py" manage.py test
coverage report
coverage html   :: generates htmlcov/index.html for a browsable line-by-line report
```

## Current status

**134 tests, all passing. 95% overall statement coverage.**

| App | Tests | What's covered |
|---|---|---|
| `accounts` | 20 | Registration (candidate/recruiter), duplicate username rejection, login/logout, role permission checks, Platform Admin Dashboard access control |
| `candidates` | 26 | Profile auto-creation, profile completion %, edit profile, education/experience CRUD, ownership isolation (candidate A can't edit/delete candidate B's data), skill add/remove with dedup |
| `companies` | 6 | Company creation, uniqueness, edit, delete + recreate, candidate blocked from creating a company |
| `recruiters` | 8 | Dashboard states (no company / has company), profile auto-creation, shortlisted/interview stat counts, avg match score |
| `jobs` | 20 | Posting with skills, validation (max < min experience rejected), role/ownership checks, close/reopen/delete, public listing filters (title, location, job type, work mode, skill keyword), match score shown to logged-in candidates |
| `applications` | 26 | Apply flow, duplicate-application prevention, closed-job blocking, role checks, status updates, applicant ranking, interview scheduling (with mode-specific validation), notification triggers |
| `resumes` | 27 | PDF/DOCX text extraction (using real generated files), corrupt-file handling, file type/size validation, re-upload replacing old file, skill/education/experience extraction (rule-based analyzer), sync-to-profile (no duplicates) |
| `matching` | 27 | Skill overlap scoring, TF-IDF text similarity, experience relevance, full weighted match integration, job ranking, skill gap reports + learning suggestions, recruiter-side applicant ranking |
| `notifications` | 8 | Notification creation, per-user isolation, mark read / mark all read, unread-count context processor, graceful failure handling |

## Master checklist coverage

Every item from the project's required test list is covered:

- [x] Registration
- [x] Login
- [x] Role permissions
- [x] Job creation
- [x] Job search (title, location, job type, work mode, skill keyword — each filter tested independently)
- [x] Application creation
- [x] Duplicate application prevention
- [x] Resume upload
- [x] Skill extraction
- [x] Matching algorithm
- [x] Recommendation system

## Notes on what's intentionally not covered

- `companies/views.py` and `matching/views.py` are unused boilerplate left over from `startapp` — companies' actual logic lives in `recruiters/views.py`, and matching's logic lives in `matching/services.py`. They contain no real code.
- Django admin registration files (`admin.py`) and simple `urls.py` route tables aren't unit-tested directly — they're exercised indirectly through every view test that hits those URLs.
- A handful of defensive branches (e.g. a notification silently failing on an unexpected DB error) are tested with mocks rather than real failure conditions, since triggering a genuine DB outage in a test isn't practical.

## A bug this test suite caught

While building Phase 13, the "notify candidate on status change" feature silently never fired. The test `test_status_change_notifies_candidate` failed and led to finding the cause: Django's `ModelForm.is_valid()` mutates `form.instance` **in place** during validation (via `construct_instance`), so capturing the "old" status *after* calling `is_valid()` was already too late — it had already been overwritten. The fix was to capture `old_status` right after fetching the object, before the form ever touches it. This is a good example of why testing side-effects (not just status codes) matters.
