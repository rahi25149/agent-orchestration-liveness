---
name: agent-orchestration-liveness
description: Supervise and recover liveness, direction, handoffs, and truthful progress in long-running architect-worker-supervisor or multi-thread Codex workflows. Use when work spans hours, agents run on multiple machines, completion handoffs can be missed, recurring heartbeats are needed, or active threads may drift away from the current business gate without closing useful work. Do not use for short single-agent tasks, ordinary technical code review, project-specific product planning, or direct machine operation.
---

# Agent Orchestration Liveness and Independent Supervision

## Preserve the three-role contract

Keep these authorities separate:

- **Architect**: own the current goal, business gate, priorities, task ownership, product and architecture decisions, integration, and acceptance. Dispatch bounded work and acknowledge its result. Do not become the routine implementation worker.
- **Worker**: own one bounded assignment and its declared hotspot. Execute autonomously inside that scope, stop at the first stable failure, and report current facts. Do not silently widen the assignment or claim a higher completion layer than the evidence supports.
- **Supervisor**: independently audit goal alignment, liveness, ownership, conflicts, truthful claims, and avoidable waste. Stay read-only. Do not assign workers, choose implementation details, operate machines, edit artifacts, or become a second architect.

Keep ordinary commit-level code review, test review, and defect adjudication in a separate technical-review workflow. If the supervisor happens to notice a material safety, funds, data-integrity, or current-gate defect, record it and route it to the appropriate reviewer instead of expanding into a continuing code review.

## Establish the current operating contract

Record only the live facts needed to supervise the workflow:

- architect and supervisor thread IDs;
- active worker thread IDs and bounded assignments;
- current business gate and its acceptance condition;
- active owner and write hotspot for each assignment;
- expected next progress boundary or bounded completion time;
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

Prefer the smallest task that closes a dependency or reduces the largest current uncertainty. Dispatch independent tasks in parallel when they own different hotspots. Preserve one executable owner for an exclusive physical machine, device, account, or other non-concurrent resource.

Do not add a Worktree, release artifact, hash chain, repeated preflight, approval step, or user reply phrase unless the actual assignment requires it. Do not ask the user to foreground a window, click an ordinary control, or repeat a fixed confirmation when available automation can perform the action safely.

## Classify liveness and relevance

Assign exactly one liveness state:

- `ACTIVE_WORK`: A named owner is executing a task that advances the current gate or removes a declared dependency, with a bounded next progress boundary.
- `BOUNDED_WAIT`: A named external operation or observation is still inside its declared deadline.
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

## Separate completion layers

State completion at the highest layer actually proven:

- **engineering complete**: the bounded implementation or repair and its direct checks passed;
- **integration complete**: the affected components completed their declared integrated path;
- **user-capability complete**: the intended user-visible or real-environment outcome was observed under its acceptance conditions.

Never use a lower layer to imply a higher one. A mock, simulator, unit test, process start, or API response is not automatically a real device, real funds, real user flow, or full business result.

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

- assignment ID and current gate;
- result and changed state;
- highest completion layer proven;
- first stable failure, if any;
- safe state of owned processes, configuration, resources, and pending work;
- one allowed next action;
- whether the user is required and the stable reason.

Require the architect to acknowledge the packet and do exactly one of these:

- close the assignment or gate;
- assign the next bounded action and owner;
- state a legitimate bounded or user wait.

A worker tool call ending without this handoff is not an orchestration close. If a completion packet is readable but transport delivery is ambiguous, treat the result as received and flag only the missing architect acknowledgement. Never duplicate work, tests, orders, or machine actions merely to test messaging.

## Track supervisor findings to closure

Give every actionable supervisor finding a stable ID such as `SUP-001` and record:

- the current gate or claim it affects;
- the smallest supporting fact;
- severity and concrete consequence;
- the required architect response boundary;
- current disposition and closure fact.

Require the architect to respond with one of:

- `ACCEPTED`: accept the finding and state the owner or next action;
- `PARTIALLY_ACCEPTED`: state the accepted portion and evidence-backed boundary;
- `REJECTED_WITH_EVIDENCE`: provide the minimal current fact that invalidates it.

