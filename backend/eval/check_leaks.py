"""Report any manifest name that still appears in the anonymized CVs."""
import csv
import re
import sys
from pathlib import Path

from eval.dataset import DATA_DIR

MANIFEST = Path(__file__).parent / "raw" / "manifest.csv"


def main() -> int:
    if not MANIFEST.exists():
        print(f"Missing {MANIFEST}")
        return 1
    names: set[str] = set()
    with open(MANIFEST, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            for full in (row.get("names") or "").split(";"):
                full = full.strip()
                if full:
                    names.add(full)
                    names.update(p for p in full.split() if len(p) >= 4)

    hits = 0
    for f in sorted((DATA_DIR / "cvs").glob("cv_*.txt")):
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for name in names:
                if re.search(rf"\b{re.escape(name)}\b", line, re.IGNORECASE):
                    print(f"{f.name}:{n}: '{name}' -> {line.strip()[:80]}")
                    hits += 1
    print(f"\n{hits} possible leak(s)." if hits else "\nNo manifest names found in the CVs.")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())