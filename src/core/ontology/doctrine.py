"""Fingerprint-bound doctrine and presentation commitments for bounded P0."""

from __future__ import annotations

from hashlib import sha256
import logging

from ..observer_core_codec import canonical_observer_bytes
from ..observer_core_kernel import crest_observer, tail_observer
from ..observer_core_semantics import infer_observer_kind
from .types import (
    InternalObserver,
    ObserverDoctrine,
    OntologyStage,
    PresentationCommitment,
)
from .validation import (
    MAX_P0_OBSERVERS,
    PositiveOntologyValidationError,
    snapshot_identifier,
    snapshot_internal_observer,
    snapshot_ontology_stage,
)
from ..proof_core_types import Pulse

logger = logging.getLogger(__name__)
P0_DOCTRINE_VERSION = "p0-v1"


def observer_doctrine(
    doctrine_id: str,
    admission_rule: str,
    metadata: tuple[str, ...],
    observers: tuple[InternalObserver, ...],
    *,
    version: str = "custom-v1",
) -> ObserverDoctrine:
    """Create a fingerprint-bound doctrine without claiming P0 target independence."""
    logger.debug("observer_doctrine entry")
    parts = _capture_doctrine_parts(
        doctrine_id, admission_rule, metadata, observers, version
    )
    result = ObserverDoctrine(*parts, _doctrine_fingerprint(*parts))
    logger.debug("observer_doctrine exit observers=%d", len(result.observers))
    return result


def p0_observer_doctrine() -> ObserverDoctrine:
    """Return the exact versioned P0 crest-then-tail pressure doctrine."""
    logger.debug("p0_observer_doctrine entry")
    programs = (crest_observer(), tail_observer())
    observers = tuple(
        InternalObserver(name, canonical_observer_bytes(program), infer_observer_kind(program))
        for name, program in zip(("crest", "tail"), programs, strict=True)
    )
    result = observer_doctrine(
        "P0-fixed-crest-tail",
        "closed-r11-ordered-prefix",
        ("target-independent", "crest-before-tail", "provisional-pressure"),
        observers,
        version=P0_DOCTRINE_VERSION,
    )
    logger.debug("p0_observer_doctrine exit")
    return result


def snapshot_observer_doctrine(value: ObserverDoctrine) -> ObserverDoctrine:
    """Validate and capture one exact fingerprint-bound doctrine."""
    logger.debug("snapshot_observer_doctrine entry")
    if type(value) is not ObserverDoctrine:
        logger.error("snapshot_observer_doctrine exact gate rejected")
        raise PositiveOntologyValidationError("doctrine-must-be-exact")
    try:
        parts = _capture_doctrine_parts(
            value.doctrine_id,
            value.admission_rule,
            value.metadata,
            value.observers,
            value.version,
        )
        fingerprint = value.fingerprint
    except AttributeError as exc:
        logger.error("snapshot_observer_doctrine missing fields")
        raise PositiveOntologyValidationError("doctrine-missing-fields") from exc
    expected = _doctrine_fingerprint(*parts)
    if type(fingerprint) is not str or fingerprint != expected:
        logger.error("snapshot_observer_doctrine fingerprint rejected")
        raise PositiveOntologyValidationError("doctrine-fingerprint-drift")
    result = ObserverDoctrine(*parts, expected)
    logger.debug("snapshot_observer_doctrine exit observers=%d", len(result.observers))
    return result


def require_p0_doctrine(value: ObserverDoctrine) -> ObserverDoctrine:
    """Require the exact fixed P0 version/fingerprint for P0 relation claims."""
    logger.debug("require_p0_doctrine entry")
    value = snapshot_observer_doctrine(value)
    expected = p0_observer_doctrine()
    if (
        value.version != P0_DOCTRINE_VERSION
        or value.fingerprint != expected.fingerprint
        or value.doctrine_id != expected.doctrine_id
    ):
        logger.error("require_p0_doctrine fixed boundary rejected")
        raise PositiveOntologyValidationError("fixed-p0-doctrine-required")
    logger.debug("require_p0_doctrine exit")
    return value


def stage_commitment(stage: OntologyStage) -> str:
    """Compute a canonical digest of one deeply captured stage."""
    logger.debug("stage_commitment entry")
    stage = snapshot_ontology_stage(stage)
    depth, cursor = 0, stage.representative
    while type(cursor) is Pulse:
        depth += 1
        cursor = cursor.tail
    digest = sha256()
    for token in (stage.stage_id, stage.doctrine_id, str(depth)):
        _digest_token(digest, token.encode("utf-8"))
    for observer in stage.observers:
        _digest_token(digest, observer.observer_id.encode("utf-8"))
        _digest_token(digest, observer.canonical)
    result = digest.hexdigest()
    logger.debug("stage_commitment exit observers=%d", len(stage.observers))
    return result


