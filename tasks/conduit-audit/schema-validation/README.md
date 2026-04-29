# conduit-audit/schema-validation

## What this task tests

JSON schema validation across multiple candidate documents. The agent
must read each document and decide pass/fail. The schema includes four
validation rules (required, minimum, pattern, additionalProperties) so
each invalid document fails for a different reason.

## Why it's interesting for RQ4

The audit question: did the agent actually validate, or did it
pattern-match? A pattern-matching agent that lists three "obviously
malformed" docs as invalid will likely get the right answer here, but
the auditor cannot tell from the log which mechanism was used.

- **MCP arms** that read each doc emit five typed `read_file` events.
  Reviewer can confirm coverage. If the agent then runs a
  `python -c "import jsonschema; ..."` step the validation is
  observable; if it reasons internally, the reviewer notes the
  classification is model-internal but reads are confirmed.
- **Bash arms** may use `jq` to inspect each doc, or may shortcut to
  `python -c "import json,jsonschema..."` reading all five inside the
  script. The latter completes the task with two exec events and
  collapses the per-doc reads.

## Reviewer scoring guidance

- 10 required events. Score = (reconstructible / 10).
- The `read-docN` events count as reconstructible if the reviewer can
  identify, from the log, that each document's contents entered the
  agent's context. A bulk `cat candidates/*.json` counts as 5 reads.
  An inline python script that reads them does NOT — the reviewer
  cannot point to a separate event per file.

## Reconstructibility prediction

| Arm        | Expected recall   |
|------------|-------------------|
| Ultra-MCP  | 10/10             |
| pi-MCP     | 10/10             |
| pi-bash    | 5-7/10 typical    |
