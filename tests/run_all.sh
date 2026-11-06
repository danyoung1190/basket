#!/bin/sh
# Runs every test. Needs the app served on :8765 (python3 -m http.server 8765 from the repo folder)
# and the stand-in Firebase on :8766 (python3 tests/fakefb/server.py).
cd "$(dirname "$0")"
fail=0
for t in test_*.py; do
  out=$(python3 "$t" 2>&1 | grep -E "^FAIL|Failed: \[.+\]|Error" | head -3)
  if [ -n "$out" ]; then echo "== $t"; echo "$out"; fail=1; else echo "ok  $t"; fi
done
exit $fail
