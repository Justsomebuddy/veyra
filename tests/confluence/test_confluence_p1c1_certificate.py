"""Certificate regression for provisional P1-C1."""

from src.core.certify_confluence import certify_confluence_p1c1


def test_confluence_p1c1_certificate_is_level_one_and_nonpromoting():
    cert = certify_confluence_p1c1()
    assert cert.name == "confluence_p1c1"
    assert cert.passed and cert.level == 1
    assert "direct-echo one-fork" in cert.method
    assert "no aggregation" in cert.method
    assert "no" in cert.method and "promotion" in cert.method
