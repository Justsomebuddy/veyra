import pytest

from src.core.modes import Mode
from src.core.spectrum import candidate_parts, resonance_spectrum, top_resonances


def test_candidate_parts_respects_bounds():
    candidates = candidate_parts(("a", "b"), max_len=2, min_len=2)
    assert [mode.word for mode in candidates] == ["aa", "ab", "ba", "bb"]


def test_candidate_parts_rejects_bad_bounds():
    with pytest.raises(ValueError):
        candidate_parts(("a",), max_len=0, min_len=1)
    with pytest.raises(ValueError):
        candidate_parts(("a",), max_len=2, min_len=0)


def test_resonance_spectrum_ranks_exact_before_bounded():
    whole = Mode.from_word("abab")
    candidates = [Mode.from_word("aa"), Mode.from_word("ab"), Mode.from_word("a")]
    spectrum = resonance_spectrum(whole, candidates, max_defects=1, include_nonresonant=True)
    assert spectrum[0].part == Mode.from_word("ab")
    assert spectrum[0].exact
    assert spectrum[0].defect_count == 0


def test_resonance_spectrum_finds_bounded_defect_candidate():
    whole = Mode.from_word("abac")
    candidates = [Mode.from_word("ab"), Mode.from_word("cc")]
    spectrum = resonance_spectrum(whole, candidates, max_defects=1, include_nonresonant=True)
    assert spectrum[0].part == Mode.from_word("ab")
    assert spectrum[0].profile.resonates
    assert spectrum[0].profile.obstruction == "bounded-defect"
    assert spectrum[0].defect_count == 1


def test_top_resonances_excludes_nonresonant_and_limits():
    whole = Mode.from_word("abac")
    candidates = [Mode.from_word("ab"), Mode.from_word("cc"), Mode.from_word("ac")]
    top = top_resonances(whole, candidates, max_defects=1, limit=1)
    assert len(top) == 1
    assert top[0].profile.resonates
