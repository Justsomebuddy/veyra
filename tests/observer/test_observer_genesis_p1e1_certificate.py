"""Direct P1-E1 certificate boundary."""

from src.core.certify_observer_genesis import certify_observer_genesis_p1e1


def test_observer_genesis_certificate_is_level_one_and_keeps_nonclaims():
    certificate = certify_observer_genesis_p1e1()
    assert certificate.passed and certificate.level == 1
    assert "Mode-only exact 24-row adapter" in certificate.method
    assert "no E2/R11 shadow" in certificate.method
    assert "consciousness" in certificate.method and "physical instantiation" in certificate.method
    assert "target-independent history" in certificate.method
    assert "R8" in certificate.method and "Sage" in certificate.method
