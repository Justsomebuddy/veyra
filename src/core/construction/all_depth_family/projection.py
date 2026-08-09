"""Resource-bounded finite projection and exact result revalidation."""

from __future__ import annotations

import logging

from .common import exact_digest, exact_natural, exact_shape, reject
from .digest import projection_result_digest, projection_run_digest
from .sources import snapshot_family_source
from .types import (
    CompletedCarrierStatus, FamilyIntroductionSource, FamilyProjectionArtifact,
    FamilyProjectionRefusal, FamilyProjectionResult, ProjectionCapability,
    ProjectionResourceBound, ProjectionStatus,
)
from ..productivity.core import (
    OUTPUT_ENCODING_ID, RESTRICTION_LAW_ID, TOTALITY_BASIS_ID,
    construct_at_depth, productive_process_source,
)
from ..productivity.types import (
    ConstructionArtifact, ExecutionPolicy, PeriodicPrefixStage, ResourceBound,
    ResourceLimitResult,
)
from ..productivity.validation import snapshot_execution_policy

logger = logging.getLogger(__name__)


# Projection runtime

logger = logging.getLogger(__name__)

def _result_fields(source, policy, run, depth, status):
    logger.debug("_result_fields entry status=%s", status.value)
    result = (
        ("source", source.source_digest.encode()),
        ("family", source.term.family_term_digest.encode()),
        ("introduction", source.introduction_evidence_digest.encode()),
        ("policy", policy.policy_digest.encode()), ("run", run.encode()),
        ("depth", depth.to_bytes(8, "big")), ("status", status.value.encode()),
    )
    logger.debug("_result_fields exit")
    return result

def _project_family_stage(
    family_source: FamilyIntroductionSource, n: int, policy: ExecutionPolicy,
) -> FamilyProjectionResult:
    logger.debug("_project_family_stage entry")
    source = snapshot_family_source(family_source)
    policy = snapshot_execution_policy(policy)
    n = exact_natural(n, "projection-depth", maximum=1_000_000)
    run = projection_run_digest(
        source.source_digest, source.term.family_term_digest,
        source.introduction_evidence_digest, policy.policy_digest, n,
    )
    if source.capability is not ProjectionCapability.PERIODIC_EXECUTABLE:
        status = ProjectionStatus.PROJECTION_UNAVAILABLE
        fields = _result_fields(source, policy, run, n, status) + (
            ("failed", b"none"), ("required", b"none"), ("allowed", b"none"),
        )
        result = FamilyProjectionRefusal(
            source.source_digest, source.term.family_term_digest,
            source.introduction_evidence_digest, policy.policy_digest, run, n,
            status, None, None, None, projection_result_digest(fields),
        )
        logger.debug("_project_family_stage exit unavailable")
        return result
    if source.term.program is None or source.generator_digest is None:
        reject("executable-family-capability-without-program")
    d1_source = productive_process_source(
        source.term.program, TOTALITY_BASIS_ID, RESTRICTION_LAW_ID,
        OUTPUT_ENCODING_ID, policy,
    )
    if d1_source.generator_digest != source.generator_digest:
        reject("projection-generator-transplant")
    d1_result = construct_at_depth(d1_source, n)
    if type(d1_result) is ResourceLimitResult:
        failed = (
            ProjectionResourceBound.DEPTH
            if d1_result.failed_bound is ResourceBound.DEPTH
            else ProjectionResourceBound.OUTPUT_BYTES
        )
        status = ProjectionStatus.RESOURCE_LIMIT
        fields = _result_fields(source, policy, run, n, status) + (
            ("failed", failed.value.encode()),
            ("required", d1_result.required_value.to_bytes(8, "big")),
            ("allowed", d1_result.allowed_value.to_bytes(8, "big")),
        )
        result = FamilyProjectionRefusal(
            source.source_digest, source.term.family_term_digest,
            source.introduction_evidence_digest, policy.policy_digest, run, n,
            status, failed, d1_result.required_value, d1_result.allowed_value,
            projection_result_digest(fields),
        )
        logger.debug("_project_family_stage exit resource-limit")
        return result
    if type(d1_result) is not ConstructionArtifact:
        reject("unexpected-d1-projection-result")
    stage = type(d1_result.stage)(
        d1_result.stage.depth, tuple(list(d1_result.stage.symbols)),
        d1_result.stage.output_encoding_id,
    )
    fields = _result_fields(source, policy, run, n, ProjectionStatus.CONSTRUCTED) + (
        ("output", d1_result.output_digest.encode()),
    )
    result = FamilyProjectionArtifact(
        source.source_digest, source.term.family_term_digest,
        source.introduction_evidence_digest, policy.policy_digest, run, n, stage,
        d1_result.output_digest, projection_result_digest(fields),
    )
    logger.debug("_project_family_stage exit constructed depth=%d", n)
    return result

