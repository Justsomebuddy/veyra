"""Tagged, count-framed digests for P1-A2 observer-relation artifacts."""

from __future__ import annotations

from hashlib import sha256
import logging

from .types import (
    ComparisonMode, ObserverRelationJudgment, RelationPairRow, RelationStage,
    StageKey, StageObservationRow, TranslationAssessment, TranslationInputKind,
    TranslationTriangleRow,
)
from .types import RelationResourceLimit

logger = logging.getLogger(__name__)


def _field(tag: str, value: bytes) -> bytes:
    """Frame one named digest field without boundary ambiguity."""
    logger.debug("relation digest field entry tag=%s bytes=%d", tag, len(value))
    name = tag.encode("ascii")
    result = len(name).to_bytes(2, "big") + name + len(value).to_bytes(8, "big") + value
    logger.debug("relation digest field exit tag=%s", tag)
    return result


def _text(tag: str, value: str) -> bytes:
    """Encode one exact text field."""
    logger.debug("relation digest text entry tag=%s", tag)
    if type(value) is not str:
        logger.error("relation digest text rejected tag=%s", tag)
        raise ValueError("relation-digest-text-required")
    result = _field(tag, value.encode("utf-8"))
    logger.debug("relation digest text exit tag=%s", tag)
    return result


def _nat(tag: str, value: int) -> bytes:
    """Encode one bounded exact natural number."""
    logger.debug("relation digest nat entry tag=%s", tag)
    if type(value) is not int or value < 0 or value.bit_length() > 64:
        logger.error("relation digest nat rejected tag=%s", tag)
        raise ValueError("relation-digest-natural-required")
    result = _field(tag, value.to_bytes(8, "big"))
    logger.debug("relation digest nat exit tag=%s", tag)
    return result


def _seq(tag: str, values: tuple[bytes, ...]) -> bytes:
    """Count-bind one ordered tuple of already framed entries."""
    logger.debug("relation digest seq entry tag=%s count=%d", tag, len(values))
    payload = len(values).to_bytes(4, "big") + b"".join(
        _field("item", value) for value in values
    )
    result = _field(tag, payload)
    logger.debug("relation digest seq exit tag=%s", tag)
    return result


def _digest(domain: str, *fields: bytes) -> str:
    """Hash one versioned domain and its framed fields."""
    logger.debug("relation digest entry domain=%s fields=%d", domain, len(fields))
    result = sha256(_field("domain", domain.encode("ascii")) + b"".join(fields)).hexdigest()
    logger.debug("relation digest exit domain=%s", domain)
    return result


def stage_commitment(version: str, stage_id: str, recurrence_bytes: bytes) -> str:
    """Commit to one canonical closed recurrence and exact stage identifier."""
    logger.debug("stage_commitment entry stage=%s", stage_id)
    result = _digest(
        "p1a2-stage-v1", _text("version", version), _text("stage-id", stage_id),
        _field("canonical-recurrence", recurrence_bytes),
    )
    logger.debug("stage_commitment exit stage=%s", stage_id)
    return result


def source_digest(
    doctrine_fingerprint: str, observer_source_digest: str, version: str,
    stages: tuple[RelationStage, ...],
) -> str:
    """Commit to the exact ordered stage source."""
    logger.debug("relation source_digest entry stages=%d", len(stages))
    entries = tuple(
        _text("stage-id", item.stage_id) + _text("commitment", item.commitment)
        for item in stages
    )
    result = _digest(
        "p1a2-source-v1", _text("doctrine", doctrine_fingerprint),
        _text("observer-source", observer_source_digest), _text("version", version),
        _seq("stages", entries),
    )
    logger.debug("relation source_digest exit")
    return result


def scope_digest(
    doctrine_fingerprint: str, observer_source_digest: str,
    stage_source_digest: str, fine_id: str, coarse_id: str,
    stages: tuple[StageKey, ...], mode: ComparisonMode,
) -> str:
    """Commit to exact stage order; the Cartesian universe is deterministic."""
    logger.debug("relation scope_digest entry stages=%d", len(stages))
    entries = tuple(
        _text("stage-id", stage_id) + _text("commitment", commitment)
        for stage_id, commitment in stages
    )
    result = _digest(
        "p1a2-scope-v1", _text("doctrine", doctrine_fingerprint),
        _text("observer-source", observer_source_digest),
        _text("stage-source", stage_source_digest), _text("fine", fine_id),
        _text("coarse", coarse_id), _text("mode", mode.value),
        _seq("stages", entries),
    )
    logger.debug("relation scope_digest exit")
    return result


