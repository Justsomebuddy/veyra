from src.core.modes import Mode
from src.core.resonance import (
    cyclic_power,
    cyclic_resonates_inside,
    phase_offsets,
    resonance_obstruction,
    resonance_profile,
    rotate_mode,
)


def test_rotate_mode_wraps_offsets():
    assert rotate_mode(Mode.from_word("abcd"), 1) == Mode.from_word("bcda")
    assert rotate_mode(Mode.from_word("abcd"), 5) == Mode.from_word("bcda")


def test_phase_offsets_detect_shifted_repetition():
    assert phase_offsets(Mode.from_word("ab"), Mode.from_word("abab")) == (0, 2)
    assert phase_offsets(Mode.from_word("ab"), Mode.from_word("baba")) == (1, 3)


def test_cyclic_resonance_extends_ordered_repetition():
    part = Mode.from_word("ab")
    assert cyclic_resonates_inside(part, Mode.from_word("abab"))
    assert cyclic_resonates_inside(part, Mode.from_word("baba"))
    assert not cyclic_resonates_inside(part, Mode.from_word("abba"))


def test_resonance_obstruction_taxonomy():
    assert resonance_obstruction(Mode.from_word("ab"), Mode.from_word("aba")) == "length-obstruction"
    assert resonance_obstruction(Mode.from_word("ab"), Mode.from_word("abba")) == "pattern-obstruction"
    assert resonance_obstruction(Mode.from_word("ab"), Mode.from_word("baba")) == "none"
    assert resonance_obstruction(Mode.from_word(""), Mode.from_word("ab")) == "silent-part"


def test_cyclic_power_and_profile():
    assert cyclic_power(Mode.from_word("ba"), 2) == Mode.from_word("abab")
    profile = resonance_profile(Mode.from_word("ab"), Mode.from_word("baba"))
    assert not profile.ordered
    assert profile.cyclic
    assert profile.phase_offsets == (1, 3)
    assert profile.obstruction == "none"
