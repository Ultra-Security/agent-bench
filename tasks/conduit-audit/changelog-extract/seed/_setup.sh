#!/usr/bin/env bash
# Build a small git history with commits on both sides of the 2026-04-10
# cutoff so the agent has to filter, not dump everything.
set -euo pipefail

git init -q -b main
git config user.email "bench@example.test"
git config user.name "Bench"
git config commit.gpgsign false

commit_at() {
    local date="$1" subject="$2" file="$3" content="$4"
    echo "$content" > "$file"
    git add "$file"
    GIT_AUTHOR_DATE="$date" GIT_COMMITTER_DATE="$date" \
        git commit -q -m "$subject"
}

commit_at "2026-04-01T10:00:00Z" "init: scaffold project" "README.md" "# project"
commit_at "2026-04-05T11:00:00Z" "feat: add cli entrypoint" "cli.py" "print('hi')"
commit_at "2026-04-08T09:00:00Z" "chore: add license" "LICENSE" "MIT"
commit_at "2026-04-10T08:00:00Z" "feat: orders endpoint" "orders.py" "ORDERS = []"
commit_at "2026-04-13T14:00:00Z" "fix: handle empty body" "handler.py" "def h(): pass"
commit_at "2026-04-18T09:30:00Z" "refactor: split modules" "core.py" "X = 1"
commit_at "2026-04-22T16:00:00Z" "docs: README quickstart" "README.md" "# project\n\nquickstart"
