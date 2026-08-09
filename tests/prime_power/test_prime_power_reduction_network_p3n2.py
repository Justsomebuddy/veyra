"""Positive finite/symbolic and boundary checks for P3-N2."""

from src.core.prime_power_reduction_network import (
    BoundaryStatus, FiniteRelation, N2Open, N2Refutation, N2ResourceLimit,
    PrimePowerReductionJudgment, RelativeStatus, ResultStatus, SymbolicKind,
    path_pressure_candidate, prime_power_reduction_judgment,
    refute_wrong_path_candidate, refute_wrong_square_candidate,
    report_missing_symbolic_evidence, square_pressure_candidate, validate_n2_open,
    validate_n2_refutation, validate_prime_power_reduction_result,
)
from prime_power_reduction_network_fixture import exact_n2_package
import pytest

pytestmark = pytest.mark.requires_lean


def test_positive_two_lane_judgment_replays():
    package = exact_n2_package()
    result = prime_power_reduction_judgment(package)
    replay = validate_prime_power_reduction_result(package, result)
    assert type(result) is PrimePowerReductionJudgment
    assert replay == result and replay is not result
    assert result.finite_status is RelativeStatus.ESTABLISHED_RELATIVE_TO_LEDGER
    assert result.symbolic_status is RelativeStatus.ESTABLISHED_RELATIVE_TO_LEDGER
    assert result.symbolic_kind is SymbolicKind.THIN_REDUCTION_PATH_COHERENT_RELATIVE_TO_TOWER


def test_identity_and_strict_relations_have_exact_scope_and_witnesses():
    result = prime_power_reduction_judgment(exact_n2_package())
    identities = [x for x in result.finite_arrows if x.fine_depth == x.coarse_depth]
    strict = [x for x in result.finite_arrows if x.fine_depth > x.coarse_depth]
    assert len(identities) == 3 and len(strict) == 3
    assert all(x.relation is FiniteRelation.TRANSLATION_ISOMORPHIC_ON_EXACT_FINITE_SCOPE
               and x.separator_family_ids is None for x in identities)
    assert all(x.relation is FiniteRelation.STRICT_REFINEMENT_ON_EXACT_FINITE_SCOPE
               and x.separator_family_ids for x in strict)


def test_arithmetic_tables_are_total_and_squares_commute():
    package = exact_n2_package()
    result = prime_power_reduction_judgment(package)
    assert all(x.total and x.square_commutes and x.preservation for x in result.finite_arrows)
    for source in package.finite.arrows:
        target_modulus = package.prime.p ** (source.coarse_depth + 1)
        assert [(x.source_residue, x.target_residue) for x in source.rows] == [
            (x, x % target_modulus)
            for x in range(package.prime.p ** (source.fine_depth + 1))
        ]


def test_symbolic_source_is_stronger_and_does_not_consume_completion_or_c2():
    result = prime_power_reduction_judgment(exact_n2_package())
    assert len(result.theorem_ids) == len(result.axiom_rows) == 7
    assert result.proof_witness_independence is RelativeStatus.ESTABLISHED_RELATIVE_TO_LEDGER
    assert result.completed_carrier is BoundaryStatus.NOT_CLAIMED
    assert not result.pomega2_final_judgment_consumed
    assert not result.p3c2_status_consumed
    assert result.promotions == 0


def test_policy_refusal_is_typed_and_has_no_theorem_payload():
    package = exact_n2_package(max_captured_bytes=1)
    result = prime_power_reduction_judgment(package)
    assert type(result) is N2ResourceLimit
    assert result.status is ResultStatus.RESOURCE_LIMIT
    assert not hasattr(result, "theorem_ids")


def test_table_row_refusal_precedes_semantic_reconstruction(monkeypatch):
    import src.core.prime_power_reduction_network_runtime as runtime

    package = exact_n2_package(max_table_rows=1)
    monkeypatch.setattr(runtime, "finite_reduction_source",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("late rebuild")))
    result = runtime.prime_power_reduction_judgment(package)
    assert type(result) is N2ResourceLimit
    assert result.failed_bound.value == "table-rows"


def test_arithmetic_p3t_digest_binds_prime_and_declared_depths():
    base = exact_n2_package()
    foreign = exact_n2_package(p=3)
    shallow = exact_n2_package(depths=(0, 1))
    digests = {base.finite.p3t_raw_source.network_digest,
               foreign.finite.p3t_raw_source.network_digest,
               shallow.finite.p3t_raw_source.network_digest}
    assert len(digests) == 3
    assert tuple(x.observer_id for x in base.finite.p3t_raw_source.observers) == (
        "rho-depth-0", "rho-depth-1", "rho-depth-2")


def test_missing_symbolic_evidence_is_open_only_for_admissible_finite_source():
    package = exact_n2_package()
    result = report_missing_symbolic_evidence(package.finite)
    assert type(result) is N2Open and result.status is ResultStatus.OPEN
    assert validate_n2_open(package.finite, result) == result


def test_valid_wrong_square_and_path_are_typed_refutations():
    package = exact_n2_package()
    square = square_pressure_candidate(package.finite, "integer:2", 1, 0, 1)
    square_result = refute_wrong_square_candidate(package, square)
    assert type(square_result) is N2Refutation
    assert square_result.status is ResultStatus.REFUTED
    assert square_result.expected_target_residue == 0
    assert validate_n2_refutation(package, square, square_result) == square_result

    path = path_pressure_candidate(package.finite, (2, 1, 0), 3, 0)
    path_result = refute_wrong_path_candidate(package, path)
    assert type(path_result) is N2Refutation
    assert path_result.expected_target_residue == 1
    assert validate_n2_refutation(package, path, path_result) == path_result


def test_pressure_lane_preserves_resource_precedence():
    base = exact_n2_package()
    candidate = path_pressure_candidate(base.finite, (2, 1, 0), 3, 0)
    refused = exact_n2_package(max_table_rows=1)
    result = refute_wrong_path_candidate(refused, candidate)
    assert type(result) is N2ResourceLimit
    assert result.failed_bound.value == "table-rows"
    malformed_candidate_result = refute_wrong_path_candidate(refused, object())
    assert malformed_candidate_result == result
