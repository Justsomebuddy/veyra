import pytest

from src.core.certify_observer_arithmetic import certify_observer_arithmetic_va
from src.core.observer_arithmetic import (
    SHADOW_LICENSED,
    bag_primitivity_agreement,
    bag_vector,
    canonical_cut,
    canonical_cut_associativity_failures,
    cut_stitch,
    cyclic_echo,
    descends,
    fibre_action,
    law_table,
    literal_laws_hold,
    nat_shadow,
    observer_arithmetic_checklist,
    parikh_shadow_primitive,
    resonates_at,
    length_divides,
    restriction_commutes,
    standard_stages,
    stitch,
    weave,
    weave_respects_cycle_violations,
)
from src.core.observer_site import BAG, CYCLE, LENGTH, WORD, ObserverSiteError, words_up_to

A, B, AB, BA = ("a",), ("b",), ("a", "b"), ("b", "a")
WORDS = words_up_to("ab", 3)


def test_stitch_and_weave_are_the_docs02_operations():
    assert stitch(AB, A) == ("a", "b", "a")
    assert weave(AB, A) == ("a", "a") and weave(A, AB) == AB and weave((), AB) == ()
    assert literal_laws_hold(WORDS)


def test_descent_pattern_matches_the_lean_cards():
    stitch_descent = {stage[0].name: descends(stage, "stitch", WORDS).passed for stage in standard_stages()}
    weave_descent = {stage[0].name: descends(stage, "weave", WORDS).passed for stage in standard_stages()}
    assert stitch_descent == {"length": True, "bag": True, "cycle": False, "word": True}
    assert weave_descent == {"length": True, "bag": True, "cycle": True, "word": True}
    report = descends((CYCLE,), "stitch", WORDS)
    assert (AB, BA, AB, AB) in report.violations and report.checked > 0
    with pytest.raises(ObserverSiteError, match="operation-does-not-descend"):
        fibre_action((CYCLE,), "stitch", WORDS)


def test_restriction_commutes_with_descending_operations():
    for coarse, fine in (((LENGTH,), (LENGTH, BAG)), ((LENGTH,), (LENGTH, WORD)), ((BAG,), (BAG, WORD))):
        assert restriction_commutes(coarse, fine, "stitch", WORDS)
        assert restriction_commutes(coarse, fine, "weave", WORDS)
    assert restriction_commutes((LENGTH,), (LENGTH, CYCLE), "weave", WORDS)
    with pytest.raises(ObserverSiteError, match="restriction-not-refinement"):
        restriction_commutes((WORD,), (LENGTH,), "stitch", WORDS)
    action = dict(((i, j), k) for i, j, k in fibre_action((LENGTH,), "stitch", WORDS))
    assert action[(1, 2)] == 3 and action[(2, 2)] == -1


def test_natural_numbers_are_the_length_fibre():
    shadow = nat_shadow(WORDS)
    assert shadow.classes == 4 and shadow.lengths == (0, 1, 2, 3)
    assert shadow.stitch_is_addition and shadow.weave_is_multiplication


def test_laws_are_stage_properties():
    rows = {row.stage: row for row in law_table(standard_stages(), WORDS)}
    assert (rows["{bag}"].stitch_commutative, rows["{word}"].stitch_commutative) == (True, False)
    assert (rows["{length}"].weave_commutative, rows["{bag}"].weave_commutative) == (True, False)
    assert (rows["{bag}"].left_distributive, rows["{word}"].left_distributive) == (True, False)
    assert rows["{cycle}"].stitch_commutative and not rows["{cycle}"].stitch_descends
    assert "stitch-comm:a,b" in rows["{word}"].witnesses
    assert "weave-comm:a,b" in rows["{bag}"].witnesses
    assert any(item.startswith("left-dist:aa,a,b") for item in rows["{word}"].witnesses)


def test_canonical_cut_breaks_ax005_while_weave_respects_cycles():
    assert cyclic_echo(AB, BA) and not cyclic_echo(AB + AB, BA + AB)
    assert canonical_cut(("b", "a", "b")) == ("a", "b", "b") and cut_stitch(A, B) == AB
    failures = canonical_cut_associativity_failures(WORDS)
    assert (A, B, AB) in failures
    assert not cyclic_echo(cut_stitch(cut_stitch(A, B), AB), cut_stitch(A, cut_stitch(B, AB)))
    assert weave_respects_cycle_violations(WORDS, 2) == 0 and weave_respects_cycle_violations(WORDS, 3) == 0


def test_bag_primitivity_is_parikh_primitivity():
    assert bag_vector(("a", "b", "a"), "ab") == (2, 1)
    assert parikh_shadow_primitive(("a", "b", "a"), "ab") and not parikh_shadow_primitive(("b", "a", "a", "b"), "ab")
    assert not parikh_shadow_primitive((), "ab")
    assert bag_primitivity_agreement(words_up_to("ab", 5), "ab") == (62, 0)
    assert SHADOW_LICENSED == ("parikh_shadow_primitive",)


def test_resonance_is_a_variable_object():
    nonempty = [word for word in WORDS if word]
    assert all(resonates_at((LENGTH,), u, x) == length_divides(u, x) for u in nonempty for x in nonempty)
    assert (
        resonates_at((WORD,), AB, AB + AB)
        and not resonates_at((WORD,), BA, AB + AB)
        and resonates_at((CYCLE,), BA, AB + AB)
    )
    assert all(
        not resonates_at((LENGTH, WORD), u, x) or resonates_at((LENGTH,), u, x) for u in nonempty for x in nonempty
    )
    assert resonates_at((WORD,), (), ()) and not resonates_at((WORD,), (), A)


def test_checklist_and_certificate():
    cards = observer_arithmetic_checklist()
    assert [card[0][:10] for card in cards] == ["THM_VA_%03d" % index for index in range(1, 15)]
    certificate = certify_observer_arithmetic_va()
    assert certificate.passed and certificate.name == "observer_arithmetic_va"
    assert "AX-005" in certificate.method
