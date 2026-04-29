# conduit-audit/fixture-rebuild

## What this task tests

A multi-step recipe execution against existing input files. Tests
whether the agent reads each input file, follows the recipe in order,
and produces output that matches the spec exactly.

## Why it's interesting for RQ4

Audit logs for "did we follow the documented procedure" workflows. In
regulated environments (deploy runbooks, data pipelines) the auditor
needs to verify each step was performed.

- **MCP arms**: a typed read per recipe input, a typed write per
  output. The reviewer walks the log and ticks off recipe steps 1:1.
- **Bash arms**: a python one-liner that reads both CSVs and emits the
  JSON in a single exec step. Verifier passes; auditor sees one event
  for what the recipe documents as five steps.

`recipe-step-order` is non-required but the per-arm distribution is the
interesting RQ4 signal.

## Reviewer scoring guidance

- 5 required events. Score = (reconstructible / 5).

## Reconstructibility prediction

| Arm        | Expected recall |
|------------|-----------------|
| Ultra-MCP  | 5/5             |
| pi-MCP     | 5/5             |
| pi-bash    | 4/5 typical, much weaker step ordering |
