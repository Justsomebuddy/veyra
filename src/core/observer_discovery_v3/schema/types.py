"""Immutable records for bounded canonical discovery representations."""

from __future__ import annotations

from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

RepresentationScalar = str | int | bool

SCHEMA_VERSION = "veyra.observer-discovery.v3.representation-schema.v1"
THREE_WAY_VERSION = "veyra.observer-discovery.v3.three-way.v1"

REPRESENTATION_BOUNDARY = (
    "canonical finite categorical representation and declared lineage only; "
    "schema admission does not establish source fidelity, observer admission, "
    "semantic explanation, object formation, or statistical generalization"
)
HARD_MAX_FIELDS = 32
HARD_MAX_CATEGORIES = 128
HARD_MAX_ROWS_PER_PRESENTATION = 8192
HARD_MAX_TOTAL_CELLS = 262_144
HARD_MAX_TEXT_BYTES = 512
HARD_MAX_INTEGER_BITS = 256


@dataclass(frozen=True, slots=True)
class RepresentationField:
    """One explicit finite categorical feature domain."""

    name: str
    kind: str
    categories: tuple[RepresentationScalar, ...]


@dataclass(frozen=True, slots=True)
class RepresentationSchema:
    """Versioned schema for one narrow categorical discovery presentation."""

    schema_id: str
    fields: tuple[RepresentationField, ...]
    target_categories: tuple[RepresentationScalar, ...]
    version: str = SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class RepresentationRow:
    """One schema-bound row with explicit record and lineage identities."""

    row_id: str
    source_id: str
    content_id: str
    group_id: str
    values: tuple[RepresentationScalar, ...]
    target: RepresentationScalar


@dataclass(frozen=True, slots=True)
class CanonicalPresentation:
    """Detached canonical schema and ordered immutable rows with evidence roots."""

    schema: RepresentationSchema
    rows: tuple[RepresentationRow, ...]
    schema_digest: str
    payload_digest: str
    boundary: str = REPRESENTATION_BOUNDARY


@dataclass(frozen=True, slots=True)
class ThreeWayPresentation:
    """Caller-declared train, validation, and locked-test presentations."""

    train: CanonicalPresentation
    validation: CanonicalPresentation
    test: CanonicalPresentation
    protocol_digest: str
    boundary: str = REPRESENTATION_BOUNDARY


class RepresentationProtocolError(ValueError):
    """Fail-closed validation error with bounded machine-readable fields."""

    def __init__(self, reason: str, detail: str) -> None:
        logger.error("RepresentationProtocolError entry reason=%s detail=%s", reason, detail)
        self.reason = reason
        self.detail = detail
        super().__init__(f"{reason}:{detail}")
        logger.debug("RepresentationProtocolError exit reason=%s", reason)
