"""Local-square, policy, and exact package construction for P3-C2."""

from __future__ import annotations
import logging
from ..confluence.generated.paths import branch_targets, generated_local_peaks
from ..confluence.generated.source import snapshot_ranked_system
from ..confluence.generated.types import RankedContinuationSystem
from .common import digest, exact_digest, exact_shape, exact_text, reject
from .paths import replay_path
from .source import HARD_CANONICAL_BYTES, HARD_MAP_ENTRIES, HARD_VALUES, snapshot_transport_doctrine
from .types import (
    LocalCommutingFiller,
    TransportAssumptionLedger,
    TotalTransportDoctrine,
    TransportPackage,
    TransportPolicy,
    TransportTheoremSource,
)

logger = logging.getLogger(__name__)
HARD_LOCAL_FILLERS = 16384
HARD_GENERATED_PATHS = 16384
HARD_SEMANTIC_WORK = 10**12
POLICY_ORACLE_VERSION = "p3-c2-policy-v1"


def local_commuting_filler(
    system: RankedContinuationSystem,
    doctrine: TotalTransportDoctrine,
    peak_id: str,
    left_path: tuple[str, ...],
    right_path: tuple[str, ...],
    target_state_id: str,
) -> LocalCommutingFiller:
    """Construct one typed same-system local filler; commutation is replayed later."""
    logger.debug("local_commuting_filler entry")
    system = snapshot_ranked_system(system)
    doctrine = snapshot_transport_doctrine(system, doctrine)
    exact_text(peak_id, "local-peak")
    exact_text(target_state_id, "local-target")
    peaks = {x.peak_id: x for x in generated_local_peaks(system)}
    peak = peaks.get(peak_id)
    if peak is None:
        reject("local-filler-peak-foreign")
    left_start, right_start = branch_targets(system, peak)
    if (
        replay_path(system, left_start, left_path) != target_state_id
        or replay_path(system, right_start, right_path) != target_state_id
    ):
        reject("local-filler-endpoint-mismatch")
    value = digest(
        "veyra.p3c2.local-filler.v1",
        (
            ("system", system.system_digest.encode()),
            ("doctrine", doctrine.doctrine_digest.encode()),
            ("peak", peak_id.encode()),
            ("left", repr(left_path).encode()),
            ("right", repr(right_path).encode()),
            ("target", target_state_id.encode()),
        ),
    )
    result = LocalCommutingFiller(
        peak_id, left_path, right_path, target_state_id, system.system_digest, doctrine.doctrine_digest, value
    )
    logger.debug("local_commuting_filler exit")
    return result


def transport_policy(
    max_values: int = HARD_VALUES,
    max_map_entries: int = HARD_MAP_ENTRIES,
    max_local_fillers: int = HARD_LOCAL_FILLERS,
    max_generated_paths: int = HARD_GENERATED_PATHS,
    max_semantic_work: int = HARD_SEMANTIC_WORK,
    max_canonical_bytes: int = HARD_CANONICAL_BYTES,
    compile_timeout_seconds: int = 120,
    max_output_bytes: int = 1024 * 1024,
) -> TransportPolicy:
    """Construct exact bounded execution policy under immutable hard maxima."""
    logger.debug("transport_policy entry")
    values = (
        max_values,
        max_map_entries,
        max_local_fillers,
        max_generated_paths,
        max_semantic_work,
        max_canonical_bytes,
        compile_timeout_seconds,
        max_output_bytes,
    )
    if any(type(x) is not int for x in values):
        reject("transport-policy-exact-integers-required")
    maxima = (
        HARD_VALUES,
        HARD_MAP_ENTRIES,
        HARD_LOCAL_FILLERS,
        HARD_GENERATED_PATHS,
        HARD_SEMANTIC_WORK,
        HARD_CANONICAL_BYTES,
        300,
        4 * 1024 * 1024,
    )
    if any(not 1 <= x <= m for x, m in zip(values, maxima, strict=True)):
        reject("transport-policy-bound-invalid")
    value = digest(
        "veyra.p3c2.policy.v1",
        (
            ("version", POLICY_ORACLE_VERSION.encode()),
            *((f"bound-{i}", x.to_bytes(8, "big")) for i, x in enumerate(values)),
        ),
    )
    result = TransportPolicy(*values, value)
    logger.debug("transport_policy exit")
    return result


