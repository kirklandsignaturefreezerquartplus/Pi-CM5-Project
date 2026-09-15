"""Local control socket (newline-delimited JSON over a Unix stream socket).

Request examples::

    {"cmd": "status"}
    {"cmd": "macro", "name": "login"}
    {"cmd": "steps", "steps": ["ctrl+alt+delete", "wait 500", "type hello"]}
    {"cmd": "type", "text": "hello"}
    {"cmd": "keys", "combo": "ctrl+alt+delete"}
    {"cmd": "release_all"}

Every reply is one JSON object with ``ok`` (bool) and either ``result`` or
``error``.
"""
from __future__ import annotations

import json
import logging
import os
import socket
import stat
from typing import Callable

log = logging.getLogger("hid-bridge.control")

MAX_REQUEST = 64 * 1024


class ControlServer:
    def __init__(self, path: str, handler: Callable[[dict], dict]):
        self.path = path
        self.handler = handler
        self.sock: socket.socket | None = None

    def open(self) -> None:
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        try:
            if stat.S_ISSOCK(os.stat(self.path).st_mode):
                os.unlink(self.path)
        except FileNotFoundError:
            pass
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.setblocking(False)
        self.sock.bind(self.path)
        os.chmod(self.path, 0o660)
        self.sock.listen(8)
        log.info("control socket listening on %s", self.path)

    def fileno(self) -> int:
        assert self.sock is not None
        return self.sock.fileno()

    def close(self) -> None:
        if self.sock is not None:
            self.sock.close()
            self.sock = None
        try:
            os.unlink(self.path)
        except OSError:
            pass

    def handle_ready(self) -> None:
        """Accept and service one pending connection (called from the main loop)."""
        assert self.sock is not None
        try:
            conn, _ = self.sock.accept()
        except (BlockingIOError, InterruptedError):
            return
        with conn:
            # Local clients send immediately; never let one hold the main loop.
            conn.settimeout(0.05)
            try:
                chunks = []
                total = 0
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    total += len(chunk)
                    if b"\n" in chunk or total > MAX_REQUEST:
                        break
                raw = b"".join(chunks).split(b"\n", 1)[0].decode("utf-8", "replace").strip()
                if not raw:
                    reply = {"ok": False, "error": "empty request"}
                else:
                    try:
                        request = json.loads(raw)
                        if not isinstance(request, dict):
                            raise ValueError("request must be a JSON object")
                        reply = {"ok": True, "result": self.handler(request)}
                    except Exception as exc:  # noqa: BLE001 - reported to the client
                        reply = {"ok": False, "error": str(exc)}
                conn.sendall((json.dumps(reply) + "\n").encode())
            except (socket.timeout, OSError) as exc:
                log.debug("control client error: %s", exc)


def send_request(path: str, request: dict, timeout: float = 5.0) -> dict:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        sock.connect(path)
        sock.sendall((json.dumps(request) + "\n").encode())
        data = b""
        while not data.endswith(b"\n"):
            chunk = sock.recv(65536)
            if not chunk:
                break
            data += chunk
    if not data:
        raise ConnectionError("no reply from hid-bridge")
    return json.loads(data.decode())
