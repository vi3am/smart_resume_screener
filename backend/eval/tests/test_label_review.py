import csv
import json

from eval import label


def test_review_mode_is_blind_and_replaces_draft_marker(tmp_path, monkeypatch, capsys):
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
    output = capsys.readouterr().out
    assert "Current label" not in output
    assert "[AI-DRAFT]" not in output

    with labels_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert rows[0]["label"] == "0"
    assert rows[0]["notes"] == "Human-reviewed: not relevant"


def test_review_can_keep_label_and_record_rationale(tmp_path, monkeypatch):
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
        "posting_id,cv_id,label,notes\np1,cv_01,1,\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(label, "DATA_DIR", data_dir)
    monkeypatch.setattr(label, "LABELS", labels_path)
    monkeypatch.setattr("sys.argv", ["eval.label", "--review", "p1"])
    monkeypatch.setattr("builtins.input", lambda _: "s Relevant domain experience and 3/5 skills")

    assert label.main() == 0

    with labels_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert rows[0]["label"] == "1"
    assert rows[0]["notes"] == "Relevant domain experience and 3/5 skills"


def test_new_labels_require_a_reason(tmp_path, monkeypatch, capsys):
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

    monkeypatch.setattr(label, "DATA_DIR", data_dir)
    monkeypatch.setattr(label, "LABELS", labels_path)
    monkeypatch.setattr("sys.argv", ["eval.label", "p1"])
    answers = iter(["1", "1 Has relevant work and required skills"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    assert label.main() == 0
    assert "Add a short human rationale" in capsys.readouterr().out

    with labels_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert rows[0]["label"] == "1"
    assert rows[0]["notes"] == "Has relevant work and required skills"
