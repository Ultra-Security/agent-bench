#!/usr/bin/env bash
# Verify: changelog-extract
#
# We compute the expected commit list directly from the live git history
# (the seed setup is deterministic). We accept any reasonable spacing
# but require the bullet lines to contain the exact short SHA and
# subject in oldest-first order.
set -euo pipefail

if [[ ! -f CHANGELOG.md ]]; then
    echo "FAIL: CHANGELOG.md missing"
    exit 1
fi

grep -qE '^# Changelog' CHANGELOG.md || { echo "FAIL: missing '# Changelog' heading"; exit 1; }
grep -qE '^## Since 2026-04-10' CHANGELOG.md || { echo "FAIL: missing '## Since 2026-04-10' heading"; exit 1; }

# Expected commits, oldest first, on or after 2026-04-10.
expected=$(git log --reverse --since=2026-04-10T00:00:00Z --pretty='%h %s')
if [[ -z "$expected" ]]; then
    echo "FAIL: verifier could not find any qualifying commits (workdir corrupted?)"
    exit 1
fi

# Extract bullet lines from CHANGELOG.md, stripping leading "- ".
bullets=()
while IFS= read -r line; do bullets+=("$line"); done < <(grep -E '^- [0-9a-f]{7} ' CHANGELOG.md | sed -E 's/^- //')
expected_lines=()
while IFS= read -r line; do expected_lines+=("$line"); done <<< "$expected"

if [[ ${#bullets[@]} -ne ${#expected_lines[@]} ]]; then
    echo "FAIL: expected ${#expected_lines[@]} bullets, got ${#bullets[@]}"
    printf '  expected: %s\n' "${expected_lines[@]}"
    printf '  actual:   %s\n' "${bullets[@]}"
    exit 1
fi

# Reject commits older than the cutoff.
if grep -qE '^- [0-9a-f]{7} init: scaffold' CHANGELOG.md; then
    echo "FAIL: includes pre-cutoff commit (init: scaffold)"
    exit 1
fi
if grep -qE '^- [0-9a-f]{7} chore: add license' CHANGELOG.md; then
    echo "FAIL: includes pre-cutoff commit (chore: add license)"
    exit 1
fi

for i in "${!expected_lines[@]}"; do
    if [[ "${bullets[$i]}" != "${expected_lines[$i]}" ]]; then
        echo "FAIL: bullet $((i+1)) mismatch"
        echo "  expected: ${expected_lines[$i]}"
        echo "  actual:   ${bullets[$i]}"
        exit 1
    fi
done

echo "PASS: changelog-extract"
exit 0
