# agent-bench

The Conduit benchmark: an empirical comparison of MCP-routed vs bash-focused
agentic environments.

This repo hosts the harness, task suites, and analysis notebooks for the
Conduit study. The full pre-registered design lives in
[`METHODOLOGY.md`](./METHODOLOGY.md) — read that first if you want to know
what this is measuring and why.

## Status

Phase 0 (April 2026): harness skeleton only. The plumbing runs end-to-end
against a stub agent. Real model wiring, the pi-MCP extension, and the
TerminalBench / SWE-bench task adapters arrive in Phase 1.

## Quickstart

```bash
git clone https://github.com/Ultra-Security/agent-bench
cd agent-bench
pip install -e ".[dev]"

pytest
python -m harness.run tasks/sanity --agent stub
```

That last command writes a row to `results/runs.sqlite` and prints something
like:

```
sanity [stub] PASS in 0.05s -> results/transcripts/sanity-stub-…/transcript.txt
```

Inspect the row:

```bash
sqlite3 results/runs.sqlite 'select task, agent, passed, wall_seconds from runs;'
```

## Layout

```
harness/        # python entry point and arm launchers
  agents/       # one module per arm: stub, ultra, pi_bash, pi_mcp
  storage/      # sqlite persistence
tasks/          # task directories (task.yaml + verify.sh [+ events.yaml])
  sanity/       # always-passes smoke task for harness validation
agents/         # arm Dockerfiles + launch scripts (added per Phase 1 ticket)
analysis/       # Quarto notebooks (Phase 1)
results/        # sqlite + transcripts (gitignored)
```

## Arms

| Arm        | Status   | Notes                                                  |
|------------|----------|--------------------------------------------------------|
| `stub`     | ready    | Always-pass agent for CI                               |
| `ultra`    | scaffold | Subprocess shape in place; needs `cmd/agent-bench-runner` |
| `pi_bash`  | scaffold | Subprocess shape in place                              |
| `pi_mcp`   | scaffold | Delegates to `pi_bash` pending the pi-MCP extension    |

## License

MIT — see [`LICENSE`](./LICENSE).
