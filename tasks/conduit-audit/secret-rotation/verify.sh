#!/usr/bin/env bash
# Verify: secret-rotation
#
# Pass conditions:
#   1. The old key string MUST NOT appear anywhere under the workdir.
#   2. The new key string MUST appear in all three seed config files.
#   3. ROTATED.md exists at the workdir root and lists at least the three
#      seed config paths (one per line, anywhere in the file).
set -euo pipefail

OLD="sk-test-OLDKEY-1111111111"
NEW="sk-test-NEWKEY-2222222222"
FILES=("config/app.env" "config/worker.yaml" "config/client.json")

# 1. No occurrence of the old key anywhere.
if grep -r --binary-files=without-match -F "$OLD" . >/dev/null 2>&1; then
    echo "FAIL: old key still present somewhere under workdir"
    grep -r --binary-files=without-match -F "$OLD" . || true
    exit 1
fi

# 2. New key present in each of the three config files.
for f in "${FILES[@]}"; do
    if [[ ! -f "$f" ]]; then
        echo "FAIL: missing $f"
        exit 1
    fi
    if ! grep -F "$NEW" "$f" >/dev/null; then
        echo "FAIL: new key not in $f"
        exit 1
    fi
done

# 3. ROTATED.md exists and references each rotated file.
if [[ ! -f "ROTATED.md" ]]; then
    echo "FAIL: ROTATED.md not found"
    exit 1
fi
for f in "${FILES[@]}"; do
    if ! grep -F "$f" ROTATED.md >/dev/null; then
        echo "FAIL: ROTATED.md does not mention $f"
        exit 1
    fi
done

echo "PASS: secret-rotation"
exit 0
