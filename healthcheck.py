# -*- coding: utf-8 -*-
"""Standalone healthcheck server for external uptime monitoring (UptimeRobot).

Runs as its own systemd service (healthcheck.service), independent of the bot.
Because it does not restart when the bot is redeployed, brief bot restarts do
NOT cause false 'down' alerts — the monitor keeps getting 200 'ok' as long as
the bot's heartbeat file was touched within the last few minutes.

Reports:
  200 'ok'    — heartbeat file updated within MAX_AGE seconds (bot alive)
  503 'stale' — heartbeat too old or missing (bot genuinely down)
"""
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.environ.get("HEALTHCHECK_PORT", "8080"))
HEARTBEAT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "heartbeat")
MAX_AGE = 600  # seconds; bot writes the heartbeat every 60s


def _is_healthy() -> bool:
    try:
        age = time.time() - os.path.getmtime(HEARTBEAT_FILE)
        return age < MAX_AGE
    except OSError:
        return False


class Handler(BaseHTTPRequestHandler):
    def _respond(self, with_body: bool):
        ok = _is_healthy()
        body = b"ok" if ok else b"stale"
        self.send_response(200 if ok else 503)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if with_body:
            self.wfile.write(body)

    def do_GET(self):
        self._respond(with_body=True)

    def do_HEAD(self):
        self._respond(with_body=False)

    def log_message(self, *args):
        pass  # silence per-request access logging


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
