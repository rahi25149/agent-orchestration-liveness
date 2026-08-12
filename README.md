# Agent Orchestration Liveness

This skill coordinates long-running architect-worker-supervisor workflows while keeping ownership, liveness, completion claims, user reporting, and independent supervision distinct.

[中文说明](README.zh-CN.md)

## What this update adds

- **Outcome batches:** group work only when it serves one externally verifiable result and one shared pass/fail acceptance boundary.
- **Review de-duplication:** use material delta to open event-review boundaries; keep ordinary repairs, tests, technical reviews, and owner handoffs inside the existing batch.
- **Risk-triggered technical review:** independently review protected semantics only when late-failure cost and independent discovery value justify the review; keep low-risk reversible work on the self-check fast path.
- **Scoped review economics:** review one invariant or direct producer-consumer path, reuse valid Worker evidence, perform one falsification-oriented check, and keep unrelated work moving.
- **Independent liveness checks:** use each active item's next observable checkpoint to detect stalls even when no material delta occurs.
- **Bounded architect execution:** permit one declared blocking hypothesis or atomic integration action, with a stop condition and handoff target.
- **Truthful surface completion:** require a representative browser, desktop, device, or remote-session probe at the first executable thin slice before claiming the corresponding higher completion layer.
- **Separated supervision state:** keep orchestration liveness, supervisor-finding state, architect disposition, and blocker/ack metadata independent.
- **Low-noise communication audit:** retain one machine-checkable internal audit field per interval without emitting healthy audit traffic to the user.
- **Bounded context lifecycle:** reuse engineering ownership without carrying unbounded chat history; rotate only at a safe handoff boundary plus a real pressure signal.
- **Low-cost runtime metrics:** compare equivalent Architect and Supervisor epochs using median input tokens, observed substantive context regressions, and cold-start turns, with no transcript collection or monitoring platform.

## File guide

- `SKILL.md`: core roles, lifecycle, completion, reporting, and supervision rules.
- `references/outcome-batching-and-review-budget.md`: batch identity, material delta, elapsed checkpoints, bounded architect execution, technical-review handoff, and finding reconciliation.
- `references/technical-review-workflow.md`: two-stage review trigger, bounded handoff, falsification check, `TECH_CLEAR` / `TECH_BLOCKED`, incremental re-review, freshness, and process-tax guardrails.
- `references/interactive-runtime-lifecycle.md`: earliest real-surface probe, unique runtime ownership, task-owned continuity, authorization checks, `USER_WAIT`, and cleanup.
- `references/user-reporting-boundaries.md`: internal versus user-visible reporting and communication-audit evidence.
- `references/review-exchange-templates.md`: architect-supervisor review and finding exchange formats.
- `references/context-lifecycle-and-runtime-metrics.md`: bounded role state, safe fresh-thread rotation, compact-hook limits, secure JSONL metrics, review thresholds, and rollback gates.
- `scripts/context_metrics.py`: strict standard-library JSONL append, validation, and baseline-versus-pilot reporting.
- `scripts/test_context_metrics.py`: deterministic tests for schema safety and decision thresholds.
- `scripts/app_server_usage_adapter.py`: strict App Server notification coalescer that persists one content-free usage record per completed turn.
- `scripts/test_app_server_usage_adapter.py`: deterministic privacy, replay, ordering, and fail-closed tests plus an opt-in real App Server smoke test.
- `scripts/desktop_rollout_usage_adapter.py`: explicitly armed Codex Desktop bridge for fresh threads whose isolated stdio App Server connection cannot be tapped directly.
- `scripts/test_desktop_rollout_usage_adapter.py`: deterministic fresh-arm, route, replay, compaction, privacy, and terminal-boundary tests for the Desktop bridge.

## Context metrics quick start

Phase 0 is manual and does not change Codex configuration. Create the log outside every repository and let the script enforce mode `0600`:

```bash
python3 scripts/context_metrics.py append \
  --path ~/.codex/orchestration-metrics/events.jsonl \
  --event epoch_started --epoch-id architect-b01 --mode baseline \
  --event-id architect-b01-start --thread-ref architect-b01 \
  --role architect --cohort outcome-batch --model gpt-5.6-luna \
  --reasoning max --source manual

python3 scripts/context_metrics.py validate \
  --path ~/.codex/orchestration-metrics/events.jsonl

python3 scripts/context_metrics.py report \
  --path ~/.codex/orchestration-metrics/events.jsonl
```