def proposal_digest(
    proposal_id: str, doctrine_fingerprint: str, observer_source_digest: str,
    fine_id: str, coarse_id: str, projection: tuple[str, ...],
) -> str:
    """Commit to one typed closed projection proposal."""
    logger.debug("proposal_digest entry id=%s steps=%d", proposal_id, len(projection))
    result = _digest(
        "p1a2-proposal-v1", _text("proposal-id", proposal_id),
        _text("doctrine", doctrine_fingerprint),
        _text("observer-source", observer_source_digest), _text("fine", fine_id),
        _text("coarse", coarse_id),
        _seq("projection", tuple(_text("step", item) for item in projection)),
    )
    logger.debug("proposal_digest exit id=%s", proposal_id)
    return result


def observation_row_digest(row: StageObservationRow) -> str:
    """Digest one fresh dual-observer stage row."""
    logger.debug("observation_row_digest entry stage=%s", row.stage[0])
    result = _digest(
        "p1a2-observation-row-v1", _text("stage-id", row.stage[0]),
        _text("commitment", row.stage[1]), _text("fine-status", row.fine_status.value),
        _text("coarse-status", row.coarse_status.value),
        _text("fine-payload", row.fine_payload_digest),
        _text("coarse-payload", row.coarse_payload_digest),
    )
    logger.debug("observation_row_digest exit stage=%s", row.stage[0])
    return result


def pair_row_digest(row: RelationPairRow) -> str:
    """Digest one exact ordered-pair comparison row."""
    logger.debug("pair_row_digest entry index=%d", row.pair_index)
    fields = (
        _nat("pair-index", row.pair_index), _text("left-id", row.left[0]),
        _text("left-commitment", row.left[1]), _text("right-id", row.right[0]),
        _text("right-commitment", row.right[1]),
        _text("fine-outcome", row.fine_outcome.value),
        _text("coarse-outcome", row.coarse_outcome.value),
        _text("fine-left", row.fine_left_payload),
        _text("fine-right", row.fine_right_payload),
        _text("coarse-left", row.coarse_left_payload),
        _text("coarse-right", row.coarse_right_payload),
    )
    result = _digest("p1a2-pair-row-v1", *fields)
    logger.debug("pair_row_digest exit index=%d", row.pair_index)
    return result


def triangle_row_digest(row: TranslationTriangleRow) -> str:
    """Digest one exact response triangle row."""
    logger.debug("triangle_row_digest entry index=%d", row.stage_index)
    result = _digest(
        "p1a2-triangle-row-v1", _nat("stage-index", row.stage_index),
        _text("stage-id", row.stage[0]), _text("commitment", row.stage[1]),
        _text("status", row.status.value), _text("fine", row.fine_payload_digest),
        _text("translated", row.translated_payload_digest),
        _text("coarse", row.coarse_payload_digest),
    )
    logger.debug("triangle_row_digest exit index=%d", row.stage_index)
    return result


def assessment_digest(value: TranslationAssessment) -> str:
    """Digest a full ordered translation assessment."""
    logger.debug("assessment_digest entry triangles=%d", len(value.triangles))
    result = _digest(
        "p1a2-assessment-v2", _text("input-kind", value.input_kind.value),
        _text("input-commitment", value.input_commitment),
        _text("morphism", value.morphism_status.value),
        _text("proposal", value.proposal_status.value),
        _seq("triangles", tuple(_text("row", item.row_digest) for item in value.triangles)),
        _text("conflict", "" if value.conflict is None else value.conflict.row_digest),
    )
    logger.debug("assessment_digest exit")
    return result


