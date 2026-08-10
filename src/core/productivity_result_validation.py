"""Exact downstream revalidation for fresh P1-D1 results."""

from __future__ import annotations

import logging
from typing import NoReturn

from .construction.finite_builder.types import TargetIndependence
from .productivity_digest import required_output_bytes
from .productivity_runtime import construct_at_depth, restriction_judgment
from .productivity_types import (
    AllDepthEvidenceStatus, AllDepthProvenance, CompletedCarrierStatus,
    ConstructionArtifact, ConstructionResult, OperationKind, OperationStatus,
    PeriodicPrefixStage, PointwiseSchemaStatus, PointwiseStatus, ProductiveProcessSource,
    ProductivityStatus, ResourceBound, ResourceLimitResult, RestrictionArtifact,
    RestrictionResult, StructuralGuardedness,
)
from .productivity_validation import (
    ProductivityValidationError, snapshot_periodic_prefix_stage,
    snapshot_productive_source,
)

logger = logging.getLogger(__name__)


def _reject(reason: str) -> NoReturn:
    logger.error("productivity result rejected reason=%s", reason)
    raise ProductivityValidationError(reason)


def _permanent(value: object) -> None:
    logger.debug("_permanent entry")
    try:
        rows = (
            value.guardedness, value.pointwise_schema, value.productivity,
            value.all_depth_family, value.all_depth_provenance,
            value.completed_carrier, value.target_independence,
        )
    except AttributeError:
        _reject("result-permanent-fields-missing")
    expected = (
        StructuralGuardedness.STRUCTURALLY_GUARDED,
        PointwiseSchemaStatus.ESTABLISHED, ProductivityStatus.PRODUCTIVE,
        AllDepthEvidenceStatus.OPEN, AllDepthProvenance.OPEN,
        CompletedCarrierStatus.NOT_ESTABLISHED, TargetIndependence.NOT_ESTABLISHED,
    )
    if any(type(item) is not type(want) or item is not want for item, want in zip(rows, expected, strict=True)):
        _reject("result-permanent-status-drift")
    logger.debug("_permanent exit")


def _snapshot_resource_limit_result(
    value: ResourceLimitResult, expected: ResourceLimitResult,
) -> ResourceLimitResult:
    """Capture a refusal with no stage, output, or trace artifact channel."""
    logger.debug("_snapshot_resource_limit_result entry")
    if type(value) is not ResourceLimitResult:
        _reject("resource-limit-result-must-be-exact")
    try:
        operation, depths, failed = value.operation, value.requested_depths, value.failed_bound
        required, allowed = value.required_value, value.allowed_value
        digests = (
            value.program_digest, value.generator_digest, value.source_digest,
            value.policy_digest, value.run_digest, value.refusal_digest,
        )
        status, scope = value.operation_status, value.scope
    except AttributeError:
        _reject("resource-limit-result-missing-fields")
    _permanent(value)
    expected_digests = (
        expected.program_digest, expected.generator_digest, expected.source_digest,
        expected.policy_digest, expected.run_digest, expected.refusal_digest,
    )
    if (
        type(operation) is not OperationKind or operation is not expected.operation
        or type(depths) is not tuple or depths != expected.requested_depths
        or any(type(item) is not int for item in depths)
        or type(failed) is not ResourceBound or failed is not expected.failed_bound
        or type(required) is not int or required != expected.required_value
        or type(allowed) is not int or allowed != expected.allowed_value
        or any(type(item) is not str or item != want for item, want in zip(digests, expected_digests, strict=True))
        or type(status) is not OperationStatus
        or status is not OperationStatus.RESOURCE_LIMIT
        or type(scope) is not str
        or scope != "operational-refusal-not-mathematical-nonexistence"
    ):
        _reject("resource-limit-result-outer-precheck-drift")
    result = ResourceLimitResult(
        operation, tuple(depths), failed, required, allowed, *expected_digests,
    )
    logger.debug("_snapshot_resource_limit_result exit")
    return result


def _snapshot_construction(
    value: ConstructionArtifact, source: ProductiveProcessSource,
    expected: ConstructionArtifact,
) -> ConstructionArtifact:
    logger.debug("_snapshot_construction entry")
    if type(value) is not ConstructionArtifact:
        _reject("construction-artifact-must-be-exact")
    try:
        digests = (
            value.program_digest, value.generator_digest, value.source_digest,
            value.policy_digest, value.run_digest,
        )
        depth, stage = value.depth, value.stage
        output, trace = value.output_digest, value.trace_digest
        status, pointwise, scope = value.operation_status, value.pointwise_status, value.scope
    except AttributeError:
        _reject("construction-artifact-missing-fields")
    _permanent(value)
    expected_digests = (
        expected.program_digest, expected.generator_digest, expected.source_digest,
        expected.policy_digest, expected.run_digest,
    )
    if (
        type(depth) is not int or depth != expected.depth
        or any(type(item) is not str or item != want for item, want in zip(digests, expected_digests, strict=True))
        or type(output) is not str or output != expected.output_digest
        or type(trace) is not str or trace != expected.trace_digest
        or type(stage) is not PeriodicPrefixStage
        or type(stage.depth) is not int or stage.depth != expected.depth
        or type(stage.symbols) is not tuple or len(stage.symbols) != expected.depth
        or type(stage.output_encoding_id) is not str
        or stage.output_encoding_id != source.output_encoding_id
    ):
        _reject("construction-artifact-outer-precheck-drift")
    encoded_bytes = required_output_bytes(
        expected.depth, source.program.period, source.output_encoding_id,
    )
    if expected.depth > source.policy.max_depth or encoded_bytes > source.policy.max_output_bytes:
        _reject("construction-artifact-policy-feasibility-drift")
    if (
        type(status) is not OperationStatus
        or status is not OperationStatus.CONSTRUCTED
        or type(pointwise) is not PointwiseStatus
        or pointwise is not PointwiseStatus.POINTWISE_CONSTRUCTIBLE
        or type(scope) is not str or scope != "one-demanded-finite-prefix-only"
    ):
        _reject("construction-artifact-status-or-scope-drift")
    stage = snapshot_periodic_prefix_stage(
        stage, source, expected.depth, encoded_bytes,
    )
    result = ConstructionArtifact(*expected_digests, depth, stage, output, trace)
    logger.debug("_snapshot_construction exit")
    return result


