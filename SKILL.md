---
name: agent-orchestration-liveness
description: Coordinate long-running or multi-agent work with architect, worker, and independent read-only supervisor roles, including liveness, outcome batching, risk-triggered technical review, truthful completion layers, low-noise user reporting, and long-lived browser, desktop, or device sessions. Do not use for ordinary short single-owner tasks, ordinary technical code review, project-specific product planning, or direct machine operation.
---

# Agent Orchestration Liveness and Independent Supervision

## Preserve the three-role contract

Keep these authorities separate:

- **Architect**: own the current goal, business gate, priorities, task ownership, product and architecture decisions, integration, and acceptance. Dispatch bounded work and acknowledge its result. Enter direct execution only for one declared blocking hypothesis or one atomic integration action; state the minimal scope, stop condition, and handoff target, then exit when the blocker clears, the first stable failure appears, the scope must expand, or a worker can take over. Do not become the routine implementation worker or starve acknowledgements, dispatch, or integration decisions.
- **Worker**: own one bounded assignment and its declared hotspot. Execute autonomously inside that scope, stop at the first stable failure, and report current facts. Do not silently widen the assignment or claim a higher completion layer than the evidence supports.
- **Supervisor**: independently audit goal alignment, liveness, ownership, conflicts, truthful claims, and avoidable waste. Stay read-only. Do not assign workers, choose implementation details, operate machines, edit artifacts, or become a second architect. When a technical reviewer already covers the current candidate, verify review coverage, integration, freshness, and completion-layer truth instead of repeating routine code review.

Keep ordinary commit-level code review, test review, and defect adjudication in a separate technical-review workflow. Treat independent technical review as a risk-triggered responsibility, not a permanent fourth role or a default gate for every candidate. The reviewer must be independent of the primary implementer, but may be another available worker; do not create a standing heartbeat, Worktree, or approval role for the function. If the supervisor happens to notice a material safety, funds, data-integrity, or current-gate defect, record it and route it to the appropriate reviewer instead of expanding into a continuing code review.

## Establish the current operating contract

Record only the live facts needed to supervise the workflow:

- architect and supervisor thread IDs;
- active worker thread IDs and bounded assignments;
- outcome-batch ID, externally verifiable outcome, and shared pass/fail acceptance boundary;
- current business gate and its acceptance condition;
- active owner and write hotspot for each assignment;
- next observable checkpoint for each active assignment;
- explicit external waits, deadlines, and user dependencies;
- sole physical-machine or device operator, if exclusivity applies;
- last meaningful state change and timestamp;
- open supervisor findings and their response deadlines.

Route by full thread ID. Treat host or transport identifiers as transport metadata, not agent identity. Report delivery failures separately from task state.

Use the current state card as an index, not as unquestionable truth. For a material direction, completion, conflict, or risk judgment, sample the smallest direct current fact needed to check the claim: a fresh worker handoff, one relevant file or diff, one current task state, or one current runtime fact. Do not rescan the repository, replay completed tests, or rebuild a proof chain.

Treat old orders, process IDs, revisions, thread states, and failure codes as historical until the current workflow makes them relevant again.

## Issue bounded worker assignments

Give each worker one compact work order containing:

1. assignment ID and current business gate;
2. current verified fact or first unresolved failure;
3. one outcome that reduces the gate;
4. allowed hotspot and ownership boundary;
5. explicit exclusions and unsafe actions;
6. smallest sufficient acceptance check;
7. first-stable-failure stop condition;
8. required completion packet.

Prefer the smallest task that closes a dependency or reduces the largest current uncertainty. When approaching a user-visible milestone, prioritize a bounded vertical assignment that completes one end-to-end user outcome over additional isolated capability slices, unless a declared dependency or material risk must be resolved first. Dispatch independent tasks in parallel when they own different hotspots. Preserve one executable owner for an exclusive physical machine, device, account, or other non-concurrent resource.

