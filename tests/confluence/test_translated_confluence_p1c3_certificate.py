"""Certificate pressure for P1-C3."""

from src.core.certify_translated_confluence import certify_translated_confluence_p1c3


def test_translated_confluence_certificate_is_level_one_and_passes():
    row = certify_translated_confluence_p1c3()
    assert row.name == "translated_confluence_p1c3"
    assert row.level == 1
    assert row.passed
    assert "no observer identity" in row.detail
