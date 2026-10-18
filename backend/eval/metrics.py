"""Ranking metrics. Pure functions, no I/O."""
from collections.abc import Iterable, Sequence


def rank_by_score(scores: dict[str, float]) -> list[str]:
    """Highest score first; ties broken by id so runs are reproducible."""
    return [cv for cv, _ in sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))]


def precision_at_k(ranked: Sequence[str], relevant: Iterable[str], k: int = 5) -> float:
    if k <= 0:
        raise ValueError("k must be positive")
    rel = set(relevant)
    return sum(1 for cv in ranked[:k] if cv in rel) / k


def reciprocal_rank(ranked: Sequence[str], relevant: Iterable[str]) -> float:
    rel = set(relevant)
    for position, cv in enumerate(ranked, start=1):
        if cv in rel:
            return 1.0 / position
    return 0.0


def mean_reciprocal_rank(
    rankings: dict[str, Sequence[str]], relevant: dict[str, set[str]]
) -> float:
    values = [reciprocal_rank(rankings[pid], relevant[pid]) for pid in rankings]
    return sum(values) / len(values) if values else 0.0