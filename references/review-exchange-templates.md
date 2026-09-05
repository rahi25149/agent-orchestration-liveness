# Architect-Supervisor Exchange Templates

Read this file for a critical event review or an actionable supervisor finding. These templates are a compact fact-exchange protocol, not a form for every heartbeat or work update. Keep entries short, omit optional fields that do not affect the assessment, and link to existing evidence instead of copying large logs or history.

## Select the permitted exchange boundary

These forms do not create review triggers. The current user/project mode takes precedence: in timer-only mode the Architect never initiates an event review, approval or progress consultation. The Supervisor uses actionable-finding forms only for facts found at its existing scheduled heartbeat; the Architect returns a disposition, not a request for an immediate re-review. GREEN remains in the Supervisor's own required snapshot, with no message to the Architect or user. Finding updates and gate-close reconciliation do not schedule a second review.

## Authority boundary

- The architect owns goals, priorities, owners, risk acceptance, and the final action decision.
- The supervisor independently reports risk, truthfulness, direction mismatch, and conditions; it does not approve releases, assign workers, or design the implementation.
- `YELLOW` requests acknowledgement or correction but does not automatically stop work.
- An independent safety or policy rule, or a `RED` risk, pauses only the affected action. Unrelated safe work continues.
- Project instructions may define stricter red lines, identifiers, or response times. Keep those project-specific rules outside this reference.

## Architect to supervisor: event review request

Use this only when the user/project explicitly permits Architect-initiated event review, at a meaningful transition rather than routine activity. It is disabled in timer-only mode:

```text
REVIEW_KIND:
Current objective or gate:
Why review now:
Facts changed since the last review:
Responsible owner or key dependency:
Highest proven completion level:
Known gap or accepted limitation:
Assessment requested:
```

Add only when relevant:

```text
Affected area:
Failure boundary:
Human or external gate:
```

Choose a review kind that describes the transition, such as goal change, pre-risk action, post-integrated-flow, integration, release, or completion claim. A project may use its own stable names.

## Supervisor to architect: event review response

Only in an event-enabled mode with a permitted exchange, a healthy review may use the following response. In timer-only mode keep GREEN in the Supervisor's own snapshot instead:

```text
Level: GREEN
Assessment:
Conditions or accepted limitations:
Follow-up boundary:
```

Do not create an empty finding and do not phrase the response as permission to continue.

For each actionable `YELLOW` or `RED` finding, send one compressed line:

```text
Finding ID | Level | Issue | Minimal evidence | Minimal correction | Follow-up boundary
```

Use one ID for one continuing fact. Do not create a new ID merely because the heartbeat changed.

## Architect to supervisor: formal response

```text
Finding ID:
Disposition: ACCEPTED | PARTIALLY_ACCEPTED | REJECTED_WITH_EVIDENCE
Fact basis:
Action and owner, or evidence-backed reason for no action:
Next gate or follow-up boundary:
```

Risk acceptance does not override an independent safety or policy prohibition.

Treat this disposition as the architect's response, not as the finding state. Finding state and legal transitions are defined in `SKILL.md`; acknowledgement, blocker, and next-check boundary remain metadata.

## Finding update and closure

When authoritative facts change before closure, record only the delta, and send it only where the selected exchange mode permits. A disposition or changed fact is not an immediate independent-review trigger:

```text
Finding ID | Changed fact | Correction still applies: yes/no/partly | Next boundary
```

When the finding closes, name one current closing fact:

```text
Finding ID | CLOSED | Closing fact
```

When a new fact or successor finding replaces the original issue, use:

```text
Finding ID | SUPERSEDED | Replacement fact or successor finding
```

At a gate close, record current finding facts without adding a heartbeat or requesting review; any independent reassessment remains on the declared cadence. Reconcile every related finding using [Outcome Batching and Review Budget](outcome-batching-and-review-budget.md). Leave an unresolved item explicitly `OPEN` with blocker, next-check boundary, and whether it blocks the claimed completion layer. Do not redefine the finding state machine in this template.

## When to use the exchange

Within the user/project's permitted review boundary, use the relevant form for:

- a goal or gate transition;
- a high-risk, irreversible, or externally consequential action;
- entry into or completion of an integrated or real-user flow;
- integration, release, or a higher-layer completion claim;
- a repeated liveness or direction failure that needs a formal finding.

Do not use it for:

- every commit, test, tool call, or ordinary progress update;
- a healthy heartbeat with no meaningful change;
- routine technical review that belongs to a separate reviewer;
- copying complete logs, process lists, revisions, hashes, or repeated history.

## Adapt the vocabulary, not the contract

| Domain | Objective or gate | Owner or key dependency | Proven completion level | Failure boundary |
| --- | --- | --- | --- | --- |
| Software | User capability or integration gate | Module, environment, or responsible owner | Implemented, integrated, or user-proven | Stable build, runtime, data, or environment failure |
| Research | Research question or decision threshold | Source, dataset, method, or reviewer | Evidence gathered, analyzed, or independently supported | Data-quality, method, or confidence limit |
| Operations | Operational outcome or service gate | Team, vendor, system, or approval dependency | Planned, executed, or outcome observed | Safety limit, rollback threshold, or external block |
| Content | Audience outcome or publication gate | Author, source, review, or distribution dependency | Drafted, reviewed, published, or outcome measured | Source gap, review failure, or publication constraint |
| Browser automation | Target outcome or page transition | Session, account, website, or human gate | UI action made, server result observed, or outcome verified | Authentication, unsafe action, or stable UI failure |

Preserve the semantic fields even when local terminology changes. The purpose is to share what is being crossed, what is actually proven, what remains, and what independent assessment is needed.
