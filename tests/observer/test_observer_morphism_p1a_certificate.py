"""Certificate boundary for provisional P1-A observer morphisms."""

import logging

from src.core.certify_observer_morphism import certify_observer_morphism_p1a

logger = logging.getLogger(__name__)


def test_p1a_certificate_is_level_one_and_explicitly_nonpromoting():
    logger.debug("test_p1a_certificate entry")
    cert = certify_observer_morphism_p1a()
    assert cert.passed and cert.level == 1
    assert "confirmed nonempty comparison domains" in cert.method
    assert "no constructibility" in cert.method
    assert "infinity" in cert.method and "PΩ" in cert.method
    assert "family extension is not refinement" in cert.method
    assert "membership, not chronology" in cert.detail
    assert "relative to declared projection" in cert.detail
    assert "pair-component loss" in cert.detail
    logger.debug("test_p1a_certificate exit")
