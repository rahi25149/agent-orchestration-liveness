#!/usr/bin/env python3
"""Coalesce Codex App Server usage notifications into strict terminal-turn metrics."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

import context_metrics as metrics

MAX_PROTOCOL_ID_BYTES = 512
TERMINAL_STATUSES = {"completed", "failed", "interrupted"}


class AdapterError(ValueError):
    pass


@dataclass(frozen=True)
class EpochIdentity:
    epoch_id: str
    thread_ref: str
    mode: str
    role: str
    cohort: str
    model: str
    reasoning: str

    def base_event(self, event: str, event_id: str, source: str) -> dict[str, Any]:
        return {
            "schemaVersion": metrics.SCHEMA_VERSION,
            "eventId": event_id,
            "at": metrics.utc_now(),
            "event": event,
            "epochId": self.epoch_id,
            "threadRef": self.thread_ref,
            "mode": self.mode,
            "role": self.role,
            "cohort": self.cohort,
            "model": self.model,
            "reasoning": self.reasoning,
            "source": source,
        }


@dataclass
class AdapterStats:
    usage_updates: int = 0
    terminal_notifications: int = 0
    appended_turns: int = 0
    duplicate_turns: int = 0
    skipped_terminal_turns: int = 0
    ignored_messages: int = 0

    def safe_summary(self) -> dict[str, int | str]:
        return {
            "status": "complete",
            "usageUpdates": self.usage_updates,
            "terminalNotifications": self.terminal_notifications,
            "appendedTurns": self.appended_turns,
            "duplicateTurns": self.duplicate_turns,
            "skippedTerminalTurns": self.skipped_terminal_turns,
            "ignoredMessages": self.ignored_messages,
        }


def _stable_hash(*values: str) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()[:40]


def _protocol_id(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > MAX_PROTOCOL_ID_BYTES:
        raise AdapterError(f"{name} must be a non-empty bounded string")
    if any(ord(character) < 0x20 or ord(character) == 0x7F for character in value):
        raise AdapterError(f"{name} must not contain control characters")
    return value


def _safe_counter(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 2**53 - 1:
        raise AdapterError(f"{name} must be a non-negative safe integer")
    return value


def _terminal_time(value: Any) -> str:
    if value is None:
        return metrics.utc_now()
    seconds = _safe_counter("completedAt", value)
    try:
        return dt.datetime.fromtimestamp(seconds, tz=dt.timezone.utc).isoformat(timespec="seconds").replace(
            "+00:00", "Z"
        )
    except (OverflowError, OSError, ValueError) as exc:
        raise AdapterError("completedAt is outside the supported UTC range") from exc


def require_repository_external(path: Path) -> Path:
    resolved = path.expanduser().resolve(strict=False)
    for parent in (resolved.parent, *resolved.parents):
        if (parent / ".git").exists():
            raise AdapterError("metrics path must be outside every Git repository")
    return resolved


def _duplicate_error(exc: metrics.MetricsError, event_id: str) -> bool:
    return str(exc) == f"eventId {event_id} appears more than once"


class AppServerUsageAdapter:
    """Consume one App Server connection and persist only terminal per-turn counters."""

    def __init__(self, path: Path, identity: EpochIdentity):
        self.path = require_repository_external(path)
        self.identity = identity
        self.stats = AdapterStats()
        self._bound_thread_id: str | None = None
        self._usage: dict[tuple[str, str], tuple[int, int, int]] = {}
        self._terminal: dict[tuple[str, str], tuple[str, str]] = {}
        self._finalized: set[tuple[str, str]] = set()
        self._next_turn_index = 1
        self._initialize_epoch()

    def _initialize_epoch(self) -> None:
        existing = metrics.load_events(self.path) if self.path.exists() else []
        epoch_events = [event for event in existing if event["epochId"] == self.identity.epoch_id]
        expected = (
            self.identity.mode,
            self.identity.role,
            self.identity.cohort,
            self.identity.model,
            self.identity.reasoning,
            self.identity.thread_ref,
        )
        for event in epoch_events:
            actual = (
                event["mode"],
                event["role"],
                event["cohort"],
                event["model"],
                event["reasoning"],
                event["threadRef"],
            )
            if actual != expected:
                raise AdapterError("existing epoch identity does not match the adapter configuration")
        if any(event["event"] == "epoch_closed" for event in epoch_events):
            raise AdapterError("cannot append usage to a closed epoch")
        completed_indexes = [
            event["turnIndex"] for event in epoch_events if event["event"] == "turn_completed"
        ]
        if completed_indexes:
            self._next_turn_index = max(completed_indexes) + 1
        if any(event["event"] == "epoch_started" for event in epoch_events):
            return
        event_id = f"epoch-start:{_stable_hash(self.identity.epoch_id)}"
        record = self.identity.base_event("epoch_started", event_id, "manual")
        try:
            metrics.append_event(self.path, record)
        except metrics.MetricsError as exc:
            if not _duplicate_error(exc, event_id):
                raise

    def consume(self, message: Any) -> None:
        if not isinstance(message, dict):
            raise AdapterError("each App Server message must be an object")
        method = message.get("method")
        if method == "model/rerouted":
            raise AdapterError("model reroute observed; start a new epoch with the exact route")
        if method == "thread/tokenUsage/updated":
            self._consume_usage(message.get("params"))
        elif method == "turn/completed":
            self._consume_terminal(message.get("params"))
        else:
            self.stats.ignored_messages += 1

    def _bind_thread(self, thread_id: str) -> None:
        if self._bound_thread_id is None:
            self._bound_thread_id = thread_id
        elif self._bound_thread_id != thread_id:
            raise AdapterError("multiple App Server threads observed in one metrics epoch")

    def _consume_usage(self, params: Any) -> None:
        if not isinstance(params, dict):
            raise AdapterError("token usage params must be an object")
        thread_id = _protocol_id("threadId", params.get("threadId"))
        turn_id = _protocol_id("turnId", params.get("turnId"))
        self._bind_thread(thread_id)
        token_usage = params.get("tokenUsage")
        if not isinstance(token_usage, dict) or not isinstance(token_usage.get("last"), dict):
            raise AdapterError("tokenUsage.last must be an object")
        last = token_usage["last"]
        usage = (
            _safe_counter("inputTokens", last.get("inputTokens")),
            _safe_counter("cachedInputTokens", last.get("cachedInputTokens")),
            _safe_counter("totalTokens", last.get("totalTokens")),
        )
        if usage[1] > usage[0] or usage[2] < usage[0]:
            raise AdapterError("token usage counters are inconsistent")
        key = (thread_id, turn_id)
        self.stats.usage_updates += 1
        if key not in self._finalized:
            self._usage[key] = usage
            self._flush(key)

    def _consume_terminal(self, params: Any) -> None:
        if not isinstance(params, dict) or not isinstance(params.get("turn"), dict):
            raise AdapterError("turn/completed params must contain a turn object")
        thread_id = _protocol_id("threadId", params.get("threadId"))
        turn = params["turn"]
        turn_id = _protocol_id("turn.id", turn.get("id"))
        status = turn.get("status")
        if status not in TERMINAL_STATUSES:
            raise AdapterError("turn/completed has an unsupported terminal status")
        self._bind_thread(thread_id)
        key = (thread_id, turn_id)
        self.stats.terminal_notifications += 1
        if key in self._finalized:
            self.stats.duplicate_turns += 1
            return
        if status != "completed":
            self._usage.pop(key, None)
            self.stats.skipped_terminal_turns += 1
            self._finalized.add(key)
            return
        self._terminal[key] = (status, _terminal_time(turn.get("completedAt")))
        self._flush(key)

    def _flush(self, key: tuple[str, str]) -> None:
        if key not in self._usage or key not in self._terminal or key in self._finalized:
            return
        thread_id, turn_id = key
        input_tokens, cached_input_tokens, total_tokens = self._usage[key]
        _, completed_at = self._terminal[key]
        event_id = f"app-turn:{_stable_hash(thread_id, turn_id)}"
        record = self.identity.base_event("turn_completed", event_id, "app_server")
        record.update(
            {
                "at": completed_at,
                "turnIndex": self._next_turn_index,
                "inputTokens": input_tokens,
                "cachedInputTokens": cached_input_tokens,
                "totalTokens": total_tokens,
            }
        )
        try:
            metrics.append_event(self.path, record)
        except metrics.MetricsError as exc:
            if not _duplicate_error(exc, event_id):
                raise
            self.stats.duplicate_turns += 1
        else:
            self.stats.appended_turns += 1
            self._next_turn_index += 1
        self._usage.pop(key, None)
        self._terminal.pop(key, None)
        self._finalized.add(key)

    def finalize(self) -> dict[str, int | str]:
        completed_without_usage = set(self._terminal) - set(self._usage)
        usage_without_terminal = set(self._usage) - set(self._terminal)
        if completed_without_usage:
            raise AdapterError("completed turn ended without a final token usage update")
        if usage_without_terminal:
            raise AdapterError("token usage stream ended before the matching turn completed")
        return self.stats.safe_summary()


def observe_stream(stream: TextIO, adapter: AppServerUsageAdapter) -> dict[str, int | str]:
    for line_number, line in enumerate(stream, start=1):
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AdapterError(f"line {line_number} is not valid App Server JSON") from exc
        adapter.consume(message)
    return adapter.finalize()


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, required=True, help="repository-external 0600 metrics JSONL")
    parser.add_argument("--epoch-id", required=True)
    parser.add_argument("--thread-ref", required=True, help="opaque local reference; never use a raw thread id")
    parser.add_argument("--mode", choices=sorted(metrics.MODES), required=True)
    parser.add_argument("--role", choices=sorted(metrics.ROLES), required=True)
    parser.add_argument("--cohort", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning", choices=sorted(metrics.REASONING), required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    identity = EpochIdentity(
        epoch_id=args.epoch_id,
        thread_ref=args.thread_ref,
        mode=args.mode,
        role=args.role,
        cohort=args.cohort,
        model=args.model,
        reasoning=args.reasoning,
    )
    try:
        adapter = AppServerUsageAdapter(args.path, identity)
        print(json.dumps(observe_stream(sys.stdin, adapter), sort_keys=True))
    except (AdapterError, metrics.MetricsError, OSError) as exc:
        print(f"app-server-usage-adapter: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