Define one outcome batch by one externally verifiable outcome and one shared acceptance boundary. Multiple workers, hotspots, or dependency chains may participate only when they are required to pass that boundary. Keep ordinary repairs, technical reviews, and internal owner handoffs inside the batch; they may be re-dispatched internally but do not automatically create a new review, integration claim, or user-reporting boundary.

Before creating, merging, splitting, pausing, or closing an outcome batch; deciding whether a lifecycle event merits a new review; mapping a technical review to a completion layer; entering a bounded architect execution mode; or reconciling findings at gate closure, read [Outcome Batching and Review Budget](references/outcome-batching-and-review-budget.md) completely.

Before deciding whether independent technical review is required, preparing its handoff, issuing or consuming `TECH_CLEAR` or `TECH_BLOCKED`, or deciding whether a prior result is stale, read [Risk-Triggered Technical Review](references/technical-review-workflow.md) completely. Use Worker self-check plus Architect spot-check for low-risk, reversible, locally testable changes. Require independent review only when a protected semantic invariant is affected and the expected late-failure cost justifies the review, handoff, duplicate-evidence, and critical-path wait costs.

Do not add a Worktree, release artifact, hash chain, repeated preflight, approval step, or user reply phrase unless the actual assignment requires it. Do not ask the user to foreground a window, click an ordinary control, or repeat a fixed confirmation when available automation can perform the action safely.

## Classify liveness and relevance

Assign exactly one liveness state:

- `ACTIVE_WORK`: A named owner is executing a task that advances the current gate or removes a declared dependency, with a next observable checkpoint.
- `BOUNDED_WAIT`: A named non-user operation, observation, or dependency is still inside its declared boundary.
- `USER_WAIT`: Progress truly requires unresolved identity, login or verification, desktop unlock, UAC, physical input, new credentials or permissions, funds, or production authority.
- `STALLED`: The gate is incomplete, a safe relevant next action exists, and no owner is executing or acknowledging it.
- `COMPLETED`: The declared gate and all required handoffs are closed.

Activity alone is not progress. Mark work as a `YELLOW` direction risk when it is active but superseded, unrelated to the current gate, duplicative, in conflict with another owner, or unable to identify which current dependency or unknown risk it reduces.

Do not require a user-visible feature every heartbeat. Compilation repair, necessary tests, migrations, dependency recovery, and integration work can remain `ACTIVE_WORK` when they are bounded and directly serve the current gate. Label them as engineering progress rather than user-visible progress.

Do not classify these as stalled:

- a worker is executing a relevant bounded task;
- an observer is inside an explicit evidence window;
- the user intentionally paused the workflow;
- the next action is unsafe or requires real user authority;
- another owner already controls the same hotspot or exclusive resource.

Do not classify owned, reversible development operations as `USER_WAIT`. Evidence required is not approval required.

Before declaring `USER_WAIT`, inspect available authorization context, reversibility, current owner capability, and whether the action truly needs a new identity, login, verification, credential, permission, physical input, funds, or production authority. Do not require every project to create a new authorization ledger. If an avoidable interactive-runtime interruption currently requires a user action, record the immediate `USER_WAIT` separately from the orchestration `YELLOW` that explains the preventable interruption.

## Separate completion layers

State completion at the highest layer actually proven:

- **engineering complete**: the bounded implementation or repair and its direct checks passed;
- **integration complete**: the affected components completed their declared integrated path;
- **user-capability complete**: the intended user-visible or real-environment outcome was observed under its acceptance conditions.

Never use a lower layer to imply a higher one. A mock, simulator, unit test, process start, or API response is not automatically a real device, real funds, real user flow, or full business result.

A technical-review `TECH_CLEAR` proves only the reviewed layer. When a higher completion claim depends on a browser, desktop, device, remote session, or other runtime surface, run a representative real-surface probe at the first executable thin slice and before scaling a second full branch or dependent implementation on that surface. Until observed, cap the completion layer at engineering or local integration as supported by the evidence.

