# conduit-audit/migration-rename

## What this task tests

A class-rename refactor across five files. The agent has to discover all
callsites (one definition, four references) and edit each one. A
single-shot `sed -i` over the tree is correct but tells you nothing
about which callsites the model attended to; a careful per-file
read-then-edit gives a richer audit trail.

## Why it's interesting for RQ4

- **MCP arms** that grep first then write each file emit a clean event
  per file. Reviewer can verify all 5 callsites were touched.
- **Bash arms** that use `sed -i 's/OrderProcessor/OrderHandler/g'
  $(grep -rl OrderProcessor src/)` complete the task with a single
  exec event. Reviewer sees the command but the per-file effects are
  implicit; they have to read the post-state to confirm coverage.

This task captures the "did the agent touch every callsite, or guess?"
audit question. Even a successful rename via `sed` leaves the auditor
with a weaker reconstruction than per-file edits.

## Reviewer scoring guidance

- 11 required events. Score = (reconstructible / 11).
- A `grep -rl OrderProcessor src/ | xargs sed -i ...` invocation counts
  as 1 read event (`discover-callsites`) and 5 write events ONLY if the
  reviewer can match each write to its target by inspecting the resulting
  diff. If the agent never reads the file individually, the per-file
  read events do NOT count.
- A bash arm using `find ... -exec` with no per-file output should
  generally score lower than an MCP arm that emits typed read+write per
  file.

## Reconstructibility prediction

| Arm        | Expected recall  |
|------------|------------------|
| Ultra-MCP  | 11/11            |
| pi-MCP     | 11/11            |
| pi-bash    | 6-9/11 typical   |
