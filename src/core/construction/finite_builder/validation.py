"""Fail-closed snapshots for provisional P1-B finite replay."""

from __future__ import annotations

import logging
from typing import NoReturn

from .codec import (
    FiniteBuilderCodecError, _canonical_builder_bytes,
    _canonical_recurrence_bytes, _decode_builder, _decode_recurrence,
)
from .digest import (
    _program_digest, _seed_digest, _source_digest,
)
from .types import (
    ConstructionSourceBinding, FiniteBuilderExpr, FiniteBuilderProgram,
    FiniteRecurrenceSeed, PulseStep, SeedRef,
)
from ...positive_ontology_doctrine import snapshot_observer_doctrine
from ...positive_ontology_types import ObserverDoctrine, OntologyStage
from ...positive_ontology_validation import (
    PositiveOntologyValidationError, snapshot_ontology_stage,
)

_LEGACY_MODULE = "src.core.finite_builder_validation"
logger = logging.getLogger(_LEGACY_MODULE)
MAX_P1B_ID_BYTES = 128
MAX_P1B_SEEDS = 128


class FiniteBuilderValidationError(ValueError):
    """An exact P1-B representation or source contract was violated."""


def _reject(reason: str) -> NoReturn:
    logger.error("finite builder rejected reason=%s", reason)
    raise FiniteBuilderValidationError(reason)


def _identifier(value: str, field: str) -> str:
    """Capture one bounded exact P1-B identifier."""
    logger.debug("_identifier entry field=%s", field)
    if type(value) is not str or not value or len(value) > MAX_P1B_ID_BYTES:
        _reject(f"invalid-{field}")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError:
        _reject(f"invalid-{field}")
    if size > MAX_P1B_ID_BYTES:
        _reject(f"invalid-{field}")
    logger.debug("_identifier exit field=%s bytes=%d", field, size)
    return value


def _hex_digest(value: str, field: str) -> str:
    """Capture one exact lowercase SHA-256 digest."""
    logger.debug("_hex_digest entry field=%s", field)
    if (
        type(value) is not str or len(value) != 64
        or any(char not in "0123456789abcdef" for char in value)
    ):
        _reject(f"invalid-{field}")
    logger.debug("_hex_digest exit field=%s", field)
    return value


def _snapshot_doctrine(value: ObserverDoctrine) -> ObserverDoctrine:
    """Normalize lower-layer doctrine errors at the P1-B boundary."""
    logger.debug("_snapshot_doctrine entry")
    try:
        result = snapshot_observer_doctrine(value)
    except PositiveOntologyValidationError as exc:
        logger.error("_snapshot_doctrine rejected")
        raise FiniteBuilderValidationError("invalid-construction-doctrine") from exc
    logger.debug("_snapshot_doctrine exit")
    return result


def _snapshot_builder_expr(value: FiniteBuilderExpr) -> FiniteBuilderExpr:
    """Capture closed exact syntax through one canonical round trip."""
    logger.debug("_snapshot_builder_expr entry")
    try:
        result = _decode_builder(_canonical_builder_bytes(value))
    except FiniteBuilderCodecError as exc:
        logger.error("_snapshot_builder_expr rejected")
        raise FiniteBuilderValidationError("invalid-finite-builder-expression") from exc
    logger.debug("_snapshot_builder_expr exit")
    return result


def _builder_shape(value: FiniteBuilderExpr) -> tuple[str, int, int]:
    """Return the sole seed, added pulse count, and exact node count."""
    logger.debug("_builder_shape entry")
    cursor: object = value
    pulses = 0
    while type(cursor) is PulseStep:
        pulses += 1
        cursor = cursor.child
    if type(cursor) is not SeedRef:
        _reject("invalid-finite-builder-expression")
    result = (cursor.seed_id, pulses, pulses + 1)
    logger.debug("_builder_shape exit pulses=%d", pulses)
    return result


def _snapshot_seed(value: FiniteRecurrenceSeed) -> FiniteRecurrenceSeed:
    """Validate and freshly decode one exact recurrence seed."""
    logger.debug("_snapshot_seed entry")
    if type(value) is not FiniteRecurrenceSeed:
        _reject("seed-must-be-exact")
    try:
        seed_id, canonical = value.seed_id, value.canonical
        supplied, scope = value.seed_digest, value.scope
    except AttributeError:
        _reject("seed-missing-fields")
    seed_id = _identifier(seed_id, "seed-id")
    supplied = _hex_digest(supplied, "seed-digest")
    if type(canonical) is not bytes or type(scope) is not str:
        _reject("invalid-seed-fields")
    canonical = memoryview(canonical).tobytes()
    try:
        recurrence = _decode_recurrence(canonical)
        if _canonical_recurrence_bytes(recurrence) != canonical:
            _reject("seed-canonical-drift")
    except FiniteBuilderCodecError as exc:
        logger.error("_snapshot_seed canonical rejected")
        raise FiniteBuilderValidationError("invalid-seed-canonical") from exc
    expected = _seed_digest(seed_id, canonical)
    if supplied != expected or scope != "admitted-finite-recurrence-seed":
        _reject("seed-digest-or-scope-drift")
    result = FiniteRecurrenceSeed(seed_id, canonical, expected)
    logger.debug("_snapshot_seed exit")
    return result


