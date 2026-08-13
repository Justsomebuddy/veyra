"""Canonical source and deterministic selection for P3-OG pressure."""

from __future__ import annotations

from dataclasses import replace
from hmac import compare_digest
import logging
from math import isqrt

from .prime_power_observer_genesis_p3og_codec import (
    bounded_int, bounded_text, canonical_bytes, digest,
)
from .prime_power_observer_genesis_p3og_types import (
    DeterministicSelectionReceipt, P3OGSource, PrimitiveModeSeed, TransitionKind,
)

logger = logging.getLogger(__name__)
RULE_ID = "canonical-pool-selector-v2"


def _is_prime(value: int) -> bool:
    """Check primality for one 31-bit exact integer."""
    logger.debug("p3og._is_prime entry value=%r", value)
    result = value >= 2 and all(
        value % factor for factor in range(2, isqrt(value) + 1)
    )
    logger.debug("p3og._is_prime exit result=%s", result)
    return result


def primitive_seed(label: str, cycle: tuple[int, ...]) -> PrimitiveModeSeed:
    """Commit one bounded cycle without evaluating its later pressure result."""
    logger.debug("p3og.primitive_seed entry")
    label = bounded_text(label, "p3og-seed-label")
    if type(cycle) is not tuple or not 2 <= len(cycle) <= 64:
        logger.error("p3og.primitive_seed invalid cycle shape")
        raise ValueError("p3og-seed-cycle")
    checked = tuple(bounded_int(item, "p3og-seed-cycle", 31) for item in cycle)
    result = PrimitiveModeSeed(label, checked, digest("seed", label, checked))
    logger.debug("p3og.primitive_seed exit digest=%s", result.seed_digest[:12])
    return result


def p3og_source(
    *, prime: int, depth: int, source_instance_label: str,
    seed_rows: tuple[tuple[str, tuple[int, ...]], ...],
    calibration_inputs: tuple[int, int], maintenance_credit: int,
    suffix: tuple[TransitionKind, ...], doctrine_label: str = "P3-OG-pressure-v2",
) -> P3OGSource:
    """Build a bounded canonical pool and complete finite pressure source."""
    logger.debug("p3og.p3og_source entry")
    prime = bounded_int(prime, "p3og-arithmetic-scope", 31)
    if not _is_prime(prime) or type(depth) is not int or not 0 <= depth <= 16:
        logger.error("p3og.p3og_source invalid arithmetic scope")
        raise ValueError("p3og-arithmetic-scope")
    source_instance_label = bounded_text(
        source_instance_label, "p3og-source-instance-label",
    )
    doctrine_label = bounded_text(doctrine_label, "p3og-doctrine-label")
    if type(seed_rows) is not tuple or not 1 <= len(seed_rows) <= 64:
        logger.error("p3og.p3og_source invalid seed rows")
        raise ValueError("p3og-seed-rows")
    seeds = []
    for row in seed_rows:
        if type(row) is not tuple or len(row) != 2:
            logger.error("p3og.p3og_source invalid seed row")
            raise ValueError("p3og-seed-row")
        seeds.append(primitive_seed(row[0], row[1]))
    ordered = tuple(sorted(seeds, key=lambda item: item.seed_digest))
    if len({item.seed_digest for item in ordered}) != len(ordered):
        logger.error("p3og.p3og_source duplicate seed digest")
        raise ValueError("p3og-seed-duplicate")
    if len({item.label for item in ordered}) != len(ordered):
        logger.error("p3og.p3og_source duplicate seed label")
        raise ValueError("p3og-seed-label-duplicate")
    if (type(calibration_inputs) is not tuple or len(calibration_inputs) != 2):
        logger.error("p3og.p3og_source invalid calibration shape")
        raise ValueError("p3og-calibration")
    calibration = tuple(
        bounded_int(item, "p3og-calibration", 4096) for item in calibration_inputs
    )
    if type(maintenance_credit) is not int or not 1 <= maintenance_credit <= 64:
        logger.error("p3og.p3og_source invalid maintenance credit")
        raise ValueError("p3og-maintenance-credit")
    if (type(suffix) is not tuple or not 1 <= len(suffix) <= 64
            or any(type(item) is not TransitionKind for item in suffix)):
        logger.error("p3og.p3og_source invalid suffix")
        raise ValueError("p3og-suffix")
    fields = (
        "p3og-pressure-source-v2", prime, depth, source_instance_label, ordered,
        calibration, maintenance_credit, suffix, doctrine_label,
    )
    result = P3OGSource(*fields, digest("source", *fields))
    logger.debug("p3og.p3og_source exit source=%s", result.source_digest[:12])
    return result


