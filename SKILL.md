---
name: agent-orchestration-liveness
description: Coordinate long-running or multi-agent work with architect, worker, and independent read-only supervisor roles, including liveness, bounded context lifecycle, outcome batching, risk-triggered technical review, truthful completion layers, low-noise user reporting, and long-lived browser, desktop, or device sessions. Use when persistent role threads need safe handoff, compaction, fresh-thread rotation, or low-cost context-efficiency measurement. Do not use for ordinary short single-owner tasks, ordinary technical code review, project-specific product planning, or direct machine operation.
---

# Agent Orchestration Liveness and Independent Supervision

## Preserve the three-role contract

Keep these authorities separate:

- **Architect**: own the current goal, business gate, priorities, task ownership, product and architecture decisions, verification and review budget, integration, and acceptance. At every new gate or outcome batch, map the smallest dependency, write-hotspot, and exclusive-resource graph before dispatch. Dispatch bounded work and acknowledge its result. Enter direct execution only for one declared blocking hypothesis or one atomic integration action; state the minimal scope, stop condition, and handoff target, then exit when the blocker clears, the first stable failure appears, the scope must expand, or a worker can take over. Do not become the routine implementation worker or starve acknowledgements, dispatch, or integration decisions.
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

## Bound long-lived context and measure rotation cost

Treat native compaction as a context safety valve, not as the authority for workflow continuity. Keep one bounded Architect authority snapshot and one smaller Supervisor overlay that references the Architect revision. Reuse an established branch, Worktree, or owner when appropriate, but do not reuse unbounded chat history merely because those engineering resources persist.

Rotate a long-lived role thread only at a safe handoff boundary plus a real pressure signal, unless continuity is already untrustworthy. Immediately before starting the fresh thread, recheck every named Architect, Worker, reviewer, and exclusive operator for queued or resumed work; a prior stop or completion acknowledgement can race with a pending assignment and does not by itself prove the boundary is still safe. Start a fresh thread with the bounded role state and current assignment; do not fork the full history to claim a context reset. The new thread must verify the smallest current facts before accepting the state packet.

Keep an Architect bootstrap bounded to the role and authority contract, freshness marker, current gate and completion layer, current owner and hotspot, one next action, applicable authorization and stop boundaries, and only the facts needed for that action. Refer to the bounded authority snapshot instead of reprinting its full acceptance matrix, old adjudications, or historical state. The first turn in which continuity checks are complete and no required fact or external wait remains is the `first actionable turn`; it must also perform the first correct advancing action before returning. For an owner-dispatch action, return the complete bounded `DISPATCH_PACKET`; if one necessary fact is missing, return `BLOCKED` with that fact. `BLOCKED` is an output protocol, not a liveness state; classify the resulting wait by the owner and nature of the missing fact. Do not split a ready action into an acknowledgement turn followed by open-ended re-planning, relabel a ready dispatch as open-ended analysis, or let the controller author or complete business content.

When direct peer-state inspection is unavailable, the controller may attach one fresh, target-bound, content-neutral liveness attestation to the authority snapshot. It may state only the target role and thread reference, observed `IDLE` or `INACTIVE` state, absence of a queued action, observation and expiry or invalidation boundary, bound authority-snapshot revision, and direct-observation source. It proves transport readiness only: it must not choose an owner, task, gate, authorization, completion layer, or business packet content. The fresh Architect may rely on it only for that runtime fact; a missing, stale, mismatched, or conflicting attestation requires only `BLOCKED: PEER_LIVENESS_UNVERIFIED`, not transport-protocol exploration or a partial packet. Recheck the target immediately before a mechanical relay, invalidate the attestation if state changed, and never edit the Architect's packet to fit the new state. This attestation does not create a direct bridge or alter a frozen manual-transport cohort.

Before `thread/start`, directly re-read and preserve the incumbent role's actual model, reasoning, service tier, approval policy and reviewer, network policy, and other declared cohort invariants. For a Git-backed role whose authorization ledger permits ordinary local or Git atomic actions, resolve the selected Worktree's absolute Git directory and necessary Git common directory, then provision the smallest effective role-turn policy that writes the ordinary workspace and only those validated Git metadata roots. Legacy `workspace-write` keeps `.git` and resolved Git directories protected read-only, so adding them as writable roots is not a correction; use a named least-privilege permission profile or a platform-equivalent policy proven by the role turn, never `danger-full-access`. Before treating the epoch as eligible, verify the first persisted or runtime `turn_context`, or equivalent effective policy, against the selected profile and every cohort invariant. Recheck that effective policy after a client, connection, host, resume, compact, or runtime transition that can change it and before the first action needing the protected capability; a first-turn match cannot prove later resumed turns. A `thread/start` response, controller-side command, or control-plane probe alone is insufficient. On any mismatch, abandon the fresh epoch without retrofit, retain the last-good role, and correct the profile at a safe boundary. Probe every new capability surface content-free and begin a new comparable cohort; retain earlier epochs only as immutable historical evidence.

