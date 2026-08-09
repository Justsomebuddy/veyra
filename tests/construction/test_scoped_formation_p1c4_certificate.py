"""Direct P1-C4 certificate smoke."""

from src.core.certify_scoped_formation import certify_scoped_formation


def test_scoped_formation_certificate_passes():
    row = certify_scoped_formation()
    assert row.name == "scoped_formation_p1c4"
    assert row.level == 1
    assert row.passed
