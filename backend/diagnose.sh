#!/usr/bin/env bash
# Read-only snapshot. Run from backend/:  bash diagnose.sh 2>&1 | tee /tmp/diagnose.txt
mask() { sed -E 's#(//[^:@/]+):[^@]*@#\1:***@#g'; }

echo "== Git =="
echo "branch: $(git branch --show-current)"
git log --oneline -5
echo "uncommitted:"; git status --short | head -20
echo "behind/ahead of upstream: $(git rev-list --left-right --count @{u}...HEAD 2>/dev/null || echo 'no upstream')"

echo; echo "== Environment =="
python -c "import sys; print('python prefix:', sys.prefix)"
echo "TEST_DATABASE_URL set: $([ -n "${TEST_DATABASE_URL:-}" ] && echo yes || echo no)"
echo "DATABASE_URL: $(grep '^DATABASE_URL=' .env | mask)"
echo "compose ports: $(grep -n '543[0-9]' ../docker-compose.yml | tr '\n' ' ')"
docker ps --format 'container: {{.Names}}  {{.Ports}}'
echo "alembic: $(alembic current 2>/dev/null | tail -1)"

echo; echo "== Dataset =="
echo "CV files: $(ls eval/data/cvs | wc -l)"
for p in p1 p2 p3; do
  echo "$p labels: $(grep -c "^$p," eval/data/labels.csv)  AI-marked: $(grep "^$p," eval/data/labels.csv | grep -ci 'ai.reviewed')  relevant: $(grep "^$p," eval/data/labels.csv | cut -d, -f3 | grep -c '^1$')"
done
echo "first-pass record: $(test -f eval/data/labels_ai_first_pass.csv && echo present || echo MISSING)"
python -m eval.validate 2>&1 | tail -4

echo; echo "== Features in code =="
echo "5-file limit: $(grep -rniE 'max_files' app | wc -l) hits | scanned-PDF check: $(grep -rniE 'scanned' app | wc -l) hits"

echo; echo "== Tests =="
[ -z "${TEST_DATABASE_URL:-}" ] && export TEST_DATABASE_URL="$(grep '^DATABASE_URL=' .env | cut -d= -f2- | sed 's#/resume_screener$#/resume_screener_test#')"
python -m pytest -q 2>&1 | tail -6 | mask

echo; echo "== Privacy =="
echo "raw CVs tracked: $(git ls-files eval/raw | wc -l) | raw CVs in history: $(git log --all --oneline -- eval/raw | wc -l) | .env tracked: $(git ls-files | grep -cE '(^|/)\.env$')"