A required technical review blocks only promotion or shared integration of the affected risk scope. Keep unrelated and non-dependent work moving. `TECH_CLEAR` applies only to the declared review scope, candidate boundary, and proven engineering layer; it never proves integration, real-surface, or user-capability completion.

For any long-lived browser, desktop, device, remote-session, or interactive automation task; the first executable surface probe; runtime keepalive or interruption handling; a possible interactive `USER_WAIT`; or runtime cleanup, read [Interactive Runtime Lifecycle](references/interactive-runtime-lifecycle.md) completely.

## Audit direction and closed-loop throughput

At each review, answer:

1. Does every active assignment map to the current gate or a declared dependency?
2. Is each hotspot owned by exactly one writer, with exclusive resources controlled by one operator?
3. Did the workflow close tasks, change the gate, or reduce a named unknown risk since the prior boundary?
4. Are engineering progress and user-capability progress described honestly?
5. Are any tasks duplicated, superseded, conflicting, or serialized without need?
6. Did a completed worker result receive an architect decision and a next step?
7. Is there one material waste or one corrective direction worth raising?

Judge closed-loop throughput over the task's declared boundary or multiple heartbeat intervals, not by commit count or constant visible activity. Long-running `ACTIVE_WORK` must still identify the dependency or uncertainty being reduced and its next observable boundary. Repeated “investigating,” “preparing,” or “validating” without task exits, gate movement, or risk reduction is a stall candidate.

Do not invent waste or a correction to fill a report field. Record them only when they materially affect progress, and raise one highest-leverage correction rather than a list of optional improvements.

## Require the completion handshake

Require each worker to finish with one compact packet:

- assignment ID, outcome-batch ID, current gate, and shared acceptance boundary;
- result and changed state;
- highest completion layer proven;
- first stable failure, if any;
- safe state of owned processes, configuration, resources, and pending work;
- one allowed next action;
- whether the user is required and the stable reason.
- technical-review disposition (`NOT_REQUIRED` or `REQUIRED`); when required, include the protected invariant, reason, and one bounded review scope.

Require the architect to acknowledge the packet and do exactly one of these:

- close the assignment or gate;
- assign the next bounded action and owner;
- state a legitimate bounded or user wait.

A worker tool call ending without this handoff is not an orchestration close. If a completion packet is readable but transport delivery is ambiguous, treat the result as received and flag only the missing architect acknowledgement. Never duplicate work, tests, orders, or machine actions merely to test messaging.

Keep a same-batch repair packet inside the existing lifecycle. A repair completion may require a new owner or technical review, but it does not by itself create a new batch, event review, integration announcement, or user update.

## Separate internal orchestration from user reporting

Keep worker-to-architect communication fast and truthful, but do not mirror internal lifecycle events into the user conversation. Worker progress, failures, completion packets, architect acknowledgements, review cycles, repairs, and re-dispatch remain internal unless they cross a user-reporting boundary.

Make the architect the communication compression layer:

- update the user when the objective or gate changes, a material risk changes, a real `USER_WAIT` or `RED` appears, the user's requested reporting boundary arrives, or an already-declared user-visible completion boundary is proven;
- maintain only `last_user_update_at` and `last_user_visible_change` as lightweight reporting state; do not require a pending-message queue;
- escalate blockers, data anomalies, safety risks, and inability to continue to the architect without delay, even while normal user-facing progress is being batched.

Let the supervisor audit lifecycle leakage, repeated user updates without a user-visible delta, and material changes left unreported. A communication `YELLOW` corrects future reporting only; it does not approve wording, pause engineering, or let the supervisor define new user-visible completion boundaries.

When auditing communication health, sample the architect's user-facing updates since the previous communication-review boundary. A current state card or single latest snapshot cannot prove that lifecycle leakage did not occur. If the interval history is unavailable, mark the communication audit `NOT_RUN` and do not claim that reporting is clear.

Include one compact internal `communication_audit` record in every interval supervision card. Use exactly one status:

