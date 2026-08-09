"""Exact fillers and a C2.2-derived cofinal boundary reconciliation."""

from __future__ import annotations
import logging
from .common import digest, exact_shape, reject
from .package import snapshot_package
from .paths import boundary_digest, paths_equivalent, replay_path
from .types import CofinalBoundaryReconciliation, GeneratedTransportFiller, TransportPackage

logger = logging.getLogger(__name__)


def generated_transport_filler(
    package: TransportPackage,
    root_state_id: str,
    left_boundary: tuple[str, ...],
    right_boundary: tuple[str, ...],
    target_state_id: str,
    left_postpath: tuple[str, ...],
    right_postpath: tuple[str, ...],
) -> GeneratedTransportFiller:
    """Construct one exact typed commuting filler for a generated boundary."""
    logger.debug("generated_transport_filler entry")
    package = snapshot_package(package)
    if type(root_state_id) is not str or type(target_state_id) is not str:
        reject("generated-filler-state-invalid")
    for row in (left_boundary, right_boundary, left_postpath, right_postpath):
        if type(row) is not tuple or any(type(x) is not str for x in row):
            reject("generated-filler-path-invalid")
    left_end = replay_path(package.system, root_state_id, left_boundary)
    right_end = replay_path(package.system, root_state_id, right_boundary)
    if (
        replay_path(package.system, left_end, left_postpath) != target_state_id
        or replay_path(package.system, right_end, right_postpath) != target_state_id
    ):
        reject("generated-filler-endpoint-invalid")
    if not paths_equivalent(
        package.system,
        package.doctrine,
        root_state_id,
        (*left_boundary, *left_postpath),
        (*right_boundary, *right_postpath),
    ):
        reject("generated-filler-does-not-commute")
    value = digest(
        "veyra.p3c2.global-filler.v1",
        (
            ("system", package.system.system_digest.encode()),
            ("doctrine", package.doctrine.doctrine_digest.encode()),
            ("root", root_state_id.encode()),
            ("left", repr(left_boundary).encode()),
            ("right", repr(right_boundary).encode()),
            ("target", target_state_id.encode()),
            ("left-post", repr(left_postpath).encode()),
            ("right-post", repr(right_postpath).encode()),
        ),
    )
    result = GeneratedTransportFiller(
        root_state_id, left_boundary, right_boundary, target_state_id, left_postpath, right_postpath, value
    )
    logger.debug("generated_transport_filler exit")
    return result


def cofinal_boundary_reconciliation(
    package: TransportPackage,
    first: GeneratedTransportFiller,
    second: GeneratedTransportFiller,
    postjoin_state_id: str,
    first_postpath: tuple[str, ...],
    second_postpath: tuple[str, ...],
) -> CofinalBoundaryReconciliation:
    """Reconcile two filler boundaries as a derived consequence of C2.2.

    This value is deliberately not a 3-cell and admits no higher-cell structure.
    """
    logger.debug("cofinal_boundary_reconciliation entry")
    if type(postjoin_state_id) is not str:
        reject("cofinal-postjoin-state-invalid")
    for row in (first_postpath, second_postpath):
        if type(row) is not tuple or any(type(x) is not str for x in row):
            reject("cofinal-postjoin-path-shape-invalid")
    package = snapshot_package(package)
    first = _snapshot_generated_filler(package, first)
    second = _snapshot_generated_filler(package, second)
    if boundary_digest(first) != boundary_digest(second):
        reject("cofinal-boundary-mismatch")
    if (
        replay_path(package.system, first.target_state_id, first_postpath) != postjoin_state_id
        or replay_path(package.system, second.target_state_id, second_postpath) != postjoin_state_id
    ):
        reject("cofinal-postjoin-path-invalid")
    root = first.root_state_id
    pairs = (
        (
            (*first.left_boundary, *first.left_postpath, *first_postpath),
            (*second.left_boundary, *second.left_postpath, *second_postpath),
        ),
        (
            (*first.right_boundary, *first.right_postpath, *first_postpath),
            (*second.right_boundary, *second.right_postpath, *second_postpath),
        ),
    )
    if any(not paths_equivalent(package.system, package.doctrine, root, left, right) for left, right in pairs):
        reject("cofinal-postcomposed-map-inequality")
    bd = boundary_digest(first)
    value = digest(
        "veyra.p3c2.cofinal-boundary-reconciliation-derived-c22.v1",
        (
            ("boundary", bd.encode()),
            ("t1", first.target_state_id.encode()),
            ("t2", second.target_state_id.encode()),
            ("s", postjoin_state_id.encode()),
            ("c", repr(first_postpath).encode()),
            ("d", repr(second_postpath).encode()),
            ("f1", first.filler_digest.encode()),
            ("f2", second.filler_digest.encode()),
            ("system", package.system.system_digest.encode()),
            ("doctrine", package.doctrine.doctrine_digest.encode()),
        ),
    )
    result = CofinalBoundaryReconciliation(
        bd,
        first.target_state_id,
        second.target_state_id,
        postjoin_state_id,
        first_postpath,
        second_postpath,
        first.filler_digest,
        second.filler_digest,
        package.system.system_digest,
        package.doctrine.doctrine_digest,
        value,
    )
    logger.debug("cofinal_boundary_reconciliation exit")
    return result


def _snapshot_generated_filler(package: TransportPackage, raw: GeneratedTransportFiller) -> GeneratedTransportFiller:
    """Rebuild a caller-supplied filler before any cofinal comparison."""
    logger.debug("_snapshot_generated_filler entry")
    exact_shape(raw, GeneratedTransportFiller, "generated-filler")
    from .common import exact_digest

    exact_digest(object.__getattribute__(raw, "filler_digest"), "generated-filler-digest")
    expected = generated_transport_filler(
        package,
        raw.root_state_id,
        raw.left_boundary,
        raw.right_boundary,
        raw.target_state_id,
        raw.left_postpath,
        raw.right_postpath,
    )
    if raw != expected:
        reject("generated-filler-drift")
    logger.debug("_snapshot_generated_filler exit")
    return expected
