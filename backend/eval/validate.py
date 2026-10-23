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
    print(f"PASS: {len(ds.postings)} postings x {len(ds.cvs)} CVs = {len(ds.labels)} labelled pairs")
    return 0


if __name__ == "__main__":
    sys.exit(main())