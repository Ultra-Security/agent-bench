#!/usr/bin/env bash
# Verify: incident-readme
#
# Pass conditions:
#   1. POSTMORTEM.md exists at workdir root
#   2. Contains a "# Postmortem:" line
#   3. Contains "## Summary" and "## Suspected commit" headings
#   4. Contains the EXACT short SHA (7 hex) of the commit whose message
#      starts with "deploy: bump connection pool"
set -euo pipefail

if [[ ! -f POSTMORTEM.md ]]; then
    echo "FAIL: POSTMORTEM.md missing"
    exit 1
fi

grep -qE '^# Postmortem:' POSTMORTEM.md || { echo "FAIL: missing '# Postmortem:' title"; exit 1; }
grep -qE '^## Summary' POSTMORTEM.md       || { echo "FAIL: missing '## Summary' section"; exit 1; }
grep -qE '^## Suspected commit' POSTMORTEM.md || { echo "FAIL: missing '## Suspected commit' section"; exit 1; }

SHA=$(git log --pretty=format:'%h %s' | awk '/deploy: bump connection pool/ {print $1; exit}')
if [[ -z "$SHA" ]]; then
    echo "FAIL: verifier could not find the suspect commit (workdir corrupted?)"
    exit 1
fi

if ! grep -qF "$SHA" POSTMORTEM.md; then
    echo "FAIL: POSTMORTEM.md does not contain the correct short SHA ($SHA)"
    exit 1
fi

echo "PASS: incident-readme"
exit 0
