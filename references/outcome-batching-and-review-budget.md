# Outcome Batching and Review Budget

Read this reference when a long-running workflow needs a batch-boundary decision, a liveness recheck, bounded architect execution, technical-review handoff, or supervisor-finding reconciliation.

## Define one outcome batch

Require both:

1. one externally verifiable outcome; and
2. one shared pass/fail acceptance boundary.

Allow multiple workers, hotspots, and dependency chains only when each is necessary to pass that boundary. Use an outcome that an external observer can verify; it may be a user capability, research conclusion, published artifact, operational result, or executable decision.

Apply the removal test:

> If removing one work item would not change whether the shared acceptance passes, exclude that item from the batch.

## Decide whether to keep, split, pause, or close

| Current fact | Batch action | Supervisor action |
| --- | --- | --- |
| Same external outcome, same acceptance boundary, no material delta | `KEEP` | Continue the existing review lifecycle |
| Ordinary repair, direct test, technical review, or internal owner handoff | `KEEP` | Do not create a new event review automatically |
| No material delta, but the next observable checkpoint passed without a fresh execution fact | `KEEP` | Perform `LIVENESS_RECHECK`; use `YELLOW/STALLED` when a safe next action exists |
| Independent externally verifiable outcome or independently closable acceptance | `SPLIT` | Open a separate lifecycle if supervision is needed |
| New production, permission, authority, irreversible, safety, or rollback boundary | `SPLIT` or redefine the boundary | Open an event review for the new material delta |
| No safe next action while waiting for a bounded non-user event | `PAUSE` | Use `BOUNDED_WAIT` |
| Only a specific user action can continue the batch | `PAUSE` | Use `USER_WAIT` after checking existing authorization and owner capability |
| Acceptance and claimed completion layer are proven and related findings are reconciled | `CLOSE` | Record the final completion layer and finding states |

Split when any one of these is true:

- the new work produces an independently useful external result;
- its acceptance can pass or fail independently;
- omitting it does not affect the original batch result;
- it adds a distinct high-risk, authority, production, or rollback boundary;
- unrelated work is being added merely to keep a blocked batch looking active.

Do not split merely because the batch has multiple owners, repositories, platforms, or internal repairs.

## Separate material delta from liveness

Use material delta to decide whether to open a new event-review boundary. Treat these as material:

- externally verifiable outcome changed;
- shared acceptance boundary changed;
- risk, authority, safety, or rollback boundary changed;
- claimed completion layer changed;
- exclusive-resource ownership conflict appeared;
- an open finding reached its next-check boundary;
- an independent safety or policy review became due.

Use the next observable checkpoint to decide whether existing work is alive. Every `ACTIVE_WORK` item must name the next fact expected from execution, not merely a vague duration. Examples include a completion packet, first stable failure, dependency response, integrated observation, or handoff decision.

If the checkpoint passes:

- fresh relevant execution fact: keep `ACTIVE_WORK` and set the next checkpoint;
- no fresh fact and a safe next action exists: keep the batch, perform a liveness recheck, and use `YELLOW/STALLED` as appropriate;
- no safe next action and a bounded external dependency remains: use `BOUNDED_WAIT`;
- a specific user action is truly required: use `USER_WAIT`;
- the outcome, acceptance, risk, authority, or completion claim changed: open an event review.

Do not let “no material delta” hide a stall, and do not convert a liveness recheck into a new batch.

## Bound architect execution

Allow the architect to execute directly only when at least one condition holds:

- the action requires architect-exclusive context or control;
- it tests one blocking integration hypothesis;
- no available worker can take it without material context loss;
- it is one atomic, reversible integration or mechanical action.

Before starting, record:

- the single blocker or hypothesis;
- minimal allowed scope;
- first-stable-failure or stop condition;
- handoff owner or responsibility domain.

Limit the action to one blocking hypothesis or one atomic integration action. Exit immediately when the blocker clears, the first stable failure occurs, the scope must expand, a worker becomes available, or a new product or architecture decision is required.

Raise `YELLOW` when the architect:

- enters implementation without a declared boundary;
- touches an undeclared scope;
- expands into a second independent result;
- becomes the continuing implementation owner for the batch;
- delays acknowledgements, dispatch, integration, or architecture decisions because of direct execution.

Allow a small-team architect to switch roles sequentially, but require the same declared scope and exit conditions.

## Consume technical review without duplicating it

Use [Risk-Triggered Technical Review](technical-review-workflow.md) to decide whether review is required, define the review scope, interpret `TECH_CLEAR` or `TECH_BLOCKED`, and determine freshness.

When a technical reviewer reports `TECH_CLEAR`, verify only:

1. the review covers the current batch and latest candidate;
2. required fixes entered the integrated result;
3. no later material delta made the review stale;
4. the exact completion layer the review proves;
5. any remaining real-surface or business acceptance.

Do not treat technical `CLEAR` as integration or user-capability completion automatically.

Sample code or evidence only when review coverage is missing, the conclusion conflicts with a current observable fact, material changes occurred after review, authority or safety truth is disputed, a completion layer is overstated, or no reviewer is available for a risk that cannot wait. Keep the sample minimal.

## Reconcile supervisor findings at gate closure

For every finding related to the closing gate, record exactly one result:

- `CLOSED`: one current closing fact proves the correction;
- `SUPERSEDED`: one replacement fact or successor finding replaces the original issue;
- `OPEN`: record blocker, next-check boundary, and whether it blocks the claimed completion layer.

Do not close a finding merely because the architect acknowledged or accepted it, the gate is otherwise green, or someone wrote “handled.” A non-blocking finding may remain `OPEN` after the batch closes, but it must remain visible.

## Reject common boundary errors

- Do not merge work merely because it shares a broad product milestone.
- Do not split every repair, test, review, commit, or internal handoff.
- Do not use a blocked batch as a container for unrelated work.
- Do not make the supervisor a second technical reviewer or release approver.
- Do not reopen terminal findings; create a new finding for recurrence and reference the old one.
