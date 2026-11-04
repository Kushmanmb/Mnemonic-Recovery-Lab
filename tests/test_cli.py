import json
import signal
from io import StringIO

import pytest

from mnemonic_recovery.__main__ import main


def test_cli_refuses_validation_without_interactive_input(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.argv", ["mnemonic-recovery", "validate"])
    monkeypatch.setattr("sys.stdin", StringIO("synthetic test phrase"))

    with pytest.raises(SystemExit, match="interactive terminal"):
        main()

    assert "Recovery phrase" not in capsys.readouterr().out


def test_validation_does_not_echo_invalid_input(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.argv", ["mnemonic-recovery", "validate"])
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr(
        "mnemonic_recovery.__main__.getpass", lambda _: "private-invalid-input"
    )
    main()

    output = capsys.readouterr()
    assert "position 1" in output.out
    assert "private-invalid-input" not in output.out + output.err


@pytest.mark.parametrize("command", ["experiment", "benchmark"])
def test_fixture_commands(
    command: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "mnemonic-recovery",
            command,
            "--fixture",
            "bip39-zero-128",
            "--missing",
            "12",
        ],
    )
    handler = signal.getsignal(signal.SIGINT)
    main()

    output = capsys.readouterr()
    result = json.loads(output.out)
    if command == "benchmark":
        assert len(result["runs"]) == 3
        assert result["median_candidates_per_second"] > 0
        result = result["runs"][0]
    assert result["fixture_matches"] == 1
    assert result["status"] == "completed"
    assert "2048/2048" in output.err
    assert "abandon" not in output.out + output.err
    assert signal.getsignal(signal.SIGINT) == handler


def test_invalid_experiment_restores_signal_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["lab", "experiment", "--fixture", "bip39-zero-128", "--missing", "0"],
    )
    handler = signal.getsignal(signal.SIGINT)
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    assert signal.getsignal(signal.SIGINT) == handler


def test_cli_cancellation_reports_final_counts_and_restores_handler(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    original_print = print

    def interrupt_on_progress(*args: object, **kwargs: object) -> None:
        original_print(*args, **kwargs)
        if args and str(args[0]).startswith("running:"):
            signal.raise_signal(signal.SIGINT)

    monkeypatch.setattr(
        "mnemonic_recovery.__main__.print", interrupt_on_progress, raising=False
    )
    monkeypatch.setattr(
        "sys.argv",
        ["lab", "experiment", "--fixture", "bip39-zero-128", "--missing", "12"],
    )
    handler = signal.getsignal(signal.SIGINT)
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 130
    assert signal.getsignal(signal.SIGINT) == handler
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "cancelled"
    assert result["checked"] == 0
