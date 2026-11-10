import pytest

from eval.metrics import (
    expected_random_metrics,
    mean_reciprocal_rank,
    precision_at_k,
    rank_by_score,
    reciprocal_rank,
)


def test_precision_at_k_counts_hits_in_top_k():
    assert precision_at_k(["a", "b", "c", "d", "e", "f"], {"a", "c", "f"}, k=5) == 2 / 5


def test_precision_at_k_divides_by_k_even_for_short_lists():
    assert precision_at_k(["a", "b"], {"a", "b"}, k=5) == 2 / 5


def test_reciprocal_rank():
    assert reciprocal_rank(["x", "y", "a"], {"a"}) == 1 / 3
    assert reciprocal_rank(["x", "y"], {"a"}) == 0.0


def test_mrr_averages_over_postings():
    rankings = {"p1": ["a", "b"], "p2": ["x", "a"]}
    relevant = {"p1": {"a"}, "p2": {"a"}}
    assert mean_reciprocal_rank(rankings, relevant) == 0.75


def test_rank_by_score_breaks_ties_by_id():
    assert rank_by_score({"b": 1.0, "a": 1.0, "c": 2.0}) == ["c", "a", "b"]


def test_random_baseline_is_exact_for_one_relevant_candidate():
    p_at_1, expected_rr = expected_random_metrics(["a", "b"], {"a"}, k=1)

    assert p_at_1 == 0.5
    assert expected_rr == 0.75


def test_random_baseline_uses_only_candidates_in_the_ranking():
    p_at_5, expected_rr = expected_random_metrics(["a", "b", "c"], {"a", "outside"}, k=5)

    assert p_at_5 == pytest.approx(0.2)
    assert expected_rr == pytest.approx(11 / 18)


def test_random_baseline_rejects_non_positive_k():
    with pytest.raises(ValueError, match="k must be positive"):
        expected_random_metrics(["a"], {"a"}, k=0)