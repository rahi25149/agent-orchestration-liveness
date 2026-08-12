#!/usr/bin/env python3

from __future__ import annotations

import io
import json
import os
import select
import shutil
import stat
import subprocess
import tempfile
import time
import unittest
import uuid
from pathlib import Path

import app_server_usage_adapter as adapter_module
import context_metrics as metrics


def identity(epoch_id: str = "architect-baseline-1") -> adapter_module.EpochIdentity:
    return adapter_module.EpochIdentity(
        epoch_id=epoch_id,
        thread_ref="architect-local-1",
        mode="baseline",
        role="architect",
        cohort="outcome-batch",
        model="gpt-5.6-terra",
        reasoning="low",
    )


def usage_message(
    *,
    thread_id: str = "raw-thread-1",
    turn_id: str = "raw-turn-1",
    input_tokens: int = 100,
    cached_input_tokens: int = 20,
    total_tokens: int = 130,
) -> dict[str, object]:
    return {
        "method": "thread/tokenUsage/updated",
        "params": {
            "threadId": thread_id,
            "turnId": turn_id,
            "tokenUsage": {
                "last": {
                    "inputTokens": input_tokens,
                    "cachedInputTokens": cached_input_tokens,
                    "outputTokens": total_tokens - input_tokens,
                    "reasoningOutputTokens": 0,
                    "totalTokens": total_tokens,
                },
                "total": {
                    "inputTokens": input_tokens,
                    "cachedInputTokens": cached_input_tokens,
                    "outputTokens": total_tokens - input_tokens,
                    "reasoningOutputTokens": 0,
                    "totalTokens": total_tokens,
                },
            },
        },
    }


def terminal_message(
    *,
    thread_id: str = "raw-thread-1",
    turn_id: str = "raw-turn-1",
    status: str = "completed",
) -> dict[str, object]:
    return {
        "method": "turn/completed",
        "params": {
            "threadId": thread_id,
            "turn": {
                "id": turn_id,
                "items": [{"type": "agentMessage", "text": "must never be recorded"}],
                "status": status,
                "completedAt": 1786492800,
            },
        },
    }