The orchestration controller is never an approval reviewer. It must not click an approval UI, use GUI or Computer Use to approve, forward or transform an approval into consent, impersonate the user, or auto-approve on the user's behalf. A named action already covered by the authorization ledger must be completed autonomously by its owning role; a sandbox denial caused by an underspecified fresh-thread capability profile is a controller correction, not `USER_WAIT`. If such a required positive action requests approval, observe without acting, abandon the defective fresh epoch, and correct the capability surface at a safe boundary. An intentionally out-of-scope negative probe may pass by producing an untouched approval request; end that disposable probe without responding and verify that the write did not occur. Do not record a context regression merely for the controller's profile defect; record one only when the role itself forgets or violates the authorization boundary. Report only a genuine identity ambiguity, UAC, desktop unlock, login or verification step, required physical input, production or real-funds boundary, new credential or permission, or action outside the ledger as a user gate.

Treat a correct first-turn continuity acknowledgement as a provisional authority transfer, not as proof that the new role will preserve its operating contract. Keep the prior role read-only and recoverable until the new role closes its first comparable outcome epoch without a handoff-linked substantive regression. Only then finalize the rotation as accepted and retire the prior role. If the new role loses its role or authority boundary, routes the wrong owner, fails to consume a required handoff, misstates a completion layer, or leaks internal lifecycle reporting because of the handoff, roll the rotation back and abort the epoch. Do not attribute an ordinary implementation defect to rotation without a direct continuity link.

Treat a declared bounded-output turn as stalled only when its required facts and Skill or state reads are complete, no tool call or external result is in flight, no result, `BLOCKED`, or new concrete missing fact has appeared, and the runtime-specific watchdog has passed. Repeated planning summaries may corroborate the stall but cannot be its sole evidence. Do not interrupt open-ended architecture analysis, an active tool or external wait, a newly identified necessary fact, or valid bounded output while it is making observable progress. If output starts but stops before a complete result and a separate runtime-specific progress watchdog passes under the same no-wait conditions, re-evaluate it as stalled. If a correctly specified fresh role reaches this state during provisional continuity and controller interruption is required to restore the last-good role, record a handoff-linked substantive regression, roll back, and abort the epoch; do not coax the failed thread or fill in its packet.

Measure context changes as a small experiment, not as a new governance system. Keep the metrics log outside the repository with user-only permissions. Never record prompts, responses, tool output, diffs, credentials, personal data, or free-form notes. Separate Architect and Supervisor cohorts, compare equivalent work and model routes, and use exactly three decision metrics:

- median input tokens per completed turn, with cached input retained only as diagnostic context;
- observed substantive context regressions, classified as `constraint_miss` or `duplicate_work`;
- cold-start turns from a fresh role thread to its first correct advancing action.

Daily token totals may help diagnose load, but must not decide whether a context policy passes. The live state card remains the workflow authority; the append-only metrics file is only an experiment record.

Before changing compaction, handoff, fresh-thread rotation, role-state schemas, context-cost instrumentation, or the related stop and rollback gates, read [Context Lifecycle and Runtime Metrics](references/context-lifecycle-and-runtime-metrics.md) completely. Begin with its local Phase 0 recorder validation. Do not hand-estimate token usage, and do not enable hooks, thread automation, a collector, database, or dashboard until real App Server turn-usage capture is verified and the manual pilot has enough comparable samples without a substantive continuity regression.

When Codex Desktop's isolated stdio App Server connection cannot be observed directly, use the reference's armed rollout bridge only for a blank non-ephemeral thread created through a controlled App Server connection. Arm it before the first turn, keep the exact model and reasoning route fixed for the epoch, and reject any existing unarmed rollout. The same controlled App Server instance must remain the sole persistence writer from `thread/start` until the measured epoch closes or rolls back. Keep it alive across every turn, and do not load, read, wait on, follow, or send to the tested role through Codex Desktop or another App Server; even read-only inspection may acquire the writer or change the effective policy. Observe the role only through the owning connection and the pre-armed content-free rollout or metrics path.

