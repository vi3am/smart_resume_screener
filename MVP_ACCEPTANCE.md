# MVP scope and acceptance criteria

This document records the buildable MVP and measurable checks for proposal
feedback items #1, #3, #7 and #13. It describes current app behavior; passing
automated checks do not establish that ranking is a valid hiring decision.

## MVP scope (#1)

The MVP is one recruiter account managing job descriptions and candidate resume
pipelines:

- Recruiter registration/login and per-owner access control.
- Create, view, and edit job descriptions with required skills, minimum years
  of experience, and minimum education level.
- Upload up to twenty PDF/DOCX resumes per batch, at no more than 5 MiB each;
  extract resume text and display parsed candidate details.
- Score processed resumes against a job and show an ordered ranking, the
  component scores, and matched/missing required skills.
- Search/filter ranked candidates, manually select a shortlist, and export
  that selection as CSV.

Large-volume ingestion, OCR, multi-language support, complex role management,
advanced comparisons, analytics, email notifications, and Excel/PDF export
remain out of scope. The MVP's batch limit is twenty; this is not large-volume
bulk processing.

## Scoring contract (#3)

For each resume, component values are percentages in `[0, 100]`. The default
overall score is the weighted mean:

```text
overall =
  0.40 * required-skill-match
+ 0.20 * experience-match
+ 0.10 * education-match
+ 0.30 * semantic-match
```

The weights sum to `1.00`. The UI shows the overall score and all four
components rather than hiding them behind one number. The API records the
weights used for each scoring run.

- **Required skills:** equal-weight match rate against the job's explicitly
  entered `required_skills`.
- **Experience:** capped ratio of extracted years to `min_years_experience`;
  a job requiring zero years receives 100 for this component.
- **Education:** degree-level comparison with partial credit for lower or
  in-progress levels.
- **Semantic:** sentence-transformer similarity between the job query
  (title, description, required skills) and up to three most relevant resume
  section chunks, mapped to 0–100 using the fixed cosine-similarity bounds
  `0.05` and `0.60`.

The current job model has no separate preferred-skills or certification
criterion, and the UI does not let recruiters configure weights. These are not
silently treated as implemented MVP features. Missing extracted experience or
education is scored as zero when a requirement is present; absent required
skills are shown as missing. If the job requirements change, the previous
ranking is stale and must be rerun before it can be fetched as the latest run.

## Skill matching contract (#7)

Resume parsing returns skills listed in a resume's skill section (including
unlisted terms) and recognizes a bounded built-in vocabulary elsewhere in the
text. Ranking does **not** rely on general-purpose spaCy NER for skills: it
matches the job's recruiter-entered required-skill list against resume text
using normalized, case-insensitive, word/phrase matching and explicit aliases.
Examples include `JS` → `JavaScript` and `Postgres` → `PostgreSQL`.

The ranking breakdown exposes matched and missing required skills. Parsed
resume skills are visible to the recruiter, but editing extracted candidate
skills is not currently supported. The alias map and parser vocabulary are
curated code data, not a complete universal skills taxonomy.

## Acceptance criteria (#13)

| Requirement | Measurable pass condition | Evidence |
|---|---|---|
| Job lifecycle | Recruiter can create, view, and edit nonblank title/description, skills, experience, and education; another recruiter cannot access the job. | `backend/tests/test_api_routes.py` |
| Resume upload | A batch of 20 files is accepted; batch of 21 is rejected. Valid PDF/DOCX with matching MIME/content is accepted; unsupported, malformed, oversized, or scanned files fail with a clear reason. | `backend/tests/test_resume_batch.py`, `backend/tests/test_resume_privacy.py` |
| Resume ownership | No-token requests return 401; cross-recruiter job/resume access is denied. | `backend/tests/test_auth_security.py`, `backend/tests/test_api_routes.py`, `backend/tests/test_resume_privacy.py` |
| Resume details | Parser returns available email/phone/name, listed or recognized skills, experience and education; missing fields remain absent rather than fabricated. | `backend/tests/test_parser_fields_regression.py`, `backend/tests/test_alembic_env_regression.py` |
| Skill matching | Alias and case variants match; substring lookalikes do not; matched/missing lists agree with the skill score. | `backend/tests/test_scoring.py` |
| Score range/formula | All component and overall scores are within 0–100; default weights are exactly 40/20/10/30 and sum to 100%. | `backend/tests/test_scoring.py` |
| Ranking | Results are ordered by overall score descending with a stable tie break; a changed job makes the prior run unavailable as latest until scoring is rerun. | `backend/app/services/scoring_runs.py`, `backend/tests/test_api_routes.py` |
| Explainability | Every result includes overall and four component scores, plus matched/missing required skills. | `backend/tests/test_api_routes.py`, `backend/app/schemas/scoring.py` |
| Search, filter, export | Search matches candidate name, filename, and skill; score threshold is honored; CSV contains only selected candidates and neutralizes spreadsheet formulas. | `frontend/src/utils/candidateResults.test.js` |
| Demonstration performance | Text-based PDF/DOCX parsing completes within 10 seconds on the actual demonstration machine. | **Not yet verified.** Time representative files on the demo machine and record the hardware and results before claiming this target. |
| Ranking validity | Human-labelled, permissioned data is independently reviewed and evaluation reports P@5/MRR on a fresh held-out set. | **Not yet met.** See [`backend/eval/METHODOLOGY.md`](./backend/eval/METHODOLOGY.md); current evaluation remains exploratory. |

Run backend tests only after setting `TEST_DATABASE_URL` to a dedicated
PostgreSQL database whose name ends with `_test`:

```sh
cd backend
.venv/bin/python -m pytest -q
```

Run the frontend checks from `frontend/`:

```sh
node --test src/utils/candidateResults.test.js
npm run lint
npm run build
```

Evaluation-dataset checks are separate:

```sh
cd backend
.venv/bin/python -m eval.validate
.venv/bin/python -m pytest -q eval/tests
```