def _snapshot_restriction(
    value: RestrictionArtifact, source: ProductiveProcessSource,
    expected: RestrictionArtifact,
) -> RestrictionArtifact:
    logger.debug("_snapshot_restriction entry")
    if type(value) is not RestrictionArtifact:
        _reject("restriction-artifact-must-be-exact")
    try:
        digests = (
            value.program_digest, value.generator_digest, value.source_digest,
            value.policy_digest, value.run_digest,
        )
        m, n = value.m, value.n
        lower, upper, restricted = value.lower_stage, value.upper_stage, value.restricted_stage
        outputs = (value.lower_output_digest, value.upper_output_digest, value.restricted_output_digest)
        law, evidence = value.restriction_law_id, value.evidence_digest
        status, pointwise, scope = value.operation_status, value.pointwise_status, value.scope
    except AttributeError:
        _reject("restriction-artifact-missing-fields")
    _permanent(value)
    expected_digests = (
        expected.program_digest, expected.generator_digest, expected.source_digest,
        expected.policy_digest, expected.run_digest,
    )
    expected_outputs = (
        expected.lower_output_digest, expected.upper_output_digest,
        expected.restricted_output_digest,
    )
    stages = (lower, upper, restricted)
    depths = (expected.m, expected.n, expected.m)
    if (
        type(m) is not int or type(n) is not int or (m, n) != (expected.m, expected.n)
        or any(type(item) is not str or item != want for item, want in zip(digests, expected_digests, strict=True))
        or any(type(item) is not str or item != want for item, want in zip(outputs, expected_outputs, strict=True))
        or type(evidence) is not str or evidence != expected.evidence_digest
        or any(type(stage) is not PeriodicPrefixStage for stage in stages)
        or any(type(stage.depth) is not int or stage.depth != depth for stage, depth in zip(stages, depths, strict=True))
        or any(type(stage.symbols) is not tuple or len(stage.symbols) != depth for stage, depth in zip(stages, depths, strict=True))
        or any(type(stage.output_encoding_id) is not str or stage.output_encoding_id != source.output_encoding_id for stage in stages)
    ):
        _reject("restriction-artifact-outer-precheck-drift")
    lower_bytes = required_output_bytes(m, source.program.period, source.output_encoding_id)
    upper_bytes = required_output_bytes(n, source.program.period, source.output_encoding_id)
    if n > source.policy.max_depth or lower_bytes + upper_bytes + lower_bytes > source.policy.max_output_bytes:
        _reject("restriction-artifact-policy-feasibility-drift")
    if (
        type(law) is not str or law != source.restriction_law_id
        or type(status) is not OperationStatus
        or status is not OperationStatus.RESTRICTION_ESTABLISHED
        or type(pointwise) is not PointwiseStatus
        or pointwise is not PointwiseStatus.POINTWISE_CONSTRUCTIBLE
        or type(scope) is not str or scope != "fresh-finite-periodic-restriction"
    ):
        _reject("restriction-artifact-status-or-scope-drift")
    lower = snapshot_periodic_prefix_stage(lower, source, m, lower_bytes)
    upper = snapshot_periodic_prefix_stage(upper, source, n, upper_bytes)
    restricted = snapshot_periodic_prefix_stage(restricted, source, m, lower_bytes)
    result = RestrictionArtifact(
        *expected_digests, m, n, lower, upper, restricted, *expected_outputs,
        law, evidence,
    )
    logger.debug("_snapshot_restriction exit")
    return result


def validate_construction_result(
    source: ProductiveProcessSource, n: int, value: ConstructionResult,
) -> ConstructionResult:
    """Recompute the raw demand and return a fresh exact result."""
    logger.debug("validate_construction_result entry")
    source = snapshot_productive_source(source)
    expected = construct_at_depth(source, n)
    if type(value) is not type(expected):
        _reject("construction-result-union-variant-drift")
    captured = (
        _snapshot_resource_limit_result(value, expected)
        if type(value) is ResourceLimitResult else _snapshot_construction(value, source, expected)
    )
    if captured != expected:
        _reject("construction-result-semantic-drift")
    logger.debug("validate_construction_result exit")
    return expected


def validate_restriction_result(
    source: ProductiveProcessSource, m: int, n: int, value: RestrictionResult,
) -> RestrictionResult:
    """Freshly recompute both rows and reject stale or transplanted artifacts."""
    logger.debug("validate_restriction_result entry")
    source = snapshot_productive_source(source)
    expected = restriction_judgment(source, m, n)
    if type(value) is not type(expected):
        _reject("restriction-result-union-variant-drift")
    captured = (
        _snapshot_resource_limit_result(value, expected)
        if type(value) is ResourceLimitResult else _snapshot_restriction(value, source, expected)
    )
    if captured != expected:
        _reject("restriction-result-semantic-drift")
    logger.debug("validate_restriction_result exit")
    return expected
