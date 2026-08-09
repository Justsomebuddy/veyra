"""All twenty-three mandatory P3-N2 attacks plus hostile envelopes."""

from dataclasses import replace

import pytest

from src.core.prime_power_reduction_network import (
    PrimePowerReductionValidationError, exact_reduction_network_package,
    prime_power_reduction_judgment, validate_prime_power_reduction_result,
)
from src.core.prime_power_reduction_network_pressure import (
    ATTACK_LABELS, required_n2_attacks,
)
from prime_power_reduction_network_fixture import exact_n2_package

pytestmark = pytest.mark.requires_lean


@pytest.fixture(scope="module")
def attack_rows():
    package = exact_n2_package()
    result = prime_power_reduction_judgment(package)
    refusal = prime_power_reduction_judgment(
        exact_reduction_network_package(max_captured_bytes=1)
    )
    return required_n2_attacks(package, result, refusal)


@pytest.mark.parametrize("index,label", tuple(enumerate(ATTACK_LABELS)))
def test_mandatory_attack(index, label, attack_rows):
    assert attack_rows[index] == (label, True)


def test_result_subclass_is_rejected_before_replay():
    package = exact_n2_package()
    result = prime_power_reduction_judgment(package)

    class Evil(type(result)):
        pass

    with pytest.raises(PrimePowerReductionValidationError, match="exact-type"):
        validate_prime_power_reduction_result(package, Evil(**result.__dict__))


def test_forged_result_digest_is_rejected():
    package = exact_n2_package()
    result = prime_power_reduction_judgment(package)
    forged = replace(result, judgment_digest="0" * 64)
    with pytest.raises(PrimePowerReductionValidationError, match="result-mismatch"):
        validate_prime_power_reduction_result(package, forged)


def test_boolean_policy_cap_is_rejected_not_normalized():
    with pytest.raises(PrimePowerReductionValidationError, match="policy-invalid"):
        exact_n2_package(max_depths=True)
