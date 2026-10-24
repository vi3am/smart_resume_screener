import csv
import json

from eval import label


def test_review_mode_replaces_draft_and_removes_draft_marker(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    cv_dir = data_dir / "cvs"
    cv_dir.mkdir(parents=True)
    (data_dir / "postings.json").write_text(
        json.dumps(
            [
                {
                    "id": "p1",
                    "title": "Test posting",
                    "description": "Test description",
                    "required_skills": ["communication"],
                    "min_years_experience": 0,
                    "min_education_level": "high_school",
                }
            ]
        ),
        encoding="utf-8",
    )
    (cv_dir / "cv_01.txt").write_text("Candidate experience", encoding="utf-8")
    labels_path = data_dir / "labels.csv"
    labels_path.write_text(
        "posting_id,cv_id,label,notes\n"
        'p1,cv_01,1,"[AI-DRAFT] proposed, review required"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(label, "DATA_DIR", data_dir)
    monkeypatch.setattr(label, "LABELS", labels_path)
    monkeypatch.setattr("sys.argv", ["eval.label", "--review", "p1"])
    monkeypatch.setattr("builtins.input", lambda _: "0 Human-reviewed: not relevant")

    assert label.main() == 0

    with labels_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert rows[0]["label"] == "0"
    assert rows[0]["notes"] == "Human-reviewed: not relevant"