class AppServerUsageAdapterTests(unittest.TestCase):
    def test_latest_usage_is_written_once_only_after_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            adapter = adapter_module.AppServerUsageAdapter(path, identity())
            adapter.consume(usage_message(input_tokens=80, cached_input_tokens=10, total_tokens=100))
            self.assertEqual(len(metrics.load_events(path)), 1)
            adapter.consume(usage_message(input_tokens=120, cached_input_tokens=20, total_tokens=150))
            adapter.consume(terminal_message())
            summary = adapter.finalize()
            events = metrics.load_events(path)
            turns = [event for event in events if event["event"] == "turn_completed"]
            self.assertEqual(summary["usageUpdates"], 2)
            self.assertEqual(summary["appendedTurns"], 1)
            self.assertEqual(len(turns), 1)
            self.assertEqual(turns[0]["inputTokens"], 120)
            self.assertEqual(turns[0]["cachedInputTokens"], 20)
            self.assertEqual(turns[0]["totalTokens"], 150)
            self.assertNotIn("raw-thread-1", path.read_text(encoding="utf-8"))
            self.assertNotIn("raw-turn-1", path.read_text(encoding="utf-8"))
            self.assertNotIn("must never be recorded", path.read_text(encoding="utf-8"))
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_usage_after_terminal_is_coalesced(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            adapter = adapter_module.AppServerUsageAdapter(path, identity())
            adapter.consume(terminal_message())
            adapter.consume(usage_message())
            self.assertEqual(adapter.finalize()["appendedTurns"], 1)

    def test_replay_is_idempotent_across_adapter_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            first = adapter_module.AppServerUsageAdapter(path, identity())
            first.consume(usage_message())
            first.consume(terminal_message())
            first.finalize()
            second = adapter_module.AppServerUsageAdapter(path, identity())
            second.consume(usage_message())
            second.consume(terminal_message())
            summary = second.finalize()
            turns = [event for event in metrics.load_events(path) if event["event"] == "turn_completed"]
            self.assertEqual(len(turns), 1)
            self.assertEqual(summary["duplicateTurns"], 1)
            self.assertEqual(summary["appendedTurns"], 0)

    def test_different_thread_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            adapter = adapter_module.AppServerUsageAdapter(path, identity())
            adapter.consume(usage_message())
            with self.assertRaisesRegex(adapter_module.AdapterError, "multiple App Server threads"):
                adapter.consume(terminal_message(thread_id="raw-thread-2"))

    def test_incomplete_stream_fails_without_turn_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            adapter = adapter_module.AppServerUsageAdapter(path, identity())
            adapter.consume(usage_message())
            with self.assertRaisesRegex(adapter_module.AdapterError, "before the matching turn completed"):
                adapter.finalize()
            self.assertFalse(any(event["event"] == "turn_completed" for event in metrics.load_events(path)))

    def test_failed_turn_is_not_counted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            adapter = adapter_module.AppServerUsageAdapter(path, identity())
            adapter.consume(usage_message())
            adapter.consume(terminal_message(status="failed"))
            summary = adapter.finalize()
            self.assertEqual(summary["skippedTerminalTurns"], 1)
            self.assertFalse(any(event["event"] == "turn_completed" for event in metrics.load_events(path)))

    def test_content_messages_are_ignored_and_not_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            adapter = adapter_module.AppServerUsageAdapter(path, identity())
            secret = "sensitive-prompt-response-tool-diff"
            adapter.consume(
                {
                    "method": "item/completed",
                    "params": {"item": {"text": secret, "diff": secret, "aggregatedOutput": secret}},
                }
            )
            adapter.consume(usage_message())
            adapter.consume(terminal_message())
            adapter.finalize()
            self.assertNotIn(secret, path.read_text(encoding="utf-8"))

    def test_model_reroute_requires_a_new_epoch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter = adapter_module.AppServerUsageAdapter(Path(temp_dir) / "events.jsonl", identity())
            with self.assertRaisesRegex(adapter_module.AdapterError, "model reroute observed"):
                adapter.consume(
                    {
                        "method": "model/rerouted",
                        "params": {"fromModel": "gpt-5.6-terra", "toModel": "another-model"},
                    }
                )

    def test_metrics_path_inside_git_repository_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".git").mkdir()
            with self.assertRaisesRegex(adapter_module.AdapterError, "outside every Git repository"):
                adapter_module.AppServerUsageAdapter(root / "private" / "events.jsonl", identity())

    def test_observe_stream_rejects_malformed_json_without_echoing_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter = adapter_module.AppServerUsageAdapter(Path(temp_dir) / "events.jsonl", identity())
            with self.assertRaisesRegex(adapter_module.AdapterError, "line 1 is not valid") as raised:
                adapter_module.observe_stream(io.StringIO('{"private":"do-not-echo"'), adapter)
            self.assertNotIn("do-not-echo", str(raised.exception))


