# Labelling rubric

## Dataset status

`labels.csv` contains the active evaluation labels. The original AI-assisted
first pass is preserved separately in `labels_ai_first_pass.csv` for comparison
and is not used to calculate evaluation metrics. Validation fails while any
`[AI-DRAFT]` notes remain and warns if active labels are marked
`[AI-REVIEWED]`; those labels are not human-verified ground truth. Use
`python -m eval.label --review` to confirm or change active labels and replace
their notes with your reasoning. The available uploads do not provide
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
- Add a short reason for every label in the `notes` column, including the main evidence for positive and negative decisions. Borderline cases: decide by "would I interview this person?" and record why.
- Single labeller (the student); a second labeller is out of scope and is listed as a limitation.
- Labels form a binary relevance ranking: the evaluation metrics judge whether relevant CVs appear early, but do not claim a human ordering between two relevant candidates.
- During review, hide the current label to reduce anchoring. Use `s reason` to retain the label and add a new reason.