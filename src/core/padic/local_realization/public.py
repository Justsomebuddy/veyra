"""Collision-safe public aliases for prime-power P3-N3/N4."""

from __future__ import annotations

from . import core as _p3n34
from . import sources as _sources
from . import types as _types

P3N34_ARTIFACT_PATH = _sources.ARTIFACT_PATH
P3N34_ARTIFACT_SHA256 = _sources.ARTIFACT_SHA256
P3N34_PREMISE_PATH = _sources.PREMISE_PATH
P3N34_PREMISE_SHA256 = _sources.PREMISE_SHA256
P3N34_PREMISE_THEOREMS = _sources.PREMISE_THEOREMS
P3N34_THEOREM_IDS = _sources.THEOREM_IDS

P3N34ValidationError = _p3n34.P3N3N4ValidationError
P3N34_NONCLAIMS = _types.N34_NONCLAIMS
P3N34Status = _types.N34Status
P3N34N3Kind = _types.N3Kind
P3N34N4Kind = _types.N4Kind
P3N34EqualityStatus = _types.EqualityStatus
P3N34FailedBound = _types.FailedBound
P3N34FormalFailureKind = _types.FormalFailureKind
P3N34Policy = _types.N34Policy
P3N34TheoremSource = _types.N34TheoremSource
P3N34BridgeDependencyRow = _types.BridgeDependencyRow
P3N34BridgeDependencyUnion = _types.BridgeDependencyUnion
P3N34AllDepthCoordinateEqualitySource = _types.AllDepthCoordinateEqualitySource
P3N34N3Request = _types.N3Request
P3N34N4Request = _types.N4Request
P3N34N3RealizationJudgment = _types.N3RealizationJudgment
P3N34N4EqualityJudgment = _types.N4EqualityJudgment
P3N34Open = _types.N34Open
P3N34Refuted = _types.N34Refuted
P3N34ResourceLimit = _types.N34ResourceLimit
P3N34FormalFailure = _types.N34FormalFailure
P3N34N3Result = _types.N3Result
P3N34N4Result = _types.N4Result
P3N34BoundedCoordinateRow = _types.BoundedCoordinateRow
P3N34BoundedCoordinateEqualitySource = _types.BoundedCoordinateEqualitySource
P3N34BoundedEqualityRequest = _types.BoundedEqualityRequest
P3N34BoundedEqualityResult = _types.BoundedEqualityResult

p3n34_all_depth_source = _p3n34.all_depth_source
p3n34_bounded_coordinate_equality_judgment = _p3n34.bounded_coordinate_equality_judgment
p3n34_bounded_coordinate_equality_source = _p3n34.bounded_coordinate_equality_source
p3n34_bounded_equality_request = _p3n34.bounded_equality_request
p3n34_local_realization_judgment = _p3n34.local_realization_judgment
p3n34_n3_dependency_union = _p3n34.n3_dependency_union
p3n34_n3_request = _p3n34.n3_request
p3n34_n4_dependency_union = _p3n34.n4_dependency_union
p3n34_n4_request = _p3n34.n4_request
p3n34_policy = _p3n34.policy
p3n34_scoped_carrier_equality_judgment = _p3n34.scoped_carrier_equality_judgment
p3n34_theorem_source = _p3n34.theorem_source
p3n34_validate_bounded_result = _p3n34.validate_bounded_result
p3n34_validate_n3_result = _p3n34.validate_n3_result
p3n34_validate_n4_result = _p3n34.validate_n4_result

__all__ = (
    "P3N34_ARTIFACT_PATH", "P3N34_ARTIFACT_SHA256", "P3N34_PREMISE_PATH",
    "P3N34_PREMISE_SHA256", "P3N34_PREMISE_THEOREMS", "P3N34_THEOREM_IDS",
    "P3N34ValidationError", "P3N34_NONCLAIMS", "P3N34Status", "P3N34N3Kind",
    "P3N34N4Kind", "P3N34EqualityStatus", "P3N34FailedBound",
    "P3N34FormalFailureKind", "P3N34Policy", "P3N34TheoremSource",
    "P3N34BridgeDependencyRow", "P3N34BridgeDependencyUnion",
    "P3N34AllDepthCoordinateEqualitySource", "P3N34N3Request", "P3N34N4Request",
    "P3N34N3RealizationJudgment", "P3N34N4EqualityJudgment", "P3N34Open",
    "P3N34Refuted", "P3N34ResourceLimit", "P3N34FormalFailure", "P3N34N3Result",
    "P3N34N4Result", "P3N34BoundedCoordinateRow",
    "P3N34BoundedCoordinateEqualitySource", "P3N34BoundedEqualityRequest",
    "P3N34BoundedEqualityResult", "p3n34_all_depth_source",
    "p3n34_bounded_coordinate_equality_judgment",
    "p3n34_bounded_coordinate_equality_source", "p3n34_bounded_equality_request",
    "p3n34_local_realization_judgment", "p3n34_n3_dependency_union",
    "p3n34_n3_request", "p3n34_n4_dependency_union", "p3n34_n4_request",
    "p3n34_policy", "p3n34_scoped_carrier_equality_judgment",
    "p3n34_theorem_source", "p3n34_validate_bounded_result",
    "p3n34_validate_n3_result", "p3n34_validate_n4_result",
)
