# conduit-audit/manifest-merge

## What this task tests

A structured-data merge with a precedence rule. The shallow-merge
semantics are deliberately specified (top-level keys replace) so the
agent can't excuse a "deep merge" that preserves base.env.REGION.

## Why it's interesting for RQ4

- **MCP arms**: typed reads, then a single typed write of the merged
  YAML. Reviewer can identify exactly which keys were read from each
  file (via the read events) and the final state.
- **Bash arms** that compose a `python -c "import yaml; ..."` one-liner
  log only the script invocation. The per-key merge logic is opaque to
  the auditor unless they inspect the script string. A bash arm that
  uses `yq` runs a command per key and exposes more fine-grained intent
  but adds a dependency.

This task probes whether substrate granularity affects "key provenance"
audits — a real pattern in regulated deploys.

## Reviewer scoring guidance

- 3 required events. Score = (reconstructible / 3).
- For the qualitative `key-provenance-traceable` signal, count keys
  whose source the reviewer can determine from the log alone.

## Reconstructibility prediction

| Arm        | Expected recall |
|------------|-----------------|
| Ultra-MCP  | 3/3             |
| pi-MCP     | 3/3             |
| pi-bash    | 3/3 verifier-pass, weaker provenance |
