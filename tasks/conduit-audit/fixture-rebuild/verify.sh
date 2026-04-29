#!/usr/bin/env bash
# Verify: fixture-rebuild
#
# Checks the JSON contents structurally. The recipe specifies 2-space
# indentation; verifier accepts the canonical content regardless of
# whitespace, but BUILD.log must contain the exact "fixture rebuilt"
# line.
set -euo pipefail

if [[ ! -f fixtures/data.json ]]; then
    echo "FAIL: fixtures/data.json missing"
    exit 1
fi
if [[ ! -f BUILD.log ]]; then
    echo "FAIL: BUILD.log missing"
    exit 1
fi

if ! grep -qx 'fixture rebuilt' BUILD.log; then
    echo "FAIL: BUILD.log does not contain exact line 'fixture rebuilt'"
    exit 1
fi

python3 - <<'PY'
import json, sys
with open("fixtures/data.json") as f:
    d = json.load(f)

expected = {
    "users": [
        {"id": 1, "name": "Alice", "email": "alice@example.test"},
        {"id": 2, "name": "Bob",   "email": "bob@example.test"},
        {"id": 3, "name": "Carol", "email": "carol@example.test"},
    ],
    "orders": [
        {"order_id": 100, "user_id": 1, "total_cents": 2500},
        {"order_id": 101, "user_id": 2, "total_cents": 1799},
        {"order_id": 102, "user_id": 1, "total_cents": 500},
        {"order_id": 103, "user_id": 3, "total_cents": 9900},
    ],
}
if d != expected:
    print("FAIL: data.json does not match expected structure")
    print("  expected:", expected)
    print("  actual:  ", d)
    sys.exit(1)

print("PASS: fixture-rebuild")
PY