@unittest.skipUnless(
    os.environ.get("RUN_CODEX_APP_SERVER_SMOKE") == "1",
    "set RUN_CODEX_APP_SERVER_SMOKE=1 for the real App Server turn",
)
class LiveAppServerUsageAdapterTest(unittest.TestCase):
    def test_real_terminal_turn_writes_one_safe_usage_record(self) -> None:
        codex = shutil.which("codex")
        if codex is None:
            self.skipTest("codex executable is unavailable")
        smoke_model = os.environ.get("CODEX_APP_SERVER_SMOKE_MODEL", "gpt-5.4-mini")
        smoke_reasoning = os.environ.get("CODEX_APP_SERVER_SMOKE_REASONING", "low")
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            process = subprocess.Popen(
                [codex, "app-server", "--stdio"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
            )
            self.addCleanup(self._stop_process, process)
            deadline = time.monotonic() + 45
            try:
                self._request(
                    process,
                    {
                        "method": "initialize",
                        "id": 1,
                        "params": {
                            "clientInfo": {
                                "name": "orchestration_metrics_phase1",
                                "title": "Orchestration Metrics Phase 1",
                                "version": "0.1.0",
                            }
                        },
                    },
                    deadline,
                )
                self._send(process, {"method": "initialized", "params": {}})
                started = self._request(
                    process,
                    {
                        "method": "thread/start",
                        "id": 2,
                        "params": {
                            "cwd": "/tmp",
                            "ephemeral": True,
                            "approvalPolicy": "never",
                            "sandbox": "read-only",
                            "model": smoke_model,
                            "baseInstructions": "Reply concisely and do not use tools.",
                            "developerInstructions": "",
                        },
                    },
                    deadline,
                )
                thread_id = started["thread"]["id"]
                epoch_id = f"adapter-smoke-{uuid.uuid4().hex[:12]}"
                live_identity = adapter_module.EpochIdentity(
                    epoch_id=epoch_id,
                    thread_ref="adapter-smoke-local",
                    mode="baseline",
                    role="architect",
                    cohort="adapter-smoke",
                    model=smoke_model,
                    reasoning=smoke_reasoning,
                )
                adapter = adapter_module.AppServerUsageAdapter(path, live_identity)
                self._request(
                    process,
                    {
                        "method": "turn/start",
                        "id": 3,
                        "params": {
                            "threadId": thread_id,
                            "input": [{"type": "text", "text": "Reply with exactly PHASE1_OK."}],
                            "model": smoke_model,
                            "effort": smoke_reasoning,
                        },
                    },
                    deadline,
                    adapter=adapter,
                )
                terminal_seen = adapter.stats.terminal_notifications > 0
                while not terminal_seen or adapter.stats.appended_turns != 1:
                    message = self._receive(process, deadline)
                    adapter.consume(message)
                    if message.get("method") == "turn/completed":
                        terminal_seen = True
                summary = adapter.finalize()
                events = metrics.load_events(path)
                turns = [event for event in events if event["event"] == "turn_completed"]
                self.assertEqual(summary["appendedTurns"], 1)
                self.assertEqual(len(turns), 1)
                self.assertGreater(turns[0]["inputTokens"], 0)
                self.assertGreater(turns[0]["totalTokens"], 0)
                raw_log = path.read_text(encoding="utf-8")
                self.assertNotIn(thread_id, raw_log)
                self.assertNotIn("PHASE1_OK", raw_log)
            finally:
                self._stop_process(process)

    @staticmethod
    def _send(process: subprocess.Popen[str], message: dict[str, object]) -> None:
        assert process.stdin is not None
        process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        process.stdin.flush()

    @classmethod
    def _request(
        cls,
        process: subprocess.Popen[str],
        message: dict[str, object],
        deadline: float,
        adapter: adapter_module.AppServerUsageAdapter | None = None,
    ) -> dict[str, object]:
        cls._send(process, message)
        while True:
            response = cls._receive(process, deadline)
            if adapter is not None:
                adapter.consume(response)
            if response.get("id") == message["id"] and "method" not in response:
                if "error" in response:
                    raise AssertionError("App Server request failed")
                return response["result"]

    @staticmethod
    def _receive(process: subprocess.Popen[str], deadline: float) -> dict[str, object]:
        assert process.stdout is not None
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise AssertionError("App Server smoke timed out")
        ready, _, _ = select.select([process.stdout], [], [], remaining)
        if not ready:
            raise AssertionError("App Server smoke timed out")
        line = process.stdout.readline()
        if not line:
            raise AssertionError("App Server closed before terminal completion")
        return json.loads(line)

    @staticmethod
    def _stop_process(process: subprocess.Popen[str]) -> None:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        for handle in (process.stdin, process.stdout):
            if handle is not None and not handle.closed:
                handle.close()


if __name__ == "__main__":
    unittest.main()
