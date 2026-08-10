"""Finite executable boundary evidence for the R13 observer-echo theorem."""
from __future__ import annotations

from dataclasses import dataclass, replace
import logging

from .intrinsic_observer_echo_source import (
    EXPECTED_ARTIFACT_DIGEST,
    intrinsic_observer_echo_source_artifact,
    verify_intrinsic_observer_echo_source_artifact,
)
from .intrinsic_vam_values import recurrence_to_intrinsic_ir
from .observer_core_kernel import crest_observer, tail_observer
from .observer_core_semantics import echo, observe
from .observer_core_support import observer_data, outcome_data
from .proof_core_codec import canonical_json, digest_data, term_data
from .proof_core_types import Pulse, Silence
from vam.src.intrinsic_ir import intrinsic_ir_data

logger = logging.getLogger(__name__)
SCHEMA = "veyra.intrinsic-observer-echo-evidence.r13.2.v1"
EVIDENCE_ID = "veyra.r13.intrinsic-observer-echo.executable.v1"
EVIDENCE_DOMAIN = "veyra-r13-intrinsic-observer-echo-evidence-v1"
EXPECTED_EVIDENCE_DIGEST = "4835777193ad8ca5967b27837be21669814f69d11b6781cd7b606f75ebd34d10"
BOUNDARY = (
    "three finite executable rows only: source replay authorizes unit-weave equality, "
    "Python evaluates echo(observer,r,r), tail/silence remains two-sided blocked, and "
    "crest nonreflection remains explicit; this is not the general theorem or promotion"
)


@dataclass(frozen=True, slots=True)
class IntrinsicObserverEchoEvidenceRow:
    """One canonical executable positive or counter-boundary row."""

    row_id: str
    observer: str
    left: str
    right: str
    observation: str
    outcome: str
    left_ir_digest: str
    right_ir_digest: str
    sources_equal: bool
    lowered_equal: bool


@dataclass(frozen=True, slots=True)
class IntrinsicObserverEchoEvidence:
    """Source-authorized finite evidence separated from the formal declaration."""

    schema: str
    evidence_id: str
    source_artifact_digest: str
    rows: tuple[IntrinsicObserverEchoEvidenceRow, ...]
    boundary: str
    digest: str


def _json(value: object) -> str:
    """Return one canonical JSON string for an already validated value."""
    logger.debug("intrinsic_observer_echo_evidence._json entry")
    result = canonical_json(value)
    logger.debug("intrinsic_observer_echo_evidence._json exit bytes=%d", len(result))
    return result


def _ir_digest(value: object) -> str:
    """Digest one exact lowered recurrence without accepting caller IR."""
    logger.debug("intrinsic_observer_echo_evidence._ir_digest entry")
    result = digest_data(
        intrinsic_ir_data(recurrence_to_intrinsic_ir(value)),
        "veyra-r13-evidence-lowered-recurrence-v1",
    )
    logger.debug("intrinsic_observer_echo_evidence._ir_digest exit digest=%s", result)
    return result


def _row(row_id: str, observer: object, left: object, right: object) -> IntrinsicObserverEchoEvidenceRow:
    """Evaluate one exact R11 row and bind both R12 lowering images."""
    logger.debug("intrinsic_observer_echo_evidence._row entry id=%s", row_id)
    left_ir, right_ir = _ir_digest(left), _ir_digest(right)
    result = IntrinsicObserverEchoEvidenceRow(
        row_id,
        _json(observer_data(observer)),
        _json(term_data(left)),
        _json(term_data(right)),
        _json(outcome_data(observe(observer, left))),
        _json(outcome_data(echo(observer, left, right))),
        left_ir,
        right_ir,
        term_data(left) == term_data(right),
        left_ir == right_ir,
    )
    logger.debug("intrinsic_observer_echo_evidence._row exit id=%s", row_id)
    return result


