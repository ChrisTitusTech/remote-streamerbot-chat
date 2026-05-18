#!/usr/bin/env python3

import argparse
import json
import shutil
import subprocess
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


def _safe_text(value, fallback=""):
    if value is None:
        return fallback
    text = str(value).strip()
    if not text:
        return fallback
    return text[:300]


class ChatRequestHandler(SimpleHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/notify":
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"})
            return

        content_length = self.headers.get("Content-Length", "0")
        try:
            size = int(content_length)
        except ValueError:
            size = 0

        if size <= 0 or size > 16_384:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "invalid body size"})
            return

        raw = self.rfile.read(size)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "invalid json"})
            return

        title = _safe_text(payload.get("title"), "StreamerBot Alert")
        body = _safe_text(payload.get("body"), "")
        urgency = _safe_text(payload.get("urgency"), "normal").lower()
        if urgency not in {"low", "normal", "critical"}:
            urgency = "normal"

        notify_send = shutil.which("notify-send")
        if not notify_send:
            self._send_json(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {"ok": False, "error": "notify-send not available"},
            )
            return

        command = [notify_send, "-u", urgency, title]
        if body:
            command.append(body)

        try:
            subprocess.run(command, check=False, timeout=2)
        except Exception as exc:
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"ok": False, "error": str(exc)},
            )
            return

        self._send_json(HTTPStatus.OK, {"ok": True})


def main():
    parser = argparse.ArgumentParser(description="Serve chat UI and local notification bridge")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--directory", required=True)
    args = parser.parse_args()

    handler = partial(ChatRequestHandler, directory=args.directory)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
