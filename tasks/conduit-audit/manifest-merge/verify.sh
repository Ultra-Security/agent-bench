#!/usr/bin/env bash
# Verify: manifest-merge
#
# Checks the parsed YAML structure of merged.yaml. Uses python so it does
# not depend on yq being installed in the container.
set -euo pipefail

if [[ ! -f merged.yaml ]]; then
    echo "FAIL: merged.yaml missing"
    exit 1
fi

python3 - <<'PY'
import sys, yaml
try:
    with open("merged.yaml") as f:
        m = yaml.safe_load(f)
except Exception as e:
    print(f"FAIL: merged.yaml not parseable: {e}")
    sys.exit(1)

expected = {
    "name": "orders-api",
    "replicas": 5,
    "image": "orders-api:1.2.3",
    "resources": {"cpu": "500m", "memory": "256Mi"},
    "env": {"LOG_LEVEL": "debug", "FEATURE_X": "enabled"},
}

if m != expected:
    print("FAIL: merged.yaml does not match expected merge")
    print("  expected:", expected)
    print("  actual:  ", m)
    sys.exit(1)

print("PASS: manifest-merge")
PY
