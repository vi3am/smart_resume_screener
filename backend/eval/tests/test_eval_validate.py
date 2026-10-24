from itertools import product

from eval.dataset import Dataset, load, validate


def test_validation_requires_review_of_ai_draft_labels():
    dataset = Dataset(
        postings={},
        cvs={},
        labels={
            ("p1", "cv_01"): "1"
        },
        split={},
        draft_labels={("p1", "cv_01")},
    )

    errors, _ = validate(dataset)

    assert any("AI drafts and require student review" in error for error in errors)


def test_labels_csv_contains_one_ai_draft_for_every_pair():
    dataset = load()

    assert set(dataset.labels) == set(product(dataset.postings, dataset.cvs))
    assert not dataset.draft_labels
    assert len(dataset.ai_reviewed_labels) == 37
    errors, warnings = validate(dataset)
    assert not errors
    assert any("reviewed by AI, not a student" in warning for warning in warnings)