def _data(evidence: IntrinsicObserverEchoEvidence, include_digest: bool) -> dict[str, object]:
    """Serialize exact immutable evidence without dataclass or enum coercion."""
    logger.debug("intrinsic_observer_echo_evidence._data entry")
    result: dict[str, object] = {
        "schema": evidence.schema,
        "evidence_id": evidence.evidence_id,
        "source_artifact_digest": evidence.source_artifact_digest,
        "rows": [
            {
                "row_id": row.row_id,
                "observer": row.observer,
                "left": row.left,
                "right": row.right,
                "observation": row.observation,
                "outcome": row.outcome,
                "left_ir_digest": row.left_ir_digest,
                "right_ir_digest": row.right_ir_digest,
                "sources_equal": row.sources_equal,
                "lowered_equal": row.lowered_equal,
            }
            for row in evidence.rows
        ],
        "boundary": evidence.boundary,
    }
    if include_digest:
        result["digest"] = evidence.digest
    logger.debug("intrinsic_observer_echo_evidence._data exit")
    return result


def _build() -> IntrinsicObserverEchoEvidence:
    """Replay phase source then construct the exact three executable rows."""
    logger.debug("intrinsic_observer_echo_evidence._build entry")
    source = intrinsic_observer_echo_source_artifact()
    if not verify_intrinsic_observer_echo_source_artifact(source).ok:
        raise ValueError("r13-evidence-source-artifact-rejected")
    unit, two = Pulse(Silence()), Pulse(Pulse(Silence()))
    seed = IntrinsicObserverEchoEvidence(
        SCHEMA,
        EVIDENCE_ID,
        source.artifact_digest,
        (
            _row("R13-EVIDENCE-READY", crest_observer(), unit, unit),
            _row("R13-EVIDENCE-TAIL-BLOCKED", tail_observer(), Silence(), Silence()),
            _row("R13-EVIDENCE-CREST-NONREFLECTION", crest_observer(), unit, two),
        ),
        BOUNDARY,
        "",
    )
    result = replace(seed, digest=digest_data(_data(seed, False), EVIDENCE_DOMAIN))
    logger.debug("intrinsic_observer_echo_evidence._build exit digest=%s", result.digest)
    return result


def _valid_shape(value: object) -> bool:
    """Reject subclasses and hostile row field types before replay equality."""
    logger.debug("intrinsic_observer_echo_evidence._valid_shape entry")
    try:
        result = (
            type(value) is IntrinsicObserverEchoEvidence
            and all(type(item) is str for item in (
                value.schema,
                value.evidence_id,
                value.source_artifact_digest,
                value.boundary,
                value.digest,
            ))
            and type(value.rows) is tuple
            and all(
                type(row) is IntrinsicObserverEchoEvidenceRow
                and all(type(item) is str for item in (
                    row.row_id,
                    row.observer,
                    row.left,
                    row.right,
                    row.observation,
                    row.outcome,
                    row.left_ir_digest,
                    row.right_ir_digest,
                ))
                and type(row.sources_equal) is bool
                and type(row.lowered_equal) is bool
                for row in value.rows
            )
        )
    except AttributeError:
        result = False
    logger.debug("intrinsic_observer_echo_evidence._valid_shape exit result=%s", result)
    return result


def intrinsic_observer_echo_evidence() -> IntrinsicObserverEchoEvidence:
    """Return only the exact reviewed executable evidence artifact."""
    logger.debug("intrinsic_observer_echo_evidence entry")
    result = _build()
    if (
        result.schema != SCHEMA
        or result.evidence_id != EVIDENCE_ID
        or result.source_artifact_digest != EXPECTED_ARTIFACT_DIGEST
        or result.digest != EXPECTED_EVIDENCE_DIGEST
    ):
        raise ValueError("r13-executable-evidence-envelope-drift")
    logger.debug("intrinsic_observer_echo_evidence exit digest=%s", result.digest)
    return result


def verify_intrinsic_observer_echo_evidence(value: object) -> bool:
    """Fail closed unless exact type, replay, rows, and digest all match."""
    logger.debug("verify_intrinsic_observer_echo_evidence entry type=%s", type(value).__name__)
    if type(value) is not IntrinsicObserverEchoEvidence or not _valid_shape(value):
        logger.debug("verify_intrinsic_observer_echo_evidence exit result=False")
        return False
    try:
        result = (
            value == _build()
            and value.digest == EXPECTED_EVIDENCE_DIGEST
            and value.digest == digest_data(_data(value, False), EVIDENCE_DOMAIN)
        )
    except (AttributeError, TypeError, ValueError):
        logger.exception("R13 executable evidence verification failed")
        result = False
    logger.debug("verify_intrinsic_observer_echo_evidence exit result=%s", result)
    return result
