"""Sole allowlisted PΩ2 prime-power tower doctrine."""

from __future__ import annotations

import logging

from .common import exact_digest, exact_shape, reject
from .digest import digest
from .types import PadicTowerDoctrine

logger = logging.getLogger(__name__)
DOCTRINE_FIELDS = (
    "pomega2-prime-power-doctrine-v1", "veyra.padic.prime-power.v1", "Nat",
    "ZMod-p-pow-n-plus-one", "p-pow-n-plus-one", "canonical-mod-reduction",
    "all-compatible-prime-power-residue-families", "ZpVeyra-compatible-family-subtype",
    "Lean-Eq-coordinate-joint-separation", "canonical-Fin-coordinatewise-commutative-ring",
    "prime-power-completion-principle-v1",
)


def padic_tower_doctrine() -> PadicTowerDoctrine:
    """Construct the exact doctrine identity."""
    logger.debug("padic_tower_doctrine entry")
    value = digest("veyra.pomega2.doctrine.v1", tuple(
        (f"field-{index}", item.encode()) for index, item in enumerate(DOCTRINE_FIELDS)
    ))
    result = PadicTowerDoctrine(*DOCTRINE_FIELDS, value)
    logger.debug("padic_tower_doctrine exit")
    return result


def snapshot_doctrine(value: PadicTowerDoctrine) -> PadicTowerDoctrine:
    """Reject alternative stage/equality/ring/completion identifiers."""
    logger.debug("snapshot_doctrine entry")
    exact_shape(value, PadicTowerDoctrine, "padic-doctrine")
    try:
        names = tuple(name for name in value.__dict__ if name != "doctrine_digest")
        if any(type(getattr(value, name)) is not str for name in names):
            reject("padic-doctrine-scalar-type-invalid")
        exact_digest(value.doctrine_digest, "padic-doctrine-digest")
    except AttributeError:
        reject("padic-doctrine-missing-fields")
    expected = padic_tower_doctrine()
    if value != expected:
        reject("padic-doctrine-drift")
    logger.debug("snapshot_doctrine exit")
    return expected
