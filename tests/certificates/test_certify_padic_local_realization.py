"""Direct certificate test for isolated P3-N3/N4."""

from src.core.certify_padic_local_realization import certify_padic_local_realization
import pytest

pytestmark = pytest.mark.requires_lean


def test_direct_p3n3n4_certificate_passes():
    certificate = certify_padic_local_realization()
    assert certificate.passed
    assert certificate.level == 1
    assert "attacks=25/25" in certificate.detail
    assert "promotions=0" in certificate.detail
