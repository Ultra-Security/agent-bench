# terminal-bench/hello-world

The simplest TerminalBench task: write `"Hello, world!"` to a file. We use
this as the Phase 0 wiring task — the goal is exercising the harness end to
end (task spec → arm launcher → verify → SQLite row), not measuring agent
capability.

## Why this task

Per the methodology Section 5, TerminalBench is one of two Phase-1 benchmarks.
Before driving the full task list, the harness needs at least one task that
provably runs through every arm. `hello-world` is the right pick because:

- Upstream reports `pass@1 = 1.0` on Sonnet, so a passing real run is
  signal that the wiring is healthy rather than a measurement of difficulty.
- Single-step, no network egress, no third-party deps — easy to reason about
  when something fails.
- Both the instruction and the verification are tiny, so this directory can
  be reviewed by eye.

## Upstream pin

| Field | Value |
|---|---|
| repo | [`laude-institute/terminal-bench`](https://github.com/laude-institute/terminal-bench) |
| commit | `1a6ffa9674b571da0ed040c470cb40c4d85f9b9b` |
| task path | `original-tasks/hello-world/` |

The pin lives in `task.yaml` under `upstream:`. Bumping the pin is a
methodology event — log it in `METHODOLOGY.md`'s CHANGELOG.

## What this directory contains

- `task.yaml` — harness-shaped task spec (image, prompt, max_iterations=25,
  wall_clock_seconds=1800 per methodology §3, plus the upstream pin)
- `verify.sh` — pass/fail check that mirrors the upstream pytest assertions
  (`tests/test_outputs.py`). Accepts either the canonical `/app/hello.txt`
  (post-containerization) or `./hello.txt` in the workdir (Phase 0)
- This `README.md`

## What this directory does NOT contain

- The upstream `Dockerfile`, `docker-compose.yaml`, `solution.sh`, or
  `tests/` directory. Phase 0 runs agents on the host, not inside the
  upstream image; pulling those files in before they're used would just
  invite drift. They will be vendored or reachable by SHA when the harness
  gains containerization (methodology §3).
- The upstream `terminal-bench-canary` GUID. We deliberately omit it so
  this repo never ships benchmark canaries.

## How to run it

See the repo `README.md` Quickstart. tl;dr:

```bash
# Stub agent — proves the task adapter parses and verifies correctly.
python -m harness.run tasks/terminal-bench/hello-world --agent stub

# Real arms in dry-run mode — exercises subprocess wiring without API calls.
python -m harness.run tasks/terminal-bench/hello-world --agent ultra   --dry-run
python -m harness.run tasks/terminal-bench/hello-world --agent pi_bash --dry-run
python -m harness.run tasks/terminal-bench/hello-world --agent pi_mcp  --dry-run
```

Note that the stub and dry-run runs intentionally do not satisfy the verify
check (no agent actually writes the file) — they exercise the harness, not
the model. A real arm with a live `ANTHROPIC_API_KEY` is what closes the
loop.
