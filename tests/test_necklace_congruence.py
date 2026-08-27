import pytest

from src.core.modes import Mode
from src.core.native_number import primitive_count_table
from src.core.necklace_congruence import (
    GaussCongruenceWitness,
    OrbitDichotomyWitness,
    fermat_orbit_witness,
    gauss_congruence_witness,
    mobius_shadow_value,
    necklace_congruence_checklist,
    orbit_dichotomy_witness,
    rotation_orbit_rows,
)


def test_rotation_orbit_rows_exact_p3_k2():
    rows = rotation_orbit_rows(("a", "b"), 3)
    assert len(rows) == 4
    assert sum(1 for row in rows if row.constant) == 2
    assert all(row.orbit_size == 1 for row in rows if row.constant)
    assert all(row.orbit_size == 3 for row in rows if not row.constant)
    assert sum(row.orbit_size for row in rows) == 8


def test_orbit_dichotomy_witnessed_for_primes():
    for prime, alphabet in ((2, ("a", "b")), (3, ("a", "b")), (5, ("a", "b")), (3, ("a", "b", "c")), (5, ("a", "b", "c"))):
        witness = orbit_dichotomy_witness(alphabet, prime)
        assert isinstance(witness, OrbitDichotomyWitness)
        assert witness.status == "witnessed"
        assert witness.obstruction == "none"
        assert witness.counterexample == ""
        assert witness.orbit_sizes in ((1, prime), (prime,)) or witness.orbit_sizes == (1, prime)
        assert witness.total_words == len(alphabet) ** prime
        assert witness.nonconstant_count == len(alphabet) ** prime - len(alphabet)


def test_orbit_dichotomy_blocked_for_composite_length_with_counterexample():
    witness = orbit_dichotomy_witness(("a", "b"), 4)
    assert witness.status == "blocked"
    assert witness.obstruction == "nonprime-length"
    assert not witness.dichotomy
    assert witness.counterexample == "abab"
    assert 2 in witness.orbit_sizes


def test_fermat_orbit_witness_exact_counts():
    witness = fermat_orbit_witness(("a", "b"), 3)
    assert witness.status == "witnessed"
    assert witness.nonconstant_count == 6
    assert witness.full_orbit_count == 2
    assert witness.partition_exact
    five = fermat_orbit_witness(("a", "b"), 5)
    assert five.status == "witnessed"
    assert five.nonconstant_count == 30
    assert five.full_orbit_count == 6
    seven = fermat_orbit_witness(("a", "b", "c"), 5)
    assert seven.status == "witnessed"
    assert seven.nonconstant_count == 240
    assert seven.full_orbit_count == 48


def test_fermat_orbit_witness_blocked_on_composite():
    witness = fermat_orbit_witness(("a", "b"), 6)
    assert witness.status == "blocked"
    assert witness.obstruction == "nonprime-length"
    assert not witness.partition_exact


def test_gauss_congruence_witnessed_and_shadow_matches():
    for length in range(1, 11):
        for alphabet in (("a", "b"), ("a", "b", "c")):
            witness = gauss_congruence_witness(alphabet, length)
            assert isinstance(witness, GaussCongruenceWitness)
            assert witness.status == "witnessed", (length, alphabet, witness.obstruction)
            assert witness.all_orbits_full
            assert witness.shadow_match
            assert witness.primitive_count % length == 0
            assert witness.mobius_shadow == witness.primitive_count


def test_gauss_exact_small_values():
    assert gauss_congruence_witness(("a", "b"), 4).primitive_count == 12
    assert gauss_congruence_witness(("a", "b"), 6).primitive_count == 54
    assert gauss_congruence_witness(("a", "b", "c"), 4).primitive_count == 72


def test_gauss_blocked_on_silent_length():
    witness = gauss_congruence_witness(("a", "b"), 0)
    assert witness.status == "blocked"
    assert witness.obstruction == "silent-length"


def test_mobius_shadow_values():
    assert [mobius_shadow_value(n) for n in range(1, 13)] == [1, -1, -1, 0, -1, 1, -1, 0, 0, 1, -1, 0]
    with pytest.raises(ValueError):
        mobius_shadow_value(0)


def test_rotation_orbit_rows_rejects_nonpositive_length():
    with pytest.raises(ValueError):
        rotation_orbit_rows(("a", "b"), 0)


def test_consistency_with_primitive_count_table():
    table = primitive_count_table(("a", "b"), 6)
    for row in table:
        witness = gauss_congruence_witness(("a", "b"), row.length)
        assert witness.primitive_count == row.ordered_primitives
        assert witness.primitive_count // row.length == row.cyclic_primitives


def test_checklist_present():
    checklist = necklace_congruence_checklist()
    assert len(checklist) == 5
    assert any("cycle_echo" in item for item in checklist)
    assert any("witnessed/blocked" in item for item in checklist)


def test_hostile_single_letter_alphabet():
    witness = orbit_dichotomy_witness(("a",), 3)
    assert witness.status == "witnessed"
    assert witness.nonconstant_count == 0
    fermat = fermat_orbit_witness(("a",), 3)
    assert fermat.status == "witnessed"
    assert fermat.full_orbit_count == 0
