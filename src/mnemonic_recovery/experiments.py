"""Bounded, offline recovery experiments on public/disposable fixtures only."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from itertools import islice, product
from statistics import median
from threading import Event
from time import perf_counter
from typing import Final, Literal

from mnemonic import Mnemonic

from mnemonic_recovery.core import estimate_search_space

MAX_CANDIDATES: Final = 100_000
FIXTURES: Final = (
    "bip39-zero-128",
    "bip39-zero-192",
    "bip39-zero-256",
    "disposable-160",
    "disposable-224",
)
_ENTROPY: Final = {
    "bip39-zero-128": bytes(16),
    "bip39-zero-192": bytes(24),
    "bip39-zero-256": bytes(32),
    "disposable-160": bytes(range(20)),
    "disposable-224": bytes(range(28)),
}
Status = Literal["running", "completed", "cancelled", "limit_reached"]


@dataclass(frozen=True)
class Progress:
    """Aggregate metrics only; never includes phrase or candidate material."""

    fixture: str
    missing_positions: tuple[int, ...]
    total_candidates: int
    checked: int
    checksum_valid: int
    fixture_matches: int
    elapsed_seconds: float
    status: Status

    @property
    def candidates_per_second(self) -> float:
        return self.checked / self.elapsed_seconds if self.elapsed_seconds > 0 else 0.0


@dataclass(frozen=True)
class Benchmark:
    """Repeated bounded runs; timing is observational, not a performance promise."""

    runs: tuple[Progress, ...]

    @property
    def median_candidates_per_second(self) -> float:
        return median(run.candidates_per_second for run in self.runs)


def fixture_words(fixture: str) -> tuple[str, ...]:
    """Return public test material only; never accepts user entropy or phrases."""
    if fixture not in _ENTROPY:
        raise ValueError("select a built-in public or disposable fixture")
    return tuple(Mnemonic("english").to_mnemonic(_ENTROPY[fixture]).split())


def run_experiment(
    fixture: str,
    missing_positions: Sequence[int],
    *,
    max_candidates: int = 2048,
    progress_every: int = 256,
    cancel: Event | None = None,
    on_progress: Callable[[Progress], None] | None = None,
) -> Progress:
    """Search fixture substitutions, never accepting arbitrary phrase input.

    Positions are one-based; searches run in English wordlist order. A match
    means exact equality with the known fixture, not evidence of wallet ownership.
    """
    if fixture not in _ENTROPY:
        raise ValueError("select a built-in public or disposable fixture")
    for value, name, maximum in (
        (max_candidates, "max_candidates", MAX_CANDIDATES),
        (progress_every, "progress_every", MAX_CANDIDATES),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 1 <= value <= maximum
        ):
            raise ValueError(f"{name} must be an integer between 1 and {maximum}")

    english = Mnemonic("english")
    target = english.to_mnemonic(_ENTROPY[fixture])
    words = target.split()
    estimate = estimate_search_space(len(words), tuple(missing_positions))
    positions = estimate.missing_positions
    cancellation = cancel if cancel is not None else Event()
    started = perf_counter()
    checked = checksum_valid = fixture_matches = 0

    def snapshot(status: Status) -> Progress:
        return Progress(
            fixture,
            positions,
            estimate.possible_combinations,
            checked,
            checksum_valid,
            fixture_matches,
            max(0.0, perf_counter() - started),
            status,
        )

    def report(status: Status) -> Progress:
        result = snapshot(status)
        if on_progress is not None:
            on_progress(result)
        return result

    report("running")
    combinations = product(english.wordlist, repeat=len(positions))
    for replacements in islice(combinations, max_candidates):
        if cancellation.is_set():
            return report("cancelled")
        for position, replacement in zip(positions, replacements, strict=True):
            words[position - 1] = replacement
        candidate = " ".join(words)
        valid = english.check(candidate)
        checked += 1
        checksum_valid += int(valid)
        fixture_matches += int(valid and candidate == target)
        if checked % progress_every == 0:
            report("running")

    status: Status = (
        "completed"
        if checked == estimate.possible_combinations
        else "cancelled"
        if cancellation.is_set()
        else "limit_reached"
    )
    return report(status)


def run_benchmark(
    fixture: str,
    missing_positions: Sequence[int],
    *,
    repeats: int = 3,
    max_candidates: int = 2048,
    progress_every: int = 256,
    cancel: Event | None = None,
    on_progress: Callable[[Progress], None] | None = None,
) -> Benchmark:
    """Measure 1-10 identical runs, stopping the batch when cancelled."""
    if (
        isinstance(repeats, bool)
        or not isinstance(repeats, int)
        or not 1 <= repeats <= 10
    ):
        raise ValueError("repeats must be an integer between 1 and 10")
    cancellation = cancel if cancel is not None else Event()
    runs: list[Progress] = []
    for _ in range(repeats):
        result = run_experiment(
            fixture,
            missing_positions,
            max_candidates=max_candidates,
            progress_every=progress_every,
            cancel=cancellation,
            on_progress=on_progress,
        )
        runs.append(result)
        if cancellation.is_set():
            break
    return Benchmark(tuple(runs))
