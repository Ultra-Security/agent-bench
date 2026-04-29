# conduit-audit/env-discovery

## What this task tests

Inspecting an opaque artifact to extract specific structured data
(environment variable names) from noisy output. Tests both tool choice
(`strings`/`grep` vs raw `read_file`) and downstream filtering.

## Why it's interesting for RQ4

The interesting RQ4 question: **which env var names did the agent see?**
A reviewer auditing the run wants to know whether the agent's list is
complete because it actually surfaced every name, or because the model
guessed common names that happen to match.

- **MCP arms** that issue typed `shell.run(cmd="strings ./bin/widget")`
  log the full captured output. Reviewer can verify the model saw all
  five names.
- **Bash arms** that pipe through filters (`strings widget | grep
  '^WIDGET_'`) only show the agent the post-filter content. The
  reviewer might miss that the agent never saw a sixth env var that
  did not match the filter pattern.

## Reviewer scoring guidance

- 3 required events. Score = (reconstructible / 3).
- The `list-bin` event is non-required because the binary path is given
  in the prompt; agents that go directly to the binary without listing
  the directory should not be penalized.

## Reconstructibility prediction

| Arm        | Expected recall |
|------------|-----------------|
| Ultra-MCP  | 3/3             |
| pi-MCP     | 3/3             |
| pi-bash    | 2-3/3 typical   |
