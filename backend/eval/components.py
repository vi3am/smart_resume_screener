"""Compute the four component scores once per (posting, CV). Weights are applied later."""
from app.services.scoring import ScoreResult, score_cv
from eval.config import AS_OF
from eval.dataset import Dataset


def compute(ds: Dataset, posting_ids: list[str]) -> dict[str, dict[str, ScoreResult]]:
    return {
        pid: {cv_id: score_cv(ds.postings[pid], text, as_of=AS_OF)
            for cv_id, text in sorted(ds.cvs.items())}
        for pid in posting_ids
    }