def snapshot_policy(raw: TransportPolicy) -> TransportPolicy:
    """Reject policy subclasses, Booleans, and digest drift."""
    logger.debug("snapshot_policy entry")
    exact_shape(raw, TransportPolicy, "transport-policy")
    exact_digest(object.__getattribute__(raw, "policy_digest"), "transport-policy-digest")
    expected = transport_policy(
        raw.max_values,
        raw.max_map_entries,
        raw.max_local_fillers,
        raw.max_generated_paths,
        raw.max_semantic_work,
        raw.max_canonical_bytes,
        raw.compile_timeout_seconds,
        raw.max_output_bytes,
    )
    if raw != expected:
        reject("transport-policy-drift")
    logger.debug("snapshot_policy exit")
    return expected


def transport_package(
    system: RankedContinuationSystem,
    doctrine: TotalTransportDoctrine,
    local_fillers: tuple[LocalCommutingFiller, ...],
    theorem_source: TransportTheoremSource,
    assumption_ledger: TransportAssumptionLedger,
    policy: TransportPolicy,
) -> TransportPackage:
    """Build one raw exact C2 package without prior results or P3-T adapters."""
    logger.debug("transport_package entry")
    system = snapshot_ranked_system(system)
    doctrine = snapshot_transport_doctrine(system, doctrine)
    if type(local_fillers) is not tuple or len(local_fillers) > HARD_LOCAL_FILLERS:
        reject("local-fillers-container-or-hard-limit")
    fillers = tuple(sorted((_snapshot_filler(system, doctrine, x) for x in local_fillers), key=lambda x: x.peak_id))
    theorem = _snapshot_theorem(theorem_source)
    from .ledger import snapshot_ledger

    ledger = snapshot_ledger(assumption_ledger)
    policy = snapshot_policy(policy)
    value = digest(
        "veyra.p3c2.package.v1",
        (
            ("system", system.system_digest.encode()),
            ("doctrine", doctrine.doctrine_digest.encode()),
            *((f"filler-{i}", x.filler_digest.encode()) for i, x in enumerate(fillers)),
            ("theorem", theorem.source_digest.encode()),
            ("ledger", ledger.ledger_digest.encode()),
            ("policy", policy.policy_digest.encode()),
        ),
    )
    result = TransportPackage(system, doctrine, fillers, theorem, ledger, policy, value)
    logger.debug("transport_package exit fillers=%d", len(fillers))
    return result


def snapshot_package(raw: TransportPackage) -> TransportPackage:
    """Deeply rebuild every raw commitment before semantic or formal work."""
    logger.debug("snapshot_package entry")
    exact_shape(raw, TransportPackage, "transport-package")
    expected = transport_package(
        raw.system, raw.doctrine, raw.local_fillers, raw.theorem_source, raw.assumption_ledger, raw.policy
    )
    exact_digest(raw.package_digest, "transport-package-digest")
    if raw != expected:
        reject("transport-package-drift")
    logger.debug("snapshot_package exit")
    return expected


def _snapshot_filler(
    system: RankedContinuationSystem, doctrine: TotalTransportDoctrine, raw: LocalCommutingFiller
) -> LocalCommutingFiller:
    logger.debug("_snapshot_filler entry")
    exact_shape(raw, LocalCommutingFiller, "local-filler")
    if type(raw.left_path) is not tuple or type(raw.right_path) is not tuple:
        reject("local-filler-path-container-invalid")
    for name in ("system_digest", "doctrine_digest", "filler_digest"):
        exact_digest(object.__getattribute__(raw, name), f"local-filler-{name}")
    expected = local_commuting_filler(system, doctrine, raw.peak_id, raw.left_path, raw.right_path, raw.target_state_id)
    if raw != expected:
        reject("local-filler-drift")
    logger.debug("_snapshot_filler exit")
    return expected


def _snapshot_theorem(raw: TransportTheoremSource) -> TransportTheoremSource:
    logger.debug("_snapshot_theorem entry")
    exact_shape(raw, TransportTheoremSource, "transport-theorem-source")
    for name in ("version", "artifact_path", "toolchain_id"):
        exact_text(object.__getattribute__(raw, name), f"transport-theorem-{name}")
    for name in ("artifact_sha256", "tcb_digest", "source_digest"):
        exact_digest(object.__getattribute__(raw, name), f"transport-theorem-{name}")
    if type(raw.theorem_ids) is not tuple or any(type(x) is not str for x in raw.theorem_ids):
        reject("transport-theorem-ids-invalid")
    from .formal import transport_theorem_source

    expected = transport_theorem_source()
    if raw != expected:
        reject("transport-theorem-source-drift")
    logger.debug("_snapshot_theorem exit")
    return expected
