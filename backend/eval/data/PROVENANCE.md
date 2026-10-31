# Dataset provenance

- Labelling by: Not recorded. `labels.csv` currently has 23 rows without an AI-status prefix and 37 marked `[AI-REVIEWED]`.
- Labelling dates: Exact review dates are not recorded. Git history shows the dataset was first committed on 2026-10-18 and labels were last changed on 2026-10-23.
- Method: `RUBRIC.md` defines the interview-fit and required-skills criteria and says to label from anonymized CVs and postings without viewing model scores. The exact workflow used for each row is not recorded.
- Model scores seen while labelling: Not recorded.
- `split.json` fixed before labelling: Not recorded. The split and initial labelled dataset first appear in the same 2026-10-18 commit, so the repository history cannot establish their order.
- Anything unusual: 37 labels remain marked `[AI-REVIEWED]`; these are not human-verified ground truth. `RUBRIC.md` also notes placeholder and very short CVs, plus likely duplicate candidate variants. Treat ranking metrics as exploratory, not validated results, until the labels and candidate set are reviewed.
First-pass labels were produced with AI assistance (37 of 60 marked AI-reviewed) and kept unchanged in
labels_ai_first_pass.csv. Final labels were assigned by me, by hand, on <dates>, from the anonymized CVs
and RUBRIC.md, without model scores. Agreement with the AI first pass: <X%>, kappa <Y>.
Limitation: p1 and p2 were relabelled after I had seen baseline scores for them; p3 was relabelled
before any score for it existed.