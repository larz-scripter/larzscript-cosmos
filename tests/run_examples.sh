#!/bin/sh
# Run every examples/*.lz and compare with its .expected file. Regenerate with: tests/run_examples.sh --update
set -u
cd "$(dirname "$0")/.."
export LARZSCRIPT_PATH="packages"
pass=0; fail=0
for f in examples/*.lz; do
  exp="${f%.lz}.expected"
  got="$(larzscript "$f" 2>&1)"
  if [ "${1:-}" = "--update" ]; then printf '%s\n' "$got" > "$exp"; echo "updated $exp"; continue; fi
  if [ "$got" = "$(cat "$exp")" ]; then pass=$((pass + 1)); else fail=$((fail + 1)); echo "FAIL $f"; echo "--- expected"; cat "$exp"; echo "--- got"; echo "$got"; fi
done
[ "${1:-}" = "--update" ] && exit 0
echo "$pass examples passed, $fail failed"
[ "$fail" -eq 0 ]
