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