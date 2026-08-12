#!/usr/bin/env python3
"""Strict local JSONL recorder and reporter for context lifecycle experiments."""

from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import json
import math
import os
import re
import stat
import sys
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any, Iterable

SCHEMA_VERSION = 1
MAX_LINE_BYTES = 4096
EVENTS = {
    "epoch_started",
    "epoch_closed",
    "turn_completed",
    "compacted",
    "rotation_completed",
    "context_regression",
}
MODES = {"baseline", "pilot"}
ROLES = {"architect", "supervisor"}
SOURCES = {"manual", "app_server", "hook", "rotator"}
REASONING = {"none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra", "unknown"}
REGRESSION_KINDS = {"constraint_miss", "duplicate_work"}
REGRESSION_IMPACTS = {"correction", "repeated_execution", "boundary_violation"}
BOUNDARY_TYPES = {"compact", "rotation", "handoff"}
ROTATION_RESULTS = {"accepted", "rolled_back"}
EPOCH_OUTCOMES = {"completed", "paused", "aborted"}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,79}$")
SAFE_LABEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+:/-]{0,63}$")

BASE_FIELDS = {
    "schemaVersion",
    "eventId",
    "at",
    "event",
    "epochId",
    "threadRef",
    "mode",
    "role",
    "cohort",
    "model",
    "reasoning",
    "source",
}
EVENT_FIELDS = {
    "epoch_started": set(),
    "epoch_closed": {"outcome"},
    "turn_completed": {
        "turnIndex",
        "inputTokens",
        "cachedInputTokens",
        "totalTokens",
    },
    "compacted": {"generation"},
    "rotation_completed": {"boundaryId", "result", "coldStartTurns"},
    "context_regression": {
        "boundaryType",
        "boundaryId",
        "kind",
        "impact",
        "evidenceRef",
    },
}


class MetricsError(ValueError):
    pass


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_utc(value: Any) -> dt.datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise MetricsError("at must be a UTC RFC3339 timestamp ending in Z")
    try:
        parsed = dt.datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise MetricsError("at must be a valid UTC RFC3339 timestamp") from exc
    if parsed.utcoffset() != dt.timedelta(0):
        raise MetricsError("at must use UTC")
    return parsed


def require_safe_id(name: str, value: Any) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise MetricsError(f"{name} must be an opaque ASCII identifier of at most 80 characters")
    return value


def require_label(name: str, value: Any) -> str:
    if not isinstance(value, str) or not SAFE_LABEL.fullmatch(value):
        raise MetricsError(f"{name} must be a stable ASCII label of at most 64 characters")
    return value


def require_nonnegative_int(name: str, value: Any, *, required: bool = True) -> int | None:
    if value is None and not required:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise MetricsError(f"{name} must be a non-negative integer")
    if value > 2**53 - 1:
        raise MetricsError(f"{name} exceeds the JavaScript safe-integer range")
    return value


