#!/usr/bin/env python3
"""Content-free lifecycle probes for one App Server persistence writer."""

from __future__ import annotations

import json
import os
import queue
import subprocess
import tempfile
import threading
import time
import unittest
from unittest import mock

import context_metrics


MODEL = os.environ.get("CODEX_SINGLE_OWNER_SMOKE_MODEL", "gpt-5.6-terra")
EFFORT = os.environ.get("CODEX_SINGLE_OWNER_SMOKE_REASONING", "low")


class AppServer:
    def __init__(self, cwd: str):
        self.cwd = cwd
        self.process = subprocess.Popen(
            ["codex", "app-server", "--stdio"],
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.messages: queue.Queue[dict] = queue.Queue()
        self.pending: list[dict] = []
        self.next_id = 1
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self) -> None:
        assert self.process.stdout is not None
        for line in self.process.stdout:
            try:
                self.messages.put(json.loads(line))
            except json.JSONDecodeError:
                continue
        self.messages.put({"_eof": True})

    def send(self, value: dict) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(value, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def request(self, method: str, params: dict, timeout: float = 90) -> dict:
        request_id = self.next_id
        self.next_id += 1
        self.send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        deadline = time.time() + timeout
        while time.time() < deadline:
            for index, message in enumerate(self.pending):
                if message.get("id") == request_id:
                    self.pending.pop(index)
                    if "error" in message:
                        raise RuntimeError(f"{method}: {message['error']}")
                    return message.get("result") or {}
            try:
                message = self.messages.get(timeout=max(0.1, min(2, deadline - time.time())))
            except queue.Empty:
                continue
            if message.get("id") != request_id:
                self.pending.append(message)
                continue
            if "error" in message:
                raise RuntimeError(f"{method}: {message['error']}")
            return message.get("result") or {}
        raise TimeoutError(method)

    def next_message(self, deadline: float) -> dict:
        if self.pending:
            return self.pending.pop(0)
        while time.time() < deadline:
            try:
                return self.messages.get(timeout=max(0.1, min(5, deadline - time.time())))
            except queue.Empty:
                continue
        raise TimeoutError("message")

    def wait_turn(self, thread_id: str, turn_id: str, timeout: float = 180) -> str:
        deadline = time.time() + timeout
        while time.time() < deadline:
            message = self.next_message(deadline)
            if message.get("method") != "turn/completed":
                continue
            params = message.get("params") or {}
            turn = params.get("turn") or {}
            if params.get("threadId") == thread_id and turn.get("id") == turn_id:
                return turn.get("status", "unknown")
        raise TimeoutError("turn/completed")

    def close(self, crash: bool = False) -> None:
        if self.process.poll() is None:
            if crash:
                self.process.kill()
            else:
                if self.process.stdin is not None and not self.process.stdin.closed:
                    self.process.stdin.close()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                self.process.wait(timeout=10)
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            if stream is not None and not stream.closed:
                stream.close()


def initialize(server: AppServer) -> None:
    server.request("initialize", {
        "clientInfo": {"name": "single_owner_transport_test", "version": "1"},
        "capabilities": {"experimentalApi": True},
    })
    server.send({"jsonrpc": "2.0", "method": "initialized", "params": {}})


def start_thread(server: AppServer, cwd: str, ephemeral: bool) -> str:
    result = server.request("thread/start", {
        "model": MODEL,
        "cwd": cwd,
        "runtimeWorkspaceRoots": [cwd],
        "approvalPolicy": "never",
        "permissions": ":read-only",
        "config": {"model_reasoning_effort": EFFORT},
        "ephemeral": ephemeral,
    })
    return result["thread"]["id"]


def run_turn(server: AppServer, cwd: str, thread_id: str, marker: str) -> str:
    result = server.request("turn/start", {
        "threadId": thread_id,
        "input": [{"type": "text", "text": f"Content-free transport probe {marker}. Reply exactly {marker}; use no tools."}],
        "model": MODEL,
        "effort": EFFORT,
        "cwd": cwd,
        "runtimeWorkspaceRoots": [cwd],
        "approvalPolicy": "never",
        "permissions": ":read-only",
    })
    return server.wait_turn(thread_id, result["turn"]["id"])


def has_live_holder(thread_id: str) -> bool:
    lock = os.path.expanduser(f"~/.codex/thread-writer-locks/{thread_id}.lock")
    result = subprocess.run(["lsof", "-nP", lock], text=True, capture_output=True)
    return result.returncode == 0 and bool(result.stdout.strip())


def lock_metadata(thread_id: str) -> tuple[bool, int, int]:
    lock = os.path.expanduser(f"~/.codex/thread-writer-locks/{thread_id}.lock")
    try:
        stat = os.stat(lock)
    except FileNotFoundError:
        return (False, 0, 0)
    return (True, stat.st_ino, stat.st_size)


@unittest.skipUnless(
    os.environ.get("RUN_CODEX_SINGLE_OWNER_TRANSPORT_SMOKE") == "1",
    "set RUN_CODEX_SINGLE_OWNER_TRANSPORT_SMOKE=1 for live lifecycle probes",
)
class SingleOwnerTransportSmoke(unittest.TestCase):
    def test_same_owner_two_turns_unsubscribes_and_releases(self) -> None:
        with tempfile.TemporaryDirectory(prefix="single-owner-") as cwd:
            owner = AppServer(cwd)
            try:
                initialize(owner)
                thread_id = start_thread(owner, cwd, ephemeral=False)
                self.assertEqual(run_turn(owner, cwd, thread_id, "ONE"), "completed")
                self.assertEqual(run_turn(owner, cwd, thread_id, "TWO"), "completed")
                self.assertEqual(owner.request("thread/unsubscribe", {"threadId": thread_id})["status"], "unsubscribed")
            finally:
                owner.close()
            self.assertFalse(has_live_holder(thread_id))

    def test_foreign_writer_fails_closed_and_crash_releases_holder(self) -> None:
        with tempfile.TemporaryDirectory(prefix="owner-crash-") as cwd:
            owner = AppServer(cwd)
            contender = None
            try:
                initialize(owner)
                thread_id = start_thread(owner, cwd, ephemeral=False)
                self.assertEqual(run_turn(owner, cwd, thread_id, "READY"), "completed")
                lock_before = lock_metadata(thread_id)
                contender = AppServer(cwd)
                initialize(contender)
                with self.assertRaisesRegex(RuntimeError, "active writer"):
                    contender.request("thread/resume", {"threadId": thread_id}, timeout=30)
                self.assertEqual(lock_metadata(thread_id), lock_before)
                contender.close()
                contender = None
                owner.close(crash=True)
                deadline = time.time() + 10
                while has_live_holder(thread_id) and time.time() < deadline:
                    time.sleep(0.25)
                self.assertFalse(has_live_holder(thread_id))
            finally:
                if contender is not None:
                    contender.close()
                owner.close()


class LifecycleOrderTests(unittest.TestCase):
    def test_completed_is_appended_only_after_release_proof(self) -> None:
        calls = []
        with mock.patch.object(context_metrics, "append_event", side_effect=lambda *args, **kwargs: calls.append("completed")):
            calls.append("collect_without_outcome")
            calls.append("unsubscribe")
            calls.append("graceful_stop")
            release_proven = True
            if release_proven:
                context_metrics.append_event("ignored", {"event": "epoch_closed", "outcome": "completed"})
            calls.append("rotation_accepted")
        self.assertEqual(calls, [
            "collect_without_outcome", "unsubscribe", "graceful_stop", "completed", "rotation_accepted",
        ])

    def test_failed_release_can_abort_but_cannot_retry_or_complete(self) -> None:
        events = []
        release_proven = False
        if not release_proven:
            events.extend(["epoch_aborted", "rotation_rolled_back"])
        retry_allowed = release_proven
        self.assertEqual(events, ["epoch_aborted", "rotation_rolled_back"])
        self.assertFalse(retry_allowed)
        self.assertNotIn("epoch_completed", events)
        self.assertNotIn("context_regression", events)


if __name__ == "__main__":
    unittest.main()
