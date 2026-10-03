"""Boundary regressions for the finite replay of the observer-site Lean cards."""

import pytest

from src.core.certify_observer_site import certify_observer_site_os
from src.core.observer_arithmetic import (
    descends,
    fibre_action,
    resonates_at,
    restriction_commutes,
    stitch,
    weave,
)
from src.core.observer_site import (
    BAG,
    CYCLE,
    LENGTH,
    WORD,
    Observer,
    ObserverSiteError,
    bounded_reader,
    echo,
    power_at,
    prime_table,
    primitive_at,
    refines,
    restriction,
    site_law_report,
    stage_name,
    standard_site,
    substages,
    undecided_pairs,
    words_up_to,
)

A, B, AA = ("a",), ("b",), ("a", "a")


def test_empty_stage_has_a_proper_power_witness_even_for_a_single_letter():
    words = words_up_to("ab", 3, include_empty=False)
    for word in words:
        witness = power_at((), word, "ab")
        assert witness is not None
        root, exponent = witness
        assert root and exponent >= 2
        assert echo((), word, root * exponent)
        assert not primitive_at((), word, "ab")
    table = prime_table(standard_site(), words, "ab")
    assert table["{}"] == ()
    assert table["{length}"] == (A, B)


@pytest.mark.parametrize("alphabet", [(), "b", "aa", ("a", 1)])
@pytest.mark.parametrize("stage", [(), (LENGTH,), (WORD,)])
def test_power_decisions_refuse_incomplete_or_malformed_alphabets(alphabet, stage):
    with pytest.raises(ObserverSiteError, match="power-alphabet"):
        power_at(stage, AA, alphabet)
    with pytest.raises(ObserverSiteError, match="power-alphabet"):
        primitive_at(stage, AA, alphabet)


def test_empty_word_primitive_decision_still_validates_the_alphabet():
    assert not primitive_at((WORD,), (), "ab")
    with pytest.raises(ObserverSiteError, match="power-alphabet"):
        primitive_at((WORD,), (), ())


def test_one_length_respecting_observer_is_enough_for_power_search():
    parity = Observer("parity", lambda word: len(word) % 2)
    stage = (parity, WORD)
    assert power_at(stage, AA, "ab") == (A, 2)
    assert primitive_at(stage, ("a", "b"), "ab")


def test_unbounded_resonance_is_refused_instead_of_a_false_negative():
    modulo_three = Observer("mod3", lambda word: len(word) % 3)
    stage = (modulo_three,)
    assert echo(stage, A, AA * 2)
    with pytest.raises(ObserverSiteError, match="stage-observer-not-length-respecting"):
        resonates_at(stage, AA, A)


def test_resonance_exact_exceptions_need_no_length_bound():
    modulo_three = Observer("mod3", lambda word: len(word) % 3)
    assert resonates_at((), AA, A)
    assert resonates_at((), (), A)
    assert resonates_at((modulo_three,), (), A * 3)
    assert not resonates_at((modulo_three,), (), A)


@pytest.mark.parametrize("stage", [(LENGTH,), (BAG,), (CYCLE,), (WORD,), (bounded_reader(1),)])
def test_bounded_resonance_matches_exact_length_witnesses(stage):
    words = words_up_to("ab", 2)
    for factor in words:
        for carrier in words:
            if not factor:
                expected = echo(stage, carrier, ())
            else:
                candidates = [
                    factor * exponent
                    for exponent in range(len(carrier) + 1)
                    if len(factor) * exponent == len(carrier)
                ]
                expected = any(echo(stage, carrier, candidate) for candidate in candidates)
            assert resonates_at(stage, factor, carrier) == expected


def test_mixed_resonance_stage_uses_its_length_respecting_observer():
    modulo_three = Observer("mod3", lambda word: len(word) % 3)
    stage = (modulo_three, LENGTH)
    assert not resonates_at(stage, AA, A)
    assert resonates_at(stage, AA, AA * 2)


