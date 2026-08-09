"""Hostile-envelope-first fresh result replay for P3-C2."""

from __future__ import annotations
import logging
from .common import exact_digest, exact_shape, reject
from .runtime import generated_transport_coherence
from .types import (
    FormalFailureKind,
    GeneratedTransportCoherence,
    GeneratedTransportFiller,
    HigherCellStructureStatus,
    P3C2_NONCLAIMS,
    TransportCoherenceStatus,
    TransportFailedBound,
    TransportFailureKind,
    TransportFormalFailure,
    TransportPackage,
    TransportResourceLimit,
    TransportResult,
)

logger = logging.getLogger(__name__)
MAX_RESULT_TUPLE = 16384
MAX_RESULT_NODES = 131072
MAX_RESULT_BYTES = 2 * 1024 * 1024
MAX_RESULT_DEPTH = 3
MAX_RESULT_PATH = 128


def validate_transport_result(raw_package: TransportPackage, value: TransportResult) -> TransportResult:
    """Validate a closed outer envelope, then freshly replay exact raw sources."""
    logger.debug("validate_transport_result entry type=%s", type(value).__name__)
    if type(value) is GeneratedTransportCoherence:
        _positive(value)
    elif type(value) is TransportResourceLimit:
        _resource(value)
    elif type(value) is TransportFormalFailure:
        _formal(value)
    else:
        reject("transport-result-variant-invalid")
    expected = generated_transport_coherence(raw_package)
    if type(value) is not type(expected) or value != expected:
        reject("transport-result-replay-mismatch")
    logger.debug("validate_transport_result exit")
    return expected


def _positive(value: GeneratedTransportCoherence) -> None:
    """Precheck all result scalars and nested global filler envelopes."""
    logger.debug("_positive entry")
    exact_shape(value, GeneratedTransportCoherence, "transport-result")
    local_rows, fillers, nonclaims = _positive_envelope(value)
    for name in (
        "system_digest",
        "doctrine_digest",
        "theorem_source_digest",
        "assumption_ledger_digest",
        "formal_receipt_digest",
        "result_digest",
    ):
        exact_digest(object.__getattribute__(value, name), name)
    if (
        type(value.formal_phase_count) is not int
        or type(value.local_square_count) is not int
        or type(value.global_boundary_count) is not int
        or type(value.semantic_work) is not int
        or min(value.formal_phase_count, value.local_square_count, value.global_boundary_count, value.semantic_work) < 0
    ):
        reject("transport-result-count-invalid")
    if (
        type(value.status) is not TransportCoherenceStatus
        or type(value.higher_cell_structure) is not HigherCellStructureStatus
    ):
        reject("transport-result-status-invalid")
    if any(type(x) is not str for x in local_rows) or any(type(x) is not str for x in nonclaims):
        reject("transport-result-row-type-invalid")
    for row in local_rows:
        exact_digest(row, "local-filler-digest")
    if type(value.finite_tlgc_scope) is not str or type(value.symbolic_natop_scope) is not str:
        reject("transport-result-scope-invalid")
    if (
        nonclaims != P3C2_NONCLAIMS
        or value.higher_cell_structure is not HigherCellStructureStatus.NOT_IMPLEMENTED
    ):
        reject("transport-result-boundary-drift")
    for row in fillers:
        _filler(row)
    logger.debug("_positive exit")


