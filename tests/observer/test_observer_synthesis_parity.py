from src.core.observer_synthesis import score_observer
from src.core.observer_synthesis_types import ObserverTerm, SynthesisConfig
from src.core.observer_synthesis_parity import (
    BOUNDARY, EXPECTED_WINNER, histogram, observer_class_includes,
    observer_class_membership, observer_classes, observer_synthesis_summary, observer_term_text,
    parity_baselines, parity_holdout_cases, parity_observer_grammar,
    parity_observer_synthesis, parity_table, parity_train_cases,
    proper_marginal_signature, strict_observer_class_certificate, xor_rows,
)
import pytest

pytestmark = pytest.mark.requires_lean


def test_proper_marginals_are_exactly_blind_on_train_and_holdout():
    for case in (parity_train_cases()[0], parity_holdout_cases()[0]):
        assert proper_marginal_signature(case.left) == proper_marginal_signature(case.right)


def test_global_parity_histogram_separates_both_splits():
    train = parity_train_cases()[0]
    holdout = parity_holdout_cases()[0]
    assert histogram(xor_rows(train.left)) == ((0, 16),)
    assert histogram(xor_rows(train.right)) == ((0, 8), (1, 8))
    assert histogram(xor_rows(holdout.left)) == ((1, 32),)
    assert histogram(xor_rows(holdout.right)) == ((0, 16), (1, 16))


def test_generic_engine_synthesizes_composition_and_validates_holdout():
    result = parity_observer_synthesis()
    assert result.status == "validated"
    assert result.fitted.winner is not None
    assert observer_term_text(result.fitted.winner.term) == "histogram(xor-rows(input))"
    assert result.fitted.winner.fit == 1.0
    assert result.holdout.winner_evaluation is not None
    assert result.holdout.winner_evaluation.fit == 1.0


def test_all_named_baselines_are_blind():
    cases = (parity_train_cases()[0], parity_holdout_cases()[0])
    grammar = parity_observer_grammar()
    rows = tuple(score_observer(item.term, cases, grammar, SynthesisConfig()) for item in parity_baselines())
    assert all(row.fit == 0.0 for row in rows)
    assert all(all(evidence.reason == "blind-collision" for evidence in row.evidence) for row in rows)


def test_scoped_strength_certificate_is_checked_without_global_claim():
    cert = strict_observer_class_certificate()
    assert cert.strictly_stronger is True
    assert cert.lean_status == "checked"
    assert cert.theorem_ids == ("THM-R6-001", "THM-R6-002")
    assert cert.class_inclusion and cert.baseline_equal_train and cert.baseline_equal_holdout
    assert cert.winner_text == EXPECTED_WINNER
    assert cert.winner_in_extended and cert.winner_outside_baseline
    assert "declared observer class" in cert.boundary
    assert "global parity is classical" in cert.boundary
    assert cert.boundary == BOUNDARY


def test_summary_reports_exact_synthesized_winner():
    assert observer_synthesis_summary() == {
        "status": "validated",
        "winner": "histogram(xor-rows(input))",
        "train_fit": 1.0,
        "holdout_fit": 1.0,
        "strictly_stronger": True,
        "lean": "checked",
    }


def test_corpus_sizes_are_locked():
    assert len(parity_table(4, 0, True)) == len(parity_table(4)) == 16
    assert len(parity_table(5, 1, True)) == len(parity_table(5)) == 32


def test_observer_class_membership_and_inclusion_reject_mutated_winners():
    baseline, extended = observer_classes()
    source = ObserverTerm("input", "bit-table")
    marginal = ObserverTerm("apply", "signature", "proper-marginals", (source,))
    mutated = ObserverTerm("apply", "signature", "histogram", (source,))
    assert observer_class_includes(extended, baseline)
    assert not observer_class_includes(baseline, extended)
    assert observer_class_membership(marginal, baseline)
    assert observer_class_membership(marginal, extended)
    assert not observer_class_membership(mutated, extended)
