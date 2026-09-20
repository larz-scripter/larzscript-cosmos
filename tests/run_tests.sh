#!/bin/sh
# Run every tests/test_*.lz. Usage: tests/run_tests.sh [name-filter]
# Needs only a `larzscript` binary on PATH (https://github.com/larz-scripter/larzscript/releases).
set -u
cd "$(dirname "$0")/.."
export LARZSCRIPT_PATH="packages:tests"
fail=0; ran=0
for f in tests/test_*.lz; do
  case "$f" in *"${1:-}"*) ;; *) continue ;; esac
  ran=$((ran + 1))
  printf '\n### %s\n' "$f"
  larzscript "$f" || fail=$((fail + 1))
done
printf '\n%s test file(s) run, %s failed\n' "$ran" "$fail"
[ "$fail" -eq 0 ] && [ "$ran" -gt 0 ]
