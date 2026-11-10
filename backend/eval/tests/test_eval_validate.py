from eval.dataset import Dataset, evaluation_readiness_reasons, validate


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


def test_validation_warns_when_label_rationales_are_missing():
    dataset = Dataset(
        postings={},
        cvs={},
        labels={("p1", "cv_01"): "1"},
        split={},
        label_notes={("p1", "cv_01"): ""},
    )

    _, warnings = validate(dataset)

    assert any("no recorded human rationale" in warning for warning in warnings)


def test_evaluation_readiness_stays_exploratory_without_review_evidence():
    dataset = Dataset(
        postings={"p1": {}},
        cvs={"cv_01": "resume"},
        labels={("p1", "cv_01"): "1"},
        split={"dev": [], "test": ["p1"]},
    )

    reasons = evaluation_readiness_reasons(dataset)

    assert any("candidate independence" in reason for reason in reasons)
    assert any("blind human review" in reason for reason in reasons)
    assert any("split's independence" in reason for reason in reasons)
