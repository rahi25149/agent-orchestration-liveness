# Risk-Triggered Technical Review

Read this reference when classifying technical-review need, preparing a review handoff, reviewing a candidate, consuming `TECH_CLEAR` or `TECH_BLOCKED`, or deciding whether a prior result is stale.

## Decide whether review has positive expected value

Use this qualitative model:

> expected avoided late-failure loss - review cost - handoff cost - duplicate-evidence cost - actual critical-path wait cost

First require a semantic change to one protected area: funds or ledgers; authentication, authorization, or permissions; persistent state, migration, or destructive data action; concurrency, idempotency, retry, replay, or event order; a shared contract used by independent consumers; device control or another external side effect; or a real-runtime boundary that ordinary automation cannot observe well.

Then require one severe condition or at least two medium conditions.

Severe conditions:

- possible real-funds loss, authorization bypass, or unrecoverable data damage;
- possible physical-device or asset risk;
- rollback cannot undo an external side effect;
- failure crosses independent actors and cannot be isolated by a local rollback.

Medium conditions:

- failure is likely to appear only after integration or in a real environment;
- two or more independent owners or consumers are affected;
- Worker self-check cannot credibly falsify the protected invariant;
- repair would require data recovery, compatibility work, or cross-component coordination;
- behavior is sensitive to retry, duplication, ordering, or recovery.

Otherwise use Worker self-check plus Architect spot-check. A local, reversible, single-surface change with direct trustworthy checks and no protected invariant or external side effect does not need independent review merely because it touches a database, DTO, GUI, device-adjacent file, or concurrent implementation.

## Prepare a bounded handoff

Include only:

- outcome batch and current gate;
- review scope and protected invariant;
- reviewable candidate boundary;
- affected producers, consumers, or state transitions;
- Worker self-check and result;
- highest completion layer proven;
- known gaps or unobserved layers;
- why independent review is required.

Add risk-specific facts only when relevant: data range, compatibility, migration, and recovery for persistence; available, reserved, charged, and refunded invariants for funds; actor, resource, action, allow, and deny paths for authorization; retry, duplicate, order, lock, transaction, and idempotency boundaries for distributed behavior; producer, consumer, version, default, and missing-field behavior for contracts; or actual surface, side effect, unique operator, safe failure, and cleanup for GUI or device work.

Do not require fixed SHAs, proof chains, or irrelevant template sections. One review covers at most one protected invariant or one shared contract with its direct producer and consumer paths.

## Review without serializing the workflow

Start when a stable semantic slice is independently reviewable; do not wait for the whole outcome batch. Freeze only the reviewed invariant, contract, and evidence path. Other owners may continue non-dependent work.

The reviewer must:

1. inspect the actual candidate change;
2. understand the protected invariant or contract;
3. check that Worker evidence addresses the real risk;
4. perform at least one independent falsification-oriented check;
5. state every unreviewed completion layer or runtime surface.

A falsification check may target a deny path, duplicate or out-of-order input, compatibility case, migration failure or recovery, invariant-breaking branch, or one real request crossing the claimed boundary. Reuse valid Worker evidence. Do not rerun full suites, all targeted tests, full GUI or device sessions, or unrelated checks unless evidence is missing, stale, or the risk itself requires it.

Sampling is allowed only when all items use the same proven mechanism, the sample exercises the protected invariant, and no unreviewed item has an independent semantic branch. Do not sample away funds, authorization allow and deny paths, migration variants, retry or replay branches, or distinct device-write paths.

## Return a scoped result

`TECH_CLEAR` means no unresolved material engineering defect was found within the declared scope and candidate boundary, and the listed evidence supports the declared engineering layer. It is not an integration, release, real-surface, user-capability, or Supervisor approval.

`TECH_BLOCKED` must include:

- `Reason`: `DEFECT`, `INSUFFICIENT_EVIDENCE`, `SCOPE_MISMATCH`, or `STALE_CANDIDATE`;
- the minimal blocker;
- the required correction or evidence;
- the exact incremental recheck scope.

Keep one technical-review lifecycle per outcome batch and risk scope. An ordinary repair returns to the original owner and receives incremental re-review of the fix and directly affected invariant; it does not create a new batch, SUP finding, user report, or full re-review.

Invalidate `TECH_CLEAR` only when semantics change in the reviewed invariant, contract, dependency path, state transition, evidence oracle, or runtime condition. Unrelated commits, formatting, documentation, behavior-neutral renames, and independent hotspots do not make it stale.

## Keep the mechanism economically small

If useful, derive at most three counts from existing review events: material defects found before integration, material defects escaping a `TECH_CLEAR` inside its original scope, and occasions when review caused real critical-path stoppage after all other safe work was exhausted. Do not create a ledger, timesheet, SLA, per-batch report, or approval chain.

Reject review-per-commit, permanent reviewer roles, full-suite repetition, unrelated-work freezes, mandatory all-risk templates, fixed repair-count limits, `TECH_CLEAR` as release approval, or a second routine technical review by the Supervisor. These turn a quality accelerator into process tax.
