#!/usr/bin/env bash
# Read-only status of every remaining task. Run from backend/:  bash status.sh
ok()   { printf "%-8s %-50s %s\n" "DONE"    "$1" "$2"; }
miss() { printf "%-8s %-50s %s\n" "MISSING" "$1" "$2"; }
chk()  { printf "%-8s %-50s %s\n" "CHECK"   "$1" "$2"; }
exists() { [ -f "$2" ] && ok "$1" "$2" || miss "$1" "no $2"; }
has()  { grep -rqiE "$2" $3 2>/dev/null && ok "$1" "found: $2" || miss "$1" "nothing matching: $2"; }

echo "== Git =="
unpushed=$(git rev-list --count @{u}..HEAD 2>/dev/null || echo "?")
dirty=$(git status --short | wc -l | tr -d ' ')
[ "$unpushed" = "0" ] && ok "all commits pushed" "" || chk "unpushed commits" "$unpushed"
[ "$dirty" = "0" ] && ok "working tree clean" "" || chk "uncommitted changes" "$dirty files"
git log --oneline -30 | grep -q "WIP snapshot" && chk "WIP snapshot commit is in main's history" "decide: keep or revert" || ok "no WIP snapshot commit in recent history" ""
grep -q "test_labels_csv_contains_one_ai_draft_for_every_pair" eval/tests/test_eval_validate.py 2>/dev/null \
  && miss "obsolete AI-draft test removed" "still in eval/tests/test_eval_validate.py" || ok "obsolete AI-draft test removed" ""
grep -qi "agreement" eval/data/PROVENANCE.md 2>/dev/null && chk "PROVENANCE mentions agreement" "read it: is every line true?" || miss "PROVENANCE has agreement numbers" "run: python -m eval.agreement p2 p3"

echo; echo "== Task 14: stored scoring runs =="
exists "schema file"  app/schemas/scoring.py
exists "service file" app/services/scoring_runs.py
exists "router file"  app/routers/scoring.py
has "router registered in main.py" "scoring\.router|routers import .*scoring" main.py
n=$(docker exec resume_screener_db psql -U admin -d resume_screener -tAc "SELECT count(*) FROM scoring_runs" 2>/dev/null | tr -d ' ')
[ -z "$n" ] && chk "a run exists in the database" "database not reachable" || { [ "$n" -gt 0 ] && ok "a run exists in the database" "$n run(s)" || miss "a run exists in the database" "0 runs, call POST scoring-runs once"; }
grep -rlq "scoring-runs" tests eval/tests 2>/dev/null && ok "API test for scoring runs" "" || miss "API test for scoring runs" ""

echo; echo "== Dashboard =="
exists "UploadPanel"     ../frontend/src/components/UploadPanel.jsx
exists "ScoringPanel"    ../frontend/src/components/ScoringPanel.jsx
exists "JobResultsPage"  ../frontend/src/pages/JobResultsPage.jsx
has "route /jobs/:jobId/results" "jobs/:jobId/results" ../frontend/src/App.jsx

echo; echo "== Evaluation =="
exists "components.py" eval/components.py
exists "tune.py"      eval/tune.py
exists "run.py"       eval/run.py
rows=$(grep -cE '^\| *[0-9]' eval/TUNING_LOG.md 2>/dev/null || echo 0)
[ "$rows" -ge 2 ] && ok "tuning log has decisions" "$rows rows" || miss "tuning log has decisions" "only the baseline"
[ -f eval/results/dev_latest.json ] && ok "harness run on dev" "" || miss "harness run on dev" "python -m eval.run"
[ -s eval/results/test_runs.log ] && chk "final test run was done" "must be exactly once: $(wc -l < eval/results/test_runs.log | tr -d ' ') logged" || miss "final test run" "not run yet (correct until weights are committed)"

echo; echo "== Tasks 9 and 10 =="
has "5-file limit (backend)" "max_files|too many files|at most 5|more than 5" app
has "scanned-PDF rejection" "scanned|no extractable text|image-based" app
has "failed status is recorded" "status *= *.failed" app/routers/resumes.py

echo; echo "== Packaging (later) =="
{ [ -f Dockerfile ] || [ -f ../Dockerfile ] || grep -q "build:" ../docker-compose.yml; } && ok "Docker for the API" "" || miss "Docker for the API" "Phase 5"