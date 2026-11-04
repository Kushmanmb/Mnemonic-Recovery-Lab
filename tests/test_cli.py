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
