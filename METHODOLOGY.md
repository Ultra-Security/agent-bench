# Conduit Benchmark Methodology (pre-registered)

> **Status: Locked** as of 2026-04-29 after internal review.
> Any change from this point requires a CHANGELOG entry below.
>
> **Lock date:** 2026-04-29

## Why this exists

Ultra's market thesis is that **MCP is the right substrate for agentic tool
calls** — every call routed through a typed, observable, policy-aware proxy
unlocks security, audit, and behavioral guarantees that bash-shelling-out
cannot match. Today this is a vibes argument. The Conduit benchmark converts
the asset we already have (`ultra agent`, the first MCP-only-by-construction
agent we know of) into empirical evidence.

This document **pre-registers** the experimental design before any data
collection. Every decision below is locked at the lock date. Post-hoc
changes get a CHANGELOG entry — full stop. The credibility of the whole
study lives or dies on whether this document is honest and the harness
reproduces it.

---

## 1. Purpose & scope

Three named arms:

- **Ultra-MCP** — `ultra agent` (MCP-only by construction)
- **pi-MCP** — pi.dev with `--no-builtin-tools` plus a thin extension that registers Ultra's MCP tools (substrate-controlled comparator for Ultra-MCP)
- **pi-bash** — pi.dev with stock recommended coding configuration (substrate-controlled comparator for pi-MCP, and end-to-end comparator for Ultra-MCP)

With three arms we can answer:

- **pi-MCP vs pi-bash** — controlled substrate test (same harness, only the tool layer changes)
- **Ultra-MCP vs pi-MCP** — "MCP-optimized reference" test (does building MCP-native beat retrofitting?)
- **Ultra-MCP vs pi-bash** — end-to-end story

**Out of scope for this study:** Aider, Claude Code, and other agents (deferred to Phase 3); cost-vs-quality Pareto curves; agent UX comparisons; "which agent should I use" buyer's-guide framing. We are testing one substrate hypothesis, not running an agent shootout.

---

## 2. Research questions & hypotheses

Six RQs, each with a **pre-registered prediction**. Hypotheses are *predictions*, not claims. We publish whatever we find.

| RQ  | Question | Hypothesis |
|-----|----------|------------|
| **RQ1** | Capability — completion-rate parity? | Substrate: pi-MCP within ±5pp of pi-bash on TerminalBench. Ultra-MCP ≥ pi-MCP. |
| **RQ2** | Cost — per-task token premium? | Substrate: MCP costs 10–30% more *input* tokens (schema overhead); ≈parity on output. Ultra-MCP slightly cheaper than pi-MCP (tighter schemas). |
| **RQ3** | Latency — per-call overhead? | Substrate: MCP adds 5–50ms per call; <2% per-task delta once LLM dominates. |
| **RQ4** | Observability — log reconstructibility? | End-to-end: Ultra-MCP ≈100%; pi-bash 60–80%. pi-MCP gets MCP-side observability "for free" via Ultra (~95%) — confirms substrate alone gets you most of the way. |
| **RQ5** | Security — adversarial defense rate? | End-to-end: Ultra-MCP wins decisively over pi-bash. pi-MCP also wins over pi-bash (substrate effect), demonstrating Ultra's policy/anomaly layer carries through to a foreign agent. |
| **RQ6** | Determinism — variance? | Substrate: MCP modestly more deterministic (smaller action space per turn). |

> **The most-interesting honest result would be Ultra-MCP losing to pi-MCP on RQ1 or RQ2.** That would say MCP-as-substrate works, but Ultra's specific implementation is over-engineered. We name this here so we can't bury it later.

---

## 3. Independent variables (locked)

| Variable | Locked value | Notes |
|----------|--------------|-------|
| **Model** | `claude-sonnet-4-6` (Anthropic Sonnet 4.6, latest as of 2026-04-28) | Pinned exact ID; no auto-update. Phase 2 may add a second model. |
| **Provider** | Anthropic API direct | Same provider for all three arms. |
| **Temperature** | `0.0` | Reproducibility. |
| **max_tokens** | `16384` per response | Ultra default; pi.dev configured to match. |
| **max_iterations** | `25` per task | Ultra `DefaultMaxIterations`; pi.dev configured to match. |
| **Wall-clock cap** | `1800s` (30 min) per task | Hard kill. |
| **Container** | Same Debian-slim base for all arms | Identical OS/toolchain; only the agent binary differs. |
| **Network policy** | Egress allow-list per task | Deny by default; tasks declare allowed hosts. |
| **Working directory** | Per-task, fresh clone of task seed | No state leakage across runs. |

