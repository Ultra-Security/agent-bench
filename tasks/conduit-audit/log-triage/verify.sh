#!/usr/bin/env bash
# Verify: log-triage
#
# The seed log contains exactly three error templates:
#   1. Connection refused to upstream <host>:<port>
#   2. Failed to parse JSON payload at offset <n>
#   3. Database query exceeded deadline of <n>ms
#
# A correct triage yields three lines in errors.txt — one per template,
# in first-seen order. Verifier requirements:
#   - errors.txt exists at workdir root
#   - has exactly 3 non-empty lines
#   - each line contains its template's distinguishing substring
#   - the order matches first appearance in the log
set -euo pipefail

if [[ ! -f errors.txt ]]; then
    echo "FAIL: errors.txt missing"
    exit 1
fi

# Load lines, stripping blanks. Use a portable read loop so this runs on
# both bash 3 (macOS dev) and bash 5 (Linux container).
LINES=()
while IFS= read -r line; do LINES+=("$line"); done < <(grep -v '^[[:space:]]*$' errors.txt)
if [[ ${#LINES[@]} -ne 3 ]]; then
    echo "FAIL: expected 3 distinct error signatures, got ${#LINES[@]}"
    printf '  line: %s\n' "${LINES[@]}"
    exit 1
fi

# Determine first-seen order from the seed log.
LOG=logs/app.log
if [[ ! -f "$LOG" ]]; then
    echo "FAIL: seed log $LOG missing (was the workdir corrupted?)"
    exit 1
fi

declare -a templates=("Connection refused to upstream" "Failed to parse JSON payload at offset" "Database query exceeded deadline of")
declare -a first_line_no=()
for t in "${templates[@]}"; do
    n=$(grep -nF "ERROR $t" "$LOG" | head -1 | cut -d: -f1)
    if [[ -z "$n" ]]; then
        echo "FAIL: template '$t' not present in seed log (verifier bug)"
        exit 1
    fi
    first_line_no+=("$n|$t")
done

# Sort templates by first-seen line number.
IFS=$'\n' sorted=($(printf '%s\n' "${first_line_no[@]}" | sort -n))
unset IFS

# Compare against errors.txt order.
i=0
for entry in "${sorted[@]}"; do
    expected_substr="${entry#*|}"
    actual="${LINES[$i]}"
    if [[ "$actual" != *"$expected_substr"* ]]; then
        echo "FAIL: line $((i+1)) of errors.txt does not contain '$expected_substr'"
        echo "  got: $actual"
        exit 1
    fi
    i=$((i+1))
done

echo "PASS: log-triage"
exit 0
