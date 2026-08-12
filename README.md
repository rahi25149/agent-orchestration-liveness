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

The new rules are project-agnostic. Project-specific model routing, business gates, credentials, machines, ports, and reporting cadence remain in each project's own instructions or live state card.
