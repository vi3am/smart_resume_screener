# Ranking evaluation protocol

## What is being measured

Each job posting is one ranking query. The same resume pool is judged for each
posting using a binary shortlist label (`1` = would shortlist for an interview,
`0` = would not). `P@5` is relevant resumes in the first five positions divided
by five. Reciprocal rank is the inverse position of the first relevant resume;
MRR is its mean across the postings in the selected split.

The harness compares an exact random-order expectation, required-skill overlap,
semantic-only scoring, the weighted hybrid, and component-removal ablations.
Machine-readable output includes per-posting scores and the anonymized top-five
resume IDs with their reference labels.

## Labels and blinding

Use the rubric in [`data/RUBRIC.md`](./data/RUBRIC.md). The single student
reviewer labels each posting/resume pair without access to model scores and
records a short reason in `labels.csv`. `python -m eval.label --review` hides
the current label; `s reason` keeps it and adds a rationale, while `0 reason`
or `1 reason` records a replacement. A second reviewer is not currently
available, so inter-rater agreement cannot be claimed.

## Split and test-set policy

`data/split.json` assigns whole job postings to dev or test; do not tune weights
or matching rules using test results. A held-out posting previously evaluated
is no longer an untouched test case. Use new, independently held-out postings
for confirmatory evaluation. The harness requires at least one dev and one test
posting for structural validity, but warns unless there are at least three test
postings; this is a minimum warning threshold, not a guarantee of statistical
power.

## Current evidence limitations

The current data has 3 postings and 20 resume texts, but only one held-out
posting, no per-label rationales, and unresolved candidate independence and
split provenance. The documented CV set includes placeholders, short examples,
and likely duplicate variants. The test posting has only two relevant CVs.
Therefore the outputs are **exploratory** and must not be presented as a
validated accuracy estimate or evidence of generalization.

`data/review_status.json` records whether these limitations have actually been
resolved. Do not mark a review flag true without recording supporting evidence
in [`data/PROVENANCE.md`](./data/PROVENANCE.md). Do not manufacture labels or
promote synthetic examples to human ground truth.

## Commands

From `backend/`:

```sh
python -m eval.validate
python -m pytest -q eval/tests
python -m eval.run
```

`python -m eval.run` evaluates dev only. Use `python -m eval.run --final` only
after establishing a fresh, untouched test split. The test-run log deliberately
blocks repeat final runs unless `--again` is supplied; a repeated test run must
be disclosed as test-set reuse, not used as fresh confirmation.
