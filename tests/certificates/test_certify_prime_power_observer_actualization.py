"""Direct certificate test for P3-N0; intentionally not registry-coupled."""

from src.core.certify_prime_power_observer_actualization import (
    certify_prime_power_observer_actualization_p3n0,
)
import pytest

pytestmark = pytest.mark.requires_lean


def test_direct_p3n0_certificate_passes_with_full_executed_matrix():
    certificate = certify_prime_power_observer_actualization_p3n0()
    assert certificate.passed
    assert "base_attacks=24" in certificate.detail
    assert "submissions=40" in certificate.detail
    assert "pending_first=1" in certificate.detail
    assert "admission_split=1" in certificate.detail
    assert "promotions=0" in certificate.detail
