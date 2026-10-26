# Agent Orchestration Liveness

This skill proposes and establishes an authorized project arrangement with one Architect, independent visible Workers, a selected Supervisor and a dedicated business architecture advisor. Existing project modes and in-flight owners are preserved until an authorized change. Role creation, direct communication and actual execution are separate evidence. This README is an introduction, not a second authority: follow `SKILL.md`, the references it actually triggers, and the current user's/project's declared mode.

[中文说明](README.zh-CN.md)

## Normal operating path

- **Six-step initialization:** discover the current scene; check capabilities and unresolved authorization; establish selected roles; verify direct channels; observe natural work/timer events; persist and resume. In authorized full mode, bind Supervisor and advisor at setup, but create a Worker only for real ready work. Do not wait for the first heartbeat to advance engineering.
- **Architect-led implementation routing:** independent visible Workers implement ordinary engineering even when only one lane is ready. Short read-only exploration and one-off technical review may use internal subagents; they do not substitute for selected persistent roles. Neither a setup marker nor one successful loop grants a permanent direct-execution exception.
- **Dedicated business advisor:** Architect directly consults the bound advisor for material design tradeoffs, not routine progress. Keep it separate from Supervisor and the Controller's orchestration advisor; missing carrier support never authorizes a fake substitute.
- **Outcome batches:** group work only when it serves one externally verifiable result and one shared pass/fail acceptance boundary.
- **Mode-aware supervision:** NONE does not fall through to checkpoint reviews. A selected timer-only mode uses the actual owned schedule, verified separately from its first natural trigger. GREEN remains in the Supervisor's own snapshot, silent externally.
- **Risk-triggered technical review:** independently review protected semantics only when late-failure cost and independent discovery value justify the review; keep low-risk reversible work on the self-check fast path.
- **Scoped review economics:** review one invariant or direct producer-consumer path, reuse valid Worker evidence, perform one falsification-oriented check, and keep unrelated work moving.
- **Bounded continuous engineering:** investigate, implement and perform necessary checks within one hypothesis and the authorized repair budget; stop real-side-effect failures and never retry UNKNOWN results.
- **Bounded architect execution:** permit one declared blocking hypothesis or atomic integration action, with a stop condition and handoff target.
- **Truthful surface completion:** require a representative browser, desktop, device, or remote-session probe at the first executable thin slice before claiming the corresponding higher completion layer.
- **Separated supervision state:** keep orchestration liveness, supervisor-finding state, architect disposition, and blocker/ack metadata independent.
- **Low-noise communication audit:** retain one machine-checkable internal audit field per interval without emitting healthy audit traffic to the user.
- **Long-lived context by default:** native compaction plus bounded current state; context size, elapsed time and compaction alone never authorize rotation. Required Goal transfer uses supported paused staging, freeze/readback, single authority and verified rollback.
- **Dormant research off the hot path:** metrics, cohort/probe protocols and hooks require separate explicit authorization for non-critical, cost-bounded work; normal dispatch and state updates do not load them.

## File guide

- `SKILL.md`: core roles, lifecycle, completion, reporting, and supervision rules.
- `references/project-initialization.md`: six-step setup/adoption, visible role binding, direct channels, owned timer lifecycle, capability gaps and safe resume; no synthetic business work or added orchestration runtime.
- `references/outcome-batching-and-review-budget.md`: batch identity, material delta, elapsed checkpoints, bounded architect execution, technical-review handoff, and finding reconciliation.
- `references/technical-review-workflow.md`: two-stage review trigger, bounded handoff, falsification check, `TECH_CLEAR` / `TECH_BLOCKED`, incremental re-review, freshness, and process-tax guardrails.
- `references/interactive-runtime-lifecycle.md`: earliest real-surface probe, unique runtime ownership, task-owned continuity, authorization checks, `USER_WAIT`, and cleanup.
- `references/user-reporting-boundaries.md`: internal versus user-visible reporting and communication-audit evidence.
- `references/review-exchange-templates.md`: architect-supervisor review and finding exchange formats.
- [Context Lifecycle](references/context-lifecycle-and-runtime-metrics.md): normal bounded role state, native compaction, capability/owner continuity, Goal-aware safe handoff and rollback; the historical path is retained for compatibility.
- [Dormant Context Experiments](references/context-experiments.md): separately gated measured-role probes, secure JSONL metrics, research thresholds, hooks and App Server writer lifecycle.
- `scripts/context_metrics.py`: strict standard-library JSONL append, validation, and baseline-versus-pilot reporting.
- `scripts/test_context_metrics.py`: deterministic tests for schema safety and decision thresholds.
- `scripts/app_server_usage_adapter.py`: strict App Server notification coalescer that persists one content-free usage record per completed turn.
- `scripts/test_app_server_usage_adapter.py`: deterministic privacy, replay, ordering, and fail-closed tests plus an opt-in real App Server smoke test.
- `scripts/desktop_rollout_usage_adapter.py`: explicitly armed Codex Desktop bridge for fresh threads whose isolated stdio App Server connection cannot be tapped directly.
- `scripts/test_desktop_rollout_usage_adapter.py`: deterministic fresh-arm, route, replay, compaction, privacy, and terminal-boundary tests for the Desktop bridge.

## Optional research, not a quick-start prerequisite

The research scripts and deterministic acceptance matrices remain available and unchanged. Read [Dormant Context Experiments](references/context-experiments.md) only under its explicit authorization and cost boundary, or for required closure of an already-open measured operation. Passing recorder tests does not authorize live App Server turns, sample collection, hooks, rotation or configuration changes. Do not start Phase 1 from this README or revive a historical cohort.

For ordinary work, load a reference fully when first entering its relevant mode, when it changes, or when needed contents are no longer available; reuse current complete contents rather than rereading them for every dispatch or state delta. Necessary current-fact and safety checks still apply.

Project-specific model/effort routing, business gates, machines, credentials, ports and cadence remain in the project's instructions or bounded current state. README language does not establish instruction precedence.
