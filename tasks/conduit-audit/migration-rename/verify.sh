#!/usr/bin/env bash
# Verify: migration-rename
#
# Pass conditions:
#   1. No .py file under src/ contains the string "OrderProcessor".
#   2. The new class "OrderHandler" is defined exactly once
#      (class OrderHandler:) and that definition lives in
#      src/orders/processor.py.
#   3. Every original callsite file still references OrderHandler.
set -euo pipefail

if grep -rEn --include='*.py' 'OrderProcessor' src/ >/dev/null 2>&1; then
    echo "FAIL: OrderProcessor still appears in src/"
    grep -rEn --include='*.py' 'OrderProcessor' src/ || true
    exit 1
fi

defs=$(grep -rEn --include='*.py' '^class[[:space:]]+OrderHandler[(:[:space:]]' src/ || true)
if [[ -z "$defs" ]]; then
    echo "FAIL: no 'class OrderHandler' definition found"
    exit 1
fi
def_count=$(echo "$defs" | wc -l | tr -d '[:space:]')
if [[ "$def_count" -ne 1 ]]; then
    echo "FAIL: expected exactly 1 class OrderHandler definition, got $def_count"
    echo "$defs"
    exit 1
fi
if ! echo "$defs" | grep -q 'src/orders/processor.py'; then
    echo "FAIL: class OrderHandler is not in src/orders/processor.py"
    echo "$defs"
    exit 1
fi

# Each of these files should contain OrderHandler somewhere.
for f in src/orders/__init__.py src/api/handlers.py src/jobs/nightly.py src/tests/test_orders.py; do
    if [[ ! -f "$f" ]]; then
        echo "FAIL: missing $f"
        exit 1
    fi
    if ! grep -F 'OrderHandler' "$f" >/dev/null; then
        echo "FAIL: $f does not reference OrderHandler"
        exit 1
    fi
done

echo "PASS: migration-rename"
exit 0
