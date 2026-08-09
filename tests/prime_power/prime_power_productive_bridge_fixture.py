"""Fresh raw-only P3-A1b package fixture."""

from src.core.padic_completion import padic_tower_doctrine, prime_source
from src.core.padic_family_introduction import integer_source
from src.core.prime_power_productive_bridge import (
    bridge_ledger, bridge_policy, bridge_theorem_source, exact_n1_theorem_source,
    offset_residue_program_source, productive_bridge_package, residue_program_source,
)


def exact_a1b_package(p=5, z=-123, **caps):
    """Build exact p/z/program/N1/bridge raw sources without prior judgments."""
    prime = prime_source(p)
    integer = integer_source(z)
    return productive_bridge_package(
        prime, integer, padic_tower_doctrine(),
        residue_program_source(prime, integer), exact_n1_theorem_source(), bridge_theorem_source(),
        bridge_ledger(), bridge_policy(**caps),
    )


def exact_offset_pressure(package, offset=1):
    """Build a closed pressure program bound to the package's exact p/z."""
    return offset_residue_program_source(package.prime, package.integer, offset)
