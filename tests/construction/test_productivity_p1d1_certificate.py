"""Certificate regression for provisional P1-D1."""

from src.core.certify_productivity import certify_productivity_p1d1


def test_productivity_p1d1_certificate_is_level_one_and_nonpromoting():
    cert = certify_productivity_p1d1()
    assert cert.name == "productivity_p1d1"
    assert cert.passed and cert.level == 1
    assert "closed nonempty periodic" in cert.method
    assert "no extensional all-depth family" in cert.method
    assert "PΩ" in cert.method and "Sage" in cert.method