def _positive_envelope(value: GeneratedTransportCoherence):
    """Bound top-level counts/nodes/bytes/depth before semantic child validation."""
    local_rows = object.__getattribute__(value, "local_filler_digests")
    fillers = object.__getattribute__(value, "global_fillers")
    nonclaims = object.__getattribute__(value, "nonclaims")
    if type(local_rows) is not tuple or type(fillers) is not tuple or type(nonclaims) is not tuple:
        reject("transport-result-container-invalid")
    if max(len(local_rows), len(fillers), len(nonclaims)) > MAX_RESULT_TUPLE:
        reject("transport-result-tuple-limit")
    global_count = object.__getattribute__(value, "global_boundary_count")
    local_count = object.__getattribute__(value, "local_square_count")
    if type(global_count) is not int or type(local_count) is not int:
        reject("transport-result-count-invalid")
    status = object.__getattribute__(value, "status")
    if (
        global_count != len(fillers)
        or max(global_count, local_count) > MAX_RESULT_TUPLE
        or len(local_rows) > local_count
        or (status is not TransportCoherenceStatus.OPEN and len(local_rows) != local_count)
    ):
        reject("transport-result-count-invariant")
    nodes = 1 + len(local_rows) + len(fillers) + len(nonclaims)
    if nodes > MAX_RESULT_NODES or MAX_RESULT_DEPTH != 3:
        reject("transport-result-node-or-depth-limit")
    byte_count = 0
    for name in (
        "system_digest",
        "doctrine_digest",
        "theorem_source_digest",
        "assumption_ledger_digest",
        "formal_receipt_digest",
        "finite_tlgc_scope",
        "symbolic_natop_scope",
        "result_digest",
    ):
        atom = object.__getattribute__(value, name)
        if type(atom) is not str:
            reject("transport-result-scalar-type-invalid")
        byte_count += len(atom.encode("utf-8"))
    if byte_count > MAX_RESULT_BYTES:
        reject("transport-result-byte-limit")
    # Every filler path container is length-bounded before any path item is read.
    for filler in fillers:
        exact_shape(filler, GeneratedTransportFiller, "global-filler")
        paths = tuple(
            object.__getattribute__(filler, name)
            for name in ("left_boundary", "right_boundary", "left_postpath", "right_postpath")
        )
        if any(type(path) is not tuple for path in paths):
            reject("global-filler-path-invalid")
        path_nodes = sum(len(path) for path in paths)
        if any(len(path) > MAX_RESULT_PATH for path in paths) or nodes + path_nodes > MAX_RESULT_NODES:
            reject("global-filler-path-limit")
        nodes += path_nodes
    for row in (*local_rows, *nonclaims):
        if type(row) is not str:
            reject("transport-result-row-type-invalid")
        byte_count += len(row.encode("utf-8"))
        if byte_count > MAX_RESULT_BYTES:
            reject("transport-result-byte-limit")
    for filler in fillers:
        for name in (
            "root_state_id",
            "target_state_id",
            "filler_digest",
            "left_boundary",
            "right_boundary",
            "left_postpath",
            "right_postpath",
        ):
            row = object.__getattribute__(filler, name)
            atoms = row if type(row) is tuple else (row,)
            if any(type(atom) is not str for atom in atoms):
                reject("global-filler-row-type-invalid")
            byte_count += sum(len(atom.encode("utf-8")) for atom in atoms)
            if byte_count > MAX_RESULT_BYTES:
                reject("transport-result-byte-limit")
    return local_rows, fillers, nonclaims


def _filler(value: GeneratedTransportFiller) -> None:
    """Precheck one derived filler without invoking hostile equality."""
    logger.debug("_filler entry")
    exact_shape(value, GeneratedTransportFiller, "global-filler")
    for name in ("root_state_id", "target_state_id"):
        if type(object.__getattribute__(value, name)) is not str:
            reject("global-filler-text-invalid")
    for name in ("left_boundary", "right_boundary", "left_postpath", "right_postpath"):
        row = object.__getattribute__(value, name)
        if type(row) is not tuple or any(type(x) is not str for x in row):
            reject("global-filler-path-invalid")
    exact_digest(value.filler_digest, "global-filler-digest")
    logger.debug("_filler exit")


def _resource(value: TransportResourceLimit) -> None:
    """Precheck payload-free typed resource refusal."""
    logger.debug("_resource entry")
    exact_shape(value, TransportResourceLimit, "transport-resource")
    if value.status is not TransportFailureKind.RESOURCE_LIMIT or type(value.failed_bound) is not TransportFailedBound:
        reject("transport-resource-kind-invalid")
    if (
        type(value.required_value) is not int
        or type(value.allowed_value) is not int
        or value.required_value <= value.allowed_value
    ):
        reject("transport-resource-values-invalid")
    exact_digest(value.source_hint_digest, "resource-hint")
    exact_digest(value.refusal_digest, "resource-digest")
    if type(value.nonclaims) is not tuple or len(value.nonclaims) != len(P3C2_NONCLAIMS):
        reject("transport-resource-nonclaims-shape-invalid")
    if any(type(x) is not str for x in value.nonclaims):
        reject("transport-resource-nonclaims-shape-invalid")
    if value.nonclaims != P3C2_NONCLAIMS:
        reject("transport-resource-nonclaims-invalid")
    logger.debug("_resource exit")


def _formal(value: TransportFormalFailure) -> None:
    """Precheck one sanitized formal failure without mathematical status."""
    logger.debug("_formal entry")
    exact_shape(value, TransportFormalFailure, "transport-formal-failure")
    if value.status is not TransportFailureKind.FORMAL_FAILURE or type(value.kind) is not FormalFailureKind:
        reject("transport-formal-kind-invalid")
    if type(value.diagnostic) is not str or value.diagnostic != f"formal execution {value.kind.value}":
        reject("transport-formal-diagnostic-invalid")
    exact_digest(value.attempt_digest, "formal-attempt")
    if type(value.nonclaims) is not tuple or len(value.nonclaims) != len(P3C2_NONCLAIMS):
        reject("transport-formal-nonclaims-shape-invalid")
    if any(type(x) is not str for x in value.nonclaims):
        reject("transport-formal-nonclaims-shape-invalid")
    if value.nonclaims != P3C2_NONCLAIMS:
        reject("transport-formal-nonclaims-invalid")
    logger.debug("_formal exit")
