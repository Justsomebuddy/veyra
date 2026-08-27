from src.core.break_locus import (
    BreakLocus,
    break_locus,
    break_locus_checklist,
    cross_check_full_lattice,
    delta_pairs,
    nonprincipal_sweep,
    pair_projection,
    power_candidates,
)

AB = ("a", "b")
ABC = ("a", "b", "c")


def test_pair_projection_and_delta():
    word = tuple("aabbcc")
    assert pair_projection(word, "a", "b") == tuple("aabb")
    assert pair_projection(word, "b", "c") == tuple("bbcc")
    target = tuple("abcabc")
    assert delta_pairs(word, target, ABC) == (("a", "b"), ("a", "c"), ("b", "c"))
    assert delta_pairs(word, tuple("aabbc") + ("c",), ABC) == ()
    assert delta_pairs(word, tuple("aabbcd"), ("a", "b", "c", "d")) is None


def test_power_candidates_aabb():
    rows = power_candidates(tuple("aabb"), AB)
    words = {row.power_word for row in rows}
    assert words == {"abab", "baba"}
    assert all(row.exponent == 2 for row in rows)


def test_break_locus_known_cells():
    aabb = break_locus(tuple("aabb"), AB)
    assert aabb.minimal_deltas == ((("a", "b"),),)
    assert aabb.principal and not aabb.literal_power

    aabbcc = break_locus(tuple("aabbcc"), ABC)
    assert aabbcc.minimal_deltas == (((("a", "b")), ("a", "c"), ("b", "c")),)
    assert aabbcc.principal

    abab = break_locus(tuple("abab"), AB)
    assert abab.literal_power
    assert abab.minimal_deltas == ((),)


def test_break_locus_absolutely_primitive_on_odd_multiset():
    locus = break_locus(tuple("aab"), AB)
    assert isinstance(locus, BreakLocus)
    assert locus.absolutely_primitive
    assert locus.minimal_deltas == ()
    check = cross_check_full_lattice(tuple("aab"), AB)
    assert check.status == "witnessed"
    assert check.mismatches == ()


def test_break_locus_blocks_foreign_word():
    locus = break_locus(tuple("axb"), AB)
    assert locus.status == "blocked"
    assert locus.obstruction == "foreign-or-empty-word"


def test_cross_check_full_lattice_zero_mismatch():
    for word, alphabet in (
        (tuple("aabb"), AB),
        (tuple("abab"), AB),
        (tuple("aabbcc"), ABC),
        (tuple("aabc"), ABC),
        (tuple("abc"), ABC),
        (tuple("aabbc"), ABC),
    ):
        report = cross_check_full_lattice(word, alphabet)
        assert report.status == "witnessed", (word, report.mismatches)
        assert report.mismatches == ()
        assert report.refused_doctrines == 0
        assert report.doctrines_checked == 2 ** (len(alphabet) * (len(alphabet) - 1) // 2)


def test_sweep_shape_structure_abc222():
    report = nonprincipal_sweep(ABC, (2, 2, 2))
    assert report.status == "witnessed"
    assert report.words_scanned == 90
    assert report.literal_powers + report.absolutely_primitive + report.principal + len(report.nonprincipal_words) == 90
    assert report.absolutely_primitive == 0
    assert report.max_locus_size >= 1


def test_sweep_refuses_oversize():
    report = nonprincipal_sweep(ABC, (4, 4, 4), word_cap=100)
    assert report.status == "refused"
    assert report.obstruction == "sweep-size-refusal"


def test_sweep_invalid_shape_blocked():
    report = nonprincipal_sweep(ABC, (2, 2), word_cap=100)
    assert report.status == "blocked"
    assert report.obstruction == "invalid-shape"


def test_principality_pinned_on_exhaustively_scanned_shapes():
    """Pinned AFTER observation: 6285 words, zero non-principal loci."""
    expected = (
        (("a", "b"), (3, 3), 20, 2),
        (("a", "b"), (4, 2), 15, 3),
        (("a", "b"), (4, 4), 70, 6),
        (("a", "b", "c"), (2, 2, 2), 90, 6),
        (("a", "b", "c"), (2, 2, 4), 420, 12),
        (("a", "b", "c"), (4, 4, 2), 3150, 30),
        (("a", "b", "c", "d"), (2, 2, 2, 2), 2520, 24),
    )
    for alphabet, counts, scanned, literal in expected:
        report = nonprincipal_sweep(alphabet, counts)
        assert report.status == "witnessed"
        assert report.words_scanned == scanned
        assert report.literal_powers == literal
        assert report.absolutely_primitive == 0
        assert report.nonprincipal_words == ()
        assert report.max_locus_size == 1
        assert report.principal == scanned - literal


def test_checklist_present():
    checklist = break_locus_checklist()
    assert len(checklist) == 5
    assert any("cross-checked, not assumed" in item for item in checklist)
    assert any("refuse, never truncate" in item for item in checklist)
