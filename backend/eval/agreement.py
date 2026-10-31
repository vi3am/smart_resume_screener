"""Agreement between the AI first pass and the human labels, for relabelled postings only.

Usage: python -m eval.agreement p3        (or: p2 p3)
"""
import csv
import sys

from eval.dataset import DATA_DIR


def read(name):
    with open(DATA_DIR / name, newline="", encoding="utf-8") as fh:
        return {(r["posting_id"], r["cv_id"]): r["label"].strip() for r in csv.DictReader(fh)}


wanted = set(sys.argv[1:])
if not wanted:
    sys.exit("Name the relabelled postings, e.g.: python -m eval.agreement p3")

ai, human = read("labels_ai_first_pass.csv"), read("labels.csv")
keys = sorted(k for k in set(ai) & set(human) if k[0] in wanted)
if not keys:
    sys.exit("No pairs found for those postings.")

n = len(keys)
agree = sum(ai[k] == human[k] for k in keys)
p_ai = sum(ai[k] == "1" for k in keys) / n
p_h = sum(human[k] == "1" for k in keys) / n
pe = p_ai * p_h + (1 - p_ai) * (1 - p_h)
kappa = (agree / n - pe) / (1 - pe) if pe < 1 else float("nan")

print(f"Postings {sorted(wanted)}: {n} pairs, agreement {agree / n:.0%}, Cohen's kappa {kappa:.2f}")
for pid in sorted(wanted):
    ks = [k for k in keys if k[0] == pid]
    print(f"  {pid}: {sum(ai[k] == human[k] for k in ks)}/{len(ks)} agree")