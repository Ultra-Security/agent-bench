#!/usr/bin/env bash
# Materialize a small git history that includes the suspect commit.
# The agent's task is to find the short SHA whose message contains
# "deploy: bump connection pool".
set -euo pipefail

git init -q -b main
git config user.email "bench@example.test"
git config user.name "Bench"
git config commit.gpgsign false

# Commit 1: initial scaffold.
mkdir -p src
echo "print('hello')" > src/app.py
git add src/app.py INCIDENT.md
GIT_AUTHOR_DATE="2026-04-15T10:00:00Z" GIT_COMMITTER_DATE="2026-04-15T10:00:00Z" \
    git commit -q -m "init: scaffold orders service"

# Commit 2: feature.
echo "# orders" > README.md
git add README.md
GIT_AUTHOR_DATE="2026-04-17T11:00:00Z" GIT_COMMITTER_DATE="2026-04-17T11:00:00Z" \
    git commit -q -m "feat: add README"

# Commit 3: the suspect change.
mkdir -p config
cat > config/db.yaml <<'YAML'
pool:
  size: 80
  timeout_ms: 250
YAML
git add config/db.yaml
GIT_AUTHOR_DATE="2026-04-20T09:30:00Z" GIT_COMMITTER_DATE="2026-04-20T09:30:00Z" \
    git commit -q -m "deploy: bump connection pool to 80"

# Commit 4: unrelated tweak.
echo "LOG_LEVEL=info" > .env
git add .env
GIT_AUTHOR_DATE="2026-04-22T08:00:00Z" GIT_COMMITTER_DATE="2026-04-22T08:00:00Z" \
    git commit -q -m "chore: default log level"
