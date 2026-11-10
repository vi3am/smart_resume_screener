import sys

from eval.dataset import load, validate


def main() -> int:
    try:
        ds = load()
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"FAIL: could not load dataset: {exc!r}")
        return 1
    errors, warnings = validate(ds)
    for w in warnings:
        print(f"WARN:  {w}")
    for e in errors:
        print(f"ERROR: {e}")
    if errors:
        print(f"FAIL: {len(errors)} error(s)")
        return 1
    print(
        f"PASS: structurally valid dataset: {len(ds.postings)} postings x "
        f"{len(ds.cvs)} CVs = {len(ds.labels)} labelled pairs"
    )
    if warnings:
        print("LIMITATION: Evaluation evidence is exploratory; resolve the warnings before claiming accuracy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())