def translation_input_commitment(
    kind: TranslationInputKind, doctrine_fingerprint: str,
    observer_source_digest: str, identity: str, fine_id: str, coarse_id: str,
    projection: tuple[str, ...], proposal_source_digest: str = "",
) -> str:
    """Commit to the exact absent, raw P1-A, or proposal input identity."""
    logger.debug("translation_input_commitment entry kind=%s", kind.value)
    result = _digest(
        "p1a2-translation-input-v1", _text("kind", kind.value),
        _text("doctrine", doctrine_fingerprint),
        _text("observer-source", observer_source_digest),
        _text("identity", identity), _text("fine", fine_id),
        _text("coarse", coarse_id),
        _seq("projection", tuple(_text("step", item) for item in projection)),
        _text("proposal-source-digest", proposal_source_digest),
    )
    logger.debug("translation_input_commitment exit kind=%s", kind.value)
    return result


def judgment_digest(value: ObserverRelationJudgment) -> str:
    """Digest exact outer laws, witnesses, coverage, and ordered evidence."""
    logger.debug("relation judgment_digest entry pairs=%d", len(value.pairs))
    witness_rows = tuple(
        "" if item is None else item.row_digest
        for item in (
            value.preservation_witness, value.reflection_witness, value.domain_witness,
        )
    )
    fields = (
        _text("doctrine", value.doctrine_fingerprint),
        _text("observer-source", value.observer_source_digest),
        _text("stage-source", value.stage_source_digest), _text("scope", value.scope_digest),
        _seq("observations", tuple(_text("row", item.row_digest) for item in value.observations)),
        _seq("pairs", tuple(_text("row", item.row_digest) for item in value.pairs)),
        _text("preservation", value.preservation.value),
        _text("reflection", value.reflection.value),
        _text("domain-equality", value.domain_equality.value),
        _seq("witnesses", tuple(_text("row", item) for item in witness_rows)),
        _text("classification", value.classification.value),
        _text("forward", value.forward.translation_digest),
        _text("reverse", value.reverse.translation_digest),
        _text("invertibility", value.structural_invertibility.value),
        _text("loss", value.information_loss.value), _text("coverage", value.coverage.value),
        _nat("charged-checks", value.charged_checks),
        _text("identity-nonclaim", value.observer_independent_identity.value),
        _text("universal-nonclaim", value.universal_refinement.value),
        _seq("nonclaims", tuple(_text("claim", item) for item in value.nonclaims)),
    )
    result = _digest("p1a2-judgment-v1", *fields)
    logger.debug("relation judgment_digest exit")
    return result


def response_payload_digest(payload: bytes) -> str:
    """Digest canonical response bytes or a fixed blocked marker."""
    logger.debug("response_payload_digest entry bytes=%d", len(payload))
    result = _digest("p1a2-response-v1", _field("payload", payload))
    logger.debug("response_payload_digest exit")
    return result


def policy_digest(version: str, max_cost: int, max_encoded_bytes: int) -> str:
    """Digest one exact versioned resource policy."""
    logger.debug("relation policy_digest entry")
    result = _digest(
        "p1a2-policy-v1", _text("version", version), _nat("max-cost", max_cost),
        _nat("max-encoded-bytes", max_encoded_bytes),
    )
    logger.debug("relation policy_digest exit")
    return result


def refusal_digest(value: RelationResourceLimit) -> str:
    """Digest exact refusal provenance, bounds, and permanent nonclaims."""
    logger.debug("relation refusal_digest entry")
    result = _digest(
        "p1a2-refusal-v1", _text("operation", value.operation.value),
        _text("status", value.status.value), _text("policy-version", value.policy_version),
        _text("policy", value.policy_digest), _text("doctrine", value.doctrine_fingerprint),
        _text("observer-source", value.observer_source_digest),
        _text("stage-source", value.stage_source_digest), _text("scope", value.scope_digest),
        _nat("required-cost", value.required_cost), _nat("allowed-cost", value.allowed_cost),
        _nat("required-bytes", value.required_encoded_bytes),
        _nat("allowed-bytes", value.allowed_encoded_bytes),
        _text("identity-nonclaim", value.observer_independent_identity.value),
        _text("universal-nonclaim", value.universal_refinement.value),
        _seq("nonclaims", tuple(_text("claim", item) for item in value.nonclaims)),
    )
    logger.debug("relation refusal_digest exit")
    return result
