"""Loopback-only dashboard server; request bodies are never logged."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from importlib.resources import files
from typing import cast
from urllib.parse import urlsplit

from mnemonic_recovery.core import validate_mnemonic

_ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
}
_MAX_REQUEST_BYTES = 8192


class DashboardHandler(BaseHTTPRequestHandler):
    """Serve fixed local assets and an input-minimal validation endpoint."""

    def log_message(self, format: str, *args: object) -> None:
        return

    def end_headers(self) -> None:
        policy = (
            "default-src 'self'; connect-src 'self'; "
            "style-src 'self'; script-src 'self'; img-src 'self'; "
            "base-uri 'none'; form-action 'none'; "
            "frame-ancestors 'none'; object-src 'none'"
        )
        self.send_header("Cache-Control", "no-store")
        self.send_header(
            "Content-Security-Policy",
            policy,
        )
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        super().end_headers()

    def _respond(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _respond_json(self, status: int, result: dict[str, object]) -> None:
        body = json.dumps(result, separators=(",", ":")).encode("utf-8")
        self._respond(status, body, "application/json; charset=utf-8")

    def do_GET(self) -> None:
        asset = _ASSETS.get(urlsplit(self.path).path)
        if asset is None:
            self._respond_json(404, {"error": "Not found."})
            return
        filename, content_type = asset
        body = files("mnemonic_recovery").joinpath("web", filename).read_bytes()
        self._respond(200, body, content_type)

    def do_POST(self) -> None:
        server = cast(HTTPServer, self.server)
        expected_host = f"127.0.0.1:{server.server_port}"
        if (
            self.headers.get("Host") != expected_host
            or self.headers.get("Origin") != f"http://{expected_host}"
            or urlsplit(self.path).path != "/api/validate"
            or self.headers.get_content_type() != "application/json"
        ):
            self._respond_json(403, {"error": "Request rejected."})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._respond_json(400, {"error": "Invalid request."})
            return
        if not 0 < content_length <= _MAX_REQUEST_BYTES:
            self._respond_json(400, {"error": "Invalid request."})
            return

        try:
            payload = json.loads(self.rfile.read(content_length))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._respond_json(400, {"error": "Invalid request."})
            return
        if (
            not isinstance(payload, dict)
            or set(payload) != {"phrase"}
            or not isinstance(payload["phrase"], str)
            or len(payload["phrase"]) > 4096
        ):
            self._respond_json(400, {"error": "Invalid request."})
            return

        result = validate_mnemonic(payload["phrase"])
        self._respond_json(
            200,
            {
                "valid": result.valid,
                "word_count": result.word_count,
                "invalid_words": [
                    {"position": item.position, "word": item.word}
                    for item in result.invalid_words
                ],
                "checksum_valid": result.checksum_valid,
            },
        )


def serve_dashboard(port: int = 8765) -> None:
    """Run the dashboard on IPv4 loopback only."""
    if not 0 < port < 65536:
        raise ValueError("port must be between 1 and 65535")
    with HTTPServer(("127.0.0.1", port), DashboardHandler) as server:
        print(f"Mnemonic Recovery Lab: http://127.0.0.1:{server.server_port}")
        print("Local only. Press Ctrl+C to stop.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
