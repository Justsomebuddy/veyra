import pytest

from src.core.certify_observer_site import certify_observer_site_os
from src.core.observer_site import (
    BAG,
    CYCLE,
    LENGTH,
    SILENT,
    WORD,
    Observer,
    ObserverSiteError,
    PairStatus,
    apart,
    bounded_reader,
    cotransitivity_failures,
    echo,
    echo_classes,
    forces_decided,
    internal_equal,
    observer_site_checklist,
    pair_status,
    power_at,
    prime_monotonicity_violations,
    prime_table,
    primitive_at,
    readable,
    refines,
    restriction,
    site_law_report,
    stage_name,
    standard_site,
    substages,
    undecided_pairs,
    words_up_to,
)

AB, BA, ABA, ABAB = ("a", "b"), ("b", "a"), ("a", "b", "a"), ("a", "b", "a", "b")
SITE = standard_site()
WORDS = words_up_to("ab", 3)


def test_stage_laws_hold_on_the_whole_lattice_without_silence():
    report = site_law_report(SITE, WORDS)
    assert report.passed
    assert (report.stages, report.pairs, report.silent_pairs) == (16, 225, 0)
    assert len(substages(SITE)) == 16 and substages(SITE)[0] == ()


def test_excluded_middle_for_equality_fails_at_the_length_stage():
    assert echo((LENGTH,), AB, BA) and not apart((LENGTH,), AB, BA)
    assert apart(SITE, AB, BA) and not internal_equal(SITE, AB, BA)
    assert not forces_decided(SITE, (LENGTH,), AB, BA)
    assert forces_decided(SITE, SITE, AB, BA)
    rows = {(row.left, row.right): row for row in undecided_pairs(SITE, (LENGTH,), WORDS)}
    assert rows[(AB, BA)].splitting_observers == ("word",)
    assert rows[(AB, BA)].status_at_stage is PairStatus.ECHO
    assert rows[(("a", "a"), AB)].splitting_observers == ("bag", "cycle", "word")
    assert undecided_pairs(SITE, SITE, WORDS) == ()


def test_apart_stages_are_up_closed_and_echo_stages_are_not():
    apart_stages = {stage_name(stage) for stage in substages(SITE) if apart(stage, AB, BA)}
    echo_stages = {stage_name(stage) for stage in substages(SITE) if echo(stage, AB, BA)}
    for stage in substages(SITE):
        for finer in substages(SITE):
            if refines(stage, finer) and stage_name(stage) in apart_stages:
                assert stage_name(finer) in apart_stages
    assert "{length}" in echo_stages and "{length,word}" not in echo_stages


def test_silence_breaks_cotransitivity_and_transitivity_of_internal_equality():
    reader = bounded_reader(1)
    assert reader.read(AB) is SILENT and reader.read(("a",)) == ("a",)
    triples = cotransitivity_failures((reader,), (("a",), AB, ("b",)))
    assert (("a",), AB, ("b",)) in triples
    assert internal_equal((reader,), ("a",), AB) and internal_equal((reader,), AB, ("b",))
    assert not internal_equal((reader,), ("a",), ("b",))
    assert pair_status((reader,), ("a",), AB) is PairStatus.SILENT
    assert not readable((reader,), AB) and readable((reader,), ("a",))
    assert cotransitivity_failures(SITE, WORDS) == ()
    mixed = site_law_report((LENGTH, reader), WORDS)
    assert mixed.passed and mixed.silent_pairs > 0


def test_echo_classes_form_a_presheaf_along_refinement():
    coarse = echo_classes((LENGTH,), WORDS)
    assert [len(group) for group in coarse.classes] == [1, 2, 4, 8]
    fine = echo_classes((LENGTH, BAG), WORDS)
    assert restriction((LENGTH,), (LENGTH, BAG), WORDS) == (0, 1, 1, 2, 2, 2, 3, 3, 3, 3)
    assert len(fine.classes) == 10
    partial = echo_classes((bounded_reader(1),), WORDS)
    assert partial.unreadable == WORDS[3:]
    with pytest.raises(ObserverSiteError, match="restriction-not-refinement"):
        restriction((WORD,), (LENGTH,), WORDS)


def test_primitivity_is_stage_relative_and_monotone():
    assert not primitive_at((LENGTH,), ABA, "ab") and power_at((LENGTH,), ABA, "ab") == (("a",), 3)
    assert primitive_at((BAG,), ABA, "ab") and primitive_at((CYCLE,), ABA, "ab") and primitive_at((WORD,), ABA, "ab")
    assert not primitive_at((WORD,), ABAB, "ab") and not primitive_at((CYCLE,), BA + BA, "ab")
    assert (
        not primitive_at((BAG,), BA + AB, "ab")
        and primitive_at((CYCLE,), BA + AB, "ab")
        and primitive_at((WORD,), BA + AB, "ab")
    )
    assert primitive_at((LENGTH,), ("a",), "ab") and not primitive_at((LENGTH,), ("a", "a"), "ab")
    table = prime_table(SITE, WORDS[1:], "ab")
    assert table["{length}"] == (("a",), ("b",))
    assert AB in table["{word}"] and ABAB not in table["{word}"]
    assert prime_monotonicity_violations(SITE, WORDS[1:], "ab") == 0


def test_bounds_and_refusals():
    with pytest.raises(ObserverSiteError, match="stage-observer-not-length-respecting"):
        power_at((Observer("weight", len),), AB, "ab")
    with pytest.raises(ObserverSiteError, match="site-duplicate-name"):
        substages((LENGTH, LENGTH))
    with pytest.raises(ObserverSiteError, match="site-size"):
        substages(tuple(Observer(str(index), len) for index in range(7)))
    with pytest.raises(ObserverSiteError, match="stage-not-in-site"):
        undecided_pairs((LENGTH,), (WORD,), WORDS)
    with pytest.raises(ObserverSiteError, match="presentations"):
        site_law_report(SITE, ())
    with pytest.raises(ObserverSiteError, match="power-word-length"):
        power_at((WORD,), (), "ab")


def test_checklist_and_certificate():
    cards = observer_site_checklist()
    assert len(cards) == 19 and [card[0][:10] for card in cards] == ["THM_OS_%03d" % index for index in range(1, 20)]
    certificate = certify_observer_site_os()
    assert certificate.passed and certificate.name == "observer_site_os"
    assert "excluded middle" in certificate.method
