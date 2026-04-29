# Phase 0 wiring — run report

This report captures the state of the harness after wiring the first
TerminalBench task adapter and `--dry-run` mode for the three real arms.
The Phase 0 exit criterion (per the methodology) is: the harness runs end
to end on one TerminalBench task with all three arms (Ultra-MCP / pi-MCP /
pi-bash) and writes a row per arm to SQLite. This report describes what
was wired, what was verified, and what is deliberately deferred.

## What was wired

### Task adapter — `tasks/terminal-bench/hello-world/`

- `task.yaml` — harness-shaped spec. Mirrors the upstream task constants
  (instruction, image) but overrides `max_iterations=25` and
  `wall_clock_seconds=1800` per methodology Section 3 (the upstream
  `max_agent_timeout_sec` of 900s is tighter; the methodology cap wins).
- `verify.sh` — passes if `/app/hello.txt` OR `./hello.txt` (workdir root)
  contains `"Hello, world!"`. The two-path acceptance bridges Phase 0
  (host-side, workdir cwd) and Phase 1 (containerized, `/app` exists).
- `README.md` — explains the task, the upstream pin, and what is
  intentionally NOT in this directory (no upstream Dockerfile, no canary
  GUID).
- Upstream pin: `laude-institute/terminal-bench` at commit
  `1a6ffa9674b571da0ed040c470cb40c4d85f9b9b` (latest `main` at the time of
  wiring), task path `original-tasks/hello-world/`.

`hello-world` was chosen because TerminalBench's published Sonnet results
report `pass@1 = 1.0` on it, and because the verification surface is small
enough to review by eye.

### `--dry-run` mode in `harness/run.py`

- New `--dry-run` flag on the CLI.
- `execute()` accepts `dry_run: bool` and forwards it to launchers via a
  small dispatcher (`_run_agent`) that introspects each launcher's `run`
  signature. The stub agent stays a one-arg implementation and is unaffected.
- Dry-run workdir paths get a `-dry` suffix so they don't collide with real
  runs in `results/transcripts/`.
- Slashes in task names (e.g. `terminal-bench/hello-world`) are normalized
  to underscores in workdir paths.

### Real-arm launchers

All three real arms (`ultra`, `pi_bash`, `pi_mcp`) now:

- Accept `dry_run=True` and write a clearly-labelled stub transcript with
  `tokens_in=0, tokens_out=0` instead of calling out.
- Pass `task.prompt` on stdin and run with `cwd=workdir` (the methodology's
  fresh-workdir contract, modulo containerization which is still TODO).
- Honor `task.max_iterations` and `task.wall_clock_seconds`.
- Print the intended command in the transcript even when stubbed, so a
  reviewer can verify the call shape without running anything.

Specific shapes:

- **`ultra`** — `ultra agent --max-iterations N`, prompt on stdin.
- **`pi_bash`** — bare `pi`, prompt on stdin.
- **`pi_mcp`** — `pi --no-builtin-tools -e agents/pi-dev-mcp/pi-ultra-mcp.ts`,
  with `ULTRA_BIN` exported so the extension can spawn Ultra over stdio.
  This replaces the previous "delegates to pi_bash" placeholder.

## What was verified

```
$ pytest
============================== 9 passed in 0.28s ==============================

$ python -m harness.run tasks/sanity --agent stub
sanity [stub] PASS in 0.00s -> results/transcripts/sanity-stub-…/transcript.txt

$ python -m harness.run tasks/terminal-bench/hello-world --agent stub
terminal-bench/hello-world [stub] FAIL in 0.06s -> …
  # expected — stub does not write hello.txt; the row landed in sqlite

$ python -m harness.run tasks/terminal-bench/hello-world --agent ultra   --dry-run
$ python -m harness.run tasks/terminal-bench/hello-world --agent pi_bash --dry-run
$ python -m harness.run tasks/terminal-bench/hello-world --agent pi_mcp  --dry-run

$ sqlite3 results/runs.sqlite \
    'select task, agent, passed, tokens_in, tokens_out from runs;'
sanity                       | stub    | 1 | 0 | 0
terminal-bench/hello-world   | stub    | 0 | 0 | 0
terminal-bench/hello-world   | ultra   | 0 | 0 | 0
terminal-bench/hello-world   | pi_bash | 0 | 0 | 0
terminal-bench/hello-world   | pi_mcp  | 0 | 0 | 0
```

`ruff check .` passes. The Phase 0 exit criterion is met: one row per arm
per task, written to SQLite, transcripts on disk, no API calls.

## What is deferred (and why)

Each item below is a Phase-1+ workstream, called out so a reviewer doesn't
mistake stubbed behavior for done behavior.

- **Real-arm runs against the model.** Gated on the user supplying
  `ANTHROPIC_API_KEY` and the binaries (`ultra`, `pi`) being on `PATH` at
  the methodology-pinned versions. The harness will run them today; this
  report just doesn't include the cost.
- **Containerization per `task.image`.** Methodology Section 3 requires all
  arms to run inside the same Debian-slim base with an egress allow-list.
  Today every launcher runs on the host with the workdir as cwd. The TODO
  is marked in each launcher and called out in `task.yaml` comments.
- **Token accounting.** `tokens_in` / `tokens_out` are `0` in dry-run rows
  and `None` in non-dry-run stub rows. Real captures need (a) the Ultra-side
  JSONL event stream from `cmd/agent-bench-runner` (planned in the upstream
  Ultra repo), and (b) parsing pi.dev's transcript or provider rate-limit
  headers for the pi.dev arms. Methodology Section 6 makes this a hard
  requirement before any results writeup.
- **Egress allow-lists per task.** The `task.yaml` has no `network` field
  yet; tasks that need network will need a schema bump alongside the
  containerization work.
- **Per-tool-call event capture.** Methodology Section 6 references a
  `runs` row plus a per-event table; only the run row exists today.

## Methodology observations

Things noticed while wiring that the methodology authors should consider —
none warrant a CHANGELOG entry yet, just a heads-up:

- The methodology and the upstream task disagree on `max_agent_timeout_sec`
  (upstream says 900s for hello-world; methodology says 1800s for every
  task). The locked methodology wins by design, but Section 3 could note
  explicitly that the harness ignores per-task upstream timeouts.
- Methodology Section 4.1 says "no custom tweaks" for Ultra config but
  Section 4.3 reuses "the same Ultra config." Worth confirming the
  pi-MCP extension doesn't require any extra MCP upstreams beyond what
  Ultra-MCP arm runs with — the extension just enumerates whatever Ultra
  exposes, so they should match by construction.

## What the user needs to do

1. (optional) Re-run the dry-run commands locally to spot-check transcripts.
2. To do a real run on one task with one arm:
   - Build/install `ultra` from the methodology-pinned commit; put it on `PATH`.
   - Install `pi` at the methodology-pinned `pi-mono` release; put it on `PATH`.
   - `cd agents/pi-dev-mcp && npm install` (only needed for `pi_mcp` arm).
   - `export ANTHROPIC_API_KEY=sk-ant-...`
   - `python -m harness.run tasks/terminal-bench/hello-world --agent ultra`
3. Once the real run lands cleanly, the next blocking workstream is
   containerization + token capture, in that order.
