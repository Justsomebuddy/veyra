"""Certificate boundary for provisional P1-B finite replay."""

import logging

from src.core.certify_finite_construction import certify_finite_construction_p1b

logger = logging.getLogger(__name__)


def test_p1b_certificate_is_level_one_and_strictly_nonpromoting():
    logger.debug("test_p1b_certificate entry")
    cert = certify_finite_construction_p1b()
    assert cert.passed and cert.level == 1
    assert "formal generability only" in cert.method
    assert "not ontic genesis" in cert.method
    assert "target independence" in cert.method
    assert "scoped-object" in cert.method
    assert "all-depth" in cert.method and "PΩ" in cert.method
    assert "fresh identities" in cert.detail
    assert "object open" in cert.detail
    logger.debug("test_p1b_certificate exit")
