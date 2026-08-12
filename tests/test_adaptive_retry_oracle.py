from fractions import Fraction

import pytest

from src.core.observer_discovery_v3.lineage import (
    AdaptiveValidityStatus,
    adaptive_retry_witness,
    validate_adaptive_retry_witness,
)
from veyra_sage.adaptive_research_line import adaptive_retry_oracle


@pytest.mark.parametrize(
    ("attempts", "numerator", "denominator"),
    ((1, 1, 20), (2, 1, 20), (5, 1, 10), (20, 1, 20), (64, 1, 4)),
)
def test_production_witness_matches_independent_exact_oracle(
    attempts: int,
    numerator: int,
    denominator: int,
) -> None:
    witness = adaptive_retry_witness(attempts, numerator, denominator)
    oracle = adaptive_retry_oracle(attempts, numerator, denominator)
    assert (witness.any_positive_numerator, witness.any_positive_denominator) == (
        oracle.any_positive_numerator,
        oracle.any_positive_denominator,
    )
    assert Fraction(witness.any_positive_numerator, witness.any_positive_denominator) == (
        1 - (1 - Fraction(numerator, denominator)) ** attempts
    )
    assert witness.local_protocol_validity_compatible
    assert validate_adaptive_retry_witness(witness)
    assert not witness.family_policy_accounted
    assert witness.adaptive_validity is AdaptiveValidityStatus.NOT_ESTABLISHED


def test_twenty_five_percent_attempts_have_the_expected_inflation() -> None:
    row = adaptive_retry_oracle(20, 1, 20)
    probability = row.any_positive_numerator / row.any_positive_denominator
    assert 0.641 < probability < 0.642


@pytest.mark.parametrize("arguments", ((0, 1, 20), (20, 0, 20), (20, 20, 20)))
def test_oracle_and_production_reject_invalid_bounds(arguments: tuple[int, int, int]) -> None:
    with pytest.raises(ValueError):
        adaptive_retry_witness(*arguments)
    with pytest.raises(ValueError):
        adaptive_retry_oracle(*arguments)
