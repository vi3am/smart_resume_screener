"""Evaluation harness.

  python -m eval.run            dev postings (the ones you tune on, so these numbers are optimistic)
  python -m eval.run --final    the test posting: logged, and refused if it was already evaluated
"""
import argparse
import json
import random
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from app.services.scoring import DEFAULT_WEIGHTS
from eval.components import compute
from eval.config import AS_OF
from eval.dataset import load, validate
from eval.metrics import precision_at_k, rank_by_score, reciprocal_rank

RESULTS = Path(__file__).parent / "results"
TEST_LOG = RESULTS / "test_runs.log"
K, RANDOM_TRIALS = 5, 1000


def combine(comps, weights):
    total = sum(weights.values())
    return {cv: sum(weights[k] * getattr(r, k) for k in weights) / total for cv, r in comps.items()}


def ablations():
    out = {}
    for drop in DEFAULT_WEIGHTS:
        w = {k: (0.0 if k == drop else v) for k, v in DEFAULT_WEIGHTS.items()}
        out[f"hybrid_without_{drop}"] = lambda c, w=w: combine(c, w)
    return out


def random_baseline(ids, relevant):
    p5 = rr = 0.0
    for seed in range(RANDOM_TRIALS):
        order = list(ids)
        random.Random(seed).shuffle(order)
        p5 += precision_at_k(order, relevant, K)
        rr += reciprocal_rank(order, relevant)
    return p5 / RANDOM_TRIALS, rr / RANDOM_TRIALS


def git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--final", action="store_true", help="evaluate the test posting (logged)")
    ap.add_argument("--again", action="store_true", help="allow a repeat test run (also logged)")
    args = ap.parse_args()

    ds = load()
    errors, _ = validate(ds)
    if errors:
        print("Dataset is not valid:", *errors[:5], sep="\n  ")
        return 1

    split = "test" if args.final else "dev"
    pids = ds.split[split]
    if args.final and TEST_LOG.exists() and TEST_LOG.read_text(encoding="utf-8").strip() and not args.again:
        print("The test posting was already evaluated (eval/results/test_runs.log).")
        print("A repeat counts as tuning on the test set. Use --again only if you will report it.")
        return 1

    comps = compute(ds, pids)
    methods = {
        "skill_overlap": lambda c: {cv: r.skills for cv, r in c.items()},
        "semantic_only": lambda c: {cv: r.semantic for cv, r in c.items()},
        "hybrid": lambda c: combine(c, DEFAULT_WEIGHTS),
        **ablations(),
    }

    results = {"random (expected)": {pid: random_baseline(sorted(comps[pid]), ds.relevant(pid)) for pid in pids}}
    for name, fn in methods.items():
        results[name] = {}
        for pid in pids:
            ranked, rel = rank_by_score(fn(comps[pid])), ds.relevant(pid)
            results[name][pid] = (precision_at_k(ranked, rel, K), reciprocal_rank(ranked, rel))

    print(f"split={split}  commit={git_commit()}  as_of={AS_OF}  weights={DEFAULT_WEIGHTS}")
    for pid in pids:
        n_rel = len(ds.relevant(pid))
        print(f"  {pid} {ds.postings[pid]['title']}: {n_rel} relevant of {len(ds.cvs)}, "
              f"P@{K} ceiling {min(K, n_rel) / K:.2f}")
    header = f"{'method':<26}" + "".join(f"{pid + ' P@5':>9}{pid + ' RR':>8}" for pid in pids) + f"{'meanP@5':>9}{'MRR':>7}"
    print("\n" + header)
    for name, per in results.items():
        cells = "".join(f"{per[pid][0]:9.2f}{per[pid][1]:8.2f}" for pid in pids)
        mean_p5 = sum(per[pid][0] for pid in pids) / len(pids)
        mrr = sum(per[pid][1] for pid in pids) / len(pids)
        print(f"{name:<26}{cells}{mean_p5:9.2f}{mrr:7.2f}")

    RESULTS.mkdir(exist_ok=True)
    payload = {
        "split": split, "commit": git_commit(), "as_of": str(AS_OF), "weights": DEFAULT_WEIGHTS,
        "postings": {pid: {"title": ds.postings[pid]["title"], "n_relevant": len(ds.relevant(pid))} for pid in pids},
        "results": {m: {pid: {"p@5": v[0], "rr": v[1]} for pid, v in per.items()} for m, per in results.items()},
    }
    (RESULTS / f"{split}_latest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if args.final:
        hybrid = results["hybrid"]
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with open(TEST_LOG, "a", encoding="utf-8") as fh:
            fh.write(f"{stamp}\t{git_commit()}\t{json.dumps(DEFAULT_WEIGHTS)}\t"
                    f"hybrid P@5={sum(v[0] for v in hybrid.values()) / len(hybrid):.3f} "
                    f"MRR={sum(v[1] for v in hybrid.values()) / len(hybrid):.3f}\n")
        print("\nLogged to eval/results/test_runs.log")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())