#!/usr/bin/env python3

from __future__ import annotations

import json
import stat
import tempfile
import unittest
from pathlib import Path

import context_metrics as metrics


def base_event(epoch_id: str, mode: str, event: str, **extra: object) -> dict[str, object]:
    record: dict[str, object] = {
        "schemaVersion": 1,
        "eventId": f"{epoch_id}:{event}",
        "at": "2026-08-12T00:00:00Z",
        "event": event,
        "epochId": epoch_id,
        "threadRef": f"thread-{epoch_id}",
        "mode": mode,
        "role": "architect",
        "cohort": "outcome-batch",
        "model": "gpt-5.6-luna",
        "reasoning": "max",
        "source": "manual",
    }
    record.update(extra)
    return record


def passing_events() -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for mode, token_count in (("baseline", 1000), ("pilot", 700)):
        epoch_count = 3 if mode == "baseline" else 5
        for number in range(1, epoch_count + 1):
            epoch_id = f"{mode}-{number}"
            events.append(base_event(epoch_id, mode, "epoch_started"))
            events.append(
                base_event(
                    epoch_id,
                    mode,
                    "turn_completed",
                    eventId=f"{epoch_id}:turn:1",
                    source="app_server",
                    turnIndex=1,
                    inputTokens=token_count,
                    cachedInputTokens=100,
                    totalTokens=token_count + 100,
                )
            )
            if mode == "pilot":
                events.append(
                    base_event(
                        epoch_id,
                        mode,
                        "rotation_completed",
                        boundaryId=f"rotation-{number}",
                        result="accepted",
                        coldStartTurns=1,
                    )
                )
            events.append(base_event(epoch_id, mode, "epoch_closed", outcome="completed"))
    return events


class ContextMetricsTests(unittest.TestCase):
    def test_append_secures_file_and_validates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            for event in passing_events():
                metrics.append_event(path, metrics.validate_event(event))
            loaded = metrics.load_events(path)
            self.assertEqual(len(loaded), len(passing_events()))
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_report_passes_comparable_epochs_and_five_rotations(self) -> None:
        report = metrics.build_report([metrics.validate_event(item) for item in passing_events()])
        result = report["decisionMetrics"][0]
        self.assertEqual(result["decision"], "pass")
        self.assertEqual(result["inputTokenReductionPercent"], 30.0)
        self.assertEqual(result["firstFiveRotationsNeedingSecondContextTurn"], 0)
        self.assertEqual(result["observedContextRegressions"]["all"], 0)

    def test_two_regressions_in_first_five_rotations_roll_back(self) -> None:
        events = passing_events()
        for number, kind in ((2, "constraint_miss"), (5, "duplicate_work")):
            events.append(
                base_event(
                    f"pilot-{number}",
                    "pilot",
                    "context_regression",
                    boundaryType="rotation",
                    boundaryId=f"rotation-{number}",
                    kind=kind,
                    impact="correction" if kind == "constraint_miss" else "repeated_execution",
                    evidenceRef=f"SUP-{number:03d}",
                )
            )
        report = metrics.build_report([metrics.validate_event(item) for item in events])
        result = report["decisionMetrics"][0]
        self.assertEqual(result["decision"], "rollback")
        self.assertIn("two_context_regressions_in_first_five_rotations", result["rollbackReasons"])

    def test_two_second_turn_recoveries_in_first_five_roll_back(self) -> None:
        events = passing_events()
        for event in events:
            if event["event"] == "rotation_completed" and event["boundaryId"] in {"rotation-2", "rotation-4"}:
                event["coldStartTurns"] = 2
        report = metrics.build_report([metrics.validate_event(item) for item in events])
        result = report["decisionMetrics"][0]
        self.assertEqual(result["decision"], "rollback")
        self.assertIn("two_rotations_need_second_context_turn_in_first_five", result["rollbackReasons"])

    def test_unknown_field_is_rejected(self) -> None:
        event = base_event("baseline-1", "baseline", "epoch_started", note="do not store narrative")
        with self.assertRaisesRegex(metrics.MetricsError, "unknown fields"):
            metrics.validate_event(event)

    def test_manual_turn_usage_is_rejected(self) -> None:
        event = base_event(
            "baseline-1",
            "baseline",
            "turn_completed",
            eventId="baseline-1:turn:1",
            turnIndex=1,
            inputTokens=100,
            cachedInputTokens=10,
            totalTokens=120,
        )
        with self.assertRaisesRegex(metrics.MetricsError, "do not hand-estimate"):
            metrics.validate_event(event)

    def test_duplicate_event_id_is_rejected_before_append(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            event = base_event("baseline-1", "baseline", "epoch_started")
            metrics.append_event(path, metrics.validate_event(event))
            with self.assertRaisesRegex(metrics.MetricsError, "eventId .* appears more than once"):
                metrics.append_event(path, metrics.validate_event(event))

    def test_jsonl_with_inconsistent_epoch_identity_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            first = base_event("epoch-1", "baseline", "epoch_started")
            second = base_event(
                "epoch-1",
                "pilot",
                "turn_completed",
                eventId="epoch-1:turn:1",
                source="app_server",
                turnIndex=1,
                inputTokens=1,
                cachedInputTokens=0,
                totalTokens=1,
            )
            path.write_text(json.dumps(first) + "\n" + json.dumps(second) + "\n", encoding="utf-8")
            path.chmod(0o600)
            with self.assertRaisesRegex(metrics.MetricsError, "changes mode"):
                metrics.load_events(path)


if __name__ == "__main__":
    unittest.main()