Carry unresolved findings across heartbeats until accepted work closes them or current evidence makes them obsolete. Do not restate a closed finding, multiply IDs for the same fact, or let the supervisor block unrelated work while awaiting a response.

## Use explicit architect-supervisor exchange templates

Use stable field templates so that a review decision and its acknowledgement cannot disappear inside free-form status prose. Keep each field short and include only current facts.

For an architect-to-supervisor event review request, send:

```text
<REVIEW_KIND>
Current gate:
Trigger and decision requested:
Facts changed since the last review:
Owners, hotspots, and exclusive operator:
Highest completion layer actually proven:
Known gap or explicitly non-blocking debt:
Proposed next action and first-stable-failure stop:
Return requested: GREEN / YELLOW / RED, decision, and necessary conditions.
```

Use review kinds that describe the transition rather than the implementation, such as `PRE_REAL_FLOW_REVIEW`, `POST_REAL_FLOW_REVIEW`, `INTEGRATION_REVIEW`, `PRE_RELEASE_REVIEW`, or `MILESTONE_COMPLETION_REVIEW`. Project-specific contracts may define narrower names.

For a new supervisor finding, send exactly one compressed line:

```text
Finding ID | Level | Core issue | Minimal current evidence | One correction | Latest response gate
```

For the architect's formal response, send:

```text
Finding ID:
Disposition: ACCEPTED | PARTIALLY_ACCEPTED | REJECTED_WITH_EVIDENCE
Fact basis:
Action and owner, or evidence-backed reason for no action:
Updated current gate:
User required: yes/no and stable reason
```

For an unresolved finding whose facts change before closure, send a compact status update containing the finding ID, changed fact, whether the original correction remains in force, and the next boundary. For closure, name the single current fact that closes it.

For a `GREEN` event review with no finding, reply only with the level, decision, necessary conditions, and whether the requested transition is allowed. Do not create an empty supervisor finding merely to acknowledge a healthy transition.

Do not copy large logs, process lists, revisions, hashes, or repeated history into these templates. Include such identifiers only when they are the smallest fact needed for the current decision.

## Use heartbeat and event-driven reviews

Use both review modes:

- **Heartbeat review**: monitor long-running work at the user's cadence; otherwise default to 30 minutes.
- **Event-driven review**: review after a goal or business-gate change, creation of a possibly unrelated task, transition from smoke check to a full or real flow, completion of a real business chain, a high-risk or irreversible action, integration, deployment, or a milestone-completion claim.

At a heartbeat, read the latest state card and recent handoffs once, compare them with the previous boundary, and remain silent when work is relevant and healthy. Do not poll rapidly or micromanage a running worker. At an event review, inspect only facts needed for that transition.

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
- open supervisor findings and response boundary;
- material waste and one correction, only if present;
- next safe action;
- whether the user is required and why;
- `GREEN`, `YELLOW`, or `RED`.

Notify the architect for `YELLOW` or `RED`. Notify the user only for `RED`, a real `USER_WAIT`, or an explicitly requested periodic report. Do not turn `GREEN` heartbeats or routine worker activity into user-facing chatter.

## Reject orchestration anti-patterns

Reject these patterns:

- treating busy workers, commits, tests, or thread count as business progress;
- treating a state card as proof without the smallest necessary current check;
- allowing indefinite `ACTIVE_WORK` without a risk, dependency, or next boundary;
- allowing the supervisor to become a second architect, dispatcher, release gatekeeper, or routine code reviewer;
- presenting engineering completion as integration or user-capability completion;
- duplicating tasks or real-world actions to prove a handoff;
- adding unnecessary approvals, reports, hashes, manifests, signatures, fixed reply phrases, or repeated validations;
- rapid polling and mid-task micromanagement when a worker has a bounded expected boundary;
- freezing unrelated safe work because one external dependency is blocked;
- keeping monitoring alive after its target workflow is complete or paused.

## Stop monitoring cleanly

Disable the heartbeat when the declared workflow completes, the user pauses it, or no long-running target set remains. Return the final gate, completion layer, and any unacknowledged handoff or open finding. Do not leave a recurring monitor running without an active target.
