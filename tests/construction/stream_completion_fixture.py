"""Shared exact PΩ1 source-package fixture."""

from src.core.stream_completion import (
    stream_alphabet_source, stream_completion_doctrine, stream_completion_ledger,
    stream_completion_package, stream_completion_policy,
    stream_completion_theorem_source,
)


def exact_package(symbols=("0", "1", "λ"), **policy_caps):
    """Return one fresh exact raw package."""
    return stream_completion_package(
        stream_completion_doctrine(), stream_alphabet_source(tuple(symbols)),
        stream_completion_theorem_source(), stream_completion_ledger(),
        stream_completion_policy(**policy_caps),
    )
