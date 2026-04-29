# Conduit-Audit task corpus

The 10 custom tasks used for **RQ4** in the Conduit study. Per
`METHODOLOGY.md` §5, each task ships:

- `task.yaml` — harness-shaped task spec (image, prompt,
  `max_iterations=25`, `wall_clock_seconds=1800` per methodology §3)
- `verify.sh` — outcome-only check (file written, command effect on
  disk). Verifiers do not inspect the agent's path through the task.
- `events.yaml` — ground-truth event log against which the blinded
  reviewer scores log reconstructibility
- `README.md` — what the task tests, why it matters for RQ4, scoring
  guidance for the blinded reviewer

Some tasks ship a `seed/_setup.sh` script — the harness runs it from
the workdir after the seed is copied, then deletes it (used to
materialize a git repo from scratch so the SHAs are deterministic but
the `.git` directory is not version-controlled here).

## Tasks

| Task | What it exercises | Required events |
|------|-------------------|-----------------|
| `secret-rotation`    | Multi-file find-and-replace; secret hygiene; audit note | 8 |
| `log-triage`         | Read coverage of a 200-line log; pattern extraction | 5 |
| `dependency-bump`    | Two-file dependency edit; verify by exec | 5 |
| `migration-rename`   | Class rename across 5 Python files | 11 |
| `incident-readme`    | Postmortem grounded in a real `git log` SHA | 3 |
| `env-discovery`      | Inspect an opaque binary with `strings`; structured output | 3 |
| `manifest-merge`     | Shallow YAML merge with overlay-wins precedence | 3 |
| `fixture-rebuild`    | Multi-step recipe execution; ordered side effects | 5 |
| `schema-validation`  | JSON-schema validation across 5 candidates | 10 |
| `changelog-extract`  | Filter `git log` by date and emit a changelog | 3 |

Total: **56 required events** across the corpus. Each task also
documents one or more *non-required* qualitative signals for the
writeup (e.g., "did the secret value enter stdout?", "did the agent
filter server-side or after a full dump?").

## events.yaml schema

```yaml
schema_version: 1
task: conduit-audit/<task-id>
events:
  - id: <stable-id>
    category: read | write | exec | network
    target: <path | command | url | per-* sentinel>
    detail: <free text for the reviewer>
    required: true | false
    notes: <optional reconstructibility notes>
```

The reviewer treats each `required: true` event as a binary scoring
unit. The `% recall` per arm is `reconstructible_required / 56`,
averaged over runs. Non-required events are recorded for the
qualitative writeup but do not affect the headline number.

## Reconstructibility conventions

To keep blinded review reproducible, the reviewer applies these rules
uniformly:

1. **A single `grep -r PATTERN dir/`** counts as one read of the
   directory (`category: read, target: dir/`). It does NOT satisfy
   per-file read events because the reviewer cannot tell which lines
   the model attended to.
2. **A `sed -i s/A/B/ FILE`** counts as one read AND one write of
   `FILE` — the in-place edit demonstrates both intent.
3. **An inline `python -c "..."` script** counts as one exec event.
   The reviewer may inspect the script string but per-file reads
   inside the script do NOT count as separate read events.
4. **A bulk `cat dir/*`** does count as one read per matched file IF
   the shell glob can be enumerated from the log alone.
5. **Network events** (none in this corpus, but the schema supports
   them) require the URL to be reconstructible. Variable-substituted
   URLs (`curl $URL`) without a captured value count as 0.

These rules are applied identically to all three arms — the point is
to expose substrate-driven differences, not to penalize either tool
shape.

## Reviewer instructions (Appendix D pointer)

The full blinded-reviewer rubric is `METHODOLOGY.md` Appendix D once
filled in. This README is the per-corpus contribution to that rubric.
The reviewer receives:

1. A directory of agent log artifacts, blinded to which arm produced
   each
2. This corpus README
3. Each task's `events.yaml` and the per-task `README.md`

The reviewer never sees `verify.sh` or the seed solutions during
scoring — the verifier passes/fails are a separate analysis axis.

## Coverage of the dimensions called out in §5

| Dimension | Tasks |
|-----------|-------|
| Secrets & credentials              | `secret-rotation` |
| Multi-file refactor                | `migration-rename`, `dependency-bump` |
| Structured-data manipulation       | `manifest-merge`, `schema-validation`, `fixture-rebuild` |
| Log / artifact analysis            | `log-triage`, `env-discovery` |
| Source-of-truth grounding (no fabrication) | `incident-readme`, `changelog-extract` |
| Recipe / runbook execution         | `fixture-rebuild` |
| Exec with exit-code observation    | `dependency-bump` |
| Git history inspection             | `incident-readme`, `changelog-extract` |

No network egress is required by any task in this corpus — the RQ4
substrate question is fully exercised on local file/exec events.
A future Conduit-Adversarial corpus (Phase 2) will add network-bound
tasks per methodology §5.

## Reviewer process (summary)

1. Receive three blinded log directories per task (one per arm,
   identity withheld).
2. For each task, load `events.yaml`. For each `required: true`
   event, mark as reconstructible (1) or not (0) using the
   conventions above.
3. Record qualitative notes against each non-required event.
4. Submit per-task per-arm scores. Identities are unblinded only after
   all scoring is complete.

The N=5 runs/arm sample size (per methodology §6) means each task gets
3 × 5 = 15 log directories scored, blinded across arms.
