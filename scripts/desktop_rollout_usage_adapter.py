#!/usr/bin/env python3
"""Bridge a freshly armed Codex Desktop rollout into content-free Phase 1 metrics.

This is a Desktop compatibility bridge, not a transcript importer. ``arm`` must run
after ``thread/start`` but before the first ``turn/start``. ``collect`` may be run
repeatedly; it extracts only final token counters, terminal turn markers, and compact
generation numbers. It never copies a prompt, response, tool payload, raw thread id,
raw turn id, or rollout path into the metrics ledger.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

import app_server_usage_adapter as app_adapter
import context_metrics as metrics

ARM_SCHEMA_VERSION = 1
THREAD_ID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
MAX_ARM_BYTES = 4096
FILESYSTEM_TIME_TOLERANCE_NS = 5_000_000_000


class DesktopRolloutError(ValueError):
    pass


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _stable_id(prefix: str, *values: str) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    return f"{prefix}:{digest.hexdigest()[:40]}"


def _require_thread_id(value: str) -> str:
    if not THREAD_ID.fullmatch(value):
        raise DesktopRolloutError("thread id must be a canonical lowercase UUID")
    return value


def _require_sessions_root(path: Path) -> Path:
    resolved = path.expanduser().resolve(strict=True)
    if not resolved.is_dir():
        raise DesktopRolloutError("sessions root must be a directory")
    return resolved


def _matching_rollouts(root: Path, thread_id: str) -> list[Path]:
    matches: list[Path] = []
    for candidate in root.rglob(f"*{thread_id}*.jsonl"):
        if candidate.is_symlink() or not candidate.is_file():
            raise DesktopRolloutError("rollout must be a regular non-symlink file")
        resolved = candidate.resolve(strict=True)
        if not resolved.is_relative_to(root):
            raise DesktopRolloutError("rollout escaped the sessions root")
        matches.append(resolved)
    return sorted(set(matches))


def _write_arm(path: Path, state: dict[str, Any]) -> None:
    target = app_adapter.require_repository_external(path)
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(target.parent, 0o700)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    encoded = json.dumps(state, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_ARM_BYTES:
        raise DesktopRolloutError("arm state is unexpectedly large")
    fd = os.open(target, flags, 0o600)
    try:
        os.fchmod(fd, 0o600)
        os.write(fd, encoded + b"\n")
        os.fsync(fd)
    finally:
        os.close(fd)


def _load_arm(path: Path) -> dict[str, Any]:
    target = app_adapter.require_repository_external(path)
    if target.is_symlink() or not target.is_file():
        raise DesktopRolloutError("arm state must be a regular non-symlink file")
    if stat.S_IMODE(target.stat().st_mode) & 0o077:
        raise DesktopRolloutError("arm state must be user-only (0600)")
    raw = target.read_bytes()
    if len(raw) > MAX_ARM_BYTES:
        raise DesktopRolloutError("arm state is unexpectedly large")
    try:
        state = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DesktopRolloutError("arm state is not valid JSON") from exc
    expected = {
        "schemaVersion",
        "armedAtNs",
        "threadDigest",
        "metricsPathDigest",
        "identity",
    }
    if not isinstance(state, dict) or set(state) != expected:
        raise DesktopRolloutError("arm state has an invalid field set")
    if state.get("schemaVersion") != ARM_SCHEMA_VERSION:
        raise DesktopRolloutError("arm state schema version is unsupported")
    armed_at_ns = state.get("armedAtNs")
    if isinstance(armed_at_ns, bool) or not isinstance(armed_at_ns, int) or armed_at_ns <= 0:
        raise DesktopRolloutError("arm state timestamp is invalid")
    for name in ("threadDigest", "metricsPathDigest"):
        value = state.get(name)
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            raise DesktopRolloutError(f"arm state {name} is invalid")
    identity = state.get("identity")
    if not isinstance(identity, dict) or set(identity) != set(asdict(_sample_identity())):
        raise DesktopRolloutError("arm state identity is invalid")
    return state


def _sample_identity() -> app_adapter.EpochIdentity:
    return app_adapter.EpochIdentity("a", "a", "baseline", "architect", "a", "a", "unknown")


def _identity_from_state(state: dict[str, Any]) -> app_adapter.EpochIdentity:
    try:
        identity = app_adapter.EpochIdentity(**state["identity"])
    except TypeError as exc:
        raise DesktopRolloutError("arm state identity is invalid") from exc
    # Reuse the metrics schema validator without writing an event.
    metrics.validate_event(identity.base_event("epoch_started", "identity-check", "manual"))
    return identity


def arm_epoch(
    *,
    sessions_root: Path,
    thread_id: str,
    arm_path: Path,
    metrics_path: Path,
    identity: app_adapter.EpochIdentity,
) -> dict[str, str]:
    root = _require_sessions_root(sessions_root)
    raw_thread_id = _require_thread_id(thread_id)
    resolved_metrics = app_adapter.require_repository_external(metrics_path)
    if resolved_metrics.exists() and any(
        event["epochId"] == identity.epoch_id for event in metrics.load_events(resolved_metrics)
    ):
        raise DesktopRolloutError("epoch id already exists; arm requires a new epoch")
    state = {
        "schemaVersion": ARM_SCHEMA_VERSION,
        "armedAtNs": time.time_ns(),
        "threadDigest": _digest(raw_thread_id),
        "metricsPathDigest": _digest(str(resolved_metrics)),
        "identity": asdict(identity),
    }
    _write_arm(arm_path, state)
    try:
        if _matching_rollouts(root, raw_thread_id):
            raise DesktopRolloutError(
                "rollout already exists; arm only a fresh thread before its first turn"
            )
        app_adapter.AppServerUsageAdapter(resolved_metrics, identity)
    except Exception:
        app_adapter.require_repository_external(arm_path).unlink(missing_ok=True)
        raise
    return {"status": "armed", "epochId": identity.epoch_id}


def _parse_rollout(
    path: Path, expected_thread_id: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    completed: list[dict[str, Any]] = []
    compacted: list[dict[str, Any]] = []
    active: dict[str, Any] | None = None
    session_meta_seen = False
    compact_generations: set[int] = set()
    compact_windows: set[str] = set()
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise DesktopRolloutError(
                    f"rollout line {line_number} is not valid JSON"
                ) from exc
            if not isinstance(record, dict):
                raise DesktopRolloutError(f"rollout line {line_number} is not an object")
            kind = record.get("type")
            payload = record.get("payload")
            if kind == "session_meta":
                if not isinstance(payload, dict):
                    raise DesktopRolloutError("session metadata is malformed")
                if payload.get("id") != expected_thread_id or payload.get("session_id") != expected_thread_id:
                    raise DesktopRolloutError("rollout session metadata does not match the armed thread")
                session_meta_seen = True
                continue
            if kind == "turn_context":
                if active is not None:
                    if not isinstance(payload, dict):
                        raise DesktopRolloutError(
                            f"turn context at line {line_number} is malformed"
                        )
                    active["routes"].add((payload.get("model"), payload.get("effort")))
                continue
            if kind == "compacted":
                if not isinstance(payload, dict):
                    raise DesktopRolloutError("compacted rollout record is malformed")
                window_id = app_adapter._protocol_id("window_id", payload.get("window_id"))
                generation = metrics.require_nonnegative_int(
                    "window_number", payload.get("window_number")
                )
                if generation == 0:
                    raise DesktopRolloutError("compaction generation must be at least 1")
                if generation in compact_generations or window_id in compact_windows:
                    raise DesktopRolloutError("rollout contains a duplicate compaction identity")
                compact_generations.add(generation)
                compact_windows.add(window_id)
                compacted.append({"windowId": window_id, "generation": generation})
                continue
            if kind != "event_msg" or not isinstance(payload, dict):
                continue
            event_type = payload.get("type")
            if event_type == "task_started":
                if active is not None:
                    raise DesktopRolloutError("rollout contains overlapping turns")
                active = {
                    "turnId": app_adapter._protocol_id("turn_id", payload.get("turn_id")),
                    "usage": None,
                    "routes": set(),
                }
            elif event_type == "token_count":
                if active is None:
                    raise DesktopRolloutError("token count appeared outside an active turn")
                info = payload.get("info")
                if not isinstance(info, dict) or not isinstance(info.get("last_token_usage"), dict):
                    raise DesktopRolloutError("token count has no final-turn usage object")
                usage = info["last_token_usage"]
                active["usage"] = {
                    "inputTokens": app_adapter._safe_counter(
                        "input_tokens", usage.get("input_tokens")
                    ),
                    "cachedInputTokens": app_adapter._safe_counter(
                        "cached_input_tokens", usage.get("cached_input_tokens")
                    ),
                    "totalTokens": app_adapter._safe_counter(
                        "total_tokens", usage.get("total_tokens")
                    ),
                }
            elif event_type in {"task_complete", "turn_aborted"}:
                if active is None:
                    raise DesktopRolloutError("terminal marker appeared without an active turn")
                terminal_turn = app_adapter._protocol_id("turn_id", payload.get("turn_id"))
                if terminal_turn != active["turnId"]:
                    raise DesktopRolloutError("terminal marker does not match the active turn")
                if event_type == "turn_aborted":
                    active["status"] = "interrupted"
                elif payload.get("error") is not None:
                    active["status"] = "failed"
                else:
                    active["status"] = "completed"
                active["completedAt"] = app_adapter._safe_counter(
                    "completed_at", payload.get("completed_at")
                )
                completed.append(active)
                active = None
            elif event_type == "model_rerouted":
                raise DesktopRolloutError("model reroute observed; start a corrected epoch")
            # Every other event may contain content and is deliberately ignored.
    if not session_meta_seen:
        raise DesktopRolloutError("rollout has no matching session metadata")
    return completed, compacted, active is not None


def _append_compaction(
    metrics_path: Path,
    identity: app_adapter.EpochIdentity,
    thread_digest: str,
    window_id: str,
    generation: int,
) -> bool:
    event_id = _stable_id("desktop-compact", thread_digest, window_id)
    record = identity.base_event("compacted", event_id, "app_server")
    record["generation"] = generation
    try:
        metrics.append_event(metrics_path, record)
    except metrics.MetricsError as exc:
        if str(exc) == f"eventId {event_id} appears more than once":
            return False
        raise
    return True


def _append_close(
    metrics_path: Path,
    identity: app_adapter.EpochIdentity,
    outcome: str,
) -> bool:
    event_id = _stable_id("epoch-close", identity.epoch_id, outcome)
    record = identity.base_event("epoch_closed", event_id, "manual")
    record["outcome"] = outcome
    try:
        metrics.append_event(metrics_path, record)
    except metrics.MetricsError as exc:
        if str(exc) == f"eventId {event_id} appears more than once":
            return False
        raise
    return True


def collect_epoch(
    *,
    sessions_root: Path,
    thread_id: str,
    arm_path: Path,
    metrics_path: Path,
    outcome: str | None,
) -> dict[str, int | str | bool]:
    root = _require_sessions_root(sessions_root)
    raw_thread_id = _require_thread_id(thread_id)
    resolved_metrics = app_adapter.require_repository_external(metrics_path)
    state = _load_arm(arm_path)
    if state["threadDigest"] != _digest(raw_thread_id):
        raise DesktopRolloutError("thread id does not match the armed epoch")
    if state["metricsPathDigest"] != _digest(str(resolved_metrics)):
        raise DesktopRolloutError("metrics path does not match the armed epoch")
    identity = _identity_from_state(state)
    matches = _matching_rollouts(root, raw_thread_id)
    if len(matches) != 1:
        raise DesktopRolloutError("expected exactly one rollout for the armed thread")
    rollout = matches[0]
    if rollout.stat().st_ctime_ns + FILESYSTEM_TIME_TOLERANCE_NS < state["armedAtNs"]:
        raise DesktopRolloutError("rollout predates the arm boundary")
    turns, compactions, open_turn = _parse_rollout(rollout, raw_thread_id)
    adapter = app_adapter.AppServerUsageAdapter(resolved_metrics, identity)
    synthetic_thread = f"desktop-{state['threadDigest'][:40]}"
    for turn in turns:
        routes = turn["routes"]
        expected_route = {(identity.model, identity.reasoning)}
        if turn["status"] == "completed" and routes != expected_route:
            raise DesktopRolloutError("turn route does not match the armed epoch")
        if turn["status"] != "completed" and routes not in (set(), expected_route):
            raise DesktopRolloutError("turn route does not match the armed epoch")
        usage = turn["usage"]
        if turn["status"] == "completed" and usage is None:
            raise DesktopRolloutError("completed turn has no final token usage")
        if usage is not None:
            adapter.consume(
                {
                    "method": "thread/tokenUsage/updated",
                    "params": {
                        "threadId": synthetic_thread,
                        "turnId": turn["turnId"],
                        "tokenUsage": {"last": usage},
                    },
                }
            )
        adapter.consume(
            {
                "method": "turn/completed",
                "params": {
                    "threadId": synthetic_thread,
                    "turn": {
                        "id": turn["turnId"],
                        "status": turn["status"],
                        "completedAt": turn["completedAt"],
                    },
                },
            }
        )
    summary = adapter.finalize()
    appended_compactions = 0
    for compact in compactions:
        appended_compactions += _append_compaction(
            resolved_metrics,
            identity,
            state["threadDigest"],
            compact["windowId"],
            compact["generation"],
        )
    closed = False
    if outcome is not None:
        if open_turn:
            raise DesktopRolloutError("cannot close an epoch while a turn is active")
        closed = _append_close(resolved_metrics, identity, outcome)
        app_adapter.require_repository_external(arm_path).unlink(missing_ok=True)
    return {
        **summary,
        "appendedCompactions": appended_compactions,
        "openTurn": open_turn,
        "epochClosed": closed,
    }


def _identity_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--epoch-id", required=True)
    parser.add_argument("--thread-ref", required=True)
    parser.add_argument("--mode", choices=sorted(metrics.MODES), required=True)
    parser.add_argument("--role", choices=sorted(metrics.ROLES), required=True)
    parser.add_argument("--cohort", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning", choices=sorted(metrics.REASONING), required=True)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    arm = subparsers.add_parser("arm", help="arm one fresh Desktop thread before its first turn")
    collect = subparsers.add_parser("collect", help="collect terminal usage from an armed thread")
    for command in (arm, collect):
        command.add_argument("--sessions-root", type=Path, default=Path("~/.codex/sessions"))
        command.add_argument("--thread-id", required=True)
        command.add_argument("--arm-path", type=Path, required=True)
        command.add_argument("--path", type=Path, required=True, help="external metrics JSONL")
    _identity_args(arm)
    collect.add_argument("--outcome", choices=sorted(metrics.EPOCH_OUTCOMES))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    try:
        if args.command == "arm":
            result = arm_epoch(
                sessions_root=args.sessions_root,
                thread_id=args.thread_id,
                arm_path=args.arm_path,
                metrics_path=args.path,
                identity=app_adapter.EpochIdentity(
                    args.epoch_id,
                    args.thread_ref,
                    args.mode,
                    args.role,
                    args.cohort,
                    args.model,
                    args.reasoning,
                ),
            )
        else:
            result = collect_epoch(
                sessions_root=args.sessions_root,
                thread_id=args.thread_id,
                arm_path=args.arm_path,
                metrics_path=args.path,
                outcome=args.outcome,
            )
        print(json.dumps(result, sort_keys=True))
    except (DesktopRolloutError, app_adapter.AdapterError, metrics.MetricsError, OSError) as exc:
        print(f"desktop-rollout-usage-adapter: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
