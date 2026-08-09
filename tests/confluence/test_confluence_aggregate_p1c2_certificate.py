"""Certificate regression for P1-C2 declared finite aggregation."""

from src.core.certify_confluence_aggregate import certify_confluence_aggregate_p1c2


def test_confluence_aggregate_certificate_is_level_one_and_nonpromoting():
    cert = certify_confluence_aggregate_p1c2()
    assert cert.name == "confluence_aggregate_p1c2"
    assert cert.passed and cert.level == 1
    assert "cycle-versus-zero-edge identity" in cert.method
    assert "no generated-path universe" in cert.method
    assert "Church-Rosser" in cert.method and "object formation" in cert.method
