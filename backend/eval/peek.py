"""Component scores for the DEV postings only. Refuses the test posting."""
import sys

from app.services.scoring import score_cv
from eval.config import AS_OF
from eval.dataset import load


def main() -> int:
    ds = load()
    dev = ds.split["dev"]
    wanted = sys.argv[1:] or dev
    for pid in wanted:
        if pid not in dev:
            print(f"Refusing {pid}: it is not a dev posting. The test posting is looked at once, at the end.")
            return 1
    for pid in wanted:
        posting, rel = ds.postings[pid], ds.relevant(pid)
        rows = sorted(((score_cv(posting, text, as_of=AS_OF), cv_id)
                       for cv_id, text in ds.cvs.items()),
                      key=lambda row: -row[0].overall)
        print(f"\n{pid} {posting['title']}  ({len(rel)} relevant)")
        print("rank  cv     label overall skills   exp   edu   sem   missing")
        for i, (r, cv_id) in enumerate(rows, 1):
            lab = "1" if cv_id in rel else "0"
            print(f"{i:>4}  {cv_id}  {lab:>5} {r.overall:7.1f} {r.skills:6.1f} "
                  f"{r.experience:5.1f} {r.education:5.1f} {r.semantic:5.1f}   "
                  f"{', '.join(r.missing_skills)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())