---

## 4. Agent configurations (locked)

### 4.1 Ultra-MCP

- Build: `make build` with tags `mcp_go_client_oauth hubserver ultra_agent`
- Version pinned: `Ultra-Security/ultra` `main` at `8361e094` (2026-04-29)
- Config: stock `~/.config/ultra/config.yaml` with `filesystem`, `shell`, `git` MCP upstreams enabled — no custom tweaks
- API key via env (`ANTHROPIC_API_KEY`); keychain disabled in containerized runs
- All Ultra interceptors active at default priority: trace, audit, logging, anomaly (passive mode), guardrails (catalog defaults)

### 4.2 pi-bash

- Source: `badlogic/pi-mono` release tag `v0.70.6` (released 2026-04-28). Rerun if pi.dev publishes a major version mid-study, with the new run reported separately.
- Recommended coding configuration per pi.dev's own docs — do not deviate
- Same Anthropic API key path
- Built-in tools enabled: `read, bash, edit, write, grep, find, ls`
- No custom skills or extensions beyond what pi.dev ships by default

### 4.3 pi-MCP

- Same pi.dev release tag as pi-bash: `v0.70.6`
- Launch with `--no-builtin-tools -e ./pi-ultra-mcp.ts`
- Extension `pi-ultra-mcp.ts` (TypeScript, in `agent-bench/agents/pi-dev-mcp/`):
  - Spawns Ultra as a subprocess via stdio (same pattern as `ultra agent`)
  - Calls `pi.registerTool(...)` once per tool exposed by Ultra's aggregator
  - Forwards each tool invocation to Ultra's MCP `CallTool`, returns the result
  - **No native fallback**: if Ultra fails, the call fails (no shelling out)
- Same Ultra `ultra.yaml` config as Ultra-MCP arm — identical upstreams, interceptors, policy
- Same Anthropic API key path

> **Fallback if pi.dev's extension API can't actually disable built-ins** (smoke test will confirm before we start runs): light fork of pi-mono with the built-in tools array stripped. Document explicitly. Same pinned commit SHA either way.

The exact `launch.sh` for each arm lives in **Appendix A**. The pi-MCP extension source lives in the agent-bench repo and is pinned in **Appendix F** — any change requires a CHANGELOG entry.

---

## 5. Benchmarks & scoring

| Benchmark | Pinned version | Used for | Scoring |
|-----------|---------------|----------|---------|
| **TerminalBench** | Git SHA + version tag *(at lock)* | RQ1, RQ3 | Upstream pass/fail; we record per-task |
| **SWE-bench Verified, 50-task stratified subset** | Git SHA *(at lock)*; stratified by difficulty + repo | RQ1, RQ2, RQ6 | Upstream `verify.sh` |
| **Conduit-Audit** (custom, 10 tasks) | Authored in Phase 1 | RQ4 | Blinded reviewer scores % of `events.yaml` ground-truth events reconstructible from each agent's log dir alone |
| **Conduit-Adversarial** (custom, 15 tasks) | Authored in Phase 2; reuses `internal/anomaly/eval` `Case` schema where feasible | RQ5 | % attacks prevented (task `verify.sh` checks the harm marker is absent) |

For Phase 1, only **TerminalBench + Conduit-Audit** are required.

---

## 6. Sample sizes & statistics

