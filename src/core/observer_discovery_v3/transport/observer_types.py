"""Immutable records for frozen-observer representation-transport checks."""

from __future__ import annotations

from dataclasses import dataclass

from .types import RepresentationObstruction


OBSERVER_TRANSPORT_VERIFIED = "OBSERVER_TRANSPORT_VERIFIED"
OBSERVER_TRANSPORT_REFUTED = "OBSERVER_TRANSPORT_REFUTED"
OBSERVER_TRANSPORT_BLOCKED = "BLOCKED"
OBSERVER_TRANSPORT_BOUNDARY = (
    "finite commuting-square check for one frozen closed observer and one declared bijective representation "
    "transport; invariance is scoped to checked rows and is not robustness, explanation, causality, or a theorem"
)


@dataclass(frozen=True, slots=True)
class ObserverTransportReceipt:
    """Root-only receipt for one completed finite commuting-square experiment."""

    representation_transport_receipt: str
    source_program_digest: str
    destination_program_digest: str
    response_map_digest: str
    source_worker_result: str
    destination_worker_result: str
    checked_rows: int
    mismatch_count: int
    result_digest: str
    boundary: str = OBSERVER_TRANSPORT_BOUNDARY


@dataclass(frozen=True, slots=True)
class ObserverTransportResult:
    """Verified/refuted completed experiment or fail-closed blocked attempt."""

    status: str
    receipt: ObserverTransportReceipt | None
    obstructions: tuple[RepresentationObstruction, ...]
    boundary: str = OBSERVER_TRANSPORT_BOUNDARY
