"""Hostile-safe exact validation for nested P3-N0 evidence containers."""

from __future__ import annotations

import logging

from .common import exact_hex, exact_shape, reject
from .types import (
    N0BoundPostbirthLedger, N0FormalAttestation, N0PhaseReceipt, N0ReplayEvidence,
)
from .types import N0AccessEdge, N0Event, N0Ledger

logger = logging.getLogger(__name__)


def bounded_text(value, label: str, *, maximum: int = 256, empty: bool = False) -> str:
    """Admit only an exact UTF-8 string inside a fixed byte envelope."""
    logger.debug("bounded_text entry label=%s", label)
    if type(value) is not str or (not empty and not value):
        reject(f"{label}-text-invalid")
    try:
        encoded = value.encode("utf-8")
    except UnicodeError:
        reject(f"{label}-text-invalid")
    if len(encoded) > maximum:
        reject(f"{label}-text-invalid")
    logger.debug("bounded_text exit label=%s", label)
    return value


def exact_tuple(value, label: str, *, maximum: int, length: int | None = None) -> tuple:
    """Check tuple type and length before iteration or indexing."""
    logger.debug("exact_tuple entry label=%s", label)
    if type(value) is not tuple or len(value) > maximum or (
            length is not None and len(value) != length):
        reject(f"{label}-tuple-invalid")
    logger.debug("exact_tuple exit label=%s length=%d", label, len(value))
    return value


def exact_bounded_int(value, label: str, *, minimum: int = 0, maximum: int = 2**31) -> int:
    """Reject Boolean integers and values outside a fixed interval."""
    logger.debug("exact_bounded_int entry label=%s", label)
    if type(value) is not int or not minimum <= value <= maximum:
        reject(f"{label}-int-invalid")
    logger.debug("exact_bounded_int exit label=%s", label)
    return value


def validate_phase_receipt_shape(value, label="n0-phase-receipt") -> dict:
    """Validate one receipt without calling operations on hostile fields first."""
    logger.debug("validate_phase_receipt_shape entry label=%s", label)
    raw = exact_shape(value, N0PhaseReceipt, label)
    exact_bounded_int(raw["phase_index"], f"{label}-phase", maximum=3)
    bounded_text(raw["artifact_name"], f"{label}-artifact", maximum=256)
    exact_hex(raw["captured_sha256"], f"{label}-captured")
    exact_bounded_int(raw["return_code"], f"{label}-return", maximum=255)
    exact_hex(raw["output_sha256"], f"{label}-output")
    exact_hex(raw["receipt_digest"], f"{label}-digest")
    logger.debug("validate_phase_receipt_shape exit label=%s", label)
    return raw


def validate_attestation_shape(value) -> dict:
    """Validate the exact four-receipt attestation shape and scalar bounds."""
    logger.debug("validate_attestation_shape entry")
    raw = exact_shape(value, N0FormalAttestation, "n0-formal-attestation")
    exact_hex(raw["theorem_source_digest"], "n0-attestation-theorem")
    hashes = exact_tuple(raw["captured_hashes"], "n0-attestation-hashes", maximum=4, length=4)
    receipts = exact_tuple(raw["receipts"], "n0-attestation-receipts", maximum=4, length=4)
    for index, item in enumerate(hashes):
        exact_hex(item, f"n0-attestation-captured-{index}")
    for index, item in enumerate(receipts):
        validate_phase_receipt_shape(item, f"n0-phase-receipt-{index}")
    exact_hex(raw["attestation_digest"], "n0-attestation-digest")
    logger.debug("validate_attestation_shape exit")
    return raw


def validate_replay_shape(value) -> dict:
    """Validate every replay field before recomputation."""
    logger.debug("validate_replay_shape entry")
    raw = exact_shape(value, N0ReplayEvidence, "n0-replay-evidence")
    bounded_text(raw["selector"], "n0-replay-selector", maximum=32)
    for name in (
        "package_digest", "network_source_digest", "network_judgment_digest",
        "n2_judgment_digest", "arrow_judgment_digest", "outcome_digest",
    ):
        exact_hex(raw[name], f"n0-replay-{name}")
    producers = exact_tuple(raw["producer_digests"], "n0-replay-producers",
                            maximum=7, length=7)
    for index, item in enumerate(producers):
        exact_hex(item, f"n0-replay-producer-{index}")
    logger.debug("validate_replay_shape exit")
    return raw


