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



