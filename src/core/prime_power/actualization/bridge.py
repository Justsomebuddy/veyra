"""Typed raw-N1 to finite-family coordinate bridge for P3-N0."""

from __future__ import annotations

import logging

from ...padic.family_introduction.common import digest as n1_digest
from .common import digest, indexed
from .types import (
    N0FamilyBridgeRow, N0FamilyFiniteBridgeSource,
)
from ..reduction_network.common import digest as n2_digest
from ..reduction_network.types import FamilyCoordinate, FiniteFamilySource

logger = logging.getLogger(__name__)


def family_finite_bridge(n1s, strict, open_lane, depths):
    """Bind every raw N1 family term to exact n,n+1 finite coordinates."""
    logger.debug("family_finite_bridge entry")
    by_integer = {
        family.integer: family
        for wrapper in (strict, open_lane) for family in wrapper.raw_package.finite.families
    }
    if 1 not in by_integer:
        nodes = strict.raw_package.finite.depths
        coords = tuple(FamilyCoordinate(
            node.depth, 1 % node.modulus,
            n2_digest("veyra.p3n2.coordinate.v1", (
                ("z", b"1"), ("node", node.node_digest.encode()),
            )),
        ) for node in nodes)
        family_digest = n2_digest("veyra.p3n2.family.v1", (
            ("z", b"1"),
            *((f"coordinate-{i}", item.coordinate_digest.encode())
              for i, item in enumerate(coords)),
        ))
        by_integer[1] = FiniteFamilySource("integer:1", 1, coords, family_digest)
    rows = []
    for package in n1s:
        family = by_integer[package.integer.z]
        family_term = n1_digest("veyra.p3n1.family-term.v1", (
            ("prime", package.prime.source_digest.encode()),
            ("integer", package.integer.source_digest.encode()),
            ("doctrine", package.doctrine.doctrine_digest.encode()),
            ("family-class", package.doctrine.family_class_id.encode()),
            ("coordinate-definition", package.theorem_source.coordinate_definition_id.encode()),
            ("family-definition", package.theorem_source.family_definition_id.encode()),
        ))
        row_digest = digest("veyra.p3n0.bridge-row.v1", (
            ("package", package.package_digest.encode()),
            ("integer", package.integer.source_digest.encode()),
            ("family", family.family_digest.encode()), ("family-term", family_term.encode()),
        ))
        rows.append(N0FamilyBridgeRow(
            family.family_id, package.package_digest, family_term, family, row_digest,
        ))
    value = digest("veyra.p3n0.bridge.v1", (
        *indexed("depth", depths), *indexed("row", (x.row_digest for x in rows)),
    ))
    result = N0FamilyFiniteBridgeSource("p3n0-bridge-v1", depths, tuple(rows), value)
    logger.debug("family_finite_bridge exit rows=%d", len(rows))
    return result