- **N=5 runs/task per arm minimum** for primary results (3 arms × N=5 = 15 runs per task baseline)
- **N=10/arm** for the deep-dive subset (top-5 most-variable + top-5 most-representative tasks)
- **Completion rate**: report as proportion with **Wilson 95% CI** per arm; pairwise comparisons use **McNemar's test** at α=0.05 paired by task
- **Token cost**: report **median + IQR** per task per arm (failure long-tail inflates means)
- **Latency**: report **p50 and p95** wall-clock per arm; per-tool-call latency captured but not the headline metric
- **Variance (RQ6)**: **Levenshtein distance over canonicalized tool-call traces**; report mean + stdev per arm across N=10
- **Multiple-comparison correction**: Bonferroni over the **18 pairwise RQ tests** (6 RQs × 3 pairwise arm comparisons) — α_per_test = 0.05/18 ≈ 0.0028

More conservative than a 2-arm design — necessary trade-off for the cleaner experimental separation between substrate and harness.

---

## 7. Bias mitigations

The credibility-load-bearing section. If a critic dismisses the comparison as rigged, this is the section they'll attack first.

- **Calibration set**: 5 tasks held out from the analysis set. **All** prompt iteration happens on calibration only. Frozen before primary runs begin.
- **No prompt engineering after lock.** Any change requires a CHANGELOG entry in this doc and re-collection of all affected runs.
- **Pre-registered analysis plan** (Section 9) — no post-hoc test selection.
- **All raw transcripts published**, including failures, in `agent-bench/results/`.
- **Blinded RQ4 review**: reviewer sees only the log directory, not which arm produced it.
- **External pre-publication review**: invite a pi.dev maintainer to review the methodology + harness before any blog post. Outcome captured in **Appendix E**.
- **"Things we'd do differently" section** in every writeup, populated honestly.

---

## 8. What gets published

- This methodology document (locked + dated)
- The full harness (public repo `Ultra-Security/agent-bench`)
- Every raw transcript and result row
- The analysis Quarto notebook
- A blog post per phase summarizing findings
- **Negative results** — yes, even if MCP loses on RQ1

---

## 9. Pre-registered analysis plan

The exact tests we will run, written *before* we look at full results. For each RQ, run all three pairwise comparisons. Bonferroni-adjusted α applied across the full 18-test family.

1. **RQ1 (capability)**: McNemar paired test on per-task completion across TerminalBench, run for each of {pi-MCP vs pi-bash, Ultra-MCP vs pi-MCP, Ultra-MCP vs pi-bash}.
2. **RQ2 (cost)**: Wilcoxon signed-rank on per-task median input + output tokens, paired by task, all three pairs. Report effect sizes.
3. **RQ3 (latency)**: Wilcoxon signed-rank on per-task wall-clock time, paired by task, all three pairs. Per-tool-call overhead reported as median + IQR per arm (descriptive, no test).
4. **RQ4 (observability)**: Reviewer scores per task per arm; report mean recall + 95% bootstrap CI per arm.
5. **RQ5 (security)**: Per-task binary outcome (attack prevented or not); McNemar paired test for all three pairs.
6. **RQ6 (determinism)**: Mean Levenshtein distance per task across N=10 runs per arm; report descriptively per arm, no significance test (variance is the point).

---

## 10. CHANGELOG

- **2026-04-29** — Initial lock after internal review. Version pins recorded for Ultra (`8361e094`) and pi.dev (`v0.70.6`). External review (pi.dev maintainer) initiated in parallel.

---

## 11. Appendices

### Appendix A — Launch scripts

*(Filled in at lock. Exact `launch.sh` for Ultra-MCP, pi-bash, pi-MCP arms.)*

### Appendix B — TerminalBench task IDs in scope

*(Filled in at lock. Lists calibration set (5 tasks, held out from analysis) and analysis set with stratification rationale.)*

### Appendix C — Conduit-Audit task list

*(Filled in at Phase 1 authoring. Lists 10 custom tasks with `events.yaml` schema and ground-truth events for each.)*

### Appendix D — RQ4 reviewer instructions

*(Filled in at Phase 1. Blinded scoring rubric for log reconstructibility. Reviewer sees three log dirs per task, blind to which arm produced each.)*

### Appendix E — External-review correspondence log

*(Entries dated when responses are received.)*

### Appendix F — `pi-ultra-mcp.ts` extension source

*(Filled in at Phase 1. Full TypeScript source committed verbatim, with a one-paragraph explanation of how it bridges pi.dev's tool registry to Ultra's MCP client.)*