At a terminal epoch boundary, first collect terminal usage without an epoch outcome; then ask the same owning connection to `thread/unsubscribe`, stop it gracefully, and verify that no live holder remains before another client resumes the thread. Only after that release proof may collection append `completed`, and the Desktop bridge requires the explicit `--writer-release-proven` close guard; append the applicable rotation event afterward. Treat `unsubscribed`, UI `IDLE`, a closed view, an empty lock file, or a product inactivity TTL as insufficient release proof by itself. If ownership is lost or a foreign writer appears, stop delivery, never steal the lock, and use one bounded recovery window only to prove safe release. If release or same-owner provenance cannot be restored within that window, collection may close the measured epoch as `aborted` and record the provisional rollback, but no client may resume or retry that thread until release is independently proven. Retain the last-good role without recording a role context regression for the controller transport defect; never append `completed` before cleanup can still fail. A change to the writer-ownership policy, App Server lifecycle policy, or Desktop-participation policy is a new transport surface and starts a new comparable cohort after a content-free probe. This bridge is never a historical transcript importer.

## Issue bounded worker assignments

Give each worker one compact work order containing:

1. assignment ID and current business gate;
2. current verified fact or first unresolved failure;
3. one outcome that reduces the gate;
4. allowed hotspot and ownership boundary;
5. explicit exclusions and unsafe actions;
6. smallest sufficient acceptance check;
7. first-stable-failure stop-and-report condition; any later same-hotspot repair requires an explicit Architect re-dispatch after the completion handshake and preserves one writer;
8. a semantic `verification_budget` separating directly affected checks, stable-candidate checks, and promotion or representative real-surface checks, with evidence invalidation conditions;
9. required completion packet.

Prefer the smallest task that closes a dependency or reduces the largest current uncertainty. When approaching a user-visible milestone, prioritize a bounded vertical assignment that completes one end-to-end user outcome over additional isolated capability slices, unless a declared dependency or material risk must be resolved first. Treat active concurrency and evidence freshness as separate Architect duties. When at least two safe, relevant, ready assignments have independent facts, owners, write hotspots, and non-exclusive resources, dispatch them concurrently by default; fill only the project-declared safe capacity with work that passes the outcome removal test. Numerical lane or Worktree counts are project-specific caps, never quotas. Do not create a Worktree, technical review, Supervisor, investigation, or acceptance lane merely to fill capacity. Use idle capacity during a long `BOUNDED_WAIT` only for a different ready hotspot, never to duplicate the same test, runtime action, or atomic outcome; an independently closable result belongs to its own batch. When fewer than two assignments qualify, name the concrete dependency, hotspot conflict, exclusive resource, unstable authority fact, or failure-blast-radius reason instead of saying only that work is sequential. Preserve one writer per hotspot and one executable owner for an exclusive physical machine, device, account, or other non-concurrent resource; do not split one atomic outcome merely to manufacture concurrency.

Reuse a passing check or review while it remains bound to the same candidate and its covered scope has not changed. Before repeating evidence collection, require one concrete invalidation fact: a covered candidate delta, repair of a failed check, relevant evidence or environment expiry, source conflict, or promotion to a higher completion layer that needs representative real-surface evidence. Do not rerun merely for a handoff, message acknowledgement, ordinary commit, same-batch repair outside the covered scope, or reviewer change. A verification budget is a semantic boundary, not a fixed time, token, or universal run-count quota: never use evidence reuse to omit the first check required for funds, identity, authorization, idempotency, production, safety, or a truthful completion-layer claim.

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

For each qualifying material event-driven Supervisor review, use a fresh, read-only, short-lived Supervisor thread scoped to that event. Bootstrap it from the latest Architect authority snapshot, the bounded Supervisor overlay, and only the `OPEN` findings relevant to the review. End the thread after it emits its review result; capture the Architect disposition and finding transition in the stable overlay and finding lifecycle without keeping the review thread alive. Heartbeats and ordinary commits, tests, same-batch repairs, technical-review results, owner handoffs, or integration preparation do not create review threads. A same-batch repair triggers a fresh scoped re-review only when it reaches an `OPEN` finding's declared next-check boundary and provides new evidence for closure or reassessment. `TECH_REVIEW` remains a separate workflow.

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
