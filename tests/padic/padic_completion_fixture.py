"""Shared exact isolated PΩ2 source-package fixture."""

from src.core.padic_completion import (
    padic_completion_ledger, padic_completion_package, padic_completion_policy,
    padic_completion_theorem_source, padic_tower_doctrine, prime_source,
)


def exact_padic_package(p=5, **policy_caps):
    """Return one fresh exact source-only PΩ2 package."""
    return padic_completion_package(
        prime_source(p), padic_tower_doctrine(), padic_completion_theorem_source(),
        padic_completion_ledger(), padic_completion_policy(**policy_caps),
    )
