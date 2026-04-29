#!/usr/bin/env bash
# Verify: dependency-bump
#
# Pass conditions:
#   1. requirements.txt pins requests==2.31.0
#   2. requirements.lock pins requests==2.31.0
#   3. click and pyyaml versions are unchanged
#   4. scripts/test.sh exits 0 when invoked
set -euo pipefail

if ! grep -qE '^requests==2\.31\.0[[:space:]]*$' requirements.txt; then
    echo "FAIL: requirements.txt does not pin requests==2.31.0"
    grep '^requests' requirements.txt || true
    exit 1
fi

if ! grep -qE '^requests==2\.31\.0([[:space:]]|#|$)' requirements.lock; then
    echo "FAIL: requirements.lock does not pin requests==2.31.0"
    grep '^requests' requirements.lock || true
    exit 1
fi

if ! grep -qE '^click==8\.1\.7[[:space:]]*$' requirements.txt; then
    echo "FAIL: click was modified in requirements.txt"
    exit 1
fi
if ! grep -qE '^pyyaml==6\.0\.1[[:space:]]*$' requirements.txt; then
    echo "FAIL: pyyaml was modified in requirements.txt"
    exit 1
fi

if ! bash scripts/test.sh >/dev/null; then
    echo "FAIL: scripts/test.sh did not exit 0"
    exit 1
fi

echo "PASS: dependency-bump"
exit 0
