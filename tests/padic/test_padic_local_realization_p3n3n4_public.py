"""Collision-safe direct public-surface checks for P3-N3/N4."""

import src.core.padic_local_realization as direct
import src.core.padic_local_realization_bounded_types as bounded_types
import src.core.padic_local_realization_public as public
import src.core.padic_local_realization_sources as sources
import src.core.padic_local_realization_types as types


def test_p3n34_public_aliases_are_exact_unique_and_closed():
    expected = {
        "P3N34_ARTIFACT_PATH": sources.ARTIFACT_PATH,
        "P3N34_ARTIFACT_SHA256": sources.ARTIFACT_SHA256,
        "P3N34_PREMISE_PATH": sources.PREMISE_PATH,
        "P3N34_PREMISE_SHA256": sources.PREMISE_SHA256,
        "P3N34_PREMISE_THEOREMS": sources.PREMISE_THEOREMS,
        "P3N34_THEOREM_IDS": sources.THEOREM_IDS,
        "P3N34ValidationError": direct.P3N3N4ValidationError,
        "P3N34_NONCLAIMS": types.N34_NONCLAIMS,
        "P3N34Status": types.N34Status,
        "P3N34N3Kind": types.N3Kind,
        "P3N34N4Kind": types.N4Kind,
        "P3N34EqualityStatus": types.EqualityStatus,
        "P3N34FailedBound": types.FailedBound,
        "P3N34FormalFailureKind": types.FormalFailureKind,
        "P3N34Policy": types.N34Policy,
        "P3N34TheoremSource": types.N34TheoremSource,
        "P3N34BridgeDependencyRow": types.BridgeDependencyRow,
        "P3N34BridgeDependencyUnion": types.BridgeDependencyUnion,
        "P3N34AllDepthCoordinateEqualitySource": types.AllDepthCoordinateEqualitySource,
        "P3N34N3Request": types.N3Request,
        "P3N34N4Request": types.N4Request,
        "P3N34N3RealizationJudgment": types.N3RealizationJudgment,
        "P3N34N4EqualityJudgment": types.N4EqualityJudgment,
        "P3N34Open": types.N34Open,
        "P3N34Refuted": types.N34Refuted,
        "P3N34ResourceLimit": types.N34ResourceLimit,
        "P3N34FormalFailure": types.N34FormalFailure,
        "P3N34N3Result": types.N3Result,
        "P3N34N4Result": types.N4Result,
        "P3N34BoundedCoordinateRow": bounded_types.BoundedCoordinateRow,
        "P3N34BoundedCoordinateEqualitySource": (
            bounded_types.BoundedCoordinateEqualitySource
        ),
        "P3N34BoundedEqualityRequest": bounded_types.BoundedEqualityRequest,
        "P3N34BoundedEqualityResult": bounded_types.BoundedEqualityResult,
        "p3n34_all_depth_source": direct.all_depth_source,
        "p3n34_bounded_coordinate_equality_judgment": (
            direct.bounded_coordinate_equality_judgment
        ),
        "p3n34_bounded_coordinate_equality_source": (
            direct.bounded_coordinate_equality_source
        ),
        "p3n34_bounded_equality_request": direct.bounded_equality_request,
        "p3n34_local_realization_judgment": direct.local_realization_judgment,
        "p3n34_n3_dependency_union": direct.n3_dependency_union,
        "p3n34_n3_request": direct.n3_request,
        "p3n34_n4_dependency_union": direct.n4_dependency_union,
        "p3n34_n4_request": direct.n4_request,
        "p3n34_policy": direct.policy,
        "p3n34_scoped_carrier_equality_judgment": (
            direct.scoped_carrier_equality_judgment
        ),
        "p3n34_theorem_source": direct.theorem_source,
        "p3n34_validate_bounded_result": direct.validate_bounded_result,
        "p3n34_validate_n3_result": direct.validate_n3_result,
        "p3n34_validate_n4_result": direct.validate_n4_result,
    }
    assert len(expected) == 48 == len(public.__all__) == len(set(public.__all__))
    assert set(public.__all__) == set(expected)
    assert all(getattr(public, name) is value for name, value in expected.items())


def test_p3n34_public_hashes_and_forbidden_exports():
    assert public.P3N34_ARTIFACT_SHA256 == (
        "db273191f8ca9ab23e182e5ed30c6cd1e328b7c87698fedd6c0992e7b180d2da"
    )
    assert public.P3N34_PREMISE_SHA256 == (
        "3d59ef92d345266d62eedba5418b24fa309a9106c8d8ee0544a934ee043ac27a"
    )
    forbidden = {
        "SCHEMA_ORACLES", "N34CompileOutcome", "compile_sources",
        "capture_sources", "continuity_holds", "required_n34_attacks",
        "schema_digest", "audit_exact_rows", "ATTACK_LABELS", "attack_matrix",
        "run_attack", "policy", "theorem_source", "N34Status", "N3Result",
        "BoundedEqualityResult",
    }
    assert forbidden.isdisjoint(public.__all__)
    assert all(not hasattr(public, name) for name in forbidden)
