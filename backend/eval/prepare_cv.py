"""Extract text from one CV, redact personal data, save it into the dataset.

Usage (from backend/):
    python -m eval.prepare_cv eval/raw/some_cv.pdf cv_01 --name "Full Name"
"""
import argparse
import sys
from pathlib import Path

from app.services.parser import extract_text
from eval.dataset import DATA_DIR
from eval.pii import find_pii, redact


def main() -> int:
    ap = argparse.ArgumentParser(description="Anonymize one CV into the dataset.")
    ap.add_argument("source", type=Path, help="original .pdf or .docx (lowercase extension)")
    ap.add_argument("cv_id", help="e.g. cv_01")
    ap.add_argument("--name", action="append", default=[], help="candidate name to redact (repeatable)")
    ap.add_argument("--force", action="store_true", help="overwrite an existing file")
    args = ap.parse_args()

    if args.source.suffix not in {".pdf", ".docx"}:
        print("Source must end in .pdf or .docx (lowercase).")
        return 1
    out = DATA_DIR / "cvs" / f"{args.cv_id}.txt"
    if out.exists() and not args.force:
        print(f"{out} already exists (use --force to overwrite).")
        return 1

    text = redact(extract_text(str(args.source)), args.name)
    if not text.strip():
        print("No text extracted. Scanned PDFs are not supported.")
        return 1
    
    if not args.source.exists():
        print(f"File not found: {args.source}")
        print("Files in eval/raw:", sorted(p.name for p in Path('eval/raw').glob('*')))
        return 1

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"Wrote {out}")
    leftover = find_pii(text)
    if leftover:
        print(f"Still contains: {sorted({kind for kind, _ in leftover})}. Edit it by hand.")
    print("Now OPEN the file and read it. Street addresses, school or employer names " + 
        "that identify a person, and unusual names are not redacted automatically.")
    return 0


if __name__ == "__main__":
    sys.exit(main())