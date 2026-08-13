#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

import app_server_usage_adapter as app_adapter
import context_metrics as metrics
import desktop_rollout_usage_adapter as desktop_adapter

THREAD_ID = "019ff6aa-1234-7abc-8def-0123456789ab"


def identity(epoch_id: str = "architect-desktop-b01") -> app_adapter.EpochIdentity:
    return app_adapter.EpochIdentity(
        epoch_id=epoch_id,
        thread_ref="architect-desktop-01",
        mode="baseline",
        role="architect",
        cohort="outcome-batch",
        model="gpt-5.6-sol",
        reasoning="ultra",
    )


def rollout_path(root: Path) -> Path:
    path = root / "2026" / "08" / "12" / f"rollout-test-{THREAD_ID}.jsonl"
    path.parent.mkdir(parents=True)
    return path


def session_meta(thread_id: str = THREAD_ID) -> dict[str, object]:
    return {
        "type": "session_meta",
        "payload": {"id": thread_id, "session_id": thread_id},
    }


def task_started(turn_id: str = "turn-1") -> dict[str, object]:
    return {
        "type": "event_msg",
        "payload": {"type": "task_started", "turn_id": turn_id, "started_at": 1},
    }


def turn_context(
    turn_id: str = "turn-1",
    *,
    model: str = "gpt-5.6-sol",
    effort: str = "ultra",
) -> dict[str, object]:
    return {
        "type": "turn_context",
        "payload": {"turn_id": turn_id, "model": model, "effort": effort},
    }


def token_count(
    *, input_tokens: int = 120, cached_input_tokens: int = 80, total_tokens: int = 150
) -> dict[str, object]:
    return {
        "type": "event_msg",
        "payload": {
            "type": "token_count",
            "info": {
                "last_token_usage": {
                    "input_tokens": input_tokens,
                    "cached_input_tokens": cached_input_tokens,
                    "output_tokens": total_tokens - input_tokens,
                    "reasoning_output_tokens": 0,
                    "total_tokens": total_tokens,
                },
                "total_token_usage": {"content": "must-not-be-read"},
            },
            "rate_limits": {"private": "must-not-be-recorded"},
        },
    }


def terminal(
    turn_id: str = "turn-1",
    event_type: str = "task_complete",
    *,
    error: object | None = None,
) -> dict[str, object]:
    record: dict[str, object] = {
        "type": "event_msg",
        "payload": {
            "type": event_type,
            "turn_id": turn_id,
            "completed_at": 1786492800,
            "last_agent_message": "private-final-answer",
        },
    }
    if error is not None:
        record["payload"]["error"] = error  # type: ignore[index]
    return record


def write_records(path: Path, records: list[dict[str, object]], *, append: bool = False) -> None:
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, separators=(",", ":")) + "\n")


class DesktopRolloutUsageAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "sessions"
        self.root.mkdir()
        self.external = Path(self.temp.name) / "private"
        self.arm_path = self.external / "armed.json"
        self.metrics_path = self.external / "events.jsonl"

    def arm(self, epoch_identity: app_adapter.EpochIdentity | None = None) -> None:
        desktop_adapter.arm_epoch(
            sessions_root=self.root,
            thread_id=THREAD_ID,
            arm_path=self.arm_path,
            metrics_path=self.metrics_path,
            identity=epoch_identity or identity(),
        )

    def collect(
        self, outcome: str | None = None, *, writer_release_proven: bool = False
    ) -> dict[str, int | str | bool]:
        return desktop_adapter.collect_epoch(
            sessions_root=self.root,
            thread_id=THREAD_ID,
            arm_path=self.arm_path,
            metrics_path=self.metrics_path,
            outcome=outcome,
            writer_release_proven=writer_release_proven,
        )

    def test_arm_refuses_an_existing_rollout_without_starting_epoch(self) -> None:
        write_records(rollout_path(self.root), [session_meta(), task_started()])
        with self.assertRaisesRegex(desktop_adapter.DesktopRolloutError, "already exists"):
            self.arm()
        self.assertFalse(self.arm_path.exists())
        self.assertFalse(self.metrics_path.exists())

    def test_collect_is_private_idempotent_and_closes_only_at_terminal_boundary(self) -> None:
        self.arm()
        path = rollout_path(self.root)
        secret = "private-prompt-response-tool-path-token"
        write_records(
            path,
            [
                {
                    "type": "session_meta",
                    "payload": {"id": THREAD_ID, "session_id": THREAD_ID, "cwd": secret},
                },
                task_started(),
                {"type": "response_item", "payload": {"type": "message", "text": secret}},
                turn_context(),
                token_count(input_tokens=90, cached_input_tokens=50, total_tokens=110),
                token_count(input_tokens=120, cached_input_tokens=80, total_tokens=150),
                terminal(),
            ],
        )
        first = self.collect()
        second = self.collect()
        self.assertEqual(first["appendedTurns"], 1)
        self.assertEqual(second["appendedTurns"], 0)
        self.assertEqual(second["duplicateTurns"], 1)
        events = metrics.load_events(self.metrics_path)
        turns = [event for event in events if event["event"] == "turn_completed"]
        self.assertEqual(len(turns), 1)
        self.assertEqual(turns[0]["inputTokens"], 120)
        self.assertEqual(turns[0]["cachedInputTokens"], 80)
        self.assertEqual(turns[0]["totalTokens"], 150)
        raw_metrics = self.metrics_path.read_text(encoding="utf-8")
        self.assertNotIn(secret, raw_metrics)
        self.assertNotIn(THREAD_ID, raw_metrics)
        self.assertNotIn("turn-1", raw_metrics)
        self.assertNotIn(str(path), raw_metrics)
        self.assertEqual(stat.S_IMODE(self.metrics_path.stat().st_mode), 0o600)

        with self.assertRaisesRegex(desktop_adapter.DesktopRolloutError, "release proof"):
            self.collect("completed")
        closed = self.collect("completed", writer_release_proven=True)
        self.assertTrue(closed["epochClosed"])
        self.assertFalse(self.arm_path.exists())
        closes = [event for event in metrics.load_events(self.metrics_path) if event["event"] == "epoch_closed"]
        self.assertEqual([event["outcome"] for event in closes], ["completed"])

    def test_open_turn_is_not_recorded_and_cannot_close_epoch(self) -> None:
        self.arm()
        path = rollout_path(self.root)
        write_records(path, [session_meta(), task_started(), turn_context(), token_count()])
        result = self.collect()
        self.assertTrue(result["openTurn"])
        self.assertEqual(result["appendedTurns"], 0)
        with self.assertRaisesRegex(desktop_adapter.DesktopRolloutError, "turn is active"):
            self.collect("completed", writer_release_proven=True)
        write_records(path, [terminal()], append=True)
        result = self.collect("completed", writer_release_proven=True)
        self.assertEqual(result["appendedTurns"], 1)
        self.assertTrue(result["epochClosed"])

    def test_not_achieved_requires_release_proof_before_inconclusive_rotation(self) -> None:
        self.arm()
        write_records(
            rollout_path(self.root),
            [session_meta(), task_started(), turn_context(), token_count(), terminal()],
        )
        self.collect()
        with self.assertRaisesRegex(desktop_adapter.DesktopRolloutError, "release proof"):
            self.collect("not_achieved")

        closed = self.collect("not_achieved", writer_release_proven=True)
        self.assertTrue(closed["epochClosed"])
        events = metrics.load_events(self.metrics_path)
        closes = [event for event in events if event["event"] == "epoch_closed"]
        self.assertEqual(
            [(event["schemaVersion"], event["outcome"]) for event in closes],
            [(2, "not_achieved")],
        )
        rotation = identity().base_event(
            "rotation_completed",
            "rotation:desktop-not-achieved",
            "manual",
        )
        rotation.update(
            {
                "boundaryId": "handoff-desktop-not-achieved",
                "result": "inconclusive",
            }
        )
        metrics.append_event(self.metrics_path, rotation)
        events = metrics.load_events(self.metrics_path)
        self.assertEqual(
            [event["result"] for event in events if event["event"] == "rotation_completed"],
            ["inconclusive"],
        )

    def test_route_mismatch_fails_closed(self) -> None:
        self.arm()
        write_records(
            rollout_path(self.root),
            [session_meta(), task_started(), turn_context(model="gpt-5.6-luna", effort="max"), token_count(), terminal()],
        )
        with self.assertRaisesRegex(desktop_adapter.DesktopRolloutError, "route does not match"):
            self.collect()
        self.assertFalse(
            any(event["event"] == "turn_completed" for event in metrics.load_events(self.metrics_path))
        )

    def test_compaction_is_recorded_once_without_replacement_content(self) -> None:
        self.arm()
        secret = "private-compaction-summary"
        write_records(
            rollout_path(self.root),
            [
                session_meta(),
                task_started(),
                turn_context(),
                token_count(),
                terminal(),
                {
                    "type": "compacted",
                    "payload": {
                        "window_id": "window-private-id",
                        "window_number": 1,
                        "message": secret,
                        "replacement_history": [{"text": secret}],
                    },
                },
            ],
        )
        first = self.collect()
        second = self.collect()
        self.assertEqual(first["appendedCompactions"], 1)
        self.assertEqual(second["appendedCompactions"], 0)
        raw_metrics = self.metrics_path.read_text(encoding="utf-8")
        self.assertNotIn(secret, raw_metrics)
        self.assertNotIn("window-private-id", raw_metrics)
        compacted = [event for event in metrics.load_events(self.metrics_path) if event["event"] == "compacted"]
        self.assertEqual([event["generation"] for event in compacted], [1])

    def test_aborted_turn_is_skipped(self) -> None:
        self.arm()
        write_records(
            rollout_path(self.root),
            [session_meta(), task_started(), token_count(), terminal(event_type="turn_aborted")],
        )
        result = self.collect("aborted")
        self.assertEqual(result["skippedTerminalTurns"], 1)
        self.assertFalse(
            any(event["event"] == "turn_completed" for event in metrics.load_events(self.metrics_path))
        )

    def test_failed_task_complete_is_not_counted(self) -> None:
        self.arm()
        write_records(
            rollout_path(self.root),
            [
                session_meta(),
                task_started(),
                turn_context(),
                token_count(),
                terminal(error={"private": "do-not-record"}),
            ],
        )
        result = self.collect("aborted")
        self.assertEqual(result["skippedTerminalTurns"], 1)
        raw_metrics = self.metrics_path.read_text(encoding="utf-8")
        self.assertNotIn("do-not-record", raw_metrics)

    def test_rollout_session_identity_must_match(self) -> None:
        self.arm()
        other = "019ff6aa-9999-7abc-8def-0123456789ab"
        write_records(
            rollout_path(self.root),
            [session_meta(other), task_started(), turn_context(), token_count(), terminal()],
        )
        with self.assertRaisesRegex(desktop_adapter.DesktopRolloutError, "metadata does not match"):
            self.collect()

    def test_wrong_thread_and_insecure_arm_state_are_rejected(self) -> None:
        self.arm()
        other = "019ff6aa-9999-7abc-8def-0123456789ab"
        with self.assertRaisesRegex(desktop_adapter.DesktopRolloutError, "does not match"):
            desktop_adapter.collect_epoch(
                sessions_root=self.root,
                thread_id=other,
                arm_path=self.arm_path,
                metrics_path=self.metrics_path,
                outcome=None,
                writer_release_proven=False,
            )
        os.chmod(self.arm_path, 0o644)
        with self.assertRaisesRegex(desktop_adapter.DesktopRolloutError, "user-only"):
            self.collect()

    def test_malformed_rollout_error_does_not_echo_content(self) -> None:
        self.arm()
        path = rollout_path(self.root)
        path.write_text('{"secret":"do-not-echo"', encoding="utf-8")
        with self.assertRaisesRegex(desktop_adapter.DesktopRolloutError, "line 1") as raised:
            self.collect()
        self.assertNotIn("do-not-echo", str(raised.exception))

if __name__ == "__main__":
    unittest.main()
