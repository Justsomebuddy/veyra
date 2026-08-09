"""Fresh raw P3-N1 fixture with no prior judgment/certificate inputs."""

from src.core.padic_completion import padic_tower_doctrine, prime_source
from src.core.padic_family_introduction import (
    integer_source, n1_assumption_ledger, n1_introduction_package,
    n1_policy, n1_theorem_source,
)


def exact_n1_package(p=5, z=-123, **caps):
    """Build one exact raw introduction package."""
    return n1_introduction_package(
        prime_source(p), integer_source(z), padic_tower_doctrine(),
        n1_theorem_source(), n1_assumption_ledger(), n1_policy(**caps),
    )
