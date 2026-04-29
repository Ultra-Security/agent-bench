# agent-bench

The Conduit benchmark: an empirical comparison of MCP-routed vs bash-focused
agentic environments.

This repo hosts the harness, task suites, and analysis notebooks for the
Conduit study. The full pre-registered design lives in
[`METHODOLOGY.md`](./METHODOLOGY.md) — read that first if you want to know
what this is measuring and why.

## Status

Phase 0 (April 2026): harness skeleton plus the first TerminalBench task
adapter (`tasks/terminal-bench/hello-world`) wired end to end. The plumbing
runs against a stub agent and against all three real arms in `--dry-run`
mode (no API key required). Real model runs, full TerminalBench / SWE-bench
coverage, and containerization arrive in Phase 1.

## Quickstart

```bash
git clone https://github.com/Ultra-Security/agent-bench
cd agent-bench
pip install -e ".[dev]"

pytest

# 1. Sanity stub — proves the harness loads, runs, and writes a row.
python -m harness.run tasks/sanity --agent stub

# 2. Real task with stub — exercises the TerminalBench task adapter.
#    The stub agent does not solve the task, so the row records passed=0.
#    That's expected: we're testing wiring, not capability.
python -m harness.run tasks/terminal-bench/hello-world --agent stub

# 3. Each real arm in dry-run mode — no LLM call, no API key needed.
#    Writes one row per arm with tokens_in=0, tokens_out=0, passed=0.
python -m harness.run tasks/terminal-bench/hello-world --agent ultra   --dry-run
python -m harness.run tasks/terminal-bench/hello-world --agent pi_bash --dry-run
python -m harness.run tasks/terminal-bench/hello-world --agent pi_mcp  --dry-run
```

Inspect the rows:

```bash
sqlite3 results/runs.sqlite 'select task, agent, passed, tokens_in, tokens_out from runs;'
```

### Real run (requires an Anthropic API key)

A real arm run hits the Anthropic API and burns tokens. Don't do this until
you've eyeballed a dry run. The arms expect:

- `ANTHROPIC_API_KEY` in env (used by all three arms via the methodology's
  shared key path)
- `ultra` on `PATH` for the `ultra` and `pi_mcp` arms, built from the
  methodology-pinned commit (see `METHODOLOGY.md` §4.1)
- `pi` on `PATH` for the `pi_bash` and `pi_mcp` arms, at the
  methodology-pinned `pi-mono` release (see `METHODOLOGY.md` §4.2)
- The pi-MCP extension installed in `agents/pi-dev-mcp/` (already shipped
  in this repo; see that directory's README for `npm install` steps)

Then drop `--dry-run`:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python -m harness.run tasks/terminal-bench/hello-world --agent ultra
```

What's still deferred: container isolation per `task.image`, egress
allow-lists, and provider token-usage capture. See `RUN_REPORT.md`.

## Layout

```
harness/        # python entry point and arm launchers
  agents/       # one module per arm: stub, ultra, pi_bash, pi_mcp
  storage/      # sqlite persistence
tasks/          # task directories (task.yaml + verify.sh [+ events.yaml])
  sanity/                    # always-passes smoke task for harness validation
  terminal-bench/hello-world # first TerminalBench task adapter (Phase 0 wiring)
agents/         # arm Dockerfiles + launch scripts (added per Phase 1 ticket)
analysis/       # Quarto notebooks (Phase 1)
results/        # sqlite + transcripts (gitignored)
```

## Arms

| Arm        | Status   | Notes                                                  |
|------------|----------|--------------------------------------------------------|
| `stub`     | ready    | Always-pass agent for CI                               |
| `ultra`    | dry-run  | Subprocess + `--dry-run`; needs `cmd/agent-bench-runner` for tokens |
| `pi_bash`  | dry-run  | Subprocess + `--dry-run`                                |
| `pi_mcp`   | dry-run  | Subprocess + `--dry-run`; invokes pi.dev with the extension and `ULTRA_BIN` |

## License

MIT — see [`LICENSE`](./LICENSE).
