import pytest
from mnemonic import Mnemonic

from mnemonic_recovery import estimate_search_space, validate_mnemonic

VALID_VECTOR = "abandon " * 11 + "about"


def test_official_bip39_vector_is_valid() -> None:
    result = validate_mnemonic(VALID_VECTOR)

    assert result.valid
    assert result.word_count == 12
    assert result.invalid_words == ()
    assert result.checksum_valid is True


def test_invalid_word_is_reported_by_position_without_phrase_retention() -> None:
    result = validate_mnemonic("abandon " * 10 + "notaword about")

    assert not result.valid
    assert result.invalid_words[0].position == 11
    assert result.invalid_words[0].word == "notaword"
    assert not hasattr(result, "phrase")


def test_checksum_is_validated() -> None:
    result = validate_mnemonic("abandon " * 12)

    assert not result.valid
    assert result.checksum_valid is False


@pytest.mark.parametrize("word_count", [12, 15, 18, 21, 24])
def test_all_supported_phrase_lengths(word_count: int) -> None:
    entropy_bytes = word_count * 4 // 3
    phrase = Mnemonic("english").to_mnemonic(bytes(entropy_bytes))

    assert validate_mnemonic(phrase).valid


def test_search_space_estimate_is_exact_power_of_two_and_does_not_search() -> None:
    estimate = estimate_search_space(12, [12])

    assert estimate.possible_combinations == 2048
    assert estimate.expected_checksum_valid_combinations == 128
    assert estimate.effective_search_bits == 7
    assert estimate.checksum_bits == 4
    assert estimate.missing_positions == (12,)


@pytest.mark.parametrize(
    ("word_count", "positions"),
    [
        (11, [1]),
        (12, []),
        (12, [0]),
        (12, [13]),
        (12, [1, 1]),
        (12, [True]),
    ],
)
def test_rejects_invalid_search_space_inputs(
    word_count: int, positions: list[int]
) -> None:
    with pytest.raises(ValueError):
        estimate_search_space(word_count, positions)