def validate_event(record: Any) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise MetricsError("each JSONL line must be an object")
    event = record.get("event")
    if event not in EVENTS:
        raise MetricsError(f"event must be one of {sorted(EVENTS)}")
    allowed = BASE_FIELDS | EVENT_FIELDS[event]
    unknown = set(record) - allowed
    if unknown:
        raise MetricsError(f"unknown fields are forbidden: {sorted(unknown)}")
    missing = BASE_FIELDS - set(record)
    if missing:
        raise MetricsError(f"missing required fields: {sorted(missing)}")

    if record.get("schemaVersion") != SCHEMA_VERSION:
        raise MetricsError(f"schemaVersion must equal {SCHEMA_VERSION}")
    parse_utc(record["at"])
    require_safe_id("eventId", record["eventId"])
    require_safe_id("epochId", record["epochId"])
    require_safe_id("threadRef", record["threadRef"])
    if record["mode"] not in MODES:
        raise MetricsError(f"mode must be one of {sorted(MODES)}")
    if record["role"] not in ROLES:
        raise MetricsError(f"role must be one of {sorted(ROLES)}")
    require_label("cohort", record["cohort"])
    require_label("model", record["model"])
    if record["reasoning"] not in REASONING:
        raise MetricsError(f"reasoning must be one of {sorted(REASONING)}")
    if record["source"] not in SOURCES:
        raise MetricsError(f"source must be one of {sorted(SOURCES)}")

    if event == "epoch_closed":
        if record.get("outcome") not in EPOCH_OUTCOMES:
            raise MetricsError(f"outcome must be one of {sorted(EPOCH_OUTCOMES)}")
    elif event == "turn_completed":
        if record["source"] != "app_server":
            raise MetricsError("turn_completed requires source=app_server; do not hand-estimate token usage")
        turn_index = require_nonnegative_int("turnIndex", record.get("turnIndex"))
        if turn_index == 0:
            raise MetricsError("turnIndex must be at least 1")
        for name in ("inputTokens", "cachedInputTokens", "totalTokens"):
            require_nonnegative_int(name, record.get(name))
        if record["cachedInputTokens"] > record["inputTokens"]:
            raise MetricsError("cachedInputTokens cannot exceed inputTokens")
        if record["totalTokens"] < record["inputTokens"]:
            raise MetricsError("totalTokens cannot be smaller than inputTokens")
    elif event == "compacted":
        generation = require_nonnegative_int("generation", record.get("generation"))
        if generation == 0:
            raise MetricsError("generation must be at least 1")
    elif event == "rotation_completed":
        require_safe_id("boundaryId", record.get("boundaryId"))
        result = record.get("result")
        if result not in ROTATION_RESULTS:
            raise MetricsError(f"result must be one of {sorted(ROTATION_RESULTS)}")
        cold = require_nonnegative_int("coldStartTurns", record.get("coldStartTurns"), required=False)
        if result == "accepted" and (cold is None or cold < 1):
            raise MetricsError("accepted rotations require coldStartTurns >= 1")
        if result == "rolled_back" and cold is not None:
            raise MetricsError("rolled-back rotations must omit coldStartTurns")
    elif event == "context_regression":
        if record.get("boundaryType") not in BOUNDARY_TYPES:
            raise MetricsError(f"boundaryType must be one of {sorted(BOUNDARY_TYPES)}")
        require_safe_id("boundaryId", record.get("boundaryId"))
        if record.get("kind") not in REGRESSION_KINDS:
            raise MetricsError(f"kind must be one of {sorted(REGRESSION_KINDS)}")
        if record.get("impact") not in REGRESSION_IMPACTS:
            raise MetricsError(f"impact must be one of {sorted(REGRESSION_IMPACTS)}")
        require_safe_id("evidenceRef", record.get("evidenceRef"))

    encoded = json.dumps(record, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_LINE_BYTES:
        raise MetricsError(f"event exceeds {MAX_LINE_BYTES} bytes")
    return record


def validate_epoch_consistency(events: Iterable[dict[str, Any]]) -> None:
    metadata: dict[str, tuple[str, str, str, str, str, str]] = {}
    starts: defaultdict[str, int] = defaultdict(int)
    closes: defaultdict[str, int] = defaultdict(int)
    event_ids: set[str] = set()
    turn_indexes: defaultdict[str, set[int]] = defaultdict(set)
    for event in events:
        epoch_id = event["epochId"]
        identity = (
            event["mode"],
            event["role"],
            event["cohort"],
            event["model"],
            event["reasoning"],
            event["threadRef"],
        )
        if epoch_id in metadata and metadata[epoch_id] != identity:
            raise MetricsError(f"epoch {epoch_id} changes mode, role, cohort, model, reasoning, or threadRef")
        metadata[epoch_id] = identity
        event_id = event["eventId"]
        if event_id in event_ids:
            raise MetricsError(f"eventId {event_id} appears more than once")
        event_ids.add(event_id)
        starts[epoch_id] += event["event"] == "epoch_started"
        closes[epoch_id] += event["event"] == "epoch_closed"
        if event["event"] == "turn_completed":
            turn_index = event["turnIndex"]
            if turn_index in turn_indexes[epoch_id]:
                raise MetricsError(f"turnIndex {turn_index} appears more than once in epoch {epoch_id}")
            turn_indexes[epoch_id].add(turn_index)
    for epoch_id in metadata:
        if starts[epoch_id] != 1:
            raise MetricsError(f"epoch {epoch_id} must contain exactly one epoch_started event")
        if closes[epoch_id] > 1:
            raise MetricsError(f"epoch {epoch_id} contains more than one epoch_closed event")


def check_secure_file(path: Path) -> None:
    if path.is_symlink():
        raise MetricsError("metrics path must not be a symlink")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise MetricsError(f"metrics file must be user-only (0600); current mode is {mode:04o}")


def parse_event_lines(lines: Iterable[bytes]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line_number, raw in enumerate(lines, start=1):
        if len(raw) > MAX_LINE_BYTES + 1:
            raise MetricsError(f"line {line_number} exceeds {MAX_LINE_BYTES} bytes")
        try:
            parsed = json.loads(raw)
            events.append(validate_event(parsed))
        except (json.JSONDecodeError, UnicodeDecodeError, MetricsError) as exc:
            raise MetricsError(f"line {line_number}: {exc}") from exc
    validate_epoch_consistency(events)
    return events


def append_event(path: Path, record: dict[str, Any]) -> None:
    validate_event(record)
    path = path.expanduser()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.exists() and path.is_symlink():
        raise MetricsError("metrics path must not be a symlink")
    flags = os.O_RDWR | os.O_CREAT | os.O_APPEND
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        os.fchmod(fd, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX)
        os.lseek(fd, 0, os.SEEK_SET)
        existing_bytes = bytearray()
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            existing_bytes.extend(chunk)
        if existing_bytes and not existing_bytes.endswith(b"\n"):
            raise MetricsError("metrics file ends with a partial JSONL line")
        existing = parse_event_lines(existing_bytes.splitlines(keepends=True)) if existing_bytes else []
        validate_epoch_consistency([*existing, record])
        payload = json.dumps(record, ensure_ascii=True, separators=(",", ":")) + "\n"
        os.write(fd, payload.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)


def load_events(path: Path) -> list[dict[str, Any]]:
    path = path.expanduser()
    if not path.exists():
        raise MetricsError(f"metrics file does not exist: {path}")
    check_secure_file(path)
    with path.open("rb") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
        return parse_event_lines(handle)


def nearest_rank_p90(values: list[int]) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.90 * len(ordered)) - 1)]


