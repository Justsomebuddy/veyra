"""Immutable records for bounded exact representation transports."""

from __future__ import annotations

from dataclasses import dataclass

from ..schema.types import CanonicalPresentation, RepresentationScalar

TRANSPORT_VERSION = "veyra.observer-discovery.v3.representation-transport.v1"
TRANSPORT_BOUNDARY = (
    "exact finite bijective representation replay only; lossless encoding transport "
    "does not establish observer-response invariance, E4 robustness, explanation, "
    "object formation, physical isolation, or a theorem"
)

TRANSPORT_APPLIED = "APPLIED"
TRANSPORT_BLOCKED = "BLOCKED"
HARD_MAX_OBSTRUCTIONS = 16


@dataclass(frozen=True, slots=True)
class CategoryBijection:
    """Ordered source-to-destination category pairs for one field or target."""

    entries: tuple[tuple[RepresentationScalar, RepresentationScalar], ...]


@dataclass(frozen=True, slots=True)
class RepresentationTransportSpec:
    """Exact bijective row, field, category, and target encoding transport."""

    transport_id: str
    source_schema_digest: str
    source_payload_digest: str
    destination_schema_id: str
    row_order: tuple[int, ...]
    field_order: tuple[int, ...]
    destination_field_names: tuple[str, ...]
    category_bijections: tuple[CategoryBijection, ...]
    target_bijection: CategoryBijection
    version: str = TRANSPORT_VERSION


@dataclass(frozen=True, slots=True)
class RepresentationTransportReceipt:
    """Replayable roots for one exact round-trip-checked representation transport."""

    transport_id: str
    source_schema_digest: str
    source_payload_digest: str
    destination_schema_digest: str
    destination_payload_digest: str
    spec_digest: str
    row_count: int
    field_count: int
    lineage_preserved: bool
    roundtrip_verified: bool
    receipt_digest: str
    boundary: str = TRANSPORT_BOUNDARY


@dataclass(frozen=True, slots=True)
class RepresentationObstruction:
    """Stable reason why a canonical representation operation was blocked."""

    reason: str
    detail: str


@dataclass(frozen=True, slots=True)
class RepresentationTransportResult:
    """Terminal transport result; blocked states carry no destination or receipt."""

    status: str
    destination: CanonicalPresentation | None
    receipt: RepresentationTransportReceipt | None
    obstructions: tuple[RepresentationObstruction, ...]
    boundary: str = TRANSPORT_BOUNDARY
