# Dataset provenance

- `labels.csv` is the active evaluation file and contains 60 complete pairs with
  no `[AI-DRAFT]` or `[AI-REVIEWED]` notes.
- `labels_ai_first_pass.csv` preserves the earlier AI-assisted labels. It has
  37 `[AI-REVIEWED]` notes; those archived labels are not used for evaluation.
- Git history records human relabelling of p2 and p3 on 2026-10-28. Exact
  review dates and the per-label workflow are not recorded.
- `RUBRIC.md` defines the interview-fit and required-skills criteria. The
  provenance of the split relative to the initial labelling is not established
  by Git history.
- Existing project notes say baseline scores had been seen before p1 and p2
  were relabelled, while p3 was relabelled before seeing scores. Treat metrics
  as exploratory rather than validated results.
- The candidate set includes placeholder and very short CVs and likely
  duplicate candidate variants; see `RUBRIC.md`.
- `review_status.json` is the machine-readable gate used by the evaluation
  harness. Its review flags intentionally remain false until candidate
  independence/source quality, blind human labels, and split provenance are
  supported by review evidence. Do not edit the flags to true without that
  evidence.
- The label CLI now hides the existing label during `--review`. Enter `s reason`
  to preserve a label while recording a fresh rationale, or enter `0 reason` /
  `1 reason` to replace it. New and changed labels require a rationale.
- The random baseline is now calculated as an exact expectation, not estimated
  by a finite number of random shuffles. Results include anonymized top-five
  CV IDs and binary relevance so the reported P@5 can be checked against the
  reference labels.
- With the current three postings and one held-out posting, the test set is
  only one query. A larger, newly gathered candidate set and multiple
  independently held-out postings are required before claiming ranking
  accuracy or generalization.
- See [`../METHODOLOGY.md`](../METHODOLOGY.md) for the metrics, blind-label
  process, split policy, and commands. The harness marks results exploratory
  until the review-status gates and data-quality warnings are resolved.