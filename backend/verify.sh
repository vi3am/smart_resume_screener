#!/usr/bin/env bash
# Run from backend/:  bash verify.sh
pass=0; fail=0

# Derive the test database URL from .env if it isn't set already
if [ -z "${TEST_DATABASE_URL:-}" ] && [ -f .env ]; then
  export TEST_DATABASE_URL="$(grep '^DATABASE_URL=' .env | cut -d= -f2- | sed 's#/resume_screener$#/resume_screener_test#')"
fi
if [ -n "${TEST_DATABASE_URL:-}" ]; then
  export DATABASE_URL="$TEST_DATABASE_URL"
fi

check() {            # passes when the command exits 0
  local name="$1"; shift
  if out=$("$@" 2>&1); then echo "PASS  $name"; pass=$((pass+1))
  else echo "FAIL  $name"; echo "$out" | tail -6 | sed 's/^/        /'; fail=$((fail+1)); fi
}

check_empty() {      # passes when the command prints nothing
  local name="$1"; shift
  out=$("$@" 2>&1)
  if [ -z "$out" ]; then echo "PASS  $name"; pass=$((pass+1))
  else echo "FAIL  $name"; echo "$out" | head -5 | sed 's/^/        /'; fail=$((fail+1)); fi
}

echo "== Environment =="
check "running inside backend/ (main.py found)" test -f main.py
check "project virtualenv is active (not another project's)" python -c "import sys; sys.exit(0 if 'smart-resume-screener' in sys.prefix else 1)"
check "app imports and .env loads" python -c "import main"

echo "== Database =="
check "database container is running" bash -c 'docker ps --format "{{.Names}}" | grep -q resume_screener_db'
if python -c 'import os,sys; from sqlalchemy.engine import make_url; url=make_url(os.environ.get("TEST_DATABASE_URL", "")); sys.exit(0 if url.get_backend_name() == "postgresql" and (url.database or "").endswith("_test") else 1)' 2>/dev/null; then
  check "test database migrations are at head" alembic upgrade head
else
  echo "FAIL  test database URL is a dedicated PostgreSQL database ending in _test"
  fail=$((fail+1))
fi

echo "== Code and tests =="
check "unit tests pass (fields, scoring, metrics, pii)" python -m pytest tests/test_fields.py tests/test_scoring.py tests/test_eval_metrics.py tests/test_eval_pii.py -q
check "full test suite passes" python -m pytest -q --import-mode=importlib
check "dataset validates (60 labelled pairs)" python -m eval.validate
check "peek refuses the test posting" python -c "import subprocess,sys,json; t=json.load(open('eval/data/split.json'))['test'][0]; sys.exit(0 if subprocess.run([sys.executable,'-m','eval.peek',t],capture_output=True).returncode==1 else 1)"
check "scoring returns four components (fake embedder)" python -c "from app.services.scoring import score_cv; p={'title':'t','description':'d','required_skills':['Python'],'min_years_experience':1,'min_education_level':'associate'}; r=score_cv(p,'Experience\nPython developer 2022 - 2024\nEducation\nBachelor of Arts',embed=lambda t:[[1.0,0.0]]*len(t)); assert 0<=r.overall<=100 and r.matched_skills==['Python'], r"
check "parser returns the new fields" python -c "from app.services.parser import parse_resume; r=parse_resume('Jane Doe\nExperience\n2020 - 2022'); assert {'years_experience','education_level','education_in_progress'} <= r.keys(), r"

echo "== Secrets and personal data =="
check_empty "no .env file tracked by git" bash -c "git ls-files | grep -E '(^|/)\.env(\..*)?$' || true"
check_empty "no uploaded files tracked by git" git ls-files uploads
check_empty "no raw CVs tracked by git" git ls-files eval/raw
check_empty "no raw CVs anywhere in git history" git log --all --oneline -- eval/raw

echo
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]