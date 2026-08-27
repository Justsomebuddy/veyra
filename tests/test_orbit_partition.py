from src.core.doctrinal_induction import InductionDoctrine, license_all_depth, uniformity_witness
from src.core.native_runtime import nod, rez
from src.core.necklace_congruence import fermat_orbit_witness
from src.core.orbit_partition import (
    Di2Evidence,
    fermat_family_contract,
    orbit_partition_checklist,
    partition_evidence,
    prime_length_witness,
    tally_bomb_contract,
)

DOCTRINE = InductionDoctrine("di2.test.v1", "alphabet-extension")


def _anchor(name: str = "di2-work"):
    return nod(rez(name), name)


def test_prime_length_witness_accepts_primes():
    for length in (2, 3, 5, 7):
        witness = prime_length_witness(_anchor(), length)
        assert witness.prime, length
        assert witness.status == "witnessed"
        assert all(row.division_status == "residual" for row in witness.rows)
        assert all(row.residual_tacts > 0 for row in witness.rows)


def test_prime_length_witness_blocks_composites_with_exact_divisor():
    witness = prime_length_witness(_anchor(), 4)
    assert not witness.prime
    assert witness.obstruction == "composite-length"
    assert witness.rows[-1].candidate == 2
    assert witness.rows[-1].division_status == "exact"
    short = prime_length_witness(_anchor(), 1)
    assert short.obstruction == "length-too-short"


def test_partition_evidence_prime_cells_witnessed():
    evidence = partition_evidence(_anchor(), 3, 2)
    assert isinstance(evidence, Di2Evidence)
    assert evidence.status == "witnessed"
    assert evidence.congruent
    assert len(evidence.fix_mode.breath.tacts) == 2
    assert len(evidence.full_mode.breath.tacts) == 2
    assert len(evidence.tally_mode.breath.tacts) == 6


def test_partition_evidence_dichotomy_fails_at_composite_length():
    evidence = partition_evidence(_anchor(), 4, 2)
    assert evidence.status == "blocked"
    assert evidence.obstruction == "dichotomy-failure"


def test_fermat_family_licensed_p3():
    license_row = license_all_depth(
        DOCTRINE, fermat_family_contract(3), _anchor(), (1, 2, 3, 4)
    )
    assert license_row.status == "licensed"
    assert license_row.obstruction == "none"
    assert license_row.max_depth == 4
    assert all(row.valid for row in license_row.probes)


def test_fermat_family_licensed_p5():
    license_row = license_all_depth(
        DOCTRINE, fermat_family_contract(5), _anchor(), (1, 2, 3)
    )
    assert license_row.status == "licensed"
    assert all(row.valid for row in license_row.probes)


def test_fermat_family_uniform_under_anchor_renaming():
    witness = uniformity_witness(DOCTRINE, fermat_family_contract(3))
    assert witness.status == "witnessed"
    assert witness.echoed


def test_composite_length_blocks_at_factory():
    license_row = license_all_depth(
        DOCTRINE, fermat_family_contract(4), _anchor(), (1, 2)
    )
    assert license_row.status == "blocked"
    assert license_row.obstruction == "composite-length"


def test_tally_bomb_blocks_at_exact_depth():
    license_row = license_all_depth(
        DOCTRINE, tally_bomb_contract(3, 3), _anchor(), (1, 2, 3, 4)
    )
    assert license_row.status == "blocked"
    assert license_row.obstruction == "step-invalid-at-depth:3"


def test_cross_tie_with_n8_full_orbit_counts():
    for length, depth, alphabet in ((3, 2, ("a", "b")), (5, 3, ("a", "b", "c"))):
        evidence = partition_evidence(_anchor(), length, depth)
        n8 = fermat_orbit_witness(alphabet, length)
        assert evidence.status == "witnessed"
        assert n8.status == "witnessed"
        assert len(evidence.full_mode.breath.tacts) == n8.full_orbit_count
        assert len(evidence.tally_mode.breath.tacts) == n8.nonconstant_count


def test_checklist_present():
    checklist = orbit_partition_checklist()
    assert len(checklist) == 5
    assert any("never by counting rotations" in item for item in checklist)
    assert any("weave" in item for item in checklist)
