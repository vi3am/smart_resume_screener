import csv
import re

from eval.dataset import DATA_DIR


def _rows(name):
    with open(DATA_DIR / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_first_pass_record_is_kept_and_complete():
    rows = _rows("labels_ai_first_pass.csv")
    assert len({(r["posting_id"], r["cv_id"]) for r in rows}) == 60


def test_final_labels_are_complete_and_not_marked_ai():
    rows = _rows("labels.csv")
    assert len(rows) == 60
    assert {r["label"].strip() for r in rows} <= {"0", "1"}
    assert not [r for r in rows if re.search(r"\bai[- ]?reviewed\b", r.get("notes") or "", re.I)]