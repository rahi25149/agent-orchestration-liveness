# Interactive Runtime Lifecycle

Read this reference for long-lived browser, desktop, device, remote-session, or interactive automation work; for the first representative real-surface probe; or before classifying an interactive interruption as `USER_WAIT`.

## Run the earliest feasible surface probe

Treat the real-surface probe as due when the first minimal executable vertical slice can cross the actual runtime boundary without requiring the whole feature.

A representative probe may prove only the boundaries relevant to the outcome, such as:

- one real control can be used;
- one runtime request is actually emitted;
- routing, browser policy, permission, or session state applies in the real surface;
- one target consumer reads the result;
- the visible state matches the claimed completion layer.

Run the probe before any one of these:

- implementing a second full branch or variant on the same runtime surface;
- scaling downstream work that assumes the unobserved surface contract;
- claiming real-surface, integrated user-flow, or user-capability completion.

If no executable surface exists yet, build the first thin slice. If the surface remains unavailable or unsafe, continue independent offline work but cap completion at the highest layer actually proven.

## Assign one runtime owner

Record:

- one owner for the interactive surface or exclusive resource;
- a stable session or resource handle when available;
- current target and environment identity;
- allowed actions and prohibited boundaries;
- next observable checkpoint;
- stop condition;
- task-owned keepalive or continuity mechanism when the environment needs one;
- cleanup responsibility.

Do not let two executable owners control the same desktop, browser account, device, or physical test resource concurrently. Other agents may remain read-only observers.

## Keep the session alive only for the task

Use a bounded, recoverable, task-owned continuity mechanism when automatic sleep, idle lock, lease expiry, or session timeout would interrupt active work. Record enough identity to release only the resource created for this task.

Do not change permanent host power policy, terminate another task's keepalive, or leave a keepalive running after the interactive phase ends.

If an avoidable lapse causes a lock or disconnect:

- record `USER_WAIT` only when an actual user unlock or verification is now required;
- separately record orchestration `YELLOW` for the preventable lifecycle failure;
- preserve the previously proven engineering or integration layer;
- resume the same outcome batch after recovery rather than inventing a new batch.

## Decide whether the user is truly required

Before declaring `USER_WAIT`, check in order:

1. the current authorization context or existing record;
2. target identity and environment;
3. whether the operation is owned, reversible, and inside declared scope;
4. whether the current runtime owner can safely perform it;
5. whether a new identity, login, verification, credential, permission, physical action, funds, production authority, desktop unlock, or UAC confirmation is truly required.

Need for additional evidence is not need for user approval. Do not ask the user to repeat an existing authorization or perform an ordinary automatable control.

When user action is unavoidable, request one minimal concrete action. Do not combine unrelated login, credential, lock, or permission issues into one generic wait.

## Observe truthful completion

Use the closest safe representative surface that preserves the runtime constraints relevant to the claim. Do not substitute a mock HTTP source, static screenshot, component test, or process start for a real browser, desktop, device, or consumer observation when the claimed layer depends on that surface.

Record:

- the surface and environment observed;
- the user or operator action, if any;
- the actual runtime result;
- the highest completion layer supported;
- accepted limitations and untested external boundaries.

Do not generalize a local, sandbox, fake-hardware, or development observation to production, real funds, real hardware, or a different operating system.

## Stop and clean up safely

At completion, pause, or first stable failure:

- stop or preserve owned processes according to the declared stop condition;
- release only task-owned keepalive and session resources;
- record the safe state of processes, ports, devices, temporary credentials, files, and pending actions without exposing secrets;
- keep unrelated services and other owners' resources untouched;
- state the one allowed next action and whether the user is required.

An interactive tool call ending is not a lifecycle close. Return a compact completion packet to the architect.

## Apply these examples carefully

| Situation | Correct classification |
| --- | --- |
| Browser slice exists but no real request has been observed | Probe is due; cap completion below real-surface completion |
| Desktop auto-locks because task continuity was omitted | Current unlock may be `USER_WAIT`; lifecycle cause is `YELLOW` |
| Existing authorization covers an owned reversible local action | Runtime owner proceeds without re-asking the user |
| Login, verification, UAC, new credential, or physical input is required | Request one concrete user action and preserve the current layer |
| Mock and unit tests pass, but the intended consumer was never run | Engineering may be complete; user capability is not proven |
| Session ends cleanly | Release task-owned resources and report safe state |
