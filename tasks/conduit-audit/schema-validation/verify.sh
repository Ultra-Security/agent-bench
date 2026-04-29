#!/usr/bin/env bash
# Verify: schema-validation
set -euo pipefail

if [[ ! -f valid.txt ]]; then echo "FAIL: valid.txt missing"; exit 1; fi
if [[ ! -f invalid.txt ]]; then echo "FAIL: invalid.txt missing"; exit 1; fi

normalize() {
    grep -v '^[[:space:]]*$' "$1" | sed 's/[[:space:]]*$//' | sort
}

EXPECTED_VALID=$'doc1.json\ndoc5.json'
EXPECTED_INVALID=$'doc2.json\ndoc3.json\ndoc4.json'

actual_valid=$(normalize valid.txt)
actual_invalid=$(normalize invalid.txt)

if [[ "$actual_valid" != "$EXPECTED_VALID" ]]; then
    echo "FAIL: valid.txt contents wrong"
    echo "  expected:"; echo "$EXPECTED_VALID" | sed 's/^/    /'
    echo "  actual:";   echo "$actual_valid"   | sed 's/^/    /'
    exit 1
fi
if [[ "$actual_invalid" != "$EXPECTED_INVALID" ]]; then
    echo "FAIL: invalid.txt contents wrong"
    echo "  expected:"; echo "$EXPECTED_INVALID" | sed 's/^/    /'
    echo "  actual:";   echo "$actual_invalid"   | sed 's/^/    /'
    exit 1
fi

echo "PASS: schema-validation"
exit 0
