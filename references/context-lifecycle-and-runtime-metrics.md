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

- **Architect authority snapshot**: the current objective, gate, outcome batch, owners, hotspots, verified facts, authorization boundary, blockers, highest proven layer, next safe action, and facts the next thread must not assume.
- **Supervisor overlay**: the Architect revision it reviewed, open findings, last event and communication-review boundaries, latest supervision delta, and next supervision action.

The Supervisor overlay must not copy the complete gate, owner map, or execution plan. It refers to the Architect revision and stores only independent supervision state.

Recommended hard limits:

- Architect state: 3 KiB;
- Supervisor overlay: 2 KiB;
- at most six concise verified facts in the Architect state;
- one current file plus one atomically replaced `last-good` copy per role;
- no append-only state history.

Use one writer per role. Increase a monotonic revision only for a material delta: a batch opening or closing, owner or hotspot change, authority change, real wait, blocker change, completion-layer change, or next-safe-action change.

Never store credentials, cookies, personal data, prompts, replies, transcripts, logs, diffs, command output, or sensitive authorization material in role state. An authorization field records what class of action is allowed, not the secret that enables it.

## Rotate at a safe boundary

Normal rotation requires both:

```text
safe handoff boundary AND at least one pressure signal
```

A safe boundary means:

- the coherent outcome batch is closed or at a stable candidate boundary;
- no completion packet still needs an Architect decision;
- no atomic browser, desktop, device, funds, deployment, or other exclusive operation is in flight;
- owners, hotspots, waits, findings, and the next safe action are in the bounded role state;
- the new role thread can verify the smallest direct current facts without replaying the project.

Pressure signals include:

- a successful compaction followed by a safe batch boundary;
- a reliably observed high-context condition;
- a material change in objective or acceptance boundary;
- repeated rereading or re-derivation of facts already frozen;
- a concrete constraint miss, owner mistake, or duplicate work after compaction.

Hard rotation does not wait for a normal boundary when continuity is already untrustworthy, such as after two compactions in one role epoch, repeated loss of a protected constraint, invalid role state, or a major authority change. Preserve the safe state of any in-flight exclusive operation before rotating.

Create a fresh thread with the role contract, bounded role state, current assignment, and only the necessary recent handoff. Do not use a full-history fork as a context reset. Reuse the existing branch, Worktree, and owner when that remains correct.

The new thread must:

1. validate the role, project, revision, and freshness marker;
2. sample the smallest current workspace or runtime fact needed to reject stale state;
3. state the current gate, next safe action, and one forbidden assumption;
4. perform the first correct advancing action;
5. return a continuity acknowledgement.

Retire or archive the old thread only after this acknowledgement. If the new thread cannot establish continuity, continue with the old thread and record a rolled-back rotation.

Use a more conservative epoch for the Architect: one coherent outcome batch or a tightly related group of batches. Use a lighter Supervisor epoch: one gate, one outcome batch, or one related finding cluster. Do not rotate the Supervisor between a finding and its immediate re-review when the communication interval or finding history is still required.

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
| `schemaVersion` | fixed integer schema version |
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
- `rotation_completed` records an accepted or rolled-back boundary and, when accepted, cold-start turns;
- `context_regression` records `constraint_miss` or `duplicate_work`, its observed impact (`correction`, `repeated_execution`, or protected `boundary_violation`), the affected compact/rotation/handoff boundary, and one opaque evidence reference.

Do not add a free-form `note`, message text, path, URL, tool result, diff, or error body. An evidence reference is a bounded opaque identifier such as `SUP-014` or `turn:17`; it is not a narrative field.

Use exactly three decision metrics, calculated separately for comparable `role + cohort + model + reasoning` groups:

1. median input tokens per completed turn;
2. direct count of observed substantive context regressions, split by constraint miss and duplicate work;
3. direct count of accepted rotations that need more than one turn to reach the first correct advancing action.

Retain cached input and daily total tokens only as diagnostics. Daily volume changes with work intensity and must never decide whether a policy passes.

The largest measurement trap is mixing different work. A token reduction is not meaningful when the pilot contains smaller tasks, a cheaper model route, fewer tool results, or fewer real decisions. Choose a stable cohort before collecting data and do not relabel epochs after seeing the report.

An App Server adapter must buffer `thread/tokenUsage/updated` notifications and append exactly one final `turn_completed` event only after the matching turn reaches its terminal completion state. It must never append intermediate or cumulative snapshots as separate turns. Derive a stable opaque `eventId` from the terminal turn identity so reconnect or replay is rejected; never store a prompt, response, raw thread identifier, or raw event body.

## Review a baseline-versus-pilot experiment

Phase 0 does not judge token improvement. It proves only that the local recorder is atomic, strict, de-duplicated, owner-only, correctly grouped, and free of content-bearing data. Do not fill real logs with hand-estimated token values.

After the App Server adapter is verified, the manual pilot compares at least three baseline epochs with at least three pilot epochs in the same cohort. Each pilot epoch should begin with a fresh role thread and one accepted or rolled-back rotation record. Collect at least five accepted pilot rotations before issuing a pass decision.

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

Proceed only after Phase 0 passes. Verify an App Server adapter that coalesces token notifications into one terminal `turn_completed` record with a stable event ID. Then establish the comparable baseline, run manual fresh-thread rotations at safe boundaries, and apply the pilot gates above. Do not automate rotation or compaction.

### Phase 2: optional compact hooks and light rotator

Proceed only after the real pilot passes. Add one small trusted hook implementation with generation de-duplication. Verify one manual and one automatic compaction on a non-critical thread before enabling it for the Architect, then the Supervisor. Disable it immediately on duplicate injection, stale state, sensitive output, or context pollution.

Only after the compact-hook pilot passes may a light controller start a fresh thread, send the bounded bootstrap, wait for a continuity acknowledgement, and archive the old thread. It must fall back to the old thread on failure.

Do not add a database, dashboard, memory MCP, transcript index, fork-based pseudo-reset, or global orchestration ledger. If the local JSONL and bounded state are insufficient, stop and reassess the design rather than scaling the instrumentation first.
