from eval.metrics import mean_reciprocal_rank, precision_at_k, rank_by_score, reciprocal_rank


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