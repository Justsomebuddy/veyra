"""O(n) pointwise construction and coherent restriction for P1-D1."""

from __future__ import annotations

import logging

from .digest import (
    execution_trace_digest, output_digest, refusal_digest, required_output_bytes,
    run_digest, tagged_digest,
)
from .types import (
    ConstructionArtifact, ConstructionResult, OperationKind, PeriodicPrefixStage,
    ProductiveProcessSource, ResourceBound, ResourceLimitResult,
    RestrictionArtifact, RestrictionResult,
)
from .validation import (
    ProductivityValidationError, snapshot_productive_source,
)

logger = logging.getLogger(__name__)


def _depth(value: int, field: str) -> int:
    logger.debug("_depth entry field=%s", field)
    if type(value) is not int or value < 0:
        logger.error("_depth rejected field=%s", field)
        raise ProductivityValidationError(f"invalid-{field}")
    logger.debug("_depth exit field=%s bits=%d", field, value.bit_length())
    return value


def _resource(
    source: ProductiveProcessSource, operation: OperationKind, depths: tuple[int, ...],
    failed: ResourceBound, required: int, allowed: int, run: str,
) -> ResourceLimitResult:
    logger.debug("_resource entry operation=%s bound=%s", operation, failed.value)
    refusal = refusal_digest(operation.value, run, failed.value, required, allowed)
    result = ResourceLimitResult(
        operation, depths, failed, required, allowed, source.program.program_digest,
        source.generator_digest, source.source_digest, source.policy.policy_digest, run,
        refusal,
    )
    logger.debug("_resource exit")
    return result


def _preflight(
    source: ProductiveProcessSource, operation: OperationKind, depths: tuple[int, ...],
) -> tuple[str, ResourceLimitResult | None]:
    """Check exact caps before allocating or iterating any demanded row."""
    logger.debug("_preflight entry operation=%s", operation)
    run = run_digest(source.source_digest, source.policy.policy_digest, operation.value, depths)
    maximum = max(depths)
    if maximum > source.policy.max_depth:
        result = _resource(
            source, operation, depths, ResourceBound.DEPTH, maximum,
            source.policy.max_depth, run,
        )
        logger.debug("_preflight exit refused=depth")
        return run, result
    one_stage = required_output_bytes(
        maximum, source.program.period, source.output_encoding_id
    )
    required = one_stage
    if operation is OperationKind.RESTRICT:
        lower = required_output_bytes(depths[0], source.program.period, source.output_encoding_id)
        required = lower + one_stage + lower
    if required > source.policy.max_output_bytes:
        result = _resource(
            source, operation, depths, ResourceBound.OUTPUT_BYTES, required,
            source.policy.max_output_bytes, run,
        )
        logger.debug("_preflight exit refused=bytes")
        return run, result
    logger.debug("_preflight exit allowed")
    return run, None


def _build_stage(source: ProductiveProcessSource, depth: int) -> PeriodicPrefixStage:
    """Build only the demanded row with one linear pass."""
    logger.debug("_build_stage entry depth=%d", depth)
    period = source.program.period
    symbols = tuple(period[index % len(period)] for index in range(depth))
    result = PeriodicPrefixStage(depth, symbols, source.output_encoding_id)
    logger.debug("_build_stage exit depth=%d", depth)
    return result


def _trace(source: ProductiveProcessSource, run: str, stage: PeriodicPrefixStage, output: str) -> str:
    logger.debug("_trace entry depth=%d", stage.depth)
    result = execution_trace_digest(
        source.program.program_digest, source.generator_digest,
        source.source_digest, run, stage, output,
    )
    logger.debug("_trace exit")
    return result


def construct_at_depth(source: ProductiveProcessSource, n: int) -> ConstructionResult:
    """Construct exactly one finite prefix or return a typed policy refusal."""
    logger.debug("construct_at_depth entry")
    source = snapshot_productive_source(source)
    n = _depth(n, "construction-depth")
    run, refusal = _preflight(source, OperationKind.CONSTRUCT, (n,))
    if refusal is not None:
        logger.debug("construct_at_depth exit resource-limit")
        return refusal
    stage = _build_stage(source, n)
    output = output_digest(stage)
    result = ConstructionArtifact(
        source.program.program_digest, source.generator_digest,
        source.source_digest, source.policy.policy_digest, run, n, stage, output,
        _trace(source, run, stage, output),
    )
    logger.debug("construct_at_depth exit constructed depth=%d", n)
    return result


def restriction_judgment(
    source: ProductiveProcessSource, m: int, n: int,
) -> RestrictionResult:
    """Freshly recompute both rows and derive exact prefix restriction."""
    logger.debug("restriction_judgment entry")
    source = snapshot_productive_source(source)
    m, n = _depth(m, "restriction-lower-depth"), _depth(n, "restriction-upper-depth")
    if m > n:
        logger.error("restriction_judgment reversed depths")
        raise ProductivityValidationError("restriction-requires-m-less-or-equal-n")
    run, refusal = _preflight(source, OperationKind.RESTRICT, (m, n))
    if refusal is not None:
        logger.debug("restriction_judgment exit resource-limit")
        return refusal
    lower, upper = _build_stage(source, m), _build_stage(source, n)
    restricted = PeriodicPrefixStage(
        m, tuple(symbol for symbol in upper.symbols[:m]), source.output_encoding_id,
    )
    if restricted.symbols != lower.symbols:
        logger.error("restriction_judgment structural law failed")
        raise RuntimeError("periodic restriction law failed unexpectedly")
    lower_digest, upper_digest = output_digest(lower), output_digest(upper)
    restricted_digest = output_digest(restricted)
    evidence = tagged_digest("veyra.p1d1.restriction-evidence.v1", (
        ("program", source.program.program_digest.encode()),
        ("generator", source.generator_digest.encode()),
        ("source", source.source_digest.encode()), ("policy", source.policy.policy_digest.encode()),
        ("run", run.encode()), ("m", m.to_bytes(8, "big")), ("n", n.to_bytes(8, "big")),
        ("lower-output", lower_digest.encode()), ("upper-output", upper_digest.encode()),
        ("restricted-output", restricted_digest.encode()),
        ("law", source.restriction_law_id.encode()),
    ))
    result = RestrictionArtifact(
        source.program.program_digest, source.generator_digest, source.source_digest,
        source.policy.policy_digest, run, m, n, lower, upper, restricted,
        lower_digest, upper_digest, restricted_digest, source.restriction_law_id, evidence,
    )
    logger.debug("restriction_judgment exit restricted m=%d n=%d", m, n)
    return result
