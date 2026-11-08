"""Coarse weight grid on the DEV postings only. The test posting is never touched here."""
import itertools

from app.services.scoring import DEFAULT_WEIGHTS
from eval.components import compute
from eval.dataset import load
from eval.metrics import precision_at_k, rank_by_score, reciprocal_rank

KEYS = ["skills", "experience", "education", "semantic"]


def evaluate(w, comps, ds, dev):
    total = sum(w.values())
    p5s, rrs, mean_ranks = [], [], []
    for pid in dev:
        scores = {cv: sum(w[k] * getattr(r, k) for k in KEYS) / total for cv, r in comps[pid].items()}
        ranked, rel = rank_by_score(scores), ds.relevant(pid)
        p5s.append(precision_at_k(ranked, rel, 5))
        rrs.append(reciprocal_rank(ranked, rel))
        mean_ranks.append(sum(ranked.index(c) + 1 for c in rel) / len(rel))
    n = len(dev)
    return sum(p5s) / n, sum(rrs) / n, sum(mean_ranks) / n


def main() -> int:
    ds = load()
    dev = ds.split["dev"]
    comps = compute(ds, dev)
    rows = []
    for tenths in itertools.product(range(6), repeat=4):
        if sum(tenths) == 10:
            w = {k: t / 10 for k, t in zip(KEYS, tenths)}
            rows.append((evaluate(w, comps, ds, dev), w))
    rows.sort(key=lambda r: (-r[0][1], -r[0][0], r[0][2]))

    def show(label, res, w):
        print(f"{label:<9} MRR {res[1]:.2f}  P@5 {res[0]:.2f}  mean rank of relevant {res[2]:5.1f}  {w}")

    print(f"Dev postings {dev}: {len(rows)} weight settings tried")
    for i, (res, w) in enumerate(rows[:10], 1):
        show(f"#{i}", res, w)
    show("default", evaluate(DEFAULT_WEIGHTS, comps, ds, dev), DEFAULT_WEIGHTS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())