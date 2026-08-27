from src.core.observer_lattice import (
    CommutationDoctrine,
    TraceEcho,
    doctrine,
    foata_layers,
    fragility_spectrum,
    observer_lattice_checklist,
    primitivity_row,
    refinement_row,
    trace_class,
    transfer_row,
    verify_class_closure,
)

ABC = ("a", "b", "c")
D_WORD = doctrine("word", ABC, ())
D_AB = doctrine("ab", ABC, (("a", "b"),))
D_AB_AC = doctrine("ab-ac", ABC, (("a", "b"), ("a", "c")))
D_BAG = doctrine("bag", ABC, (("a", "b"), ("a", "c"), ("b", "c")))


def test_doctrine_rejects_reflexive_and_foreign_pairs():
    assert doctrine("bad", ABC, (("a", "a"),)).obstruction == "invalid-pair"
    assert doctrine("bad2", ABC, (("a", "z"),)).obstruction == "invalid-pair"


def test_trace_class_word_node_is_singleton():
    echo = trace_class(D_WORD, tuple("aabb"))
    assert isinstance(echo, TraceEcho)
    assert echo.size == 1


def test_trace_class_bag_node_counts_permutations():
    echo = trace_class(D_BAG, tuple("aabbcc"))
    assert isinstance(echo, TraceEcho)
    assert echo.size == 90
    assert verify_class_closure(D_BAG, echo)


def test_trace_class_refuses_at_cap():
    refusal = trace_class(D_BAG, tuple("aabbcc"), cap=10)
    assert refusal == ("class-size-refusal", 10)


def test_tampered_class_fails_closure():
    echo = trace_class(D_AB, tuple("aabb"))
    assert isinstance(echo, TraceEcho)
    dropped = TraceEcho(echo.doctrine_id, frozenset(sorted(echo.words)[:-1]))
    assert not verify_class_closure(D_AB, dropped)


def test_foata_layers_reconstruct_multiset_and_respect_dependence():
    layers = foata_layers(D_AB_AC, tuple("aabbcc"))
    flattened = tuple(sorted(letter for layer in layers for letter in layer))
    assert flattened == tuple(sorted("aabbcc"))
    assert all(len(set(layer)) == len(layer) for layer in layers)


def test_refinement_rows():
    assert refinement_row(D_WORD, D_BAG).status == "witnessed"
    reversed_row = refinement_row(D_BAG, D_WORD)
    assert reversed_row.status == "blocked"
    assert reversed_row.obstruction == "not-a-refinement"
    assert len(reversed_row.extra_pairs) == 3


def test_primitivity_jumps_for_aabb():
    fine = primitivity_row(D_WORD, tuple("aabb"))
    coarse = primitivity_row(D_AB, tuple("aabb"))
    assert fine.primitive and fine.class_size == 1
    assert not coarse.primitive
    assert coarse.power_word == "abab"
    assert coarse.power_root == "ab" and coarse.power_exponent == 2


def test_transfer_row_break_exhibit_outside_fine():
    row = transfer_row(D_WORD, D_AB, tuple("aabb"))
    assert row.status == "witnessed"
    assert row.fine_primitive and not row.coarse_primitive
    assert row.omega_word == "abab" and row.omega_exponent == 2
    assert row.omega_outside_fine


def test_transfer_row_blocked_on_non_refinement():
    row = transfer_row(D_BAG, D_WORD, tuple("aabb"))
    assert row.status == "blocked"
    assert row.obstruction == "not-a-refinement"


def test_fragility_spectrum_aabbcc_breaks_exactly_at_bc_edge():
    chain = (D_WORD, D_AB, D_AB_AC, D_BAG)
    report = fragility_spectrum(chain, tuple("aabbcc"))
    assert report.status == "witnessed"
    assert [row.primitive for row in report.nodes] == [True, True, True, False]
    assert report.first_break_edge == "ab-ac->bag"
    final = report.edges[-1]
    assert final.omega_word == "abcabc"
    assert final.omega_root == "abc" and final.omega_exponent == 2
    assert final.omega_outside_fine


def test_fragility_spectrum_stable_word_never_breaks():
    chain = (D_WORD, D_AB, D_BAG)
    report = fragility_spectrum(chain, tuple("aab"))
    assert report.status == "witnessed"
    assert report.first_break_edge == ""
    assert all(row.primitive for row in report.nodes)


def test_spectrum_chain_too_short_blocked():
    report = fragility_spectrum((D_WORD,), tuple("aabb"))
    assert report.status == "blocked"
    assert report.obstruction == "chain-too-short"


def test_monotonicity_holds_on_sample_lattice():
    words = [tuple("aabb"), tuple("abab"), tuple("aabbcc"), tuple("abc"), tuple("aabc")]
    chain = (D_WORD, D_AB, D_AB_AC, D_BAG)
    for word in words:
        rows = [primitivity_row(node, word) for node in chain]
        for fine, coarse in zip(rows, rows[1:]):
            assert not (coarse.primitive and not fine.primitive), word


def test_checklist_present():
    checklist = observer_lattice_checklist()
    assert len(checklist) == 5
    assert any("omega exhibit" in item for item in checklist)
    assert any("refuse, never truncate" in item for item in checklist)