- `NO_NEW_UPDATES`: actually query the user-facing interval and confirm it contains no new architect updates; record `window` and `source`.
- `CHECKED`: actually read the interval; record `window`, `source`, `delta` (`none`, `objective`, `risk`, `decision`, or `completion`), and `result` (`CLEAR` or `YELLOW`).
- `NOT_RUN`: interval history is unavailable, the read failed, or only a latest snapshot is visible; record the stable reason and make no communication-health claim.

The field is mandatory even when liveness is `GREEN`, but the expanded template is not. Keep `NO_NEW_UPDATES` and `CHECKED/CLEAR` internal and silent to the user. A current state card, one latest message, or an architect self-report cannot support `NO_NEW_UPDATES` or `CHECKED/CLEAR`.

Before establishing or auditing user-facing reporting for a long-running workflow, read [User Reporting Boundaries and Batching](references/user-reporting-boundaries.md) completely. Let the active user request, project contract, or current objective declare any exact cadence or completion boundary; do not impose a universal interval.

## Track supervisor findings to closure

Give every actionable supervisor finding a stable ID such as `SUP-001` and record:

- the current gate or claim it affects;
- the smallest supporting fact;
- severity and concrete consequence;
- the required architect response boundary;
- finding state (`OPEN`, `CLOSED`, or `SUPERSEDED`), architect disposition, next-check boundary, and any terminal fact.

Require the architect to respond with one of:

- `ACCEPTED`: accept the finding and state the owner or next action;
- `PARTIALLY_ACCEPTED`: state the accepted portion and evidence-backed boundary;
- `REJECTED_WITH_EVIDENCE`: provide the minimal current fact that invalidates it.

Treat disposition as the architect's response, not as finding state. Keep `architect_ack`, `blocker`, and `next_check_boundary` as metadata. Carry `OPEN` findings across heartbeats until one current fact closes them or a replacement fact supersedes them. Transition only `OPEN → CLOSED` with one closing fact or `OPEN → SUPERSEDED` with one replacement fact or successor finding; both terminal states remain closed. A recurrence creates a new finding that references the old one.

When a business gate closes, reconcile every related finding as `CLOSED`, `SUPERSEDED`, or still `OPEN`. An `OPEN` finding must retain its blocker, next-check boundary, and whether it blocks the claimed completion layer. It may remain open and non-blocking, but it must not disappear silently.

## Use an explicit architect-supervisor exchange

Keep one minimum communication contract so that a critical review and its acknowledgement do not disappear inside free-form status prose:

- an event review request states the current objective or gate, why review now, changed facts, responsible owner or key dependency, highest proven completion layer, known gap or accepted limitation, and the assessment requested;
- an actionable supervisor finding has a stable ID, level, issue, minimal evidence, minimal correction, and follow-up boundary;
- the architect response records disposition, fact basis, action or evidence-backed reason for no action, and the next gate or follow-up boundary.

Before composing, responding to, updating, or closing an event review or supervisor finding, read [Architect-Supervisor Exchange Templates](references/review-exchange-templates.md) completely and use the applicable template. Do not apply the full templates to ordinary heartbeats, commits, tests, or routine progress updates.

Supervisor output is advisory: the supervisor identifies risk, conditions, and direction mismatch but has no general approval authority. A `YELLOW` does not automatically pause work. Only an independent safety or policy boundary, or a `RED` risk, pauses the affected action; unrelated safe work continues. The architect may accept a non-prohibited risk when the fact basis and follow-up boundary are explicit.

## Use heartbeat and event-driven reviews

Use both review modes:

- **Heartbeat review**: monitor long-running work at the cadence declared by the user or project. If none is declared, choose a cadence that matches the task's expected progress boundary instead of imposing a universal interval.
- **Event-driven review**: open a new review boundary only when there is a material delta in the externally verifiable outcome, shared acceptance boundary, risk or authority boundary, claimed completion layer, exclusive-resource conflict, or an open finding reaching its declared next-check boundary. An independent safety or policy check may also require a review.