def validate_event_shape(value) -> dict:
    """Validate one event's exact nested shape and bounded scalar fields."""
    logger.debug("validate_event_shape entry")
    raw = exact_shape(value, N0Event, "n0-event")
    bounded_text(raw["event_id"], "n0-event-id", maximum=64)
    bounded_text(raw["kind"], "n0-event-kind", maximum=64)
    parents = exact_tuple(raw["parents"], "n0-event-parents", maximum=16)
    for index, parent in enumerate(parents):
        bounded_text(parent, f"n0-event-parent-{index}", maximum=64)
    if raw["token_id"] is not None:
        exact_hex(raw["token_id"], "n0-event-token")
    bounded_text(raw["lineage_id"], "n0-event-lineage", maximum=256)
    for name in ("scope_digest", "payload_digest", "event_digest"):
        exact_hex(raw[name], f"n0-event-{name}")
    logger.debug("validate_event_shape exit")
    return raw


def validate_edge_shape(value) -> dict:
    """Validate one access edge before hashing its fields."""
    logger.debug("validate_edge_shape entry")
    raw = exact_shape(value, N0AccessEdge, "n0-access-edge")
    bounded_text(raw["consumer_id"], "n0-edge-consumer", maximum=64)
    bounded_text(raw["producer_id"], "n0-edge-producer", maximum=64)
    bounded_text(raw["lineage_id"], "n0-edge-lineage", maximum=256)
    for name in ("token_id", "scope_digest", "edge_digest"):
        exact_hex(raw[name], f"n0-edge-{name}")
    logger.debug("validate_edge_shape exit")
    return raw


def validate_bound_ledger_shape(value) -> dict:
    """Validate the three exact bounded ledger rows and all digest fields."""
    logger.debug("validate_bound_ledger_shape entry")
    raw = exact_shape(value, N0BoundPostbirthLedger, "n0-bound-postbirth-ledger")
    rows = exact_tuple(raw["row_payloads"], "n0-bound-ledger-rows", maximum=3, length=3)
    for index, row in enumerate(rows):
        pair = exact_tuple(row, f"n0-bound-ledger-row-{index}", maximum=2, length=2)
        bounded_text(pair[0], f"n0-bound-ledger-label-{index}", maximum=8)
        exact_hex(pair[1], f"n0-bound-ledger-payload-{index}")
    for name in (
        "strict_outcome_digest", "open_outcome_digest", "strict_efficacy_digest",
        "open_efficacy_digest", "ledger_digest",
    ):
        exact_hex(raw[name], f"n0-bound-ledger-{name}")
    logger.debug("validate_bound_ledger_shape exit")
    return raw


def validate_ledger_shape(value, label="n0-ledger") -> dict:
    """Validate one frozen schema ledger without iterating hostile containers."""
    logger.debug("validate_ledger_shape entry label=%s", label)
    raw = exact_shape(value, N0Ledger, label)
    bounded_text(raw["version"], f"{label}-version", maximum=64)
    bounded_text(raw["provenance"], f"{label}-provenance", maximum=256)
    rows = exact_tuple(raw["ordered_rows"], f"{label}-rows", maximum=64)
    edges = exact_tuple(raw["direct_edges"], f"{label}-edges", maximum=256)
    roots = exact_tuple(raw["roots"], f"{label}-roots", maximum=16)
    imports = exact_tuple(raw["imports"], f"{label}-imports", maximum=64)
    axioms = exact_tuple(raw["axioms"], f"{label}-axioms", maximum=32)
    for kind, values in (("row", rows), ("root", roots), ("import", imports),
                         ("axiom", axioms)):
        for index, item in enumerate(values):
            bounded_text(item, f"{label}-{kind}-{index}", maximum=256)
    for index, edge in enumerate(edges):
        pair = exact_tuple(edge, f"{label}-edge-{index}", maximum=2, length=2)
        bounded_text(pair[0], f"{label}-edge-child-{index}", maximum=64)
        bounded_text(pair[1], f"{label}-edge-parent-{index}", maximum=64)
    exact_hex(raw["ledger_digest"], f"{label}-digest")
    logger.debug("validate_ledger_shape exit label=%s", label)
    return raw
