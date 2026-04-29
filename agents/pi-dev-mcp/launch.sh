#!/usr/bin/env bash
# launch.sh
#
# Wrapper around `docker run` for the pi-ultra-mcp benchmark image.
# Mounts:
#   - the host Ultra binary at /opt/ultra/ultra (required)
#   - an optional Ultra config dir at /etc/ultra
#   - the host workspace at /workspace (the repo the agent operates on)
#
# Required env:
#   ULTRA_BIN_HOST   absolute path to the ultra binary on the host
#   ANTHROPIC_API_KEY  for pi.dev to talk to Claude
#
# Optional env:
#   ULTRA_CONFIG_HOST  absolute path to ultra config (mounted to /etc/ultra)
#   WORKSPACE_HOST     absolute path to the workspace dir (default: $PWD)
#   IMAGE              docker image tag (default: pi-ultra-mcp:dev)
#
# Usage:
#   ULTRA_BIN_HOST=/usr/local/bin/ultra \
#   ANTHROPIC_API_KEY=sk-ant-... \
#     ./launch.sh "find all TODOs in this repo"

set -euo pipefail

: "${ULTRA_BIN_HOST:?Set ULTRA_BIN_HOST to the absolute path of the ultra binary}"
: "${ANTHROPIC_API_KEY:?Set ANTHROPIC_API_KEY}"
WORKSPACE_HOST="${WORKSPACE_HOST:-$PWD}"
IMAGE="${IMAGE:-pi-ultra-mcp:dev}"

if [[ ! -x "$ULTRA_BIN_HOST" ]]; then
  echo "ULTRA_BIN_HOST '$ULTRA_BIN_HOST' is not executable" >&2
  exit 2
fi

mounts=(
  -v "$ULTRA_BIN_HOST:/opt/ultra/ultra:ro"
  -v "$WORKSPACE_HOST:/workspace"
)

env_args=(
  -e "ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY"
  -e "ULTRA_BIN=/opt/ultra/ultra"
)

if [[ -n "${ULTRA_CONFIG_HOST:-}" ]]; then
  mounts+=( -v "$ULTRA_CONFIG_HOST:/etc/ultra:ro" )
  env_args+=( -e "ULTRA_CONFIG=/etc/ultra/config.yaml" )
fi

if [[ -n "${ULTRA_ARGS:-}" ]]; then
  env_args+=( -e "ULTRA_ARGS=$ULTRA_ARGS" )
fi

exec docker run --rm -it \
  "${mounts[@]}" \
  "${env_args[@]}" \
  "$IMAGE" \
  pi --no-builtin-tools -e /app/pi-ultra-mcp.ts "$@"
