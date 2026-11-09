"""Generate test evidence into eval/results/evidence.md.

Covers parsing on varied layouts (20 anonymized CVs), scoring consistency, and the automated tests.
Only the DEV postings are scored here.

Usage (from backend/):  python -m eval.evidence
"""
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.services.parser import parse_resume
from app.services.scoring import score_cv
from eval.config import AS_OF
from eval.dataset import load

OUT = Path(__file__).parent / "results" / "evidence.md"
COMPONENTS = ("skills", "experience", "education", "semantic", "overall")


def git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], text=True).strip()
    except Exception:
        return "unknown"


def parsing_section(ds) -> list[str]:
    lines = [
        "Names, emails and phones were redacted from these CVs, so this table covers experience, "
        "education and skills only.", "",
        "| CV | chars | years | education | in progress | skills found |",
        "|---|---|---|---|---|---|",
    ]
    zero_years = no_edu = no_skills = 0
    for cv_id, text in sorted(ds.cvs.items()):
        r = parse_resume(text)
        years = r.get("years_experience") or 0.0
        edu, prog = r.get("education_level"), r.get("education_in_progress")
        skills = r.get("skills") or []
        zero_years += years == 0.0
        no_edu += edu is None and prog is None
        no_skills += not skills
        lines.append(f"| {cv_id} | {len(text)} | {years} | {edu or '-'} | {prog or '-'} | {len(skills)} |")
    lines += ["",
              f"Of {len(ds.cvs)} CVs: {zero_years} with 0 years of experience found, {no_edu} with no "
              f"education level, {no_skills} with no skills found. These are measured limitations "
              "(multi-column layouts, template placeholder dates, unrecognized headings)."]
    return lines


def consistency_section(ds) -> list[str]:
    pid = ds.split["dev"][0]
    posting, sample, worst = ds.postings[pid], sorted(ds.cvs)[:5], 0.0
    for cv_id in sample:
        a = score_cv(posting, ds.cvs[cv_id], as_of=AS_OF)
        b = score_cv(posting, ds.cvs[cv_id], as_of=AS_OF)
        worst = max(worst, *(abs(getattr(a, k) - getattr(b, k)) for k in COMPONENTS))
    return [f"Scored {len(sample)} CVs twice against dev posting {pid} with a fixed reference date ({AS_OF}).",
            f"Largest difference between the two runs, over the four components and the overall score: {worst:.6f}"]


def tests_section() -> list[str]:
    if not os.environ.get("TEST_DATABASE_URL"):
        return ["Not run: set TEST_DATABASE_URL first (verify.sh shows how)."]
    p = subprocess.run([sys.executable, "-m", "pytest", "-q"], capture_output=True, text=True)
    tail = "\n".join(p.stdout.strip().splitlines()[-8:])
    tail = re.sub(r"//[^:@/\s]+:[^@\s]*@", "//***:***@", tail)  # never write a password into a file
    return ["```", tail, "```"]


def main() -> int:
    ds = load()
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out = [
        "# Test evidence (generated)", "",
        f"Generated {stamp} at commit {git('rev-parse', '--short', 'HEAD')}.", "",
        "## 1. Parsing on varied layouts (20 anonymized CVs)", "", *parsing_section(ds), "",
        "## 2. Scoring consistency", "", *consistency_section(ds), "",
        "## 3. Automated API and failure-case tests", "", *tests_section(), "",
    ]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())