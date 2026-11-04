import json
from collections.abc import Iterator
from http.server import HTTPServer
from threading import Thread
from unittest.mock import Mock
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from mnemonic_recovery.experiments import run_experiment
from mnemonic_recovery.server import DashboardHandler


@pytest.fixture
def origin() -> Iterator[str]:
    with HTTPServer(("127.0.0.1", 0), DashboardHandler) as server:
        thread = Thread(target=server.serve_forever)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            thread.join()


def test_reference_is_local_public_material(origin: str) -> None:
    with urlopen(f"{origin}/api/reference") as response:
        data = json.loads(response.read())
        assert response.headers["Cache-Control"] == "no-store"
    assert len(data["wordlist"]) == 2048
    assert {len(fixture["words"]) for fixture in data["fixtures"]} == {
        12,
        15,
        18,
        21,
        24,
    }
    assert data["fixtures"][0]["words"] == ["abandon"] * 11 + ["about"]


def test_fixture_stream_reports_counts_without_candidates(origin: str) -> None:
    request = Request(
        f"{origin}/api/experiment",
        data=json.dumps(
            {
                "fixture": "bip39-zero-128",
                "missing_positions": [12],
                "max_candidates": 2048,
            }
        ).encode(),
        headers={"Content-Type": "application/json", "Origin": origin},
    )
    with urlopen(request) as response:
        body = response.read()
        updates = [json.loads(line) for line in body.splitlines()]
        assert response.headers["Content-Type"].startswith("application/x-ndjson")
        assert response.headers["Cache-Control"] == "no-store"
    assert updates[0]["checked"] == 0
    assert updates[-1]["status"] == "completed"
    assert updates[-1]["checked"] == 2048
    assert updates[-1]["checksum_valid"] == 128
    assert updates[-1]["fixture_matches"] == 1
    assert b"abandon" not in body
    assert all("phrase" not in update and "words" not in update for update in updates)


@pytest.mark.parametrize(
    "override",
    [
        {"fixture": "unknown"},
        {"fixture": []},
        {"missing_positions": [0]},
        {"missing_positions": [True]},
        {"missing_positions": [12, 12]},
        {"missing_positions": []},
        {"missing_positions": "12"},
        {"max_candidates": True},
        {"max_candidates": 100001},
        {"phrase": "public fixture only"},
    ],
)
def test_fixture_endpoint_rejects_bad_inputs(
    origin: str, override: dict[str, object]
) -> None:
    payload = {
        "fixture": "bip39-zero-128",
        "missing_positions": [12],
        "max_candidates": 2048,
    } | override
    request = Request(
        f"{origin}/api/experiment",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Origin": origin},
    )
    with pytest.raises(HTTPError) as error:
        urlopen(request)
    with error.value as response:
        assert response.code == 400
        assert b"public fixture only" not in response.read()


def test_disconnect_cancels_fixture_search_without_logging(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    handler = object.__new__(DashboardHandler)
    handler.wfile = Mock()
    handler.wfile.write.side_effect = [1, BrokenPipeError()]
    for method in ("send_response", "send_header", "end_headers"):
        monkeypatch.setattr(handler, method, Mock())
    runner = Mock(wraps=run_experiment)
    monkeypatch.setattr("mnemonic_recovery.server.run_experiment", runner)

    handler._experiment(
        {
            "fixture": "bip39-zero-128",
            "missing_positions": [1, 12],
            "max_candidates": 100000,
        }
    )

    assert runner.call_args.kwargs["cancel"].is_set()
    assert handler.wfile.write.call_count == 2
    output = capsys.readouterr()
    assert not output.out + output.err


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

        with urlopen(f"{origin}/favicon.ico") as response:
            assert response.status == 204

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


@pytest.mark.parametrize("route", ["validate", "experiment"])
def test_server_rejects_cross_origin_validation_request(route: str) -> None:
    server = HTTPServer(("127.0.0.1", 0), DashboardHandler)
    thread = Thread(target=server.serve_forever)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    request = Request(
        f"{origin}/api/{route}",
        data=b'{"phrase":"not a real phrase"}',
        headers={"Content-Type": "application/json", "Origin": "http://example.test"},
        method="POST",
    )
    try:
        with pytest.raises(HTTPError) as error:
            urlopen(request)
        with error.value as response:
            assert response.code == 403
            response.read()
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
