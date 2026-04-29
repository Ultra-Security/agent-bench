#!/usr/bin/env bash
# Verify wrapper for the upstream terminal-bench/hello-world task.
#
# Upstream's tests assert two things (see tests/test_outputs.py at the pinned
# SHA in task.yaml):
#
#   1. /app/hello.txt exists
#   2. its trimmed contents equal "Hello, world!"
#
# Phase 0 of the harness does not yet run agents inside the upstream Docker
# image, so /app does not exist on the host. This wrapper accepts EITHER:
#
#   - the canonical /app/hello.txt (when we eventually run inside the image), or
#   - hello.txt at the workdir root (the Phase 0 contract — agents are spawned
#     with cwd=workdir and write artifacts there)
#
# Both targets enforce the same content check. When the harness gains
# containerization (methodology §3), the workdir-root branch becomes dead
# code and can be removed.

set -euo pipefail

CANDIDATES=("/app/hello.txt" "./hello.txt")

found=""
for path in "${CANDIDATES[@]}"; do
    if [[ -f "$path" ]]; then
        found="$path"
        break
    fi
done

if [[ -z "$found" ]]; then
    echo "FAIL: hello.txt not found at /app/hello.txt or ./hello.txt"
    exit 1
fi

actual="$(tr -d '[:space:]' < "$found")"
expected="Hello,world!"
if [[ "$actual" != "$expected" ]]; then
    echo "FAIL: $found contents mismatch"
    echo "  expected (whitespace-stripped): $expected"
    echo "  actual   (whitespace-stripped): $actual"
    exit 1
fi

echo "PASS: $found contains 'Hello, world!'"
exit 0
