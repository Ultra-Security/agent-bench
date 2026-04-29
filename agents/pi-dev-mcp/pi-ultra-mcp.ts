/**
 * pi-ultra-mcp.ts
 *
 * pi.dev extension for the Conduit benchmark.
 *
 * Maps to methodology §4.3 ("MCP-substrate variant of pi.dev"):
 *   - §4.3.1  Spawn Ultra as a stdio subprocess
 *   - §4.3.2  Connect via the MCP TypeScript SDK
 *   - §4.3.3  tools/list -> register every tool with pi.registerTool()
 *   - §4.3.4  Each registered tool forwards to Ultra's tools/call
 *   - §4.3.5  No native fallback — failures surface to the agent
 *
 * Run with:
 *   pi --no-builtin-tools -e ./pi-ultra-mcp.ts
 *
 * `--no-builtin-tools` (verified against pi-mono v0.70.6 README and
 * docs/extensions.md §"Overriding Built-in Tools") disables pi's read/bash/edit/
 * write/grep/find/ls so the only tools the LLM sees are the ones this
 * extension registers from Ultra. That's the substrate isolation the
 * methodology requires.
 */

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { Type, type TSchema } from "typebox";

// ---------------------------------------------------------------------------
// §4.3.1 Subprocess configuration
//
// ULTRA_BIN  - path to the ultra binary (default: "ultra" on PATH)
// ULTRA_ARGS - extra args passed after "start" (space-separated)
// ULTRA_CONFIG - shorthand for --config <path>
//
// Mirrors the Go reference at
// /Users/chase/Projects/ultra/internal/agent/mcpclient/client.go
// ---------------------------------------------------------------------------
function ultraCommand(): { command: string; args: string[] } {
	const command = process.env.ULTRA_BIN ?? "ultra";
	const args: string[] = ["start"];
	if (process.env.ULTRA_CONFIG) {
		args.push("--config", process.env.ULTRA_CONFIG);
	}
	if (process.env.ULTRA_ARGS) {
		// Cheap split. Methodology pins env vars; we don't need shell quoting here.
		for (const piece of process.env.ULTRA_ARGS.split(/\s+/)) {
			if (piece.length > 0) args.push(piece);
		}
	}
	return { command, args };
}

// ---------------------------------------------------------------------------
// §4.3.3 Schema bridging
//
// Ultra returns each tool's input schema as raw JSON Schema (per the MCP spec).
// pi.dev's registerTool expects a TypeBox `TSchema`. TypeBox's `Type.Unsafe<T>(schema)`
// is the documented escape hatch for "I already have JSON Schema, just trust it" —
// the runtime stores the literal schema object and pi.dev forwards it to the LLM
// provider as-is. No structural validation is added on top.
//
// We default to an empty open object when a tool ships no schema — matches what
// the MCP SDK does internally.
// ---------------------------------------------------------------------------
function toTypeBoxSchema(jsonSchema: unknown): TSchema {
	if (jsonSchema && typeof jsonSchema === "object") {
		return Type.Unsafe(jsonSchema as Record<string, unknown>) as TSchema;
	}
	return Type.Object({}, { additionalProperties: true });
}

// ---------------------------------------------------------------------------
// §4.3.4 Result formatting
//
// MCP CallTool results are arrays of content blocks (text/image/resource).
// pi.dev tools return { content: [...], details: {...} }. We flatten Ultra's
// text content into a single string and pass image/resource blocks through
// where shapes line up. Errors from Ultra (isError=true) are surfaced by
// throwing — pi.dev marks the tool result as failed and the LLM sees it.
// ---------------------------------------------------------------------------
type McpContentBlock =
	| { type: "text"; text: string }
	| { type: "image"; data: string; mimeType: string }
	| { type: "resource"; resource: unknown }
	| { type: string; [key: string]: unknown };

function flattenMcpContent(content: McpContentBlock[] | undefined): string {
	if (!content || content.length === 0) return "";
	const parts: string[] = [];
	for (const block of content) {
		if (block.type === "text" && typeof (block as { text?: unknown }).text === "string") {
			parts.push((block as { text: string }).text);
		} else {
			// Non-text content: include a JSON-stringified summary so the LLM
			// at least knows something came back. Production benchmarks should
			// treat image/resource passthrough as future work.
			parts.push(`[non-text content: ${block.type}]`);
		}
	}
	return parts.join("\n");
}