def project_family_stage(
    family_source: FamilyIntroductionSource, n: int, policy: ExecutionPolicy,
) -> FamilyProjectionResult:
    """Project one demanded coordinate without changing family admission status."""
    logger.debug("project_family_stage entry")
    candidate = _project_family_stage(family_source, n, policy)
    result = validate_family_projection(family_source, n, policy, candidate)
    logger.debug("project_family_stage exit type=%s", type(result).__name__)
    return result


# Result revalidation

logger = logging.getLogger(__name__)

def validate_family_projection(
    family_source: FamilyIntroductionSource, n: int, policy: ExecutionPolicy,
    value: FamilyProjectionResult,
) -> FamilyProjectionResult:
    """Recompute from source/depth/policy and reject forged union variants."""
    logger.debug("validate_family_projection entry")
    expected = _project_family_stage(family_source, n, policy)
    if type(value) is not type(expected):
        reject("family-projection-union-variant-drift")
    if type(value) is FamilyProjectionArtifact:
        _validate_artifact(value)
    elif type(value) is FamilyProjectionRefusal:
        _validate_refusal(value)
    else:
        reject("unknown-family-projection-result")
    if value != expected:
        reject("family-projection-semantic-drift")
    logger.debug("validate_family_projection exit")
    return expected

def _validate_common(value) -> None:
    logger.debug("_validate_common entry")
    for field in (
        "source_digest", "family_term_digest", "introduction_evidence_digest",
        "policy_digest", "run_digest",
    ):
        exact_digest(getattr(value, field), field.replace("_", "-"))
    if type(value.completed_carrier) is not CompletedCarrierStatus:
        reject("projection-completed-carrier-lookalike")
    if type(value.scope) is not str:
        reject("invalid-projection-scope")
    logger.debug("_validate_common exit")

def _validate_artifact(value: FamilyProjectionArtifact) -> None:
    logger.debug("_validate_artifact entry")
    exact_shape(value, FamilyProjectionArtifact, "family-projection-artifact")
    _validate_common(value)
    if type(value.status) is not ProjectionStatus or value.status is not ProjectionStatus.CONSTRUCTED:
        reject("projection-artifact-status-drift")
    if type(value.depth) is not int or value.depth < 0:
        reject("projection-artifact-depth-drift")
    exact_shape(value.stage, PeriodicPrefixStage, "projected-stage")
    if (
        type(value.stage.depth) is not int or value.stage.depth != value.depth
        or type(value.stage.symbols) is not tuple
        or any(type(symbol) is not str for symbol in value.stage.symbols)
        or type(value.stage.output_encoding_id) is not str
    ):
        reject("projected-stage-shape-drift")
    exact_digest(value.output_digest, "output-digest")
    exact_digest(value.projection_digest, "projection-digest")
    logger.debug("_validate_artifact exit")

def _validate_refusal(value: FamilyProjectionRefusal) -> None:
    logger.debug("_validate_refusal entry")
    exact_shape(value, FamilyProjectionRefusal, "family-projection-refusal")
    _validate_common(value)
    if type(value.status) is not ProjectionStatus or value.status not in (
        ProjectionStatus.RESOURCE_LIMIT, ProjectionStatus.PROJECTION_UNAVAILABLE,
    ):
        reject("projection-refusal-status-drift")
    if type(value.requested_depth) is not int or value.requested_depth < 0:
        reject("projection-refusal-depth-drift")
    if value.status is ProjectionStatus.RESOURCE_LIMIT:
        if (
            type(value.failed_bound) is not ProjectionResourceBound
            or type(value.required_value) is not int or value.required_value < 0
            or type(value.allowed_value) is not int or value.allowed_value < 0
        ):
            reject("resource-refusal-payload-drift")
    elif any(item is not None for item in (
        value.failed_bound, value.required_value, value.allowed_value,
    )):
        reject("unavailable-refusal-resource-payload")
    exact_digest(value.refusal_digest, "refusal-digest")
    logger.debug("_validate_refusal exit")