def validate_source(source: P3OGSource) -> P3OGSource:
    """Validate outer and nested shapes before any public dereference escapes."""
    logger.debug("p3og.validate_source entry")
    if type(source) is not P3OGSource:
        logger.error("p3og.validate_source wrong outer type")
        raise ValueError("p3og-source-type")
    try:
        if (type(source.seeds) is not tuple
                or not 1 <= len(source.seeds) <= 64):
            logger.error("p3og.validate_source seed envelope exceeded")
            raise ValueError("p3og-source-seeds-size")
        if any(
                type(seed) is not PrimitiveModeSeed for seed in source.seeds):
            raise ValueError("p3og-source-seeds-type")
        rows = tuple((seed.label, seed.cycle) for seed in source.seeds)
        expected = p3og_source(
            prime=source.prime, depth=source.depth,
            source_instance_label=source.source_instance_label, seed_rows=rows,
            calibration_inputs=source.calibration_inputs,
            maintenance_credit=source.maintenance_credit, suffix=source.suffix,
            doctrine_label=source.doctrine_label,
        )
        equal = compare_digest(canonical_bytes(source), canonical_bytes(expected))
    except (AttributeError, TypeError, UnicodeError, ValueError) as exc:
        logger.error("p3og.validate_source malformed nested source=%s", exc)
        raise ValueError("p3og-source-malformed") from exc
    if not equal:
        logger.error("p3og.validate_source source drift")
        raise ValueError("p3og-source-drift")
    logger.debug("p3og.validate_source exit source=%s", source.source_digest[:12])
    return replace(expected)


def validate_seed(
    source: P3OGSource, seed: PrimitiveModeSeed,
) -> tuple[P3OGSource, PrimitiveModeSeed]:
    """Return a validated source and its canonical exact seed member."""
    logger.debug("p3og.validate_seed entry")
    source = validate_source(source)
    if type(seed) is not PrimitiveModeSeed:
        logger.error("p3og.validate_seed wrong seed type")
        raise ValueError("p3og-seed-type")
    try:
        candidate = primitive_seed(seed.label, seed.cycle)
        equal = compare_digest(canonical_bytes(seed), canonical_bytes(candidate))
    except (AttributeError, TypeError, UnicodeError, ValueError) as exc:
        logger.error("p3og.validate_seed malformed seed=%s", exc)
        raise ValueError("p3og-seed-malformed") from exc
    if equal:
        for canonical in source.seeds:
            if compare_digest(canonical.seed_digest, candidate.seed_digest):
                logger.debug(
                    "p3og.validate_seed exit seed=%s", canonical.seed_digest[:12],
                )
                return source, canonical
    logger.error("p3og.validate_seed foreign seed")
    raise ValueError("p3og-machine-seed")


def deterministic_select(source: P3OGSource) -> DeterministicSelectionReceipt:
    """Select from a canonical unique pool without a caller-controlled nonce."""
    logger.debug("p3og.deterministic_select entry")
    source = validate_source(source)
    result = _deterministic_select_validated(source)
    logger.debug("p3og.deterministic_select exit index=%d", result.selected_index)
    return result


def _deterministic_select_validated(
    source: P3OGSource,
) -> DeterministicSelectionReceipt:
    """Select from an already validated canonical source."""
    logger.debug("p3og._deterministic_select_validated entry")
    pool = digest("pool", tuple(seed.seed_digest for seed in source.seeds))
    selector = digest(
        "selector", RULE_ID, source.prime, source.depth,
        source.doctrine_label, pool,
    )
    index = int(selector, 16) % len(source.seeds)
    seed = source.seeds[index]
    result = DeterministicSelectionReceipt(
        source.source_digest, pool, index, seed.seed_digest, RULE_ID,
        digest("selection-receipt", source.source_digest, pool, index,
               seed.seed_digest, RULE_ID),
    )
    logger.debug("p3og._deterministic_select_validated exit index=%d", index)
    return result
