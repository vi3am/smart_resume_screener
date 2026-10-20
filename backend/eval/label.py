"""Label CV/posting pairs one posting at a time, blind (no scores are shown).

Usage (from backend/):  python -m eval.label [p1 p2 p3]
At the prompt:  1 = relevant, 0 = not relevant, s = skip, u = undo, q = quit.
Add a note after the label, e.g.:  1 borderline, 1 year of internship only
Use --review to confirm or change existing labels, including AI-drafted labels.
"""
import csv
import json
import random
import sys
import shutil
import argparse

from eval.dataset import DATA_DIR

LABELS = DATA_DIR / "labels.csv"
FIELDS = ["posting_id", "cv_id", "label", "notes"]
SEED = "20261017"


def read_labels() -> dict[tuple[str, str], dict]:
    if not LABELS.exists():
        return {}
    with open(LABELS, newline="", encoding="utf-8") as fh:
        # return {
        #     (r["posting_id"], r["cv_id"]): r
        #     for r in csv.DictReader(fh)
        #     if r["label"] in {"0", "1"}
        # }
        return {
            (r["posting_id"].strip(), r["cv_id"].strip()): {**r, "label": r["label"].strip()}
            for r in csv.DictReader(fh)
            if r["label"].strip() in {"0", "1"}
        }


def write_labels(rows: dict[tuple[str, str], dict]) -> None:
    with open(LABELS, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for key in sorted(rows):
            writer.writerow({f: rows[key].get(f, "") for f in FIELDS})


def show(posting: dict, cv_id: str, text: str, position: str) -> None:
    line = "=" * 72
    print(f"\n{line}\nPOSTING {posting['id']}: {posting['title']}")
    print(posting["description"])
    print(f"Required skills: {', '.join(posting['required_skills'])}")
    print(f"Min years: {posting['min_years_experience']} | "
        f"Min education: {posting['min_education_level']}")
    print(f"{'-' * 72}\nCV {cv_id}  ({position})\n{'-' * 72}")
    print(text)
    print(line)


def main() -> int:
    parser = argparse.ArgumentParser(description="Label or review CV/posting pairs.")
    parser.add_argument("postings", nargs="*", help="posting IDs to label (default: all)")
    parser.add_argument(
        "--review",
        action="store_true",
        help="review existing labels; s keeps the current label",
    )
    args = parser.parse_args()

    postings = {
        p["id"]: p
        for p in json.loads((DATA_DIR / "postings.json").read_text(encoding="utf-8"))
    }
    cvs = {
        f.stem: f.read_text(encoding="utf-8")
        for f in sorted((DATA_DIR / "cvs").glob("cv_*.txt"))
    }
    wanted = args.postings or list(postings)
    unknown = [p for p in wanted if p not in postings]
    if unknown:
        print(f"Unknown posting id(s): {unknown}. Known: {list(postings)}")
        return 1
    if LABELS.exists():
        shutil.copy(LABELS, LABELS.with_name("labels.backup.csv"))

    rows = read_labels()
    total = len(postings) * len(cvs)

    for pid in wanted:
        order = sorted(cvs)
        random.Random(f"{SEED}-{pid}").shuffle(order)  # random, so order hints nothing
        if args.review:
            todo = [c for c in order if (pid, c) in rows]
        else:
            todo = [c for c in order if (pid, c) not in rows]
        history: list[tuple[str, dict | None]] = []

        while todo:
            cv_id = todo[0]
            done_here = len(order) - len(todo) + 1
            position = f"{done_here}/{len(order)} for {pid}"
            if args.review:
                current = rows[(pid, cv_id)]
                print(
                    f"Current label: {current['label']}; "
                    f"note: {current.get('notes', '')}"
                )
                position = f"review {done_here}/{len(todo)} for {pid}"
            show(postings[pid], cv_id, cvs[cv_id], position)
            prompt = "1/0/s/u/q > " if not args.review else "1/0 replace, s keep, u undo, q quit > "
            raw = input(f"[{len(rows)}/{total} labelled]  {prompt}").strip()
            cmd, _, note = raw.partition(" ")
            cmd = cmd.lower()

            if cmd in {"1", "0"}:
                previous = rows.get((pid, cv_id))
                rows[(pid, cv_id)] = {"posting_id": pid, "cv_id": cv_id,
                                    "label": cmd, "notes": note.strip()}
                write_labels(rows)
                history.append((cv_id, previous))
                todo.pop(0)
            elif cmd == "s":
                if args.review:
                    todo.pop(0)
                else:
                    todo.append(todo.pop(0))
            elif cmd == "u":
                if history:
                    last, previous = history.pop()
                    if previous is None:
                        rows.pop((pid, last), None)
                    else:
                        rows[(pid, last)] = previous
                    write_labels(rows)
                    todo.insert(0, last)
                else:
                    print("Nothing to undo in this session.")
            elif cmd == "q":
                print(f"Saved. {len(rows)}/{total} labelled.")
                return 0
            else:
                print("Type 1, 0, s, u or q.")

        print(f"\nPosting {pid} {'reviewed' if args.review else 'finished'}.")

    action = "reviewed" if args.review else "labelled"
    print(f"All requested postings {action}. {len(rows)}/{total} labelled.")
    return 0


if __name__ == "__main__":
    sys.exit(main())