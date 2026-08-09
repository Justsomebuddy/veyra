"""Fresh raw fixtures for isolated P3-N3/N4."""

from src.core.padic_completion import (
    padic_completion_ledger, padic_completion_package, padic_completion_policy,
    padic_completion_theorem_source, padic_tower_doctrine, prime_source,
)
from src.core.padic_family_introduction import (
    integer_source, n1_assumption_ledger, n1_introduction_package,
    n1_policy, n1_theorem_source,
)
from src.core.padic_local_realization import (
    all_depth_source, n3_request, n4_request, policy,
)


def exact_n34_packages(p=5, z=-123, **n34_caps):
    """Build raw source packages and exact N3/N4 requests."""
    prime, doctrine = prime_source(p), padic_tower_doctrine()
    n1 = n1_introduction_package(prime, integer_source(z), doctrine,
        n1_theorem_source(), n1_assumption_ledger(), n1_policy())
    p2 = padic_completion_package(prime, doctrine, padic_completion_theorem_source(),
        padic_completion_ledger(), padic_completion_policy())
    n3 = n3_request(n1, p2,
        execution_policy=None if not n34_caps else policy(**n34_caps))
    premise = all_depth_source(n1, n1, p2)
    n4 = n4_request(n1, n1, p2, premise)
    return n1, p2, n3, n4