// ---------------------------------------------------------------------------
// §4.3.2 + §4.3.3 + §4.3.4: extension factory
//
// pi.dev awaits async factories before session_start, so by the time the user
// sends their first prompt, every Ultra tool is already registered.
// ---------------------------------------------------------------------------
export default async function piUltraMcp(pi: ExtensionAPI): Promise<void> {
	const { command, args } = ultraCommand();

	// §4.3.1 Spawn Ultra as a stdio subprocess.
	// We let StdioClientTransport own the spawn so it can wire stdin/stdout
	// to the JSON-RPC framer and forward stderr to our stderr for debugging.
	const transport = new StdioClientTransport({
		command,
		args,
		// Pass the parent env through plus any caller-set Ultra config.
		// process.env values may legitimately be undefined; filter those out
		// so we satisfy StdioClientTransport's Record<string, string> type.
		env: Object.fromEntries(
			Object.entries(process.env).filter(
				(entry): entry is [string, string] => typeof entry[1] === "string",
			),
		),
		stderr: "inherit",
	});

	const client = new Client(
		{
			name: "pi-ultra-mcp",
			version: "0.1.0",
		},
		{
			capabilities: {},
		},
	);

	// §4.3.2 Connect. If this fails (Ultra missing, config invalid, etc.) we
	// throw — pi.dev surfaces the factory error and refuses to start the
	// session. That's the desired "no native fallback" behavior.
	await client.connect(transport);

	// §4.3.3 Enumerate every Ultra tool, paginating through cursors.
	const tools: Tool[] = [];
	let cursor: string | undefined = undefined;
	do {
		const page = await client.listTools(cursor ? { cursor } : undefined);
		tools.push(...page.tools);
		cursor = page.nextCursor;
	} while (cursor);

	if (tools.length === 0) {
		// Don't silently succeed with zero tools — the benchmark would run
		// with an empty toolset and produce meaningless results.
		throw new Error(
			"pi-ultra-mcp: Ultra returned zero tools from tools/list. Check Ultra's MCP server config.",
		);
	}

	// §4.3.3 Register every Ultra tool with pi. We do this synchronously inside
	// the async factory so all tools are present before session_start fires.
	for (const tool of tools) {
		const toolName = tool.name;
		const description = tool.description ?? `Tool ${toolName} (proxied through Ultra)`;
		const parameters = toTypeBoxSchema(tool.inputSchema);

		pi.registerTool({
			name: toolName,
			label: tool.title ?? toolName,
			description,
			parameters,

			// §4.3.4 + §4.3.5 Forward to Ultra. No fallback. No retry.
			async execute(_toolCallId, params, signal) {
				if (signal?.aborted) {
					throw new Error(`pi-ultra-mcp: ${toolName} aborted before dispatch`);
				}

				const result = await client.callTool(
					{
						name: toolName,
						arguments: (params ?? {}) as Record<string, unknown>,
					},
					undefined,
					signal ? { signal } : undefined,
				);

				const text = flattenMcpContent(result.content as McpContentBlock[] | undefined);

				if (result.isError) {
					// §4.3.5 No native fallback. Throwing marks the tool result
					// as failed in pi.dev so the LLM sees the error.
					throw new Error(text || `pi-ultra-mcp: ${toolName} returned isError`);
				}

				return {
					content: [{ type: "text", text }],
					details: {
						source: "ultra-mcp",
						toolName,
					},
				};
			},
		});
	}

	// Best-effort cleanup. pi.dev doesn't expose a guaranteed shutdown hook
	// in the extension API for the SIGINT case, so we register process-level
	// handlers. Ultra's subprocess will also see EOF on stdin when pi exits.
	const shutdown = async (): Promise<void> => {
		try {
			await client.close();
		} catch {
			// best-effort
		}
	};
	process.once("exit", () => {
		void shutdown();
	});
	process.once("SIGINT", () => {
		void shutdown();
	});
	process.once("SIGTERM", () => {
		void shutdown();
	});
}
