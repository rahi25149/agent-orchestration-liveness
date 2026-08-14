# Context Lifecycle and Runtime Metrics

Read this reference before changing compaction, handoff, fresh-thread rotation, Architect or Supervisor state, context-cost instrumentation, or the related stop and rollback gates.

## Contents

1. [Keep one authority and one overlay](#keep-one-authority-and-one-overlay)
2. [Rotate at a safe boundary](#rotate-at-a-safe-boundary)
3. [Keep compaction responsibilities narrow](#keep-compaction-responsibilities-narrow)
4. [Record only decision-grade metrics](#record-only-decision-grade-metrics)
5. [Review a baseline-versus-pilot experiment](#review-a-baseline-versus-pilot-experiment)
6. [Stop, roll back, or advance](#stop-roll-back-or-advance)
7. [Phase the automation](#phase-the-automation)

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

## Rotate at a safe boundary

Normal rotation requires both:

```text
safe handoff boundary AND at least one pressure signal
```

A safe boundary means:

- the coherent outcome batch is closed or at a stable candidate boundary;
- no completion packet still needs an Architect decision;
- no atomic browser, desktop, device, funds, deployment, or other exclusive operation is in flight;
- when persisted Goal continuity is required, neither an incumbent continuation nor a Goal-management operation is in flight or queued, and the Goal transfer envelope and budget scope are current;
- immediately before `thread/start`, every named Architect, Worker, reviewer, and exclusive operator has been rechecked for a queued or resumed action after the stop boundary;
- owners, hotspots, waits, findings, and the next safe action are in the bounded role state;
- the new role thread can verify the smallest direct current facts without replaying the project.

A stop response, idle snapshot, or completion acknowledgement is not durable proof of this boundary. A previously queued assignment or automatic continuation may start after that observation. If any new execution fact appears before the fresh thread starts, invalidate the boundary, preserve the resulting state, and begin a new boundary check instead of treating the new epoch as comparable.

Pressure signals include:

- a successful compaction followed by a safe batch boundary;
- a reliably observed high-context condition;
- a material change in objective or acceptance boundary;
- repeated rereading or re-derivation of facts already frozen;
- a concrete constraint miss, owner mistake, or duplicate work after compaction.

Hard rotation does not wait for a normal boundary when continuity is already untrustworthy, such as after two compactions in one role epoch, repeated loss of a protected constraint, invalid role state, or a major authority change. Preserve the safe state of any in-flight exclusive operation before rotating.

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

If the fresh Architect cannot directly inspect peer task state, the controller may attach one content-neutral liveness attestation bound to the exact target and authority-snapshot revision. Limit it to the target role and thread reference, observed `IDLE` or `INACTIVE` state, no queued action, observation time, expiry or invalidation condition, and direct-observation source. It proves only that the target was ready to receive transport; it cannot select the owner, task, gate, authorization, completion layer, or packet content. Missing, stale, mismatched, or conflicting evidence requires `BLOCKED: PEER_LIVENESS_UNVERIFIED`; do not explore transport protocols or draft a partial packet. Immediately before a mechanical relay, recheck the target and refuse the relay without editing the packet if the attestation has become invalid. Treat a future direct peer-state bridge as a different transport cohort, not as an equivalent implementation of this attestation.

Preserve the incumbent role's directly observed model, reasoning, service tier, approval policy and reviewer, network policy, and every other declared cohort invariant at the final boundary check. Filesystem capability is not business authorization. When the authorization ledger already permits ordinary local or Git atomic actions, the owning role must execute them without asking the user; the rotation controller must never review, click, relay, or auto-approve an approval request. If the fresh role cannot create the required Git lock because its capability profile omitted Git metadata, leave the approval request untouched, abandon the defective fresh epoch, and correct the profile at a safe boundary rather than declaring `USER_WAIT` or escalating the same authorized action. Do not attribute a context regression to the role unless it independently forgot or violated the authorization boundary after receiving the required capability.

For a Git-backed fresh role, resolve `--absolute-git-dir` and `--git-common-dir` immediately before creation, canonicalize and validate that they belong to the intended repository, and deduplicate them. Do not try to reopen them through legacy `workspace-write`: that policy protects `<writable_root>/.git` and a pointer file's resolved Git directory recursively. On App Server, opt into `capabilities.experimentalApi`, call `permissionProfile/list` with the project `cwd`, require the selected profile to be allowed, and pass its id in `thread/start.permissions` without `sandbox`. Permission profiles and legacy sandbox settings do not compose. Grant ordinary workspace write plus only the exact Git directory and common-directory write needed; preserve the incumbent approval reviewer and network policy, keep `.agents` and `.codex` protections, and do not use `danger-full-access`, another repository, or a broad user directory.

Run the capability probe from a normal agent turn under that profile, never from controller execution or another control-side path that may bypass the role sandbox. Require (1) lock create and release, (2) a disposable local fast-forward equivalent covering the branch ref, `ORIG_HEAD`, and index, (3) an out-of-scope harmless write denied or left as an untouched approval request, and (4) the real project branch, Worktree, refs, and pending state unchanged after cleanup. If the negative probe produces an approval request, never answer it; end the disposable probe and verify that no write occurred. After the first actual role turn starts and before authority transfer or sample counting, inspect its persisted or runtime `turn_context`, or equivalent effective policy, and require the selected profile plus exact model, reasoning, service-tier, approval, reviewer, and network invariants. Repeat that check after any client, connection, host, resume, compact, or runtime transition that can change the effective policy and before the first action needing the protected capability; a first-turn match cannot qualify later resumed turns. Cohort eligibility requires both actual role-turn provenance and invariant checks across those transitions and the positive and negative capability behavior; neither alone is sufficient. Profile provenance in a creation response is supporting evidence only. Missing or mismatched effective policy aborts the fresh epoch without retrofit. The controller may restore the least-privilege surface already declared by the owning Architect and authorization ledger; the defective profile being narrower does not require a new business packet. Carrying the packet verbatim authorizes no client, host, sandbox, permission set, or execution channel beyond that declaration. A different surface requires explicit Architect re-authorization in a new packet and remains subject to every least-privilege and safety prohibition; absent that packet, return the missing fact without rerouting or declaring `USER_WAIT`. Probe every corrected or new surface content-free. If a measured epoch is open, close it `aborted` before the change and begin a fresh blank, pre-armed epoch in a new cohort; do not pool earlier samples.

The new thread must:

1. validate the role, project, revision, and freshness marker;
2. sample the smallest current workspace or runtime fact needed to reject stale state;
3. state the current gate, next safe action, and one forbidden assumption;
4. when Goal continuity is required, verify the staged Goal revision and paused lifecycle without treating it as business authority;
5. after the freeze sequence grants authority and activates the Goal, first consume and adjudicate any existing Worker completion before dispatching new work;
6. after consuming any existing completion and before the first dispatch, rescan current ready lanes instead of inheriting the incumbent's prior SERIAL decision;
7. perform the first correct advancing action in the first turn where those checks are complete and no required fact or external wait remains;
8. return a continuity acknowledgement.

Goal continuity does not replace direct role channels, the Worker completion handshake, existing-owner reconciliation, the first correct advancing action, or the first clean outcome required for accepted rotation.

Call that response the `first actionable turn`. When its action is owner dispatch, it must include a complete bounded `DISPATCH_PACKET`; when one necessary fact is missing, it must return `BLOCKED` and name only that fact. `BLOCKED` is an output protocol, not a liveness state; classify the resulting wait from the missing fact's owner and dependency. Do not manufacture an acknowledgement-only turn, relabel a ready dispatch as open-ended architecture analysis, or defer an already-ready action to a second planning turn. A legitimate Skill read, current-fact check, tool call, or external wait may make a later response the first actionable turn, but once the needed result arrives the role must produce the action rather than restart broad analysis.

The acknowledgement establishes `PROVISIONAL` continuity and permits active traffic to move to the new thread only after every required Goal freeze, activation, and read-back check also succeeds. Keep the prior thread read-only and recoverable; a reversible archive is allowed, but do not destroy its recovery path. Finalize the rotation as `accepted` only after the new role closes its first comparable outcome epoch and no substantive regression is directly linked to the handoff. Until then, do not emit an accepted `rotation_completed` event. If the new thread cannot establish first-turn continuity, loses required Goal state, later loses the role/authority contract, routes the wrong owner, misses a required handoff, duplicates an existing assignment, misstates the completion layer, or leaks internal lifecycle reporting because of the handoff, record `rolled_back`, abort the epoch, and resume the prior or last-good role only through the verified Goal rollback sequence. Ordinary implementation defects without a direct continuity link do not retroactively fail the rotation.

For a declared bounded-output action, a liveness watchdog may interrupt only when all of these observable conditions hold: the facts and required Skill or state reads are complete; no tool call, external result, or evidence return is in flight; the role has produced neither the bounded result nor `BLOCKED` nor a new concrete missing fact; valid output has not begun; and the runtime-specific watchdog has passed. Repeated planning summaries are corroborating evidence only, never the sole trigger, and the Skill does not define one cross-project timeout. Do not apply this rule to open-ended architecture analysis, active tools or waits, or a newly discovered necessary fact. Output that has begun suspends the start watchdog only while it continues making observable progress; if it stops before a complete result and a separate runtime-specific progress watchdog passes under the same no-wait conditions, re-evaluate the stall. If a correctly specified fresh role meets all conditions during `PROVISIONAL` continuity and must be interrupted so the last-good role can resume, classify the failure as handoff-linked working-mode regression, append `rolled_back`, abort the epoch, and do not rescue the sample through repeated coaxing or controller-authored business content.

Use a more conservative epoch for the Architect: one coherent outcome batch or a tightly related group of batches. Use a lighter Supervisor epoch: one gate, one outcome batch, or one related finding cluster. Keep that Supervisor epoch across review turns only when an explicit cross-boundary obligation exists, such as an open finding, declared recurring heartbeat or checkpoint, completion-ack follow-up, or finding follow-up boundary; elapsed duration, GUI or remote work, and exclusive-resource use alone are insufficient. Reuse it for a material review inside the same gate, and do not rotate it between a finding and its immediate re-review when the communication interval or finding history is still required. For an isolated event with no continuing obligation, use a fresh short-lived Supervisor. At gate close, pause, real user wait, loss of every safe next action, or end of supervision value, reconcile findings and end the Supervisor epoch. If context pressure requires replacement before then, transfer only the bounded overlay at a safe boundary and verify its Architect revision and finding states before the successor reviews anything.

## Keep compaction responsibilities narrow

Do not override the native compact prompt during the initial experiment.

If hooks are piloted later, give them only these responsibilities:

- **PreCompact**: validate the current role-state schema, size, role, project, and revision; atomically preserve one `last-good` copy.
- **PostCompact**: increment one compact generation and record the trigger and state revision. Do not summarize or inject context.
- **SessionStart from compact**: inject the latest valid `last-good` state once for a generation. If it is invalid, inject only a continuity-unverified warning and require current-fact verification.

The injection path must be generation-idempotent. Multiple delayed hook events must not inject the same state repeatedly. Never let a hook infer a new owner, gate, finding, authorization, or next action.

Do not combine a custom compact prompt, a transcript-derived PreCompact summary, a PostCompact summary, and a state-card injection. That creates duplicated summaries, larger prompts, and conflicting authorities.

## Record only decision-grade metrics

Start with the local standard-library script:

```bash
python3 scripts/context_metrics.py append --help
python3 scripts/context_metrics.py validate --help
python3 scripts/context_metrics.py report --help
```

The JSONL file must be outside every source repository and readable only by the current user. The script creates or tightens the file to mode `0600`, rejects symlink targets, rejects unknown fields, and limits every line to 4096 bytes.

Each event repeats a small cohort identity so reports can reject inconsistent epochs:

| Field | Purpose |
| --- | --- |
| `schemaVersion` | strict integer schema version; readers accept historical v1 while all new events use v2 |
| `eventId` | stable locally unique identifier used to reject replays |
| `at` | UTC RFC3339 timestamp |
| `event` | strict event enum |
| `epochId` | opaque role-epoch identifier |
| `threadRef` | opaque local reference for the role thread; never transcript content |
| `mode` | `baseline` or `pilot` |
| `role` | `architect` or `supervisor` |
| `cohort` | stable class of comparable work |
| `model` | exact model route used for the epoch |
| `reasoning` | reasoning route used for the epoch |
| `source` | `manual`, `app_server`, `hook`, or `rotator` |

Supported event types:

- `epoch_started` and `epoch_closed` bound a sample;
- `turn_completed` records one turn index plus final input, cached-input, and total-token counters;
- `compacted` records only the compact generation;
- `rotation_completed` records the terminal continuity result: `accepted` only after the first comparable outcome epoch closes cleanly, `rolled_back` after a handoff-linked failure, or v2 `inconclusive` when a valid measured attempt closes `not_achieved`; only accepted records include the already-observed cold-start turns;
- `context_regression` records `constraint_miss` or `duplicate_work`, its observed impact (`correction`, `repeated_execution`, or protected `boundary_violation`), the affected compact/rotation/handoff boundary, and one opaque evidence reference.

Epoch-close outcomes are intentionally distinct:

- `completed`: the declared outcome passed its shared acceptance boundary; it is the only outcome counted as a token sample;
- `not_achieved` (v2 only): the writer closed safely, but the declared outcome did not pass; append one v2 `inconclusive` rotation after the close, without cold-start turns or a context regression;
- `paused`: work stopped intentionally with a legitimate continuation boundary rather than a terminal outcome result;
- `aborted`: measurement, transport, or continuity validity failed, so the epoch is unusable as an outcome observation.

Treat v1 events as immutable historical input: v1 accepts only `completed`, `paused`, and `aborted` plus accepted or rolled-back rotation; every newly appended event uses v2. A mixed v1/v2 ledger remains valid, including a v2 terminal close for an epoch opened under v1, provided all other epoch identity fields remain consistent. Once an epoch contains v2 it cannot downgrade to v1.

Do not add a free-form `note`, message text, path, URL, tool result, diff, error body, Goal objective, Goal transfer envelope, or raw Goal API output. An evidence reference is a bounded opaque identifier such as `SUP-014` or `turn:17`; it is not a narrative field.

Use exactly three decision metrics, calculated separately for comparable `role + cohort + model + reasoning` groups:

1. median input tokens per completed turn;
2. direct count of observed substantive context regressions, split by constraint miss and duplicate work;
3. direct count of accepted rotations that need more than one turn to reach the first correct advancing action.

Retain cached input and daily total tokens only as diagnostics. Daily volume changes with work intensity and must never decide whether a policy passes.

The largest measurement trap is mixing different work. A token reduction is not meaningful when the pilot contains smaller tasks, a cheaper model route, fewer tool results, or fewer real decisions. Before the cohort's first measured epoch, freeze a content-neutral work envelope: expected decision and tool-surface bands, target completion layer, verification class, and any resource class that materially changes context load. Also freeze prospective enrollment: the Architect alone selects, splits, and routes business work; the controller enrolls every chronologically next normally routed fresh epoch that matches the envelope, or follows a deterministic cadence fixed in advance, and must not choose, split, delay, substitute, or omit work to obtain a sample. Bind the rule to an opaque envelope revision in bounded controller state, define its inclusive and exclusive boundaries in advance, and make `indeterminate` mean no enrollment. Immediately before `thread/start`, the incumbent Architect must declare the chronologically next normally routed outcome and its content-neutral classification in the bounded authority snapshot; the controller applies the frozen rule without inference, and leaves an out-of-envelope or indeterminate outcome on its normal unmeasured business route. The envelope is a comparability bound and cohort invariant, not a backlog or task selector. If an epoch has already begun or the envelope changes, start a new cohort without relabeling history. Retain the business result and diagnostic usage of an epoch begun without an envelope, but close its measurement as `aborted`; after provisional authority transfer, append `rolled_back` after the close, retain the last-good role, and record no context regression. Exclude `not_achieved` epochs because failures often stop early and consume fewer tokens; counting those turns would reward failure and bias the experiment toward an apparently cheaper policy. Before a baseline-versus-pilot decision, compare their actual distributions across the frozen envelope dimensions symmetrically; membership alone is insufficient, and a material imbalance remains non-comparable rather than supporting a pass. Choose a stable cohort before collecting data and do not relabel epochs after seeing the report.

An App Server adapter must buffer `thread/tokenUsage/updated` notifications and append exactly one final `turn_completed` event only after the matching turn reaches its terminal completion state. It must never append intermediate or cumulative snapshots as separate turns. Derive a stable opaque `eventId` from the terminal turn identity so reconnect or replay is rejected; never store a prompt, response, raw thread identifier, or raw event body.

## Review a baseline-versus-pilot experiment

Phase 0 does not judge token improvement. It proves only that the local recorder is atomic, strict, de-duplicated, owner-only, correctly grouped, and free of content-bearing data. Do not fill real logs with hand-estimated token values.

After the App Server adapter is verified, the manual pilot compares at least three baseline epochs with at least three pilot epochs in the same cohort. Each pilot epoch should begin with a fresh role thread. Its first-turn acknowledgement remains provisional; append exactly one terminal rotation after the measured epoch closes: accepted for a clean comparable outcome, rolled back for a handoff-linked failure, or v2 inconclusive for `not_achieved`. Collect at least five accepted pilot rotations before issuing a pass decision. Paused, aborted, and `not_achieved` epochs do not satisfy this gate.

The report emits a decision per comparable group:

- `insufficient_data`: fewer than three baseline epochs, three pilot epochs, or five accepted pilot rotations;
- `pass`: median input tokens fall by at least 25%, no substantive regression is observed, and at most one of the first five rotations needs a second context-recovery turn;
- `continue_pilot`: the sample is complete but does not yet meet a pass or rollback gate;
- `rollback`: a defined rollback condition occurs.

Review the actual regression evidence before acting on the count. A user changing the objective is not a constraint miss. A deliberate verification of one current fact is not duplicate work. Re-reading a completed investigation, rerunning an already accepted test without a stale-evidence reason, or violating an explicit owner, authority, gate, or completion-layer boundary is a regression.

Treat three versus three epochs and five rotations as an operational pilot, not statistical proof. Use direct counts for small samples. A cold-start percentile may be displayed as diagnostic data only after at least ten accepted rotations, and must never become a release gate. Do not optimize thresholds after looking at the same sample.

## Stop, roll back, or advance

Roll back to native compaction plus manual bounded handoff when any of these occurs:

- one protected authority, permission, safety, funds, production, or completion boundary is lost after rotation;
- at least two substantive regressions are linked to the first five pilot rotations;
- at least two of the first five accepted pilot rotations require a second context-recovery turn;
- after three comparable pilot epochs, median input-token reduction is below 20%;
- the wrong project or role state is injected;
- one compact generation injects the full role state more than once;
- a stale state causes an owner, gate, authorization, or completion-layer mistake;
- Supervisor rotation makes a required communication-audit interval unavailable;
- instrumentation captures prohibited content or becomes another workflow authority.

One observed substantive regression prevents a pass even when it does not yet trigger rollback. Zero logged regressions means none were observed; it does not prove that none existed. Investigate a regression inside the current pilot boundary; do not invent additional metrics or monitoring infrastructure.

Advance only when the report passes and a manual review confirms that the baseline and pilot cohorts were genuinely comparable.

## Phase the automation

### Phase 0: recorder and state-boundary validation

- run `python3 scripts/test_context_metrics.py -v` and require every named acceptance test to pass;
- keep native compaction defaults;
- do not set a custom compact prompt or compact threshold;
- keep role state and metrics outside repositories;
- validate atomic append, stable event de-duplication, schema rejection, file permissions, role and epoch grouping, and content privacy;
- exercise report logic with synthetic test fixtures only;
- do not enter hand-estimated token usage in the real log;
- do not change Codex Desktop, App Server, hooks, or global configuration.

This test matrix is the Phase 0 recorder gate. It covers serial and concurrent append, stable replay rejection, malformed and partial JSONL, content-field exclusion, owner-only permissions, symlink rejection, role/thread/epoch grouping, synthetic decision logic, and small-ledger latency. Passing it does not authorize real token capture or any Phase 1 integration.

Stop Phase 0 immediately if prohibited content is recorded, a replay is counted twice, role or thread attribution is wrong, malformed data is silently accepted, instrumentation affects normal work, or the metrics log is used as workflow state.

### Phase 1: real usage adapter and manual rotation pilot

Proceed only after Phase 0 passes. Verify an App Server adapter that coalesces token notifications into one terminal `turn_completed` record with a stable event ID. The deterministic matrix must cover usage-before-terminal and terminal-before-usage ordering, repeated usage snapshots, replay across restart, mixed-thread rejection, model-reroute rejection, malformed or incomplete streams, owner-only repository-external storage, and content exclusion. Then run one opt-in real App Server turn and require one final usage record plus one matching `turn/completed` notification. Use an explicitly bounded low-cost smoke route rather than inheriting the operator's global model route, and do not change global Codex configuration.

A successful smoke verifies adapter mechanics, not a baseline. Attach the adapter to each role's next fresh App Server connection at a safe handoff boundary; do not retrofit an already-running thread or persist its raw protocol stream. Only epochs closed with `outcome=completed` contribute token samples or completed-epoch counts; open, `not_achieved`, paused, and aborted epochs cannot satisfy the sample gate. Establish the comparable baseline, run manual fresh-thread rotations at safe boundaries, and apply the pilot gates above. Do not automate rotation or compaction.

Codex Desktop may own an isolated stdio App Server connection that cannot be tapped by an external observer. In that case, create a blank non-ephemeral thread through one controlled App Server connection and arm `scripts/desktop_rollout_usage_adapter.py` after `thread/start` but before the first `turn/start`. The arm operation must confirm that no rollout exists yet. Keep that App Server instance alive as the sole persistence writer for the complete measured epoch, including every later turn. Continue each turn through the same owning connection; do not resume or inspect the tested role through Codex Desktop, a thread read or wait tool, a follower, or a second App Server. A UI or API operation described as read-only may still load the persisted thread, acquire its writer, attach a follower, or change the effective permission profile.

Observe and relay only through the owning connection. Collection may replay the resulting local rollout only for that pre-armed epoch; it validates every completed turn's exact model and reasoning route, hashes protocol identities in memory, records compact generations without their replacement history, and persists only the same terminal counters accepted from the live App Server adapter. Existing or active unarmed threads are ineligible. Any format drift, route mismatch, malformed record, foreign writer, or attempt to close an active turn fails closed. This compatibility bridge changes no Codex configuration and is not a general transcript collector.

Close the normal owner lifecycle in this order after the final turn is terminal: run collection without `--outcome` to append terminal usage only; call `thread/unsubscribe` on the same owning connection; gracefully stop that App Server; use content-neutral runtime inspection to confirm that no live process holds the thread writer; run collection with either `--outcome completed --writer-release-proven` or `--outcome not_achieved --writer-release-proven`. Append accepted only after `completed`; append inconclusive only after `not_achieved`. Do not append either release-sensitive close while writer cleanup can still fail. `thread/unsubscribe` removes the requesting connection's subscription; its `unsubscribed` response is not writer-release proof. Neither UI `IDLE`, closing a view, a `thread/closed` notification, an empty lock file, nor elapsed inactivity alone proves release. Never delete or unlink a writer lock, edit thread storage, archive or fork to bypass ownership, kill an unverified holder, or start another App Server to race for the thread.

An `inconclusive` attempt remains a content-free attrition diagnostic, not a fourth decision metric. It cannot be accepted or rolled back later, and its `boundaryId` cannot be reused by a later epoch. The same Architect may continue ordinary business work, but those later turns do not retroactively enter the closed measured attempt. Begin the next measurable attempt only from another fresh, blank, pre-armed thread at a safe boundary; otherwise excluded bootstrap and failure costs could be hidden behind a warmed success.

If the owner process or connection exits unexpectedly, ownership provenance becomes ambiguous, or a foreign writer appears, stop all delivery to the measured role. Name one recovery observation and deadline and enter `BOUNDED_WAIT` only to establish that no turn is active and no live holder remains. Treat any implementation-specific unload or inactivity TTL as a bounded cleanup window, never as a writer lease or release guarantee; do not poll through Desktop because the observation may reload the thread. If same-owner provenance and an uninterrupted measurement stream cannot be restored, or release is not proven by the deadline, append `epoch_closed(outcome=aborted)` rather than `completed`, then append `rotation_completed(result=rolled_back)` when continuity was provisional and retain the last-good role. An aborted metric close records a terminal experiment decision; it does not grant thread ownership. Start any retry from a fresh thread only after the old live holder is independently proven absent. Classify this as a controller transport defect, not `USER_WAIT` or a role context regression, unless the role itself lost or violated its contract.

Treat the writer-ownership topology, App Server lifecycle policy, and Desktop-participation policy as transport-cohort invariants. A normal fresh App Server instance per epoch under the same declared policy does not create another cohort. A semantic change to any of those policies requires a content-free capability and lifecycle probe and a new comparable cohort; keep earlier epochs as immutable historical evidence and do not pool them with the corrected transport cohort.

### Phase 2: optional compact hooks and light rotator

Proceed only after the real pilot passes. Add one small trusted hook implementation with generation de-duplication. Verify one manual and one automatic compaction on a non-critical thread before enabling it for the Architect, then the Supervisor. Disable it immediately on duplicate injection, stale state, sensitive output, or context pollution.

Only after the compact-hook pilot passes may a light controller start a fresh thread, send the bounded bootstrap, wait for a continuity acknowledgement, and archive the old thread. When Goal continuity is required, it must also stage and verify the successor Goal while paused, freeze and verify the incumbent Goal and continuation queue, transfer authority while both are paused, activate and verify the successor, and use the ordered Goal rollback on failure. It must never invent Goal content or budget scope, treat a prompt as Goal state, or archive the old thread before the first clean outcome closes.

Do not add a database, dashboard, memory MCP, transcript index, fork-based pseudo-reset, or global orchestration ledger. If the local JSONL and bounded state are insufficient, stop and reassess the design rather than scaling the instrumentation first.
