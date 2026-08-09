"""Certificate gate for P1-A2.1/A2.2."""

from src.core.certify_observer_relations import certify_observer_relations_p1a2


def test_observer_relations_certificate_is_level_one_and_passes():
    certificate = certify_observer_relations_p1a2()
    assert certificate.name == "observer_relations_p1a2"
    assert certificate.passed
    assert certificate.level == 1
    assert "NOT_ESTABLISHED" in certificate.detail
