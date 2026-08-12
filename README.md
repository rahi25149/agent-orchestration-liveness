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

## File guide

- `SKILL.md`: core roles, lifecycle, completion, reporting, and supervision rules.
- `references/outcome-batching-and-review-budget.md`: batch identity, material delta, elapsed checkpoints, bounded architect execution, technical-review handoff, and finding reconciliation.
- `references/technical-review-workflow.md`: two-stage review trigger, bounded handoff, falsification check, `TECH_CLEAR` / `TECH_BLOCKED`, incremental re-review, freshness, and process-tax guardrails.
- `references/interactive-runtime-lifecycle.md`: earliest real-surface probe, unique runtime ownership, task-owned continuity, authorization checks, `USER_WAIT`, and cleanup.
- `references/user-reporting-boundaries.md`: internal versus user-visible reporting and communication-audit evidence.
- `references/review-exchange-templates.md`: architect-supervisor review and finding exchange formats.

The new rules are project-agnostic. Project-specific model routing, business gates, credentials, machines, ports, and reporting cadence remain in each project's own instructions or live state card.
