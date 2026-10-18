"""Anonymize many CVs at once.

Reads eval/raw/manifest.csv (columns: file,names). 'names' holds the name(s) to
redact, separated by ';'. Already-processed files are skipped, so re-running is
safe. The originals, the manifest and the id map stay in eval/raw/ (gitignored).

Usage (from backend/):  python -m eval.prepare_batch
"""
import csv
import hashlib
import random
import re
import sys
from pathlib import Path

from app.services.parser import extract_text
from eval.dataset import DATA_DIR, EXPECTED_CVS
from eval.pii import find_pii, redact

RAW_DIR = Path(__file__).parent / "raw"
MANIFEST = RAW_DIR / "manifest.csv"
ID_MAP = RAW_DIR / "id_map.csv"
CV_DIR = DATA_DIR / "cvs"
SEED = 20261016  # fixed, so the shuffle is reproducible


def fingerprint(text: str) -> str:
    return hashlib.sha256(" ".join(text.lower().split()).encode()).hexdigest()


def next_index() -> int:
    nums = [int(m.group(1)) for p in CV_DIR.glob("cv_*.txt")
            if (m := re.fullmatch(r"cv_(\d+)", p.stem))]
    return max(nums, default=0) + 1


def load_done() -> set[str]:
    if not ID_MAP.exists():
        return set()
    with open(ID_MAP, newline="", encoding="utf-8") as fh:
        return {row["file"] for row in csv.DictReader(fh)}


def main() -> int:
    if not MANIFEST.exists():
        print(f"Create {MANIFEST} first (columns: file,names).")
        return 1
    with open(MANIFEST, newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r.get("file", "").strip()]

    done = load_done()
    todo = [r for r in rows if r["file"].strip() not in done]
    random.Random(SEED).shuffle(todo)  # so numbering does not reveal the domain

    CV_DIR.mkdir(parents=True, exist_ok=True)
    seen = {fingerprint(p.read_text(encoding="utf-8")) for p in CV_DIR.glob("cv_*.txt")}
    idx, new_map = next_index(), []

    for row in todo:
        fname = row["file"].strip()
        src = RAW_DIR / fname
        names = [n.strip() for n in (row.get("names") or "").split(";") if n.strip()]

        if not src.exists():
            print(f"SKIP   {fname}: file not found in eval/raw")
            continue
        if src.suffix not in {".pdf", ".docx"}:
            print(f"SKIP   {fname}: extension must be lowercase .pdf or .docx")
            continue
        try:
            text = redact(extract_text(str(src)), names)
        except Exception as exc:
            print(f"SKIP   {fname}: could not read ({exc!r})")
            continue
        if not text.strip():
            print(f"SKIP   {fname}: no text extracted (scanned PDF?)")
            continue
        fp = fingerprint(text)
        if fp in seen:
            print(f"SKIP   {fname}: identical to a CV already in the dataset")
            continue

        cv_id = f"cv_{idx:02d}"
        (CV_DIR / f"{cv_id}.txt").write_text(text, encoding="utf-8")
        seen.add(fp)
        idx += 1
        new_map.append({"file": fname, "cv_id": cv_id})

        notes = []
        if not names:
            notes.append("no name given, so no name was redacted")
        left = sorted({kind for kind, _ in find_pii(text)})
        if left:
            notes.append(f"still contains {left}")
        print(f"OK     {fname} -> {cv_id}" + (f"   ({'; '.join(notes)})" if notes else ""))

    if new_map:
        write_header = not ID_MAP.exists()
        with open(ID_MAP, "a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["file", "cv_id"])
            if write_header:
                writer.writeheader()
            writer.writerows(new_map)

    total = len(list(CV_DIR.glob("cv_*.txt")))
    print(f"\n{total} CVs in the dataset, target {EXPECTED_CVS}.")
    print("Now OPEN every new cv_XX.txt and read it. Street addresses, employer or school "
        "names that identify a person, and names you did not list are not redacted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())