def build_report(events: list[dict[str, Any]]) -> dict[str, Any]:
    groups: defaultdict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    daily_totals: defaultdict[str, int] = defaultdict(int)
    for event in events:
        key = (event["role"], event["cohort"], event["model"], event["reasoning"])
        groups[key].append(event)
        if event["event"] == "turn_completed":
            daily_totals[event["at"][:10]] += event["totalTokens"]

    results = []
    for key, items in sorted(groups.items()):
        role, cohort, model, reasoning = key
        completed_epoch_ids = {
            mode: {
                item["epochId"]
                for item in items
                if item["mode"] == mode
                and item["event"] == "epoch_closed"
                and item["outcome"] == "completed"
            }
            for mode in MODES
        }
        epochs = {
            mode: completed_epoch_ids[mode]
            for mode in MODES
        }
        turns = {
            mode: [
                item
                for item in items
                if item["mode"] == mode
                and item["event"] == "turn_completed"
                and item["epochId"] in completed_epoch_ids[mode]
            ]
            for mode in MODES
        }
        baseline_inputs = [item["inputTokens"] for item in turns["baseline"]]
        pilot_inputs = [item["inputTokens"] for item in turns["pilot"]]
        baseline_median = float(median(baseline_inputs)) if baseline_inputs else None
        pilot_median = float(median(pilot_inputs)) if pilot_inputs else None
        reduction = None
        if baseline_median not in (None, 0) and pilot_median is not None:
            reduction = round((baseline_median - pilot_median) * 100.0 / baseline_median, 2)

        pilot_regressions = [
            item for item in items if item["mode"] == "pilot" and item["event"] == "context_regression"
        ]
        regression_counts = {
            kind: sum(item["kind"] == kind for item in pilot_regressions)
            for kind in sorted(REGRESSION_KINDS)
        }
        impact_counts = {
            impact: sum(item["impact"] == impact for item in pilot_regressions)
            for impact in sorted(REGRESSION_IMPACTS)
        }
        accepted_rotations = [
            item
            for item in items
            if item["mode"] == "pilot"
            and item["event"] == "rotation_completed"
            and item["result"] == "accepted"
        ]
        cold_starts = [item["coldStartTurns"] for item in accepted_rotations]
        cold_p90_diagnostic = nearest_rank_p90(cold_starts) if len(cold_starts) >= 10 else None
        corrections = sum(value > 1 for value in cold_starts)
        first_five_rotations = accepted_rotations[:5]
        first_five_ids = {item["boundaryId"] for item in first_five_rotations}
        first_five_corrections = sum(item["coldStartTurns"] > 1 for item in first_five_rotations)

        first_five_regressions = [
            item
            for item in pilot_regressions
            if item["boundaryType"] == "rotation" and item["boundaryId"] in first_five_ids
        ]
        protected_boundary_violation = any(
            item["impact"] == "boundary_violation" for item in pilot_regressions
        )

        enough = (
            len(epochs["baseline"]) >= 3
            and len(epochs["pilot"]) >= 3
            and len(accepted_rotations) >= 5
            and baseline_median is not None
            and pilot_median is not None
        )
        rollback_reasons = []
        if protected_boundary_violation:
            rollback_reasons.append("protected_boundary_violation")
        if len(first_five_rotations) == 5 and len(first_five_regressions) >= 2:
            rollback_reasons.append("two_context_regressions_in_first_five_rotations")
        if len(first_five_rotations) == 5 and first_five_corrections >= 2:
            rollback_reasons.append("two_rotations_need_second_context_turn_in_first_five")
        if enough and reduction is not None and reduction < 20.0:
            rollback_reasons.append("input_token_reduction_below_20_percent")

        if rollback_reasons:
            decision = "rollback"
        elif not enough:
            decision = "insufficient_data"
        elif reduction is not None and reduction >= 25.0 and not pilot_regressions and first_five_corrections <= 1:
            decision = "pass"
        else:
            decision = "continue_pilot"

        results.append(
            {
                "group": {
                    "role": role,
                    "cohort": cohort,
                    "model": model,
                    "reasoning": reasoning,
                },
                "epochs": {mode: len(epochs[mode]) for mode in sorted(MODES)},
                "turns": {mode: len(turns[mode]) for mode in sorted(MODES)},
                "medianInputTokens": {"baseline": baseline_median, "pilot": pilot_median},
                "inputTokenReductionPercent": reduction,
                "observedContextRegressions": {
                    "all": len(pilot_regressions),
                    "byKind": regression_counts,
                    "byImpact": impact_counts,
                },
                "acceptedRotations": len(accepted_rotations),
                "rotationsNeedingSecondContextTurn": corrections,
                "firstFiveRotationsNeedingSecondContextTurn": first_five_corrections,
                "coldStartTurnsP90Diagnostic": cold_p90_diagnostic,
                "decision": decision,
                "rollbackReasons": rollback_reasons,
            }
        )

    return {
        "schemaVersion": SCHEMA_VERSION,
        "decisionMetrics": results,
        "diagnosticsOnly": {"dailyTotalTokens": dict(sorted(daily_totals.items()))},
    }


