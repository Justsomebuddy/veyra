"""Direct P3-N2 certificate check."""

from src.core.certify_prime_power_reduction_network import (
    certify_prime_power_reduction_network,
)
import pytest

pytestmark = pytest.mark.requires_lean


def test_direct_p3n2_certificate_passes_all_attacks():
    result = certify_prime_power_reduction_network()
    assert result.passed
    assert "attacks=23/23" in result.detail
    assert "refutations=2 open=1" in result.detail
    assert "completed_carrier_premise=0" in result.detail