def _one_argument_descent_oracle(stage, operation, words):
    """Directly replay both quantifier clauses of Lean ``Descends``."""
    op = {"stitch": stitch, "weave": weave}[operation]
    checked = 0
    violations = []
    for fixed in words:
        for left in words:
            for right in words:
                if not echo(stage, left, right):
                    continue
                for row in ((fixed, fixed, left, right), (left, right, fixed, fixed)):
                    checked += 1
                    x, x_prime, y, y_prime = row
                    if not echo(stage, op(x, y), op(x_prime, y_prime)):
                        violations.append(row)
    return checked, sorted(violations)


def test_descent_includes_unreadable_fixed_operands():
    stage = (bounded_reader(0),)
    words = ((), A)
    assert echo(stage, (), ()) and not echo(stage, A, A)
    report = descends(stage, "stitch", words)
    assert not report.passed and report.checked == 4
    assert (A, A, (), ()) in report.violations
    assert ((), (), A, A) in report.violations
    assert descends(stage, "weave", words).passed
    with pytest.raises(ObserverSiteError, match="operation-does-not-descend"):
        fibre_action(stage, "stitch", words)


@pytest.mark.parametrize("stage", [(), (LENGTH,), (CYCLE,), (bounded_reader(0),), (bounded_reader(1),)])
@pytest.mark.parametrize("operation", ["stitch", "weave"])
def test_descent_agrees_with_both_lean_clauses_on_finite_families(stage, operation):
    words = words_up_to("ab", 2)
    checked, violations = _one_argument_descent_oracle(stage, operation, words)
    report = descends(stage, operation, words)
    assert report.checked == checked
    assert sorted(report.violations) == violations
    assert report.passed == (not violations)


def test_same_name_cannot_replace_an_admitted_observer():
    word_reader = Observer("aliased", lambda word: word, True)
    length_reader = Observer("aliased", len, True)
    coarse, fine = (word_reader,), (length_reader,)
    words = (A, B)
    assert not refines(coarse, fine)
    assert not refines((Observer("length", len, True),), (LENGTH,))
    assert refines((LENGTH,), (LENGTH, WORD)) and refines((), fine)
    with pytest.raises(ObserverSiteError, match="restriction-not-refinement"):
        restriction(coarse, fine, words)
    with pytest.raises(ObserverSiteError, match="stage-not-in-site"):
        undecided_pairs(fine, coarse, words)
    with pytest.raises(ObserverSiteError, match="restriction-not-refinement"):
        restriction_commutes(coarse, fine, "stitch", words)


@pytest.mark.parametrize("name", ["", "x,y", "{x", "x}", None])
def test_ambiguous_stage_labels_are_refused_before_tables_are_built(name):
    observer = Observer(name, len)
    with pytest.raises(ObserverSiteError, match="site-observer-name"):
        substages((observer,))
    with pytest.raises(ObserverSiteError, match="site-observer-name"):
        stage_name((observer,))


def test_stage_name_collision_cannot_corrupt_law_and_prime_tables():
    site = (
        Observer("x,y", lambda word: 0, True),
        Observer("x", lambda word: word, True),
        Observer("y", lambda word: 0, True),
    )
    with pytest.raises(ObserverSiteError, match="site-observer-name"):
        site_law_report(site, (A, B))
    with pytest.raises(ObserverSiteError, match="site-observer-name"):
        prime_table(site, (A, B), "ab")
    site = standard_site()
    assert len({stage_name(stage) for stage in substages(site)}) == 16
    assert site_law_report(site, (A, B)).passed


def test_site_certificate_rejects_a_forged_nonempty_bottom_prime_row(monkeypatch):
    from src.core import certify_observer_site as certificate_module

    actual_prime_table = certificate_module.prime_table

    def forged_prime_table(*args):
        table = actual_prime_table(*args)
        return {**table, "{}": (A,)}

    monkeypatch.setattr(certificate_module, "prime_table", forged_prime_table)
    assert not certify_observer_site_os().passed