def common_record(args: argparse.Namespace) -> dict[str, Any]:
    record: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "at": args.at or utc_now(),
        "event": args.event,
        "eventId": args.event_id,
        "epochId": args.epoch_id,
        "threadRef": args.thread_ref,
        "mode": args.mode,
        "role": args.role,
        "cohort": args.cohort,
        "model": args.model,
        "reasoning": args.reasoning,
        "source": args.source,
    }
    if args.event == "epoch_closed":
        record["outcome"] = args.outcome
    elif args.event == "turn_completed":
        record.update(
            {
                "inputTokens": args.input_tokens,
                "cachedInputTokens": args.cached_input_tokens,
                "totalTokens": args.total_tokens,
                "turnIndex": args.turn_index,
            }
        )
    elif args.event == "compacted":
        record["generation"] = args.generation
    elif args.event == "rotation_completed":
        record.update({"boundaryId": args.boundary_id, "result": args.result})
        if args.cold_start_turns is not None:
            record["coldStartTurns"] = args.cold_start_turns
    elif args.event == "context_regression":
        record.update(
            {
                "boundaryType": args.boundary_type,
                "boundaryId": args.boundary_id,
                "kind": args.kind,
                "impact": args.impact,
                "evidenceRef": args.evidence_ref,
            }
        )
    return validate_event(record)


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--path", type=Path, required=True, help="repository-external JSONL file")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    append = subparsers.add_parser("append", help="append one strict event")
    add_common_arguments(append)
    append.add_argument("--event", choices=sorted(EVENTS), required=True)
    append.add_argument("--event-id", required=True)
    append.add_argument("--epoch-id", required=True)
    append.add_argument("--thread-ref", required=True)
    append.add_argument("--mode", choices=sorted(MODES), required=True)
    append.add_argument("--role", choices=sorted(ROLES), required=True)
    append.add_argument("--cohort", required=True)
    append.add_argument("--model", required=True)
    append.add_argument("--reasoning", choices=sorted(REASONING), required=True)
    append.add_argument("--source", choices=sorted(SOURCES), required=True)
    append.add_argument("--at", help="UTC RFC3339 timestamp ending in Z; defaults to now")
    append.add_argument("--outcome", choices=sorted(EPOCH_OUTCOMES))
    append.add_argument("--input-tokens", type=int)
    append.add_argument("--turn-index", type=int)
    append.add_argument("--cached-input-tokens", type=int)
    append.add_argument("--total-tokens", type=int)
    append.add_argument("--generation", type=int)
    append.add_argument("--boundary-id")
    append.add_argument("--result", choices=sorted(ROTATION_RESULTS))
    append.add_argument("--cold-start-turns", type=int)
    append.add_argument("--boundary-type", choices=sorted(BOUNDARY_TYPES))
    append.add_argument("--kind", choices=sorted(REGRESSION_KINDS))
    append.add_argument("--impact", choices=sorted(REGRESSION_IMPACTS))
    append.add_argument("--evidence-ref")

    validate = subparsers.add_parser("validate", help="validate schema, permissions, and epoch consistency")
    add_common_arguments(validate)

    report = subparsers.add_parser("report", help="compare baseline and pilot cohorts")
    add_common_arguments(report)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    try:
        if args.command == "append":
            record = common_record(args)
            append_event(args.path, record)
            print(json.dumps({"status": "appended", "event": record["event"], "epochId": record["epochId"]}))
        elif args.command == "validate":
            events = load_events(args.path)
            print(json.dumps({"status": "valid", "events": len(events)}))
        else:
            events = load_events(args.path)
            print(json.dumps(build_report(events), indent=2, sort_keys=True))
    except (OSError, MetricsError) as exc:
        print(f"context-metrics: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