def snapshot_presentation_commitment(
    value: PresentationCommitment, stage: OntologyStage
) -> PresentationCommitment:
    """Validate a stage commitment without treating it as construction evidence."""
    logger.debug("snapshot_presentation_commitment entry")
    stage = snapshot_ontology_stage(stage)
    if type(value) is not PresentationCommitment:
        logger.error("snapshot_presentation_commitment exact gate rejected")
        raise PositiveOntologyValidationError("presentation-commitment-must-be-exact")
    try:
        witness_id, stage_id = value.witness_id, value.stage_id
        commitment, rule = value.stage_commitment, value.rule
    except AttributeError as exc:
        logger.error("snapshot_presentation_commitment missing fields")
        raise PositiveOntologyValidationError("presentation-commitment-missing-fields") from exc
    witness_id = snapshot_identifier(witness_id, "presentation-commitment-id")
    if (
        stage_id != stage.stage_id
        or type(commitment) is not str
        or commitment != stage_commitment(stage)
        or rule != "finite-recurrence-presentation"
    ):
        logger.error("snapshot_presentation_commitment binding rejected")
        raise PositiveOntologyValidationError("invalid-presentation-commitment-binding")
    result = PresentationCommitment(witness_id, stage.stage_id, commitment)
    logger.debug("snapshot_presentation_commitment exit")
    return result


def _capture_doctrine_parts(
    doctrine_id: object,
    admission_rule: object,
    metadata: object,
    source_observers: object,
    version: object,
) -> tuple[str, str, tuple[str, ...], tuple[InternalObserver, ...], str]:
    logger.debug("_capture_doctrine_parts entry")
    doctrine_id = snapshot_identifier(doctrine_id, "doctrine-id")  # type: ignore[arg-type]
    admission_rule = snapshot_identifier(admission_rule, "admission-rule")  # type: ignore[arg-type]
    version = snapshot_identifier(version, "doctrine-version")  # type: ignore[arg-type]
    if type(metadata) is not tuple or not 1 <= len(metadata) <= 16:
        logger.error("_capture_doctrine_parts metadata rejected")
        raise PositiveOntologyValidationError("invalid-doctrine-metadata")
    captured_metadata = tuple(snapshot_identifier(item, "doctrine-metadata") for item in metadata)
    if type(source_observers) is not tuple or not 1 <= len(source_observers) <= MAX_P0_OBSERVERS:
        logger.error("_capture_doctrine_parts observer family rejected")
        raise PositiveOntologyValidationError("invalid-doctrine-observers")
    observers = tuple(snapshot_internal_observer(item) for item in source_observers)
    ids = tuple(item.observer_id for item in observers)
    canonicals = tuple(item.canonical for item in observers)
    if len(set(ids)) != len(ids):
        logger.error("_capture_doctrine_parts duplicate observer id")
        raise PositiveOntologyValidationError("duplicate-doctrine-observer-id")
    if len(set(canonicals)) != len(canonicals):
        logger.error("_capture_doctrine_parts duplicate observer program")
        raise PositiveOntologyValidationError("duplicate-doctrine-observer-program")
    result = (doctrine_id, admission_rule, captured_metadata, observers, version)
    logger.debug("_capture_doctrine_parts exit observers=%d", len(observers))
    return result


def _doctrine_fingerprint(
    doctrine_id: str,
    admission_rule: str,
    metadata: tuple[str, ...],
    observers: tuple[InternalObserver, ...],
    version: str,
) -> str:
    logger.debug("_doctrine_fingerprint entry")
    digest = sha256()
    for token in (doctrine_id, admission_rule, version, *metadata):
        _digest_token(digest, token.encode("utf-8"))
    for observer in observers:
        _digest_token(digest, observer.observer_id.encode("utf-8"))
        _digest_token(digest, observer.canonical)
    result = digest.hexdigest()
    logger.debug("_doctrine_fingerprint exit")
    return result


def _digest_token(digest: object, token: bytes) -> None:
    logger.debug("_digest_token entry bytes=%d", len(token))
    digest.update(len(token).to_bytes(4, "big"))  # type: ignore[attr-defined]
    digest.update(token)  # type: ignore[attr-defined]
    logger.debug("_digest_token exit")
