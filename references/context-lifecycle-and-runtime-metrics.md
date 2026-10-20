# Context Lifecycle

This compatibility path contains the normal bounded-state and safe-handoff contract. Read it when actually changing lifecycle/state mechanisms or performing a handoff, Goal transfer, or continuity/capability recovery; reuse its fully read, current contents for ordinary dispatch, small state updates, and native peer reads.

Normal work does not require experimental cohorts, metric events, capability-negative probes, App Server writer instrumentation, or hooks. Those unchanged research protocols are isolated in [Dormant Context Experiments](context-experiments.md), loaded only for explicitly authorized non-critical, cost-bounded research or the necessary safe closure/recovery of an already-open measured operation. Neither this link nor a policy edit authorizes starting or resuming an experiment.

For project setup, adoption and ordinary continuation, use [Project Initialization and Resume](project-initialization.md). Resume the adopted agreement and existing state; do not treat a missing setup marker as a handoff, permission to replay work, or authority to activate a paused Goal. This lifecycle reference is required when actually changing state storage or transferring authority, not for every ordinary resume.

## Contents

1. [Keep one authority and one overlay](#keep-one-authority-and-one-overlay)
2. [Use long-lived context and hand off at a safe boundary](#use-long-lived-context-and-hand-off-at-a-safe-boundary)
3. [Keep native compaction narrow](#keep-native-compaction-narrow)

## Keep one authority and one overlay

Compaction is a context safety valve. It is not a workflow database and cannot make stale state correct.

Keep two deliberately asymmetric role files outside the project repository:

- **Architect authority snapshot**: the current objective, gate, outcome batch, owners, hotspots, verified facts, authorization boundary, blockers, highest proven layer, next safe action, facts the next thread must not assume, and—when persisted Goal continuity is required—only the opaque Goal revision, lifecycle status, transfer state, declared budget scope, and ephemeral transfer-envelope reference.
- **Supervisor overlay**: the Architect revision it reviewed, open findings, last gate-relevant progress, last event and communication-review boundaries, latest supervision delta, and the declared cadence, checkpoint, or next supervision action.

The Supervisor overlay must not copy the complete gate, owner map, or execution plan. It refers to the Architect revision and stores only independent supervision state.

Recommended hard limits:

- Architect state: 3 KiB;
- Supervisor overlay: 2 KiB;
- at most six concise verified facts in the Architect state;
- one current file plus one atomically replaced `last-good` copy per role;
- no append-only state history.

Use one writer per role. Increase a monotonic revision only for a material delta: a batch opening or closing, owner or hotspot change, authority change, real wait, blocker change, completion-layer change, or next-safe-action change.

Never store credentials, cookies, personal data, prompts, replies, transcripts, logs, diffs, command output, or sensitive authorization material in role state. An authorization field records what class of action is allowed, not the secret that enables it.

A persisted Goal is a separate thread-scoped continuation contract. Do not copy its exact objective into the 3 KiB Architect state or metrics ledger, where it could be truncated, duplicated, or become a competing source of truth. Keep the exact incumbent-signed objective and its completion and stop conditions only in the incumbent Goal, one exact one-time transfer envelope, and the successor Goal after staging. The controller may transmit that envelope mechanically and hold only its opaque reference while the handoff is open; it must clear that reference when the handoff closes and must not summarize, edit, infer, or retain the envelope as experiment history.

## Use long-lived context and hand off at a safe boundary

The default is one project-native, long-lived Architect using native compaction plus bounded current state. Do not start a handoff solely because of elapsed time, turn count, context percentage, a high-context observation, a material objective change, or one or more successful compactions. Those facts may trigger a bounded review of freshness, quality, latency, and cost; they are not handoff authorization.

A handoff may begin only when the user or current business authority explicitly chooses a lifecycle migration, or when direct evidence shows that authority, Goal, project, route, capability, transport, or working-mode continuity is untrustworthy and cannot be repaired in place through one bounded correction. Repeated rereading, re-derivation, constraint loss, owner mistakes, or duplicate work are evidence only when directly observed; context size or compaction count is not a proxy for them.

A safe boundary means:

- the coherent outcome batch is closed or at a stable candidate boundary;
- no completion packet still needs an Architect decision;
- no atomic browser, desktop, device, funds, deployment, or other exclusive operation is in flight;
- when persisted Goal continuity is required, neither an incumbent continuation nor a Goal-management operation is in flight or queued, and the Goal transfer envelope and budget scope are current;
- immediately before `thread/start`, every named Architect, Worker, reviewer, and exclusive operator has been rechecked for a queued or resumed action after the stop boundary;
- owners, hotspots, waits, findings, and the next safe action are in the bounded role state;
- the new role thread can verify the smallest direct current facts without replaying the project.

A stop response, idle snapshot, or completion acknowledgement is not durable proof of this boundary. A previously queued assignment or automatic continuation may start after that observation. If any new execution fact appears before the fresh thread starts, invalidate the boundary, preserve the resulting state, and begin a new boundary check instead of declaring continuity verified.

When continuity is already untrustworthy, freeze new business effects and preserve the safe state of every in-flight exclusive operation before recovery. Do not treat two compactions, a large context, or a major objective change as proof that continuity is untrustworthy; require the actual authority, constraint, owner, duplication, Goal, project, capability, transport, or working-mode failure.

Create a fresh thread with the role contract, bounded role state, current assignment, and only the necessary recent handoff. Do not use a full-history fork as a context reset. Reuse the existing branch, Worktree, and owner when that remains correct.

When the incumbent already has a persisted Goal, or the user or project requires one, the fresh thread does not inherit it from the project, authority snapshot, or bootstrap. Require an incumbent-signed one-time Goal transfer envelope containing the exact objective, lifecycle, completion and stop conditions, token budget and usage when present, declared budget scope, and an opaque Goal revision. If a required incumbent Goal or exact envelope is missing, return `BLOCKED: ARCHITECT_GOAL_UNDECLARED`. Do not impose this gate on an ordinary one-off Architect task for which no Goal was present or required.

Stage the successor Goal with the exact objective in `paused` state and read it back before authority transfer. A staged candidate has no business authority and may not dispatch, write, start runtime, or rely on automatic continuation. At the final boundary, use this fail-closed freeze sequence:

1. verify no incumbent or peer turn, automatic continuation, completion packet, or exclusive action is in flight or queued;
2. pause the incumbent Goal and read it back;
3. recheck that no incumbent continuation became queued across the pause boundary;
4. transfer authority to the successor while both Goals remain paused;
5. activate the successor Goal and read back its exact objective, active status, and declared budget policy before permitting business action.

Do not call that sequence atomic. Prefer a short interval with neither Goal active over any interval with both active. If successor activation or verification fails before a successor business action, first pause and verify the successor, then return authority to the incumbent, then resume and verify the incumbent. If any read, queue state, or lifecycle remains ambiguous, leave both Goals paused, permit no business action, and return `BLOCKED: PERSISTENT_GOAL_STATE_UNVERIFIED`; never guess that rollback succeeded. A normal prompt containing the same words is not persisted-Goal evidence, and a runtime without a supported Goal set/read surface cannot complete a required Goal-aware handoff.

Do not infer budget scope from the runtime counters. If the signed envelope declares one cross-thread product-Goal cap, set the successor budget to `max(0, incumbent tokenBudget - incumbent tokensUsed)` as a new handoff safety cap, not as inherited usage accounting. If it declares a per-thread cap, use the declared successor amount. If it declares no budget, preserve no budget. If a budget exists but its scope is undeclared, keep the successor paused and block transfer. Preserve a paused Goal as paused; do not revive a terminal or budget-limited Goal without a new Architect or user decision.

For an Architect, the bootstrap should contain the role and authority contract, freshness marker, current gate and completion layer, current owner and hotspot, one next action, applicable authorization and stop boundaries, and only the facts needed for that action. Point to the bounded Architect authority snapshot instead of copying its full acceptance matrix, historical adjudications, or old lifecycle detail into the prompt. The controller may carry and transmit this state, but it must not write, complete, or correct the Architect's business packet.

Prefer directly verified role communication and native peer-state reads. If a handoff already authorizes a content-neutral liveness attestation, bind it to the exact target and authority-snapshot revision and include only the role/thread reference, observed idle state, no queued action, observation time, expiry/invalidation, and direct source. It is readiness evidence, not permission to choose work, repair a business packet, widen transport, or replace a required direct role channel. Missing or conflicting peer evidence is `BLOCKED: PEER_LIVENESS_UNVERIFIED`; use the existing authorized surface, not experimental transport exploration.

Preserve the incumbent role's directly observed model, reasoning, service tier, approval/reviewer and network policy unless the user explicitly authorized a change. Verify actual effective capability, not only creation settings. Filesystem capability does not expand business authorization; the controller never reviews, clicks, relays or auto-approves an approval request. Authorized ordinary actions belong to the owning role. A fresh profile mismatch is a setup defect: leave approvals untouched and correct only the already-declared least-privilege surface at a safe boundary, not by broadening access or claiming `USER_WAIT`. A different surface requires the owning Architect's explicit authorization; genuine new permission or other human gates remain unchanged.

For a Git-backed role, verify that the effective supported permission surface covers only the intended workspace and required Git metadata, preserves protected configuration and other policy boundaries, and does not change real refs, index, worktrees or unrelated resources merely to prove setup. Required capability must be established before the first action that uses it and rechecked after a transition that could invalidate it. Normal native handoff does not require the experimental App Server profile/positive-and-negative probe matrix; that matrix remains in the separately gated research reference.

The new thread must:

1. validate the role, project, revision, and freshness marker;
2. sample the smallest current workspace or runtime fact needed to reject stale state;
3. state the current gate, next safe action, and one forbidden assumption;
4. when Goal continuity is required, verify the staged Goal revision and paused lifecycle without treating it as business authority;
5. after the freeze sequence grants authority and activates the Goal, first consume and adjudicate any existing Worker completion before dispatching new work;
6. after consuming any existing completion and before the first dispatch, rescan current ready lanes instead of inheriting the incumbent's prior SERIAL decision;
7. perform the first correct advancing action in the first turn where those checks are complete and no required fact or external wait remains;
8. return a continuity acknowledgement.

Goal continuity does not replace direct role channels, the Worker completion handshake, existing-owner reconciliation, the first correct advancing action, or the first clean outcome required to confirm a handoff.

Call that response the `first actionable turn`. When its action is owner dispatch, it must include a complete bounded `DISPATCH_PACKET`; when one necessary fact is missing, it must return `BLOCKED` and name only that fact. `BLOCKED` is an output protocol, not a liveness state; classify the resulting wait from the missing fact's owner and dependency. Do not manufacture an acknowledgement-only turn, relabel a ready dispatch as open-ended architecture analysis, or defer an already-ready action to a second planning turn. A legitimate Skill read, current-fact check, tool call, or external wait may make a later response the first actionable turn, but once the needed result arrives the role must produce the action rather than restart broad analysis.

The acknowledgement establishes `PROVISIONAL` continuity and permits active traffic only after every required Goal freeze, activation and read-back check succeeds. Keep the prior role read-only and recoverable. Confirm the handoff only after the new role closes its first clean outcome with no directly handoff-linked regression; a continuity ACK alone is insufficient. If the new role loses Goal, authority, owner/channel continuity or completion truth, preserve in-flight state and use the verified Goal rollback sequence before returning authority. Ordinary implementation defects without a direct continuity link do not retroactively fail a handoff. No metrics event or sample is required outside an authorized experiment.

For a declared bounded-output action, a liveness watchdog may interrupt only when all of these observable conditions hold: the facts and required Skill or state reads are complete; no tool call, external result, or evidence return is in flight; the role has produced neither the bounded result nor `BLOCKED` nor a new concrete missing fact; valid output has not begun; and the runtime-specific watchdog has passed. Repeated planning summaries are corroborating evidence only, never the sole trigger, and the Skill does not define one cross-project timeout. Do not apply this rule to open-ended architecture analysis, active tools or waits, or a newly discovered necessary fact. Output that has begun suspends the start watchdog only while it continues making observable progress; if it stops before a complete result and a separate runtime-specific progress watchdog passes under the same no-wait conditions, re-evaluate the stall. If a correctly specified successor stalls under these conditions during `PROVISIONAL` continuity, preserve pending actions and use the verified rollback path; do not rescue it with repeated coaxing or controller-authored business content.

Keep Architect continuity across coherent outcomes rather than rotating routinely. Keep one read-only Supervisor for its declared continuing obligation, with only the bounded overlay; a project-selected timer-only mode is exclusive and never gains event, checkpoint or finding-deadline reviews from this reference. Healthy scheduled reviews retain their own-task snapshot while staying silent externally. Configuration marked ACTIVE is not evidence that the timer ran. Reconcile findings without inventing an extra review when a gate closes. Stop recurring supervision when the objective closes, the user explicitly pauses business/supervision, or no continuing supervision value remains; temporary `USER_WAIT`, a local transport problem or a blocked lane alone is not a stop condition. Only explicitly authorized event-mode reviews with no continuing obligation use a short-lived Supervisor. Replace a continuing Supervisor only after an authorized migration or directly proven continuity failure that one bounded in-place correction could not fix; at the safe boundary transfer and verify only its overlay and role communication.


## Keep native compaction narrow

Use native compaction plus bounded current state by default. Compaction does not transfer authority, recreate a Goal, reset attempts, invalidate fresh evidence or trigger handoff. A compact-related policy/permission transition requires only the current checks necessary for the next action. Do not add custom compact prompts, hooks or transcript-derived reinjection to ordinary dispatch. Hook responsibilities and experimental metrics live only in the separately authorized [research protocol](context-experiments.md).
