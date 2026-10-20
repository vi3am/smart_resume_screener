#!/usr/bin/env bash
# Run from backend/:  bash verify.sh
pass=0; fail=0

check() {            # passes when the command exits 0
  local name="$1"; shift
  if out=$("$@" 2>&1); then echo "PASS  $name"; pass=$((pass+1))
  else echo "FAIL  $name"; echo "$out" | head -5 | sed 's/^/        /'; fail=$((fail+1)); fi
}

check_empty() {      # passes when the command prints nothing
  local name="$1"; shift
  out=$("$@" 2>&1)
  if [ -z "$out" ]; then echo "PASS  $name"; pass=$((pass+1))
  else echo "FAIL  $name"; echo "$out" | head -5 | sed 's/^/        /'; fail=$((fail+1)); fi
}

echo "== Environment =="
check "running inside backend/ (main.py found)" test -f main.py
check "project virtualenv is active" python -c "import os,sys; sys.exit(0 if sys.prefix.startswith(os.getcwd()) else 1)"
check "app imports and .env loads" python -c "import main"

echo "== Database =="
check "database container is running" bash -c 'docker ps --format "{{.Names}}" | grep -q resume_screener_db'
check "alembic is at head" bash -c 'test "$(alembic current 2>/dev/null | tail -1 | cut -d" " -f1)" = "$(alembic heads 2>/dev/null | tail -1 | cut -d" " -f1)"'

echo "== Tests and dataset =="
check "pytest passes" python -m pytest -q --import-mode=importlib
check "dataset validates (60 labelled pairs)" python -m eval.validate

echo "== Secrets and personal data =="
check_empty "no .env file tracked by git" bash -c "git ls-files | grep -E '(^|/)\.env(\..*)?$' || true"
check_empty "no uploaded files tracked by git" git ls-files uploads
check_empty "no raw CVs tracked by git" git ls-files eval/raw
check_empty "no raw CVs anywhere in git history" git log --all --oneline -- eval/raw

echo
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]