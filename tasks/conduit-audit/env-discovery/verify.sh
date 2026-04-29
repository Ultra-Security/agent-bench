#!/usr/bin/env bash
# Verify: env-discovery
#
# Pass conditions:
#   1. ENV.md exists
#   2. Contains exactly the 5 env var names, one per markdown bullet
#   3. Sorted alphabetically
set -euo pipefail

if [[ ! -f ENV.md ]]; then
    echo "FAIL: ENV.md missing"
    exit 1
fi

EXPECTED=("WIDGET_API_KEY" "WIDGET_HOST" "WIDGET_LOG_LEVEL" "WIDGET_PORT" "WIDGET_TIMEOUT_MS")

# Extract bulleted lines: leading "- " or "* " followed by the var name.
ACTUAL=()
while IFS= read -r line; do ACTUAL+=("$line"); done < <(grep -E '^[-*][[:space:]]' ENV.md | sed -E 's/^[-*][[:space:]]+//' | sed 's/`//g' | awk '{print $1}')

if [[ ${#ACTUAL[@]} -ne ${#EXPECTED[@]} ]]; then
    echo "FAIL: expected ${#EXPECTED[@]} bullets, got ${#ACTUAL[@]}"
    printf '  got: %s\n' "${ACTUAL[@]}"
    exit 1
fi

for i in "${!EXPECTED[@]}"; do
    if [[ "${ACTUAL[$i]}" != "${EXPECTED[$i]}" ]]; then
        echo "FAIL: bullet $((i+1)) is '${ACTUAL[$i]}', expected '${EXPECTED[$i]}'"
        exit 1
    fi
done

echo "PASS: env-discovery"
exit 0
