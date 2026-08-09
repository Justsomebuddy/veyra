"""Fail-closed local-square replay and finite/global P3-C2 judgment."""

from __future__ import annotations
import logging
from ..confluence.generated.paths import branch_targets, generated_local_peaks, generated_reachable
from .common import digest, reject
from .formal import check_transport_theorems
from .package import snapshot_package
from .paths import (
    derive_indexed_global_fillers,
)
from .index import (
    HARD_GENERATED_PATHS,
    build_transport_index,
    index_equivalent,
    index_replay,
    semantic_work_charge,
)
from .types import (
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
FINITE_SCOPE = "finite-ranked-root-reachable-generated-paths-and-declared-finite-setoid-carriers"
NATOP_SCOPE = "separate-symbolic-natop-lean-theorems-not-derived-from-finite-tlgc"


def generated_transport_coherence(raw: TransportPackage) -> TransportResult:
    """Establish exact C2.2 or return typed resource/formal/semantic boundary."""
    logger.debug("generated_transport_coherence entry")
    refusal, raw_charge = _raw_preflight(raw)
    if refusal is not None:
        return refusal
    package = snapshot_package(raw)
    index = build_transport_index(package.system, package.doctrine, HARD_GENERATED_PATHS)
    reachable = generated_reachable(package.system)[0]
    path_sizes = tuple(len(index.paths[state]) for state in reachable)
    generated_work = max(sum(path_sizes), sum(size * size for size in path_sizes))
    if generated_work > package.policy.max_generated_paths:
        return _resource(
            package,
            TransportFailedBound.GENERATED_PATHS,
            generated_work,
            package.policy.max_generated_paths,
        )
    work = semantic_work_charge(index, raw_charge.canonical_bytes + raw_charge.validation_nodes, package.local_fillers)
    if work.total > package.policy.max_semantic_work:
        return _resource(package, TransportFailedBound.SEMANTIC_WORK, work.total, package.policy.max_semantic_work)
    peaks = generated_local_peaks(package.system)
    cells = {x.peak_id: x for x in package.local_fillers}
    if len(cells) != len(package.local_fillers):
        reject("duplicate-local-filler")
    if set(cells) != {x.peak_id for x in peaks}:
        result = _semantic(
            package, (), len(peaks), 0, work.total, TransportCoherenceStatus.OPEN, "missing-or-extra-local-square"
        )
        logger.debug("generated_transport_coherence exit open")
        return result
    edges = {x.edge_id: x for x in package.system.edges}
    for peak in peaks:
        cell = cells[peak.peak_id]
        left, right = branch_targets(package.system, peak)
        left_full = (peak.left_edge_id, *cell.left_path)
        right_full = (peak.right_edge_id, *cell.right_path)
        if (
            index_replay(index, peak.source_state_id, left_full) != cell.target_state_id
            or index_replay(index, peak.source_state_id, right_full) != cell.target_state_id
        ):
            reject("local-square-path-drift")
        if not index_equivalent(index, peak.source_state_id, left_full, right_full):
            result = _semantic(
                package, (), len(peaks), 0, work.total, TransportCoherenceStatus.REFUTED, "noncommuting-local-square"
            )
            logger.debug("generated_transport_coherence exit refuted")
            return result
        if edges[peak.left_edge_id].source_id != edges[peak.right_edge_id].source_id:
            raise RuntimeError("internal peak source drift")
    formal = check_transport_theorems(
        package.theorem_source, package.policy.compile_timeout_seconds, package.policy.max_output_bytes
    )
    if formal.kind is not None:
        result = TransportFormalFailure(
            TransportFailureKind.FORMAL_FAILURE,
            formal.kind,
            f"formal execution {formal.kind.value}",
            formal.receipt_digest,
            P3C2_NONCLAIMS,
        )
        logger.debug("generated_transport_coherence exit formal-failure")
        return result
    fillers = derive_indexed_global_fillers(index, package.policy.max_generated_paths)
    result = _positive(package, fillers, len(peaks), work.total, formal.receipt_digest, formal.phase_count)
    logger.debug("generated_transport_coherence exit established fillers=%d", len(fillers))
    return result


def _raw_preflight(raw: TransportPackage):
    """Atomically charge every raw nested source before semantic replay."""
    logger.debug("_raw_preflight entry")
    from .preflight import charge_raw_package

    charge = charge_raw_package(raw)
    policy = object.__getattribute__(raw, "policy")
    bounds = tuple(
        object.__getattribute__(policy, name)
        for name in (
            "max_values",
            "max_map_entries",
            "max_local_fillers",
            "max_generated_paths",
            "max_semantic_work",
            "max_canonical_bytes",
            "compile_timeout_seconds",
            "max_output_bytes",
        )
    )
    if any(type(x) is not int for x in bounds):
        reject("transport-policy-bound-type-invalid")
    maxima = (4096, 16384, 16384, 16384, 10**12, 2 * 1024 * 1024, 300, 4 * 1024 * 1024)
    if any(not 1 <= value <= maximum for value, maximum in zip(bounds, maxima, strict=True)):
        reject("transport-policy-bound-invalid")
    counts = (
        (TransportFailedBound.VALUES, charge.values, bounds[0]),
        (TransportFailedBound.MAP_ENTRIES, charge.map_entries, bounds[1]),
        (TransportFailedBound.LOCAL_FILLERS, charge.local_fillers, bounds[2]),
        (TransportFailedBound.CANONICAL_BYTES, charge.canonical_bytes, bounds[5]),
    )
    for bound, required, allowed in counts:
        if required > allowed:
            return _resource(raw, bound, required, allowed), charge
    logger.debug("_raw_preflight exit clear")
    return None, charge


def _resource(
    package: TransportPackage, bound: TransportFailedBound, required: int, allowed: int
) -> TransportResourceLimit:
    """Construct one payload-free first-bound resource refusal."""
    logger.debug("_resource entry bound=%s", bound.value)
    hint = digest("veyra.p3c2.resource-hint.v1", (("package", package.package_digest.encode()),))
    value = digest(
        "veyra.p3c2.resource-limit.v1",
        (
            ("hint", hint.encode()),
            ("bound", bound.value.encode()),
            ("required", str(required).encode()),
            ("allowed", str(allowed).encode()),
        ),
    )
    result = TransportResourceLimit(
        TransportFailureKind.RESOURCE_LIMIT, bound, required, allowed, hint, P3C2_NONCLAIMS, value
    )
    logger.debug("_resource exit")
    return result


def _semantic(
    package: TransportPackage,
    fillers: tuple[GeneratedTransportFiller, ...],
    local_count: int,
    global_count: int,
    semantic_work: int,
    status: TransportCoherenceStatus,
    reason: str,
) -> GeneratedTransportCoherence:
    """Construct OPEN/REFUTED without formal or global-coherence promotion."""
    logger.debug("_semantic entry status=%s", status.value)
    value = digest(
        "veyra.p3c2.semantic-result.v1",
        (("package", package.package_digest.encode()), ("status", status.value.encode()), ("reason", reason.encode())),
    )
    result = GeneratedTransportCoherence(
        package.system.system_digest,
        package.doctrine.doctrine_digest,
        package.theorem_source.source_digest,
        package.assumption_ledger.ledger_digest,
        "0" * 64,
        semantic_work,
        tuple(x.filler_digest for x in package.local_fillers),
        fillers,
        local_count,
        global_count,
        0,
        FINITE_SCOPE,
        NATOP_SCOPE,
        status,
        HigherCellStructureStatus.NOT_IMPLEMENTED,
        P3C2_NONCLAIMS,
        value,
    )
    logger.debug("_semantic exit")
    return result


def _positive(
    package: TransportPackage,
    fillers: tuple[GeneratedTransportFiller, ...],
    local_count: int,
    semantic_work: int,
    receipt: str,
    phases: int,
) -> GeneratedTransportCoherence:
    """Construct C2.2; genuine higher cell-structure C2.3 is not implemented."""
    logger.debug("_positive entry")
    value = digest(
        "veyra.p3c2.positive-result.v1",
        (
            ("package", package.package_digest.encode()),
            ("receipt", receipt.encode()),
            *((f"global-{i}", x.filler_digest.encode()) for i, x in enumerate(fillers)),
            ("finite-scope", FINITE_SCOPE.encode()),
            ("natop-scope", NATOP_SCOPE.encode()),
            ("semantic-work", str(semantic_work).encode()),
            ("higher-cell-structure", b"not-implemented"),
        ),
    )
    result = GeneratedTransportCoherence(
        package.system.system_digest,
        package.doctrine.doctrine_digest,
        package.theorem_source.source_digest,
        package.assumption_ledger.ledger_digest,
        receipt,
        phases,
        tuple(x.filler_digest for x in package.local_fillers),
        fillers,
        local_count,
        len(fillers),
        semantic_work,
        FINITE_SCOPE,
        NATOP_SCOPE,
        TransportCoherenceStatus.GENERATED_TRANSPORT_COHERENT_RELATIVE_TO_SYSTEM,
        HigherCellStructureStatus.NOT_IMPLEMENTED,
        P3C2_NONCLAIMS,
        value,
    )
    logger.debug("_positive exit")
    return result
