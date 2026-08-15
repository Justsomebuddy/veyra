"""Executable level-1 certificate for provisional P1-D1 productivity."""

from __future__ import annotations

import logging

from .certify_types import Certificate
from .construction.finite_builder.types import TargetIndependence
from .infinity_prefix import prefix_alphabet
from .productivity import (
    OUTPUT_ENCODING_ID,
    RESTRICTION_LAW_ID,
    TOTALITY_BASIS_ID,
    construct_at_depth,
    execution_policy,
    periodic_program,
    productive_process_source,
    restriction_judgment,
    validate_construction_result,
)
from .productivity_types import (
    AllDepthEvidenceStatus,
    AllDepthProvenance,
    CompletedCarrierStatus,
    ConstructionArtifact,
    OperationStatus,
    PointwiseSchemaStatus,
    ProductivityStatus,
    ResourceLimitResult,
    RestrictionArtifact,
)

logger = logging.getLogger(__name__)


def certify_productivity_p1d1() -> Certificate:
    """Certify structural pointwise productivity without an all-depth carrier."""
    logger.debug("certify_productivity_p1d1 entry")
    alphabet = prefix_alphabet(("a", "b"))
    program = periodic_program(alphabet, ("a", "b", "a"))
    first_policy = execution_policy(8, 4096)
    second_policy = execution_policy(16, 8192)
    first_source = productive_process_source(
        program,
        TOTALITY_BASIS_ID,
        RESTRICTION_LAW_ID,
        OUTPUT_ENCODING_ID,
        first_policy,
    )
    second_source = productive_process_source(
        program,
        TOTALITY_BASIS_ID,
        RESTRICTION_LAW_ID,
        OUTPUT_ENCODING_ID,
        second_policy,
    )
    first = construct_at_depth(first_source, 6)
    if type(first) is not ConstructionArtifact:
        reason = "productivity certificate first result type invariant failed"
        logger.error(reason)
        raise RuntimeError(reason)
    again = construct_at_depth(first_source, 6)
    if type(again) is not ConstructionArtifact:
        reason = "productivity certificate repeated result type invariant failed"
        logger.error(reason)
        raise RuntimeError(reason)
    cross_policy = construct_at_depth(second_source, 6)
    if type(cross_policy) is not ConstructionArtifact:
        reason = "productivity certificate cross-policy result type invariant failed"
        logger.error(reason)
        raise RuntimeError(reason)
    identity = restriction_judgment(first_source, 6, 6)
    if type(identity) is not RestrictionArtifact:
        reason = "productivity certificate identity result type invariant failed"
        logger.error(reason)
        raise RuntimeError(reason)
    lower_mid = restriction_judgment(first_source, 2, 4)
    if type(lower_mid) is not RestrictionArtifact:
        reason = "productivity certificate lower-mid result type invariant failed"
        logger.error(reason)
        raise RuntimeError(reason)
    mid_upper = restriction_judgment(first_source, 4, 6)
    if type(mid_upper) is not RestrictionArtifact:
        reason = "productivity certificate mid-upper result type invariant failed"
        logger.error(reason)
        raise RuntimeError(reason)
    lower_upper = restriction_judgment(first_source, 2, 6)
    if type(lower_upper) is not RestrictionArtifact:
        reason = "productivity certificate lower-upper result type invariant failed"
        logger.error(reason)
        raise RuntimeError(reason)
    refusal = construct_at_depth(first_source, 9)
    if type(refusal) is not ResourceLimitResult:
        reason = "productivity certificate refusal result type invariant failed"
        logger.error(reason)
        raise RuntimeError(reason)
    revalidated = validate_construction_result(first_source, 6, first)
    permanent = (
        first.pointwise_schema is refusal.pointwise_schema is PointwiseSchemaStatus.ESTABLISHED
        and first.productivity is refusal.productivity is ProductivityStatus.PRODUCTIVE
        and first.all_depth_family is refusal.all_depth_family is AllDepthEvidenceStatus.OPEN
        and first.all_depth_provenance is refusal.all_depth_provenance is AllDepthProvenance.OPEN
        and first.completed_carrier is refusal.completed_carrier is CompletedCarrierStatus.NOT_ESTABLISHED
        and first.target_independence is refusal.target_independence is TargetIndependence.NOT_ESTABLISHED
    )
    passed = (
        first.stage.symbols == ("a", "b", "a", "a", "b", "a")
        and first.output_digest == again.output_digest == cross_policy.output_digest
        and first.trace_digest == again.trace_digest
        and first is not again
        and first.stage is not again.stage
        and first.stage.symbols is not again.stage.symbols
        and revalidated is not first
        and revalidated.stage is not first.stage
        and first.program_digest == cross_policy.program_digest
        and first.generator_digest == cross_policy.generator_digest
        and first.policy_digest != cross_policy.policy_digest
        and first.source_digest != cross_policy.source_digest
        and first.run_digest != cross_policy.run_digest
        and identity.operation_status is OperationStatus.RESTRICTION_ESTABLISHED
        and identity.restricted_output_digest == identity.lower_output_digest
        and lower_upper.restricted_output_digest == lower_mid.restricted_output_digest
        and mid_upper.restricted_output_digest == mid_upper.lower_output_digest
        and refusal.operation_status is OperationStatus.RESOURCE_LIMIT
        and not hasattr(refusal, "stage")
        and not hasattr(refusal, "output_digest")
        and not hasattr(refusal, "trace_digest")
        and permanent
    )
    method = (
        "closed nonempty periodic structurally guarded pointwise finite construction "
        "and coherent restriction; no extensional all-depth family, completed carrier, "
        "target independence, compactness/choice/König/inverse-limit, observer-independent "
        "infinity, PΩ, novelty, R8, layer, or Sage promotion"
    )
    detail = (
        "one O(n) demanded row, fresh deterministic replay, restriction identity/composition, "
        "same generator across policies, typed cap refusal, permanent nonclaims"
    )
    result = Certificate("productivity_p1d1", method, passed, detail, 1)
    logger.debug("certify_productivity_p1d1 exit result=%r", result)
    return result
