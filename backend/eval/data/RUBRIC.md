# Labelling rubric

## Dataset status

`labels.csv` distinguishes proposed `[AI-DRAFT]` labels from labels reviewed
by AI (`[AI-REVIEWED]`) and labels reviewed by the student (no status prefix).
AI-reviewed labels are not human-verified ground truth. Validation fails while
any `[AI-DRAFT]` notes remain and warns when AI-reviewed labels remain. Metrics
based on AI-reviewed labels are exploratory; do not report them as validated
results. Use `python -m eval.label --review` to confirm or change labels and
replace their notes with your reasoning. The available uploads do not provide
20 independent, usable CVs:
`cv_02.txt` and `cv_08.txt` are placeholder templates, `cv_06.txt`, `cv_19.txt`,
and `cv_20.txt` are very short samples, and some other files appear to be
variants of the same candidate (`cv_03`/`cv_17`/`cv_18` and
`cv_11`/`cv_15`/`cv_16`). Do not report ranking metrics as a valid evaluation
until the candidate set and all labels have been reviewed.

Label 1 (relevant) if a recruiter would shortlist this CV for an interview for the posting:
- it shows work, internship or substantial project experience in the posting's own domain, and
- it shows roughly half or more of the required skills, stated directly or by a clear equivalent.

Label 0 otherwise.

Rules:
- Minimum years and education are guidance, not hard cut-offs. Judge the overall fit.
- Ignore name, gender, photo, layout and writing polish.
- Label from the anonymized CV text and the posting only. Never look at any model score while labelling.
- Borderline cases: decide by "would I interview this person?" and note the reason in the notes column.
- Single labeller (the student); a second labeller is out of scope and is listed as a limitation.