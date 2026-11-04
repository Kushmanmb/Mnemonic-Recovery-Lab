"""BIP-39 English phrase validation and non-searching analysis."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Final

from mnemonic import Mnemonic

WORD_COUNTS: Final = frozenset({12, 15, 18, 21, 24})
_ENGLISH = Mnemonic("english")
_ENGLISH_WORDS = frozenset(_ENGLISH.wordlist)


@dataclass(frozen=True)
class InvalidWord:
    """A word not found in the BIP-39 English list, with its one-based position."""

    position: int
    word: str


@dataclass(frozen=True)
class ValidationResult:
    """Phrase validation outcome; intentionally does not contain the input phrase."""

    valid: bool
    word_count: int
    invalid_words: tuple[InvalidWord, ...]
    checksum_valid: bool | None


@dataclass(frozen=True)
class SearchSpaceEstimate:
    """Theoretical missing-word search-space metrics; no candidates are generated."""

    word_count: int
    missing_positions: tuple[int, ...]
    possible_combinations: int
    expected_checksum_valid_combinations: int
    effective_search_bits: int
    checksum_bits: int


def validate_mnemonic(phrase: str) -> ValidationResult:
    """Validate English word membership and BIP-39 checksum without storing input."""
    if not isinstance(phrase, str):
        raise TypeError("phrase must be a string")

    words = unicodedata.normalize("NFKD", phrase).lower().split()
    invalid_words = tuple(
        InvalidWord(position, word)
        for position, word in enumerate(words, start=1)
        if word not in _ENGLISH_WORDS
    )
    supported_length = len(words) in WORD_COUNTS

    if invalid_words or not supported_length:
        return ValidationResult(
            valid=False,
            word_count=len(words),
            invalid_words=invalid_words,
            checksum_valid=None,
        )

    checksum_valid = _ENGLISH.check(" ".join(words))
    return ValidationResult(
        valid=checksum_valid,
        word_count=len(words),
        invalid_words=(),
        checksum_valid=checksum_valid,
    )


def estimate_search_space(
    word_count: int, missing_positions: list[int] | tuple[int, ...]
) -> SearchSpaceEstimate:
    """Estimate combinations and checksum filtering without enumerating any phrases.

    Positions are one-based. The checksum-valid count is an expectation, not a
    guarantee; the BIP-39 checksum only filters candidates and cannot identify the
    correct wallet.
    """
    if word_count not in WORD_COUNTS:
        raise ValueError("word_count must be 12, 15, 18, 21, or 24")
    if not missing_positions:
        raise ValueError("at least one missing position is required")
    if any(
        isinstance(position, bool)
        or not isinstance(position, int)
        or not 1 <= position <= word_count
        for position in missing_positions
    ):
        raise ValueError("missing positions must be valid one-based word positions")
    if len(set(missing_positions)) != len(missing_positions):
        raise ValueError("missing positions must be unique")

    count = len(missing_positions)
    checksum_bits = word_count // 3
    combinations = 1 << (11 * count)
    expected_valid = 1 << (11 * count - checksum_bits)
    return SearchSpaceEstimate(
        word_count=word_count,
        missing_positions=tuple(sorted(missing_positions)),
        possible_combinations=combinations,
        expected_checksum_valid_combinations=expected_valid,
        effective_search_bits=11 * count - checksum_bits,
        checksum_bits=checksum_bits,
    )
