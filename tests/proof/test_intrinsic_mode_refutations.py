from src.core.intrinsic_mode_refutations import erasure_boundary_rows


def test_label_erasure_does_not_reflect_general_cyclic_resonance():
    label = erasure_boundary_rows()[0]
    assert label.intrinsic_echo
    assert not label.cyclic_resonance
    assert label.phase_offsets == ()
    assert label.separated


def test_phase_offsets_are_not_recoverable_from_erased_pair():
    phase = erasure_boundary_rows()[1]
    assert phase.intrinsic_echo
    assert phase.cyclic_resonance
    assert phase.phase_offsets == (1, 3)
    assert "(0, 2) vs (1, 3)" in phase.finding
    assert phase.separated


def test_silent_intrinsic_reflexivity_is_not_word_cyclic_resonance():
    silent = erasure_boundary_rows()[2]
    assert silent.intrinsic_echo
    assert not silent.cyclic_resonance
    assert silent.phase_offsets == ()
    assert silent.separated


def test_all_refutations_state_the_non_equivalence_boundary():
    rows = erasure_boundary_rows()
    assert len(rows) == 3
    assert all(row.separated for row in rows)
    assert all("neither reflects" in row.boundary for row in rows)