def _snapshot_program(value: FiniteBuilderProgram) -> FiniteBuilderProgram:
    """Validate one exact target-free closed builder program."""
    logger.debug("_snapshot_program entry")
    if type(value) is not FiniteBuilderProgram:
        _reject("builder-program-must-be-exact")
    try:
        builder_id, stage_id = value.builder_id, value.output_stage_id
        observer_ids, canonical = value.observer_ids, value.canonical
        seed_ids, supplied, scope = (
            value.referenced_seed_ids, value.program_digest, value.scope,
        )
    except AttributeError:
        _reject("builder-program-missing-fields")
    builder_id = _identifier(builder_id, "builder-id")
    stage_id = _identifier(stage_id, "output-stage-id")
    supplied = _hex_digest(supplied, "program-digest")
    if (
        type(observer_ids) is not tuple or len(observer_ids) > 64
        or type(seed_ids) is not tuple or type(canonical) is not bytes
        or type(scope) is not str
    ):
        _reject("invalid-builder-program-fields")
    observers = tuple(_identifier(item, "observer-id") for item in observer_ids)
    seeds = tuple(_identifier(item, "seed-id") for item in seed_ids)
    canonical = memoryview(canonical).tobytes()
    try:
        expression = _decode_builder(canonical)
    except FiniteBuilderCodecError as exc:
        logger.error("_snapshot_program canonical rejected")
        raise FiniteBuilderValidationError("invalid-builder-canonical") from exc
    referenced, _, _ = _builder_shape(expression)
    if seeds != (referenced,):
        _reject("builder-referenced-seed-drift")
    expected = _program_digest(
        builder_id, stage_id, observers, canonical, seeds
    )
    if supplied != expected or scope != "closed-target-free-finite-recurrence-builder":
        _reject("builder-program-digest-or-scope-drift")
    result = FiniteBuilderProgram(
        builder_id, stage_id, observers, canonical, seeds, expected
    )
    logger.debug("_snapshot_program exit")
    return result


def _snapshot_source(
    value: ConstructionSourceBinding, doctrine: ObserverDoctrine
) -> ConstructionSourceBinding:
    """Validate exact builder/seed membership against one doctrine snapshot."""
    logger.debug("_snapshot_source entry")
    doctrine = _snapshot_doctrine(doctrine)
    if type(value) is not ConstructionSourceBinding:
        _reject("construction-source-must-be-exact")
    try:
        binding_id, fingerprint = value.binding_id, value.doctrine_fingerprint
        program, source_seeds = value.program, value.seeds
        supplied, scope = value.membership_digest, value.scope
    except AttributeError:
        _reject("construction-source-missing-fields")
    binding_id = _identifier(binding_id, "construction-binding-id")
    supplied = _hex_digest(supplied, "construction-source-digest")
    if type(fingerprint) is not str or type(scope) is not str:
        _reject("construction-source-string-fields-required")
    program = _snapshot_program(program)
    if (
        type(source_seeds) is not tuple or not source_seeds
        or len(source_seeds) > MAX_P1B_SEEDS
    ):
        _reject("invalid-construction-seeds")
    seeds = tuple(_snapshot_seed(item) for item in source_seeds)
    ids = tuple(item.seed_id for item in seeds)
    if len(set(ids)) != len(ids) or ids != program.referenced_seed_ids:
        _reject("construction-seed-membership-drift")
    prefix = tuple(item.observer_id for item in doctrine.observers[:len(program.observer_ids)])
    if program.observer_ids != prefix:
        _reject("construction-observer-prefix-drift")
    expected = _source_digest(
        binding_id, doctrine.fingerprint, program.program_digest,
        ids, tuple(item.seed_digest for item in seeds),
    )
    if (
        fingerprint != doctrine.fingerprint or supplied != expected
        or scope != "immutability-membership-not-chronology-or-target-independence"
    ):
        _reject("construction-source-binding-drift")
    result = ConstructionSourceBinding(
        binding_id, doctrine.fingerprint, program, seeds, expected
    )
    logger.debug("_snapshot_source exit")
    return result


def _snapshot_target_stage(
    value: OntologyStage, doctrine: ObserverDoctrine
) -> OntologyStage:
    """Capture a target only after replay and require the exact doctrine prefix."""
    logger.debug("_snapshot_target_stage entry")
    try:
        result = snapshot_ontology_stage(value)
    except PositiveOntologyValidationError as exc:
        logger.error("_snapshot_target_stage rejected")
        raise FiniteBuilderValidationError("invalid-construction-target") from exc
    prefix = doctrine.observers[:len(result.observers)]
    if result.doctrine_id != doctrine.doctrine_id or result.observers != prefix:
        _reject("construction-target-doctrine-drift")
    logger.debug("_snapshot_target_stage exit")
    return result


for _legacy_object in (
    FiniteBuilderValidationError,
    _reject,
    _identifier,
    _hex_digest,
    _snapshot_doctrine,
    _snapshot_builder_expr,
    _builder_shape,
    _snapshot_seed,
    _snapshot_program,
    _snapshot_source,
    _snapshot_target_stage,
):
    _legacy_object.__module__ = _LEGACY_MODULE
del _legacy_object, _LEGACY_MODULE
