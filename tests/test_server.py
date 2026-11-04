import json
from http.server import HTTPServer
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from mnemonic_recovery.server import DashboardHandler


def test_loopback_dashboard_serves_assets_and_validates_locally() -> None:
    server = HTTPServer(("127.0.0.1", 0), DashboardHandler)
    thread = Thread(target=server.serve_forever)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(origin) as response:
            assert response.status == 200
            assert b"Offline mnemonic validation" in response.read()
            assert response.headers["Cache-Control"] == "no-store"

        request = Request(
            f"{origin}/api/validate",
            data=json.dumps(
                {
                    "phrase": (
                        "abandon abandon abandon abandon abandon abandon abandon "
                        "abandon abandon abandon abandon about"
                    )
                }
            ).encode(),
            headers={
                "Content-Type": "application/json",
                "Origin": origin,
            },
            method="POST",
        )
        with urlopen(request) as response:
            result = json.loads(response.read())
            assert result["valid"] is True
            assert "phrase" not in result
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_server_rejects_cross_origin_validation_request() -> None:
    server = HTTPServer(("127.0.0.1", 0), DashboardHandler)
    thread = Thread(target=server.serve_forever)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    request = Request(
        f"{origin}/api/validate",
        data=b'{"phrase":"not a real phrase"}',
        headers={"Content-Type": "application/json", "Origin": "http://example.test"},
        method="POST",
    )
    try:
        with pytest.raises(HTTPError) as error:
            urlopen(request)
        assert error.value.code == 403
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