At a heartbeat, read the latest state card and recent handoffs once, compare them with the previous boundary, and remain silent when work is relevant and healthy. Do not poll rapidly or micromanage a running worker. At an event review, inspect only facts needed for that transition.

Material delta does not replace liveness detection. If a next observable checkpoint passes without a fresh execution fact while a safe relevant action exists, keep the same outcome batch and perform a liveness recheck; mark `YELLOW/STALLED` when appropriate. Ordinary commits, tests, same-batch repairs, technical-review `TECH_CLEAR`, owner handoffs, or integration preparation are not new event-review boundaries by themselves.

## Detect and recover stalls

Use these recovery steps:

1. Recognize meaningful progress only when a gate fact, completed dependency, verified repair, ownership state, bounded wait, or named uncertainty changes.
2. If a worker finished without architect acknowledgement, send one wake-up containing the completion packet and required decision.
3. If the architect is idle while a safe relevant action exists, send one wake-up naming the current gate and the missing decision; do not assign the worker on the architect's behalf.
4. If active work is off-goal, send one correction naming the mismatched gate and the result that must be restored; do not prescribe the code solution.
5. Do not repeat the same wake-up more than once per heartbeat interval.

Use severity sparingly:

- `GREEN`: Goal-aligned work or a legitimate bounded wait; owners are clear, claims match evidence, and no material conflict exists. Stay silent unless a report was requested.
- `YELLOW`: First missed handoff, first direction mismatch, first full interval without meaningful progress while a safe action exists, or one material ownership or truthfulness concern. Wake the architect and set a response boundary.
- `RED`: The same unresolved `YELLOW` persists across two review boundaries, two control threads contend for one exclusive resource, or a new action risks production, credentials, funds, data integrity, or unrecoverable state. Pause only the affected new action and request a decision.

Clear a warning immediately when a current fact, acknowledged assignment, legitimate wait, corrected direction, or completed gate resolves it. Do not preserve obsolete warnings.

## Report compactly

Keep one internal supervision card with:

- current gate and acceptance condition;
- liveness state and highest completion layer;
- last meaningful progress and time;
- active owners, hotspots, and exclusive operator;
- explicit wait and deadline;
- duplicate, conflict, or direction mismatch;
- smallest sampled evidence;
- communication audit: `NO_NEW_UPDATES`, `CHECKED` with `CLEAR/YELLOW`, or `NOT_RUN`, with the required evidence fields;
- open supervisor findings and response boundary;
- material waste and one correction, only if present;
- next safe action;
- whether the user is required and why;
- `GREEN`, `YELLOW`, or `RED`.

Notify the architect for `YELLOW` or `RED`. Notify the user only at the boundaries defined above: an objective or gate change, a material risk change, a real `USER_WAIT` or `RED`, an explicitly requested report, or a declared user-visible completion boundary. Do not turn `GREEN` heartbeats or routine worker activity into user-facing chatter.

## Reject orchestration anti-patterns

Reject these patterns:

- treating busy workers, commits, tests, or thread count as business progress;
- treating a state card as proof without the smallest necessary current check;
- allowing indefinite `ACTIVE_WORK` without a risk, dependency, or next boundary;
- allowing the supervisor to become a second architect, dispatcher, release gatekeeper, or routine code reviewer;
- requiring independent technical review for every candidate, commit, or low-risk reversible change;
- making a reviewer rerun all Worker evidence or block unrelated safe work;
- presenting engineering completion as integration or user-capability completion;
- duplicating tasks or real-world actions to prove a handoff;
- adding unnecessary approvals, reports, hashes, manifests, signatures, fixed reply phrases, or repeated validations;
- rapid polling and mid-task micromanagement when a worker has a bounded expected boundary;
- freezing unrelated safe work because one external dependency is blocked;
- keeping monitoring alive after its target workflow is complete or paused.

## Stop monitoring cleanly

Disable the heartbeat when the declared workflow completes, the user pauses it, or no long-running target set remains. Return the final gate, completion layer, and any unacknowledged handoff or open finding. Do not leave a recurring monitor running without an active target.
