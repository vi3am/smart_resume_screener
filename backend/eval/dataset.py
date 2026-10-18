"""Load and validate the labelled dataset in eval/data/."""
import csv
import json
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path

from app.core.education import EDUCATION_LEVELS
from eval.pii import find_pii

DATA_DIR = Path(__file__).parent / "data"
EXPECTED_POSTINGS = 3
EXPECTED_CVS = 20
REQUIRED_POSTING_KEYS = {
    "id", "title", "description", "required_skills",
    "min_years_experience", "min_education_level",
}


@dataclass
class Dataset:
    postings: dict[str, dict]
    cvs: dict[str, str]
    labels: dict[tuple[str, str], str]
    split: dict
    duplicate_labels: list[tuple[str, str]] = field(default_factory=list)

    def relevant(self, posting_id: str) -> set[str]:
        return {cv for (pid, cv), y in self.labels.items() if pid == posting_id and y == "1"}


def load(data_dir: Path = DATA_DIR) -> Dataset:
    postings_list = json.loads((data_dir / "postings.json").read_text(encoding="utf-8"))
    postings = {p["id"]: p for p in postings_list}
    if len(postings) != len(postings_list):
        raise ValueError("duplicate posting ids in postings.json")

    cvs = {f.stem: f.read_text(encoding="utf-8") for f in sorted((data_dir / "cvs").glob("*.txt"))}

    labels: dict[tuple[str, str], str] = {}
    duplicates: list[tuple[str, str]] = []
    with open(data_dir / "labels.csv", newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            key = (row["posting_id"].strip(), row["cv_id"].strip())
            if key in labels:
                duplicates.append(key)
            labels[key] = row["label"].strip()

    split = json.loads((data_dir / "split.json").read_text(encoding="utf-8"))
    return Dataset(postings, cvs, labels, split, duplicates)


def validate(ds: Dataset) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if len(ds.postings) != EXPECTED_POSTINGS:
        errors.append(f"expected {EXPECTED_POSTINGS} postings, found {len(ds.postings)}")
    for pid, p in ds.postings.items():
        missing = REQUIRED_POSTING_KEYS - p.keys()
        if missing:
            errors.append(f"posting {pid}: missing {sorted(missing)}")
            continue
        skills = p["required_skills"]
        if not (isinstance(skills, list) and skills
                and all(isinstance(s, str) and s.strip() for s in skills)):
            errors.append(f"posting {pid}: required_skills must be a non-empty list of strings")
        years = p["min_years_experience"]
        if isinstance(years, bool) or not isinstance(years, int) or years < 0:
            errors.append(f"posting {pid}: min_years_experience must be an integer >= 0")
        if p["min_education_level"] not in EDUCATION_LEVELS:
            errors.append(f"posting {pid}: min_education_level must be one of {EDUCATION_LEVELS}")

    if len(ds.cvs) != EXPECTED_CVS:
        errors.append(f"expected {EXPECTED_CVS} CVs, found {len(ds.cvs)}")
    for cv_id, text in ds.cvs.items():
        if not text.strip():
            errors.append(f"{cv_id}: file is empty")
        kinds = sorted({kind for kind, _ in find_pii(text)})
        if kinds:
            errors.append(f"{cv_id}: contains personal data ({', '.join(kinds)})")

    expected = set(product(ds.postings, ds.cvs))
    given = set(ds.labels)
    missing = sorted(expected - given)
    if len(missing) > 5:
        errors.append(f"{len(missing)} of {len(expected)} pairs have no label (run: python -m eval.label)")
    else:
        for pid, cid in missing:
            errors.append(f"missing label for ({pid}, {cid})")
    for pid, cid in sorted(given - expected):
        errors.append(f"label for unknown pair ({pid}, {cid})")
    for pid, cid in ds.duplicate_labels:
        errors.append(f"duplicate label for ({pid}, {cid})")
    for (pid, cid), value in ds.labels.items():
        if value not in {"0", "1"}:
            errors.append(f"label for ({pid}, {cid}) must be 0 or 1, got {value!r}")

    for pid in ds.postings:
        labelled = {cv for (p, cv), y in ds.labels.items() if p == pid and y in {"0", "1"}}
        if len(labelled) < len(ds.cvs):
            continue  # unfinished posting, already reported above
        n_rel, n_all = len(ds.relevant(pid)), len(ds.cvs)
        if n_rel == 0 or n_rel == n_all:
            errors.append(f"posting {pid}: {n_rel}/{n_all} relevant, ranking metrics would be meaningless")
        elif n_rel < 3 or n_rel > 10:
            warnings.append(f"posting {pid}: {n_rel} relevant of {n_all}; 3-10 gives a more informative P@5/MRR")

    dev, test = ds.split.get("dev", []), ds.split.get("test", [])
    if len(dev) != 2 or len(test) != 1:
        errors.append("split must have exactly 2 dev postings and 1 test posting")
    if set(dev) & set(test):
        errors.append("a posting is in both dev and test")
    if set(dev) | set(test) != set(ds.postings):
        errors.append("split must cover exactly the postings in postings.json")

    return errors, warnings