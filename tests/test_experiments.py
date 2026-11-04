from dataclasses import asdict
from threading import Event

import pytest

from mnemonic_recovery.experiments import (
    FIXTURES,
    Progress,
    run_benchmark,
    run_experiment,
)


def test_complete_published_vector_search() -> None:
    updates: list[Progress] = []
    result = run_experiment("bip39-zero-128", [12], on_progress=updates.append)

    assert result.status == "completed"
    assert result.checked == result.total_candidates == 2048
    assert result.checksum_valid == 128
    assert result.fixture_matches == 1
    assert result.candidates_per_second > 0
    assert updates[0].checked == 0
    assert updates[-1] == result
    assert [update.checked for update in updates] == sorted(
        update.checked for update in updates
    )
    assert "abandon" not in repr(updates)
    assert "phrase" not in asdict(result)


def test_cancel_before_start() -> None:
    cancel = Event()
    cancel.set()
    result = run_experiment("bip39-zero-128", [1], cancel=cancel)

    assert result.status == "cancelled"
    assert result.checked == result.checksum_valid == result.fixture_matches == 0


def test_cancel_from_progress_callback() -> None:
    cancel = Event()

    def stop(progress: Progress) -> None:
        if progress.checked == 3:
            cancel.set()

    result = run_experiment(
        "bip39-zero-128", [1], cancel=cancel, on_progress=stop, progress_every=1
    )

    assert result.status == "cancelled"
    assert result.checked == 3


def test_multiple_missing_positions_are_bounded_and_sorted() -> None:
    result = run_experiment("bip39-zero-128", [12, 1], max_candidates=7)

    assert result.status == "limit_reached"
    assert result.checked == 7
    assert result.total_candidates == 2048**2
    assert result.missing_positions == (1, 12)


@pytest.mark.parametrize("positions", [[], [0], [13], [1, 1], [True]])
def test_invalid_positions(positions: list[int]) -> None:
    with pytest.raises(ValueError):
        run_experiment("bip39-zero-128", positions)


@pytest.mark.parametrize("limit", [0, -1, 100_001, True, 1.5])
@pytest.mark.parametrize("parameter", ["max_candidates", "progress_every"])
def test_invalid_limits(parameter: str, limit: int) -> None:
    with pytest.raises(ValueError):
        run_experiment("bip39-zero-128", [1], **{parameter: limit})


def test_arbitrary_phrase_is_not_a_fixture() -> None:
    with pytest.raises(ValueError, match="built-in"):
        run_experiment("abandon " * 11 + "about", [12])


@pytest.mark.parametrize(
    ("fixture", "word_count"), tuple(zip(FIXTURES, (12, 18, 24, 15, 21), strict=True))
)
@pytest.mark.parametrize("position", [1, 6, -1])
def test_all_fixture_lengths_and_missing_locations(
    fixture: str, word_count: int, position: int
) -> None:
    result = run_experiment(fixture, [word_count if position == -1 else position])

    assert result.status == "completed"
    assert result.fixture_matches == 1
    assert result.checksum_valid >= 1
    if position == -1:
        assert result.checksum_valid == 2 ** (11 - word_count // 3)


def test_benchmarks_repeat_identical_work() -> None:
    benchmark = run_benchmark("bip39-zero-128", [12], repeats=3)

    assert len(benchmark.runs) == 3
    assert {run.checked for run in benchmark.runs} == {2048}
    assert {run.fixture_matches for run in benchmark.runs} == {1}
    rates = sorted(run.candidates_per_second for run in benchmark.runs)
    assert benchmark.median_candidates_per_second == rates[1]


@pytest.mark.parametrize("repeats", [0, -1, 11, True, 1.5])
def test_invalid_benchmark_repeats(repeats: int) -> None:
    with pytest.raises(ValueError, match="repeats"):
        run_benchmark("bip39-zero-128", [12], repeats=repeats)


def test_benchmark_cancellation_stops_repeats() -> None:
    cancel = Event()

    def stop(_: Progress) -> None:
        cancel.set()

    benchmark = run_benchmark("bip39-zero-128", [12], cancel=cancel, on_progress=stop)

    assert len(benchmark.runs) == 1
    assert benchmark.runs[0].status == "cancelled"
    assert benchmark.runs[0].checked == 0


def test_fixture_search_never_uses_network_or_writes_outputs(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("offline experiment attempted network or file output")

    monkeypatch.setattr("socket.socket.connect", forbidden)
    monkeypatch.setattr("socket.socket.connect_ex", forbidden)
    monkeypatch.setattr("socket.socket.sendto", forbidden)
    monkeypatch.setattr("pathlib.Path.write_text", forbidden)
    monkeypatch.setattr("pathlib.Path.write_bytes", forbidden)
    result = run_experiment("bip39-zero-128", [12])

    assert result.fixture_matches == 1
    assert not caplog.records
    output = capsys.readouterr()
    assert not output.out + output.err


def test_zero_duration_rate_is_safe() -> None:
    progress = Progress("bip39-zero-128", (12,), 2048, 0, 0, 0, 0.0, "running")
    assert progress.candidates_per_second == 0
