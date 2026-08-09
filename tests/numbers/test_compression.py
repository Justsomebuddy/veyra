import pytest

from src.core.compression import (
    CompressionWeights,
    best_compression,
    compression_scores,
    explanation_cost,
    phase_penalty,
)
from src.core.modes import Mode
from src.core.spectrum import candidate_parts, resonance_spectrum


def test_phase_penalty_only_charges_shift():
    assert phase_penalty(None) == 0.0
    assert phase_penalty(0) == 0.0
    assert phase_penalty(2) == 1.0


def test_explanation_cost_for_bounded_defect():
    whole = Mode.from_word("abac")
    entry = resonance_spectrum(whole, [Mode.from_word("ab")], max_defects=1)[0]
    assert explanation_cost(entry, CompressionWeights(defect_weight=2.0, phase_weight=0.25)) == 4.0
    assert explanation_cost(entry, CompressionWeights(defect_weight=1.0, phase_weight=0.25)) == 3.0


def test_explanation_cost_rejects_nonresonant():
    whole = Mode.from_word("cccc")
    entry = resonance_spectrum(whole, [Mode.from_word("ab")], max_defects=1)[0]
    with pytest.raises(ValueError):
        explanation_cost(entry)


def test_compression_scores_rank_positive_saving():
    whole = Mode.from_word("ababab")
    candidates = [Mode.from_word("ab"), Mode.from_word("abab"), Mode.from_word("a")]
    scores = compression_scores(whole, candidates, max_defects=0)
    assert scores[0].part == Mode.from_word("ab")
    assert scores[0].saving == 4.0
    assert scores[0].ratio == pytest.approx(4 / 6)


def test_best_compression_returns_none_without_resonance():
    whole = Mode.from_word("cccc")
    candidates = [Mode.from_word("ab")]
    assert best_compression(whole, candidates, max_defects=1) is None


def test_best_compression_on_candidate_parts():
    whole = Mode.from_word("abac")
    candidates = candidate_parts(("a", "b", "c"), max_len=2, min_len=2)
    best = best_compression(whole, candidates, max_defects=1, weights=CompressionWeights(defect_weight=1.0))
    assert best is not None
    assert best.part in {Mode.from_word("ab"), Mode.from_word("ac"), Mode.from_word("ba"), Mode.from_word("ca")}
    assert best.saving == 1.0
