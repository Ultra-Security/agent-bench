#!/usr/bin/env bash
# smoke-test.sh
#
# Validates that the extension can:
#   1. Spawn a subprocess that speaks MCP over stdio
#   2. Successfully run tools/initialize and tools/list
#   3. Register every returned tool with pi.dev
#
# We do NOT require a real Ultra binary or an Anthropic API key here.
# Instead we stub Ultra with a tiny Node script that speaks MCP just well
# enough for the extension to enumerate two fake tools.
#
# Pass criterion: the smoke driver reports "registered N tools (N >= 1)".
#
# This script does not invoke the real `pi` CLI — that would require an
# Anthropic key and an interactive TUI. Instead we drive the extension
# directly with a minimal mock ExtensionAPI, exercising the same code path
# pi.dev itself uses (the default-exported async factory).

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

if [[ ! -d node_modules ]]; then
  echo "node_modules not found. Run 'npm install' first." >&2
  exit 2
fi

# Mock Ultra: a Node script that responds to JSON-RPC over stdio with two tools.
MOCK_ULTRA_DIR="$(mktemp -d -t pi-ultra-mcp-smoke.XXXXXX)"
MOCK_ULTRA="$MOCK_ULTRA_DIR/mock-ultra.mjs"
DRIVER="$MOCK_ULTRA_DIR/driver.ts"
trap 'rm -rf "$MOCK_ULTRA_DIR"' EXIT

cat >"$MOCK_ULTRA" <<'EOF'
// Minimal MCP server stub. Speaks only what the smoke test needs:
//   - initialize          -> capabilities { tools: {} }
//   - tools/list          -> two tools
//   - tools/call          -> echo args
//   - notifications/initialized (ignored)
import { createInterface } from "node:readline";

const rl = createInterface({ input: process.stdin });

function send(msg) {
  process.stdout.write(JSON.stringify(msg) + "\n");
}

rl.on("line", (line) => {
  if (!line.trim()) return;
  let req;
  try { req = JSON.parse(line); } catch { return; }
  if (req.method === "initialize") {
    send({
      jsonrpc: "2.0",
      id: req.id,
      result: {
        protocolVersion: "2025-06-18",
        capabilities: { tools: {} },
        serverInfo: { name: "mock-ultra", version: "0.0.0" },
      },
    });
  } else if (req.method === "tools/list") {
    send({
      jsonrpc: "2.0",
      id: req.id,
      result: {
        tools: [
          {
            name: "mock_echo",
            description: "Echo back the provided text.",
            inputSchema: {
              type: "object",
              properties: { text: { type: "string" } },
              required: ["text"],
            },
          },
          {
            name: "mock_ping",
            description: "Return pong.",
            inputSchema: { type: "object", properties: {} },
          },
        ],
      },
    });
  } else if (req.method === "tools/call") {
    send({
      jsonrpc: "2.0",
      id: req.id,
      result: {
        content: [{ type: "text", text: `mock:${req.params?.name}` }],
        isError: false,
      },
    });
  } else if (req.method === "notifications/initialized" || req.id === undefined) {
    // notifications, no response needed
  } else if (req.id !== undefined) {
    send({ jsonrpc: "2.0", id: req.id, error: { code: -32601, message: "method not found" } });
  }
});
EOF

# Wrapper that ignores its arg list and execs the mock on stdin/stdout.
WRAPPER="$MOCK_ULTRA_DIR/ultra-wrapper.sh"
cat >"$WRAPPER" <<WEOF
#!/usr/bin/env bash
exec node "$MOCK_ULTRA"
WEOF
chmod +x "$WRAPPER"

# Driver: load the extension with a fake ExtensionAPI and count registrations.
cat >"$DRIVER" <<EOF
// Drives pi-ultra-mcp.ts with a stub ExtensionAPI and the mock Ultra above.
//
// pi-ultra-mcp's ultraCommand() always prepends "start" as argv[1]. We work
// around that by using a wrapper shell script as ULTRA_BIN that ignores
// argv (the literal "start") and execs node on the mock instead.
process.env.ULTRA_BIN = "$MOCK_ULTRA_DIR/ultra-wrapper.sh";
process.env.ULTRA_ARGS = "";

const registered: string[] = [];
const fakePi = {
  on: () => {},
  registerTool: (def: any) => { registered.push(def.name); },
  registerCommand: () => {},
  registerShortcut: () => {},
  registerFlag: () => {},
  registerProvider: () => {},
  registerMessageRenderer: () => {},
  sendMessage: () => {},
  sendUserMessage: () => {},
  events: { emit: () => {}, on: () => () => {} },
  exec: async () => ({ stdout: "", stderr: "", exitCode: 0 }),
  appendEntry: () => {},
  setActiveTools: () => {},
  getActiveTools: () => [],
  getAllTools: () => [],
  addAutocompleteProvider: () => () => {},
  setModel: () => {},
  setThinkingLevel: () => {},
};

import("$HERE/pi-ultra-mcp.ts").then(async (mod) => {
  const factory = mod.default;
  await factory(fakePi as any);
  console.log("registered " + registered.length + " tools: " + registered.join(", "));
  if (registered.length < 1) {
    console.error("FAIL: zero tools registered");
    process.exit(1);
  }
  console.log("PASS: registered N tools (N >= 1)");
  process.exit(0);
}).catch((err) => {
  console.error("FAIL:", err?.stack ?? err);
  process.exit(1);
});
EOF

# tsx runs TypeScript directly, no compile step needed.
exec npx --no-install tsx "$DRIVER"
