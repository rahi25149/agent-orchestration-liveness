# User Reporting Boundaries and Batching

Read this reference when establishing or auditing user-facing reporting for a long-running architect-worker-supervisor workflow. It separates truthful internal coordination from concise user communication; it is not a message-approval process.

## Keep two communication channels

### Internal orchestration

Keep this channel high-frequency enough to preserve liveness and truth:

- worker progress and first stable failures;
- blockers, data anomalies, safety risks, and inability to continue;
- completion packets and architect acknowledgements;
- review feedback, repairs, re-dispatch, and ownership changes.

These events update the current state card and inform architect decisions. They do not automatically produce a user message.

### User reporting

Merge internal facts into one current-state update only when they cross a user-reporting boundary. Describe the objective, user-visible change, material risk, required decision, or proven completion layer. Do not replay worker lifecycle events.

## Maintain only two reporting facts

The architect keeps:

- `last_user_update_at`: when the last user-facing update was sent;
- `last_user_visible_change`: the objective, gate, material risk, user dependency, or completion boundary last reported.

Do not create a mandatory `pending_summary` queue. When a reporting boundary is reached, derive one summary from the current state card and the delta since `last_user_visible_change`.

## Classify each internal event

Use this order:

1. Record and acknowledge the internal fact without delaying the worker or next safe action.
2. **Immediate user boundary:** report now if a real `USER_WAIT` or `RED` appears, the active objective or gate materially changes, a material risk changes user expectations or requires a decision, or a declared user-visible outcome is proven.
3. **Declared reporting boundary:** when a user-requested cadence, milestone, or completion boundary arrives, send one merged update if there is a user-visible delta. If there is no delta, stay silent unless the user explicitly requested an unchanged heartbeat.
4. **Internal only:** otherwise keep the event inside orchestration and continue working.

A declared boundary must come from the active user request, project contract, or current objective. The supervisor may audit whether it was respected but must not invent a new user-visible completion boundary.

## Treat routine lifecycle events as internal

The following usually remain internal when they do not change the objective, risk, decision need, or proven completion layer:

- a worker starting or resuming;
- an ordinary test passing or a transient test failure repaired inside the same work cycle;
- review feedback, a repair starting, or a review becoming clear;
- commit, push, merge preparation, or task re-dispatch;
- a healthy `GREEN` heartbeat;
- repeated statements that the same gate is still in progress.

These facts still belong in worker handoffs and the state card. Batching user communication must never suppress internal truth.

## Compose one compact user update

Use only the fields that carry a meaningful delta:

```text
Current objective or gate:
Meaningful change since the last update:
Highest completion layer proven:
Material risk or user action, if any:
Next user-reporting boundary:
```

Prefer one merged paragraph when the result is simpler than the template.

## Audit communication health

### Establish the evidence window

Inspect the architect's user-facing updates once from the previous communication-audit boundary to now. On the first audit, use the start of the supervised interval or the most recent known user-reporting boundary. Exclude worker-to-architect traffic and other internal orchestration unless it is needed to classify a visible update.

Do not infer communication health from the current state card, a single latest message, or one compact task snapshot. If the platform cannot expose the interval, record the communication audit as `NOT_RUN`; do not claim there was no lifecycle leakage.

Record the audit in this compact form:

```text
Communication audit:
Window:
Source:
Observed delta:
Result: CLEAR | YELLOW | NOT_RUN
```

The record is not proof by itself. Use `CLEAR` only after actually reading the architect's user-facing updates across the stated interval. If only a state card, worker summary, or latest message is available, use `NOT_RUN`; do not infer a clear interval from the absence of evidence.

Compare each visible update with the previously reported objective, gate, material risk, user decision need, and completion layer. Message volume can support the judgment but is never the sole criterion.

The supervisor uses a combined judgment, not a raw message-count limit. Raise a communication `YELLOW` when current facts show one of these patterns:

- a sequence of user updates consists only of worker starts, tests, review cycles, repairs, commits, or re-dispatch, without an objective, risk, decision, or completion-layer change;
- the same user-visible state is repeated before a declared reporting boundary;
- normal internal events repeatedly bypass the architect's compression layer;
- a material objective, risk, `USER_WAIT`, `RED`, or declared completion change remains unreported beyond its applicable boundary.

The minimal correction is to merge future routine updates or restore the missing material update. A communication `YELLOW` does not pause engineering, approve wording, or authorize the supervisor to take over architect decisions. Message volume alone is not sufficient evidence.

## Prevent under-reporting

Reducing user noise must not reduce internal reporting:

- workers immediately report blockers, anomalies, safety concerns, and inability to continue to the architect;
- the architect immediately tells the user when such a fact creates a real `USER_WAIT`, `RED`, material expectation change, or decision need;
- ordinary resolved failures can be included in the next merged update when they change the proven result, or remain internal when they do not;
- never defer a required safety, policy, financial, credential, or data-integrity escalation to satisfy a reporting cadence.

## Examples

Bad user-facing lifecycle stream:

```text
The worker started the repair.
The tests passed.
Review requested one change.
The worker is repairing it.
Review is clear and integration is starting.
```

Better merged update:

```text
The affected capability is now engineering-complete and its direct checks pass. Integration remains in progress; no new risk or user action is required. I will report again at the declared integration boundary.
```

Internal failure that must not be hidden:

```text
Worker to architect: the task cannot continue because the target identity is ambiguous; no write was made.
Architect to user, when this creates USER_WAIT: the affected action is paused at identity confirmation. Other safe work continues; the only required input is the target identity.
```
