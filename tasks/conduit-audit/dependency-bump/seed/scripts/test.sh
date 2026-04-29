#!/usr/bin/env bash
# Stub test script. In a real project this would run pytest. For the bench
# we assert that requirements.txt and requirements.lock both pin requests
# to the same version, and that version is 2.31.0.
set -euo pipefail

req_v=$(grep -E '^requests==' requirements.txt | head -1 | sed 's/.*==//' | tr -d '[:space:]')
lock_v=$(grep -E '^requests==' requirements.lock | head -1 | sed 's/[# ].*//' | sed 's/.*==//' | tr -d '[:space:]')

if [[ "$req_v" != "2.31.0" ]]; then
    echo "TEST FAIL: requirements.txt has requests==$req_v, expected 2.31.0"
    exit 1
fi
if [[ "$lock_v" != "2.31.0" ]]; then
    echo "TEST FAIL: requirements.lock has requests==$lock_v, expected 2.31.0"
    exit 1
fi

echo "TEST OK: requests pinned to 2.31.0 in both files"
exit 0
