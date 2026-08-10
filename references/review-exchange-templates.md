# Architect-Supervisor Exchange Templates

Read this file for a critical event review or an actionable supervisor finding. These templates are a compact fact-exchange protocol, not a form for every heartbeat or work update. Keep entries short, omit optional fields that do not affect the assessment, and link to existing evidence instead of copying large logs or history.

## Authority boundary

- The architect owns goals, priorities, owners, risk acceptance, and the final action decision.
- The supervisor independently reports risk, truthfulness, direction mismatch, and conditions; it does not approve releases, assign workers, or design the implementation.
- `YELLOW` requests acknowledgement or correction but does not automatically stop work.
- An independent safety or policy rule, or a `RED` risk, pauses only the affected action. Unrelated safe work continues.
- Project instructions may define stricter red lines, identifiers, or response times. Keep those project-specific rules outside this reference.

## Architect to supervisor: event review request

Use this at a meaningful transition, not for routine activity:

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

For a healthy review with no actionable finding:

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

## Finding update and closure

When facts change before closure, send only the delta:

```text
Finding ID | Changed fact | Correction still applies: yes/no/partly | Next boundary
```

When the finding closes, name one current closing fact:

```text
Finding ID | CLOSED | Closing fact
```

## When to use the exchange

Use it for:

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
