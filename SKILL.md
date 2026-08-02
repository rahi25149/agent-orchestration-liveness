---
name: agent-orchestration-liveness
description: Monitor and recover liveness in long-running multi-agent or multi-thread Codex workflows. Use when work spans hours, agents run on multiple machines, completion handoffs can be missed, an architect may become idle after a worker finishes, or a recurring heartbeat must distinguish productive work from stalled orchestration. Do not use for short single-agent tasks or as a substitute for technical review, project management, or direct machine operation.
---

# Agent Orchestration Liveness

## Act as a watchdog, not a second architect

Observe the current gate, active owners, recent progress facts, completion handoffs, and the architect's next action. Detect silence and broken handoffs; do not redesign the plan, run tests, operate a machine, edit code, or create competing work.

Use the target architect's current state card as the source of truth. Treat old orders, PIDs, thread states, and prior failure codes as historical until reconfirmed.

## Establish the monitored workflow

Record:

- architect thread ID;
- active worker thread IDs and their bounded assignments;
- current business gate and owner;
- expected next progress boundary;
- explicit waits, deadlines, and user dependencies;
- sole physical-machine operator, if any;
- last confirmed state change and timestamp.

Route by full thread ID. Treat `hostID` as transport metadata, not a globally unique agent identity. Never invent or mutate host IDs. If delivery fails, report the transport failure separately from task state.

When recurring monitoring is requested, use the product's automation mechanism. Use the user's cadence; otherwise default to 30 minutes for multi-hour work. Disable the monitor when the workflow completes or the user pauses it.

## Classify liveness

Assign exactly one state:

- `ACTIVE_WORK`: An owner is running a relevant task or produced a new fact within the current interval.
- `BOUNDED_WAIT`: A named external operation is still inside its declared deadline.
- `USER_WAIT`: Progress truly requires UAC, desktop unlock, login/verification, unresolved identity, real physical input, production approval, or new credentials/permissions.
- `STALLED`: The gate is incomplete, a safe next action exists, and no owner is executing or acknowledging it.
- `COMPLETED`: The declared gate and handoff are closed.

Do not classify these as stalled:

- a worker is visibly executing a relevant bounded task;
- an observer is inside an explicitly bounded evidence window;
- the user has intentionally paused the workflow;
- the next action is unsafe or requires real user authority;
- another owner already controls the same hotspot or physical machine.

Do not classify ordinary, owned, reversible development operations as `USER_WAIT`. “Evidence required” is not “user approval required.”

## Require a completion handshake

Require each worker to finish with one compact packet:

- assignment ID or current gate;
- result and changed state;
- first stable failure, if any;
- safe state of owned processes, configuration, and pending work;
- one allowed next action;
- whether the user is required and why.

Require the architect to acknowledge the packet and either close the gate, assign the next bounded action, or state a legitimate wait. A worker's tool completion without this handoff is not a completed orchestration step.

If a completion packet is readable but delivery status is ambiguous, treat the work result as received and flag only the missing acknowledgement. Never duplicate orders, tests, or machine actions to test messaging.

## Detect and recover stalls

At each heartbeat:

1. Read the latest state card and recent messages once.
2. Compare the current gate, owners, and evidence with the previous heartbeat.
3. Recognize meaningful progress only when a business fact, verified repair, ownership state, or explicit bounded wait changed.
4. If progress is active or legitimately bounded, record it without interrupting work.
5. If a worker finished and the architect has not acknowledged it, send one wake-up containing the completion packet and required decision.
6. If the architect is idle while a safe next action exists, send one wake-up naming that action and its owner.
7. Do not retry the same wake-up more than once per heartbeat interval.

Use severity sparingly:

- `YELLOW`: First missed handoff or first full interval with no meaningful progress while a safe next action exists. Wake the architect before the next expensive action.
- `RED`: The same unresolved stall persists across two consecutive intervals, two control threads contend for one physical device, or a new write would risk production, credentials, funds, or unrecoverable state. Pause new affected writes and request a decision.

Clear a warning immediately when a new fact, acknowledged assignment, legitimate bounded wait, or completed gate appears. Do not keep obsolete warnings alive.

## Report compactly

Return only:

- current gate;
- liveness state;
- last meaningful progress and time;
- active owner or missing owner;
- explicit wait and deadline, if any;
- first missed handoff or stall reason;
- wake-up sent and response deadline;
- next safe action;
- whether the user is required;
- `GREEN`, `YELLOW`, or `RED`.

Notify the user only for `RED`, a real `USER_WAIT`, or a requested periodic report. Do not produce routine chatter for `ACTIVE_WORK` or `BOUNDED_WAIT`.

## Stop monitoring cleanly

End or disable the heartbeat when the declared workflow completes, the user pauses it, or no long-running thread set remains. Return the final state and any unacknowledged handoff; do not leave a recurring monitor running without an active target.
