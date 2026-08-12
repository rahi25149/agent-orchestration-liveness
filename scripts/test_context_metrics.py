#!/usr/bin/env python3

from __future__ import annotations

import json
import stat
import subprocess
import sys
import tempfile
import time
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


def append_cli_args(path: Path, epoch_id: str, *, event_id: str | None = None) -> list[str]:
    return [
        sys.executable,
        str(Path(__file__).with_name("context_metrics.py")),
        "append",
        "--path",
        str(path),
        "--event",
        "epoch_started",
        "--event-id",
        event_id or f"{epoch_id}:epoch_started",
        "--epoch-id",
        epoch_id,
        "--thread-ref",
        f"thread-{epoch_id}",
        "--mode",
        "baseline",
        "--role",
        "architect",
        "--cohort",
        "outcome-batch",
        "--model",
        "gpt-5.6-luna",
        "--reasoning",
        "max",
        "--source",
        "manual",
        "--at",
        "2026-08-12T00:00:00Z",
    ]


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

    def test_report_excludes_open_paused_and_aborted_epochs_from_samples(self) -> None:
        events = passing_events()
        for suffix, outcome in (("open", None), ("paused", "paused"), ("aborted", "aborted")):
            epoch_id = f"baseline-{suffix}"
            events.extend(
                [
                    base_event(epoch_id, "baseline", "epoch_started"),
                    base_event(
                        epoch_id,
                        "baseline",
                        "turn_completed",
                        eventId=f"{epoch_id}:turn:1",
                        source="app_server",
                        turnIndex=1,
                        inputTokens=999999,
                        cachedInputTokens=0,
                        totalTokens=999999,
                    ),
                ]
            )
            if outcome is not None:
                events.append(base_event(epoch_id, "baseline", "epoch_closed", outcome=outcome))
        report = metrics.build_report([metrics.validate_event(item) for item in events])
        result = report["decisionMetrics"][0]
        self.assertEqual(result["epochs"]["baseline"], 3)
        self.assertEqual(result["turns"]["baseline"], 3)
        self.assertEqual(result["medianInputTokens"]["baseline"], 1000.0)
        self.assertEqual(result["decision"], "pass")

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

    def test_accepted_rotation_from_aborted_epoch_does_not_count(self) -> None:
        events = passing_events()
        for event in events:
            if event["epochId"] == "pilot-5" and event["event"] == "epoch_closed":
                event["outcome"] = "aborted"
        report = metrics.build_report([metrics.validate_event(item) for item in events])
        result = report["decisionMetrics"][0]
        self.assertEqual(result["epochs"]["pilot"], 4)
        self.assertEqual(result["acceptedRotations"], 4)
        self.assertEqual(result["decision"], "insufficient_data")

    def test_rolled_back_attempts_count_toward_first_five_regression_gate(self) -> None:
        events = passing_events()
        for number in (2, 4):
            for event in events:
                if event["event"] == "rotation_completed" and event["boundaryId"] == f"rotation-{number}":
                    event["result"] = "rolled_back"
                    event.pop("coldStartTurns")
                    break
            for event in events:
                if event["epochId"] == f"pilot-{number}" and event["event"] == "epoch_closed":
                    event["outcome"] = "aborted"
                    break
            events.append(
                base_event(
                    f"pilot-{number}",
                    "pilot",
                    "context_regression",
                    boundaryType="rotation",
                    boundaryId=f"rotation-{number}",
                    kind="constraint_miss",
                    impact="correction",
                    evidenceRef=f"SUP-{number:03d}",
                )
            )
        report = metrics.build_report([metrics.validate_event(item) for item in events])
        result = report["decisionMetrics"][0]
        self.assertEqual(result["acceptedRotations"], 3)
        self.assertEqual(result["decision"], "rollback")
        self.assertIn("two_context_regressions_in_first_five_rotations", result["rollbackReasons"])

    def test_unknown_field_is_rejected(self) -> None:
        event = base_event("baseline-1", "baseline", "epoch_started", note="do not store narrative")
        with self.assertRaisesRegex(metrics.MetricsError, "unknown fields"):
            metrics.validate_event(event)

    def test_content_bearing_fields_are_rejected_before_file_creation(self) -> None:
        prohibited = {
            "prompt": "user text",
            "reply": "assistant text",
            "path": "/private/source",
            "url": "https://example.invalid/private",
            "toolOutput": "command output",
            "diff": "sensitive patch",
            "credential": "secret",
            "userData": "personal data",
            "note": "narrative",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            for field, value in prohibited.items():
                with self.subTest(field=field):
                    path = Path(temp_dir) / f"{field}.jsonl"
                    event = base_event("baseline-1", "baseline", "epoch_started", **{field: value})
                    with self.assertRaisesRegex(metrics.MetricsError, "unknown fields"):
                        metrics.append_event(path, event)
                    self.assertFalse(path.exists())

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

    def test_concurrent_duplicate_event_id_has_one_winner(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            command = append_cli_args(path, "baseline-race", event_id="stable-event-id")
            processes = [
                subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                for _ in range(2)
            ]
            results = [process.communicate(timeout=15) + (process.returncode,) for process in processes]
            return_codes = sorted(result[2] for result in results)
            self.assertEqual(return_codes, [0, 2], results)
            self.assertEqual(len(metrics.load_events(path)), 1)

    def test_concurrent_cli_append_is_atomic_and_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            expected_ids = {f"concurrent-{number}:epoch_started" for number in range(12)}
            processes = [
                subprocess.Popen(
                    append_cli_args(path, f"concurrent-{number}"),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for number in range(12)
            ]
            results = [process.communicate(timeout=15) + (process.returncode,) for process in processes]
            self.assertTrue(all(result[2] == 0 for result in results), results)
            loaded = metrics.load_events(path)
            self.assertEqual({event["eventId"] for event in loaded}, expected_ids)
            self.assertEqual(len(loaded), len(expected_ids))
            self.assertTrue(path.read_bytes().endswith(b"\n"))
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_cli_validate_and_report_use_the_strict_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            for event in passing_events():
                metrics.append_event(path, event)
            script = str(Path(__file__).with_name("context_metrics.py"))
            validated = subprocess.run(
                [sys.executable, script, "validate", "--path", str(path)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(json.loads(validated.stdout), {"status": "valid", "events": len(passing_events())})
            reported = subprocess.run(
                [sys.executable, script, "report", "--path", str(path)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(json.loads(reported.stdout)["decisionMetrics"][0]["decision"], "pass")

    def test_malformed_and_partial_jsonl_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            malformed = Path(temp_dir) / "malformed.jsonl"
            malformed.write_bytes(b'{"schemaVersion":1')
            malformed.chmod(0o600)
            with self.assertRaisesRegex(metrics.MetricsError, "line 1"):
                metrics.load_events(malformed)

            partial = Path(temp_dir) / "partial.jsonl"
            partial.write_text(json.dumps(base_event("baseline-1", "baseline", "epoch_started")), encoding="utf-8")
            partial.chmod(0o600)
            with self.assertRaisesRegex(metrics.MetricsError, "partial JSONL line"):
                metrics.append_event(
                    partial,
                    base_event("baseline-2", "baseline", "epoch_started"),
                )

    def test_symlink_targets_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "target.jsonl"
            target.write_text(
                json.dumps(base_event("baseline-1", "baseline", "epoch_started")) + "\n",
                encoding="utf-8",
            )
            target.chmod(0o600)
            link = Path(temp_dir) / "events.jsonl"
            link.symlink_to(target)
            with self.assertRaisesRegex(metrics.MetricsError, "must not be a symlink"):
                metrics.load_events(link)
            with self.assertRaisesRegex(metrics.MetricsError, "must not be a symlink"):
                metrics.append_event(
                    link,
                    base_event("baseline-2", "baseline", "epoch_started"),
                )

    def test_unsafe_existing_permissions_are_rejected_then_tightened_on_append(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            path.write_text(
                json.dumps(base_event("baseline-1", "baseline", "epoch_started")) + "\n",
                encoding="utf-8",
            )
            path.chmod(0o644)
            with self.assertRaisesRegex(metrics.MetricsError, "must be user-only"):
                metrics.load_events(path)

            metrics.append_event(
                path,
                base_event("baseline-1", "baseline", "epoch_closed", outcome="completed"),
            )
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(len(metrics.load_events(path)), 2)

    def test_report_groups_roles_without_mixing_thread_identity(self) -> None:
        events: list[dict[str, object]] = []
        for role in ("architect", "supervisor"):
            epoch_id = f"{role}-baseline-1"
            events.extend(
                [
                    base_event(epoch_id, "baseline", "epoch_started", role=role),
                    base_event(
                        epoch_id,
                        "baseline",
                        "turn_completed",
                        eventId=f"{epoch_id}:turn:1",
                        role=role,
                        source="app_server",
                        turnIndex=1,
                        inputTokens=100,
                        cachedInputTokens=10,
                        totalTokens=120,
                    ),
                    base_event(epoch_id, "baseline", "epoch_closed", role=role, outcome="completed"),
                ]
            )
        validated = [metrics.validate_event(event) for event in events]
        metrics.validate_epoch_consistency(validated)
        groups = metrics.build_report(validated)["decisionMetrics"]
        self.assertEqual([group["group"]["role"] for group in groups], ["architect", "supervisor"])
        self.assertTrue(all(group["epochs"]["baseline"] == 1 for group in groups))

        changed_thread = dict(validated[1], threadRef="other-thread")
        with self.assertRaisesRegex(metrics.MetricsError, "changes mode, role, cohort"):
            metrics.validate_epoch_consistency([validated[0], changed_thread])

    def test_small_ledger_append_latency_stays_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            started = time.perf_counter()
            for number in range(64):
                metrics.append_event(
                    path,
                    base_event(f"latency-{number}", "baseline", "epoch_started"),
                )
            elapsed = time.perf_counter() - started
            self.assertEqual(len(metrics.load_events(path)), 64)
            self.assertLess(elapsed, 5.0, f"64 durable appends took {elapsed:.3f}s")

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