Record only structured counters and opaque evidence references. Do not put prompts, replies, paths, URLs, tool output, diffs, credentials, or narrative notes in the log. Phase 0 validates append, de-duplication, schema, permissions, grouping, and privacy only. After a verified App Server adapter supplies final per-turn usage, collect at least three comparable baseline epochs, three pilot epochs, and five pilot rotations before using the report as a decision aid. Never hand-estimate token usage.

Run the complete Phase 0 recorder acceptance matrix with:

```bash
python3 scripts/test_context_metrics.py -v
```

The named tests cover durable serial and concurrent append, stable replay rejection, malformed or partial JSONL rejection, strict content-field exclusion, owner-only permissions, symlink rejection, role/thread/epoch grouping, synthetic report decisions, and a bounded small-ledger latency smoke check. Passing this matrix approves only the local recorder. It does not approve an App Server adapter, real token collection, automated rotation, compact hooks, or any Codex configuration change.

## Phase 1 App Server adapter gate

Run the deterministic adapter matrix first:

```bash
python3 scripts/test_app_server_usage_adapter.py -v
```

Then opt in to one bounded real App Server turn. The smoke test defaults to `gpt-5.4-mini` with `low` reasoning so protocol verification does not inherit an expensive global route; it changes no Codex configuration:

```bash
RUN_CODEX_APP_SERVER_SMOKE=1 \
  python3 scripts/test_app_server_usage_adapter.py \
  LiveAppServerUsageAdapterTest.test_real_terminal_turn_writes_one_safe_usage_record -v
```

Integrate `AppServerUsageAdapter.consume()` only on the server-to-client side of a controlled App Server connection. The standalone adapter command accepts an already-live JSONL tap on stdin; it is not a bidirectional App Server proxy. Never persist the raw protocol stream. Supply the exact role, cohort, model, and reasoning route for the epoch. A model reroute, mixed thread, missing terminal notification, or missing final usage update fails closed and requires a new or corrected epoch.

Passing the real smoke approves the adapter mechanics only. Start comparable Architect and Supervisor baseline epochs at their next safe handoff boundaries, capture normal work without changing compaction or rotation behavior, and collect the required three baseline epochs before starting the manual fresh-thread pilot. Reports count token samples only from epochs closed with `outcome=completed`; open, paused, and aborted epochs remain visible in the ledger but cannot satisfy the sample gate. Do not retrofit usage onto an already-running thread, hand-estimate tokens, enable hooks, or automate rotation.

### Codex Desktop fresh-thread bridge

Codex Desktop currently owns an isolated stdio App Server connection, so an external sidecar cannot subscribe to that already-running connection. When the role must remain in Desktop, use the armed rollout bridge instead of a protocol proxy. The bridge must be armed after creating a blank non-ephemeral thread and before starting its first turn. It refuses any thread that already has a rollout file, so it cannot be used as a retrospective importer.

```bash
python3 scripts/desktop_rollout_usage_adapter.py arm \
  --sessions-root ~/.codex/sessions \
  --thread-id '<fresh-raw-thread-id>' \
  --arm-path ~/.codex/orchestration-metrics/armed/architect-b01.json \
  --path ~/.codex/orchestration-metrics/events.jsonl \
  --epoch-id architect-b01 --thread-ref architect-b01 \
  --mode baseline --role architect --cohort outcome-batch \
  --model gpt-5.6-sol --reasoning ultra

python3 scripts/desktop_rollout_usage_adapter.py collect \
  --sessions-root ~/.codex/sessions \
  --thread-id '<fresh-raw-thread-id>' \
  --arm-path ~/.codex/orchestration-metrics/armed/architect-b01.json \
  --path ~/.codex/orchestration-metrics/events.jsonl
```

Run `collect` repeatedly at safe checkpoints; replay is idempotent. Add `--outcome completed` only after the coherent role epoch is closed and no turn is active. Use `paused` or `aborted` when that is the truthful outcome. The raw thread id is accepted only to locate the local rollout and verify the arm; it is hashed in memory and is never persisted. The bridge ignores content-bearing records and persists only terminal usage counters plus compact generation numbers. It fails closed on a route mismatch, malformed rollout, active-turn close attempt, or format drift.

Run its deterministic matrix with:

```bash
python3 scripts/test_desktop_rollout_usage_adapter.py -v
```

The bridge is a compatibility path for a fresh Desktop connection, not permission to mine historical rollouts. Direct App Server notifications remain the preferred source when the operator surface can expose the server-to-client stream safely.

The new rules are project-agnostic. Project-specific model routing, business gates, credentials, machines, ports, and reporting cadence remain in each project's own instructions or live state card.
