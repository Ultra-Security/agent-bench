# pi-ultra-mcp

A [pi.dev](https://github.com/badlogic/pi-mono) extension that proxies every
tool call through Ultra over MCP stdio. Built for the **Conduit benchmark**
(see [`METHODOLOGY.md`](../../METHODOLOGY.md) §4.3) to isolate two questions
that would otherwise be confounded:

| Variable | Native pi.dev | This extension | Ultra agent |
|---|---|---|---|
| **Substrate** (how tools are dispatched) | direct | MCP stdio | MCP stdio |
| **Harness** (how the agent loop is driven) | pi.dev | pi.dev | Ultra |

Native pi.dev vs `pi-ultra-mcp` measures the cost of routing tool calls
through MCP. `pi-ultra-mcp` vs Ultra measures the cost of Ultra's harness on
top of the same substrate.

## What it does

1. Spawns `ultra start` as a stdio subprocess.
2. Connects with the `@modelcontextprotocol/sdk` TypeScript client.
3. Calls `tools/list` (paginated) to enumerate Ultra's aggregated tools.
4. For each tool, registers a pi.dev tool with the same name, description,
   and JSON Schema.
5. Each tool's handler forwards `params` to Ultra's `tools/call` and returns
   the flattened text result.
6. **No native fallback.** If Ultra fails, the call fails.

The Go reference for the subprocess + stdio pattern lives at
`internal/agent/mcpclient/client.go` in the Ultra repo.

## Prerequisites

- **Node.js** ≥ 20.6.0
- **An Ultra binary** built from commit `8361e094` (or the methodology-pinned commit)
- **`ANTHROPIC_API_KEY`** for pi.dev to talk to Claude

## Pinned versions (per methodology)

| Component | Version |
|---|---|
| pi-mono (`@mariozechner/pi-coding-agent`) | `0.70.6` |
| `@modelcontextprotocol/sdk` | `1.29.0` |
| `typebox` | `1.1.34` |
| Ultra | commit `8361e094` |

## Local run

```bash
npm install

# Required env
export ULTRA_BIN=/absolute/path/to/ultra
export ANTHROPIC_API_KEY=sk-ant-...

# Optional env
export ULTRA_CONFIG=/path/to/ultra/config.yaml   # passed as `--config`
export ULTRA_ARGS="--foo bar"                     # appended after `start`

# Methodology requires --no-builtin-tools so the only tools the LLM sees
# are the ones this extension registers from Ultra.
pi --no-builtin-tools -e ./pi-ultra-mcp.ts "your prompt here"
```

## Docker run

The included `Dockerfile` bakes in pi.dev and the extension. The Ultra
binary is **not** baked in — mount it at runtime via `launch.sh`:

```bash
docker build -t pi-ultra-mcp:dev .

ULTRA_BIN_HOST=/usr/local/bin/ultra \
ANTHROPIC_API_KEY=sk-ant-... \
WORKSPACE_HOST="$PWD" \
  ./launch.sh "find all TODOs in this repo"
```

`launch.sh` mounts:
- the host Ultra binary at `/opt/ultra/ultra` (read-only)
- the host workspace at `/workspace` (read-write, this is where the agent operates)
- `ULTRA_CONFIG_HOST` (optional) at `/etc/ultra` (read-only)

## Smoke test

`./smoke-test.sh` exercises the full extension factory against a stubbed
MCP server (a small Node script that responds to `initialize`, `tools/list`,
and `tools/call`). It asserts that at least one tool was registered.

It does **not** require a real Ultra binary or an Anthropic API key — both
intentionally, so the test can run anywhere `node` and `npm install` work.

```bash
./smoke-test.sh
# expected: "registered 2 tools: mock_echo, mock_ping" then "PASS: ..."
```

The smoke test does not exercise the real `pi` CLI because that would
require an Anthropic key and an interactive TUI. It directly invokes the
default-exported async factory with a mock `ExtensionAPI`, which is the
same code path pi.dev uses internally (see
`packages/coding-agent/src/core/extensions/loader.ts` in pi-mono).

## Verified pi.dev API surface

The methodology assumed two things; both verified against pi-mono v0.70.6:

| Assumption | Status | Source |
|---|---|---|
| `--no-builtin-tools` flag exists and disables built-ins | ✅ | `packages/coding-agent/README.md` line 536; `docs/extensions.md` line 1797 |
| `pi.registerTool(...)` is the public extension API | ✅ | `docs/extensions.md` §"Custom Tools"; `examples/extensions/dynamic-tools.ts` |
| `pi.registerTool` is callable from an `async` factory before `session_start` | ✅ | `docs/extensions.md` §"Async factory functions" — pi awaits the factory before continuing startup |

No fork is needed. Everything we want is exposed through the public
`ExtensionAPI` interface in `@mariozechner/pi-coding-agent`.

### Fork fallback (only if upstream regresses)

If a future pi-mono release removes `--no-builtin-tools`, the fork would:

1. Vendor `@mariozechner/pi-coding-agent@0.70.6` into `packages/pi-fork/`
2. Patch `packages/coding-agent/src/cli.ts` to keep the flag's old behavior
   (skip built-in tool registration in `createAgentSession()` when the flag
   is set)
3. Bump `package.json` to depend on the fork via a relative path or a
   private GitHub tarball

We don't do any of that today; the flag is supported in 0.70.6.

## Schema bridging note

Ultra's MCP tools advertise raw JSON Schema for their `inputSchema`. pi.dev's
`registerTool` expects a TypeBox `TSchema`. We bridge with `Type.Unsafe(jsonSchema)`,
which is TypeBox's documented "trust this schema as-is" escape hatch.
TypeScript-level argument typing on the handler is `unknown` and the schema is
forwarded verbatim to the LLM provider. This matches the methodology's "thin
proxy" requirement — we add no validation Ultra didn't already require.

## File layout

```
pi-ultra-mcp-staging/
├── pi-ultra-mcp.ts     # the extension
├── package.json        # pinned deps
├── tsconfig.json       # strict, ES2022, NodeNext
├── Dockerfile          # node:20-slim + pi + extension
├── launch.sh           # `docker run` wrapper
├── smoke-test.sh       # mock-Ultra MCP server + driver
├── .gitignore
└── README.md           # this file
```
