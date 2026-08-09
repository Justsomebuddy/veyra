from src.core.compression import CompressionWeights
from src.core.modes import Mode
from src.core.native_number import (
    compare_spectrum_compression,
    cycle_echo,
    cycle_equivalent,
    cyclic_weave_echo,
    native_number_checklist,
    primitive_count_table,
    primitive_phase_profile,
)


def test_cycle_echo_keeps_orbit_not_single_representative():
    echo = cycle_echo(Mode.from_word("baba"))
    assert echo.orbit_size == 2
    assert echo.words == ("abab", "baba")
    assert echo.contains(Mode.from_word("abab"))
    assert cycle_equivalent(Mode.from_word("ab"), Mode.from_word("ba"))


def test_cyclic_weave_echo_avoids_cut_choice():
    mapping = {"a": Mode.from_word("x"), "b": Mode.from_word("yy")}
    left = cyclic_weave_echo(Mode.from_word("ab"), mapping)
    right = cyclic_weave_echo(Mode.from_word("ba"), mapping)
    assert left == right
    assert left.words == ("xyy", "yxy", "yyx")


def test_primitive_count_table_shows_cycle_collapse():
    rows = primitive_count_table(("a", "b"), 3)
    assert [(r.length, r.ordered_primitives, r.cyclic_primitives, r.collapse) for r in rows] == [
        (1, 2, 2, 0),
        (2, 2, 1, 1),
        (3, 6, 2, 4),
    ]


def test_primitive_phase_profile_links_resonance_and_primitivity():
    profile = primitive_phase_profile(Mode.from_word("ab"), Mode.from_word("baba"))
    assert profile.part_primitive
    assert not profile.whole_primitive
    assert profile.exponent == 2
    assert profile.resonance.cyclic
    assert profile.resonance.phase_offsets == (1, 3)
    assert profile.part_echo == cycle_echo(Mode.from_word("ba"))


def test_spectrum_compression_comparison_keeps_both_orders():
    rows = compare_spectrum_compression(
        Mode.from_word("abac"),
        [Mode.from_word("ab"), Mode.from_word("ac"), Mode.from_word("cc")],
        max_defects=1,
        weights=CompressionWeights(defect_weight=1.0),
    )
    assert rows[0].part == Mode.from_word("ab")
    assert rows[0].spectrum_rank == 0
    assert rows[0].compression_rank is not None
    assert rows[0].saving == 1.0
    assert rows[-1].compression_rank is None


def test_native_number_checklist_names_all_sprint_a_surfaces():
    text = "\n".join(native_number_checklist())
    assert "cycle echo" in text
    assert "ordered primitive" in text
    assert "spectrum rank" in text
    assert "aura echoes" in text


def test_cycle_divisibility_rows_expose_lifts_and_obstructions():
    from src.core.native_number import cycle_divisibility_row

    hit = cycle_divisibility_row(Mode.from_word("ba"), Mode.from_word("abab"))
    miss = cycle_divisibility_row(Mode.from_word("aba"), Mode.from_word("abab"))
    assert hit.status == "divides"
    assert hit.exponent == 2
    assert hit.lift_word == "baba"
    assert miss.status == "blocked"
    assert miss.obstruction == "length-obstruction"


def test_prime_obstruction_rows_keep_numeric_prime_as_shadow():
    from src.core.native_number import prime_obstruction_rows

    rows = prime_obstruction_rows([Mode.from_word("ab"), Mode.from_word("aa"), Mode.from_word("a")])
    assert [row.status for row in rows] == ["variant", "blocked", "blocked"]
    assert rows[0].profile.ordered_resonance_prime
    assert rows[1].obstruction == "cycle-power"
    assert rows[2].obstruction == "unit-or-silent"


def test_rank_factor_comparison_keeps_factor_lift_separate():
    from src.core.native_number import native_number_theory_checklist, rank_factor_comparison

    rows = rank_factor_comparison(Mode.from_word("abab"), [Mode.from_word("ab"), Mode.from_word("ba"), Mode.from_word("aa")], 0, CompressionWeights(defect_weight=1.0))
    assert [row.factor_status for row in rows] == ["divides", "divides", "blocked"]
    assert rows[0].compression_rank == 0
    assert rows[-1].compression_rank is None
    assert len(native_number_theory_checklist()) == 4
