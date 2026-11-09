#!/usr/bin/env python3
"""Event-driven Herdr agent status watcher.

Watches Herdr agent panes for status transitions using Herdr's UNIX domain socket API
and events.subscribe.
"""

from __future__ import annotations

import argparse
import json
import os
import select
import socket
import sys
import time
from typing import Any
import uuid


def parse_until_states(
    until_input: str | list[str] | set[str] | tuple[str, ...]
) -> set[str]:
    """Parse comma-separated or collection of target status names into a lowercase set."""
    if isinstance(until_input, (list, tuple, set)):
        result = set()
        for item in until_input:
            for part in str(item).split(","):
                part = part.strip().lower()
                if part:
                    result.add(part)
        return result
    return {s.strip().lower() for s in str(until_input).split(",") if s.strip()}


class HerdrWatcher:
    """Event-driven watcher for Herdr agent status transitions."""

    def __init__(
        self,
        socket_path: str | None = None,
        sock: socket.socket | None = None,
    ) -> None:
        self.socket_path = socket_path or os.environ.get("HERDR_SOCKET_PATH")
        self.sock = sock
        if not self.sock and not self.socket_path:
            raise ValueError(
                "HERDR_SOCKET_PATH not set and no socket_path provided"
            )

    def connect(self) -> socket.socket:
        """Connect to the Herdr UNIX domain socket."""
        if self.sock is not None:
            return self.sock
        if not self.socket_path:
            raise ValueError("No socket path configured")
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self.socket_path)
        return sock

    @staticmethod
    def _send_request(
        sock: socket.socket, method: str, params: dict[str, Any]
    ) -> str:
        req_id = uuid.uuid4().hex
        payload = json.dumps({"id": req_id, "method": method, "params": params}) + "\n"
        sock.sendall(payload.encode("utf-8"))
        return req_id

    def resolve_targets(
        self,
        sock: socket.socket,
        lanes: list[str],
        buffer: str = "",
        timeout: float = 10.0,
    ) -> tuple[dict[str, str], dict[str, Any], str]:
        """Resolve lane or agent names to pane_ids using agent.list.

        Returns (lane_to_pane, resolved_agents_by_lane, remaining_buffer).
        """
        req_id = self._send_request(sock, "agent.list", {})
        deadline = time.monotonic() + timeout

        agents: list[dict[str, Any]] | None = None
        while agents is None:
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                msg = json.loads(line)
                if msg.get("id") == req_id:
                    if "error" in msg:
                        raise RuntimeError(f"agent.list failed: {msg['error']}")
                    agents = msg.get("result", {}).get("agents", [])
                    break

            if agents is not None:
                break

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Timed out waiting for agent.list response")

            r, _, _ = select.select([sock], [], [], min(remaining, 0.5))
            if not r:
                continue

            chunk = sock.recv(4096)
            if not chunk:
                raise ConnectionError(
                    "Socket closed while waiting for agent.list response"
                )
            buffer += chunk.decode("utf-8")

        lane_to_pane: dict[str, str] = {}
        resolved_agents: dict[str, Any] = {}

        for lane in lanes:
            matched: dict[str, Any] | None = None
            for a in agents:
                if (
                    a.get("name") == lane
                    or a.get("agent") == lane
                    or a.get("pane_id") == lane
                    or a.get("display_agent") == lane
                    or a.get("title") == lane
                    or a.get("terminal_title") == lane
                    or a.get("terminal_title_stripped") == lane
                ):
                    matched = a
                    break
            if matched is None:
                raise ValueError(
                    f"Target lane/agent '{lane}' not found in agent.list"
                )

            pane_id = matched.get("pane_id")
            if not pane_id:
                raise ValueError(
                    f"Target '{lane}' has no pane_id in agent.list entry: {matched}"
                )

            lane_to_pane[lane] = pane_id
            resolved_agents[lane] = matched

        return lane_to_pane, resolved_agents, buffer

    def watch(
        self,
        lanes: list[str],
        until: str | list[str] | set[str] | tuple[str, ...] = (
            "idle",
            "done",
            "blocked",
        ),
        timeout: float = 600.0,
        receipt_prefix: str | None = None,
        require_all: bool = False,
    ) -> dict[str, Any]:
        """Watch lanes until any (or all) enters one of the specified until states.

        Returns structured match dictionary.
        """
        until_set = parse_until_states(until)
        owned_socket = False
        sock = self.sock
        if sock is None:
            sock = self.connect()
            owned_socket = True

        buffer = ""
        try:
            # 1. Resolve targets
            lane_to_pane, resolved_agents, buffer = self.resolve_targets(
                sock, lanes, buffer=buffer, timeout=min(timeout, 10.0)
            )

            # 2. Polling loop with receipt verification
            import subprocess

            start_time = time.monotonic()
            deadline = start_time + timeout
            completed_lanes: set[str] = set()

            while time.monotonic() < deadline:
                time.sleep(2.0)
                proc = subprocess.run(
                    ["herdr", "agent", "list"], capture_output=True, text=True
                )
                if proc.returncode == 0:
                    try:
                        data = json.loads(proc.stdout)
                        cur_agents = data.get("result", {}).get("agents", [])
                        for lane in lanes:
                            if lane in completed_lanes:
                                continue
                            for a in cur_agents:
                                if (
                                    a.get("name") == lane
                                    or a.get("pane_id") == lane
                                ):
                                    st = a.get("agent_status", "")
                                    if st.lower() == "blocked":
                                        return {
                                            "matched": True,
                                            "lane": lane,
                                            "pane_id": a.get("pane_id", ""),
                                            "status": st,
                                            "reason": "blocked_detected",
                                            "data": a,
                                        }
                                    if st.lower() in until_set:
                                        if receipt_prefix:
                                            rf = f"{receipt_prefix}{lane}-result.md"
                                            if not os.path.exists(rf):
                                                continue
                                        if require_all:
                                            completed_lanes.add(lane)
                                            if set(lanes) == completed_lanes:
                                                return {
                                                    "matched": True,
                                                    "lanes": list(completed_lanes),
                                                    "status": "all_completed",
                                                    "reason": "receipt_verified",
                                                }
                                        else:
                                            return {
                                                "matched": True,
                                                "lane": lane,
                                                "pane_id": a.get("pane_id", ""),
                                                "status": st,
                                                "reason": "event_received",
                                                "data": a,
                                            }
                    except Exception:
                        pass

            return {
                "matched": False,
                "error": "timeout",
                "timeout": timeout,
            }

        finally:
            if owned_socket:
                sock.close()


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for HerdrWatcher."""
    parser = argparse.ArgumentParser(
        description="Event-driven Herdr agent status watcher"
    )
    parser.add_argument(
        "--lanes",
        nargs="+",
        required=True,
        help="One or more lane or agent names to watch",
    )
    parser.add_argument(
        "--until",
        default="idle,done,blocked",
        help="Target statuses to watch for (comma-separated, default: idle,done,blocked)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=600.0,
        help="Timeout in seconds (default: 600)",
    )
    parser.add_argument(
        "--socket-path",
        default=None,
        help="Path to Herdr UNIX socket (overrides HERDR_SOCKET_PATH)",
    )
    parser.add_argument(
        "--receipt-prefix",
        default=None,
        help="Path prefix for completion receipt files (e.g. /tmp/handoff-1794019395-)",
    )
    parser.add_argument(
        "--require-all",
        action="store_true",
        help="Wait until all lanes complete rather than stopping at the first lane",
    )
    args = parser.parse_args(argv)

    try:
        watcher = HerdrWatcher(socket_path=args.socket_path)
        result = watcher.watch(
            lanes=args.lanes,
            until=args.until,
            timeout=args.timeout,
            receipt_prefix=args.receipt_prefix,
            require_all=args.require_all,
        )
        print(json.dumps(result))
        return 0 if result.get("matched") else 1
    except Exception as exc:
        print(json.dumps({"matched": False, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
