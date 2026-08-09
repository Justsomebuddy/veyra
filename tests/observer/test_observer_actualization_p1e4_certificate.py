"""Direct certificate and isolated public-surface checks for P1-E4."""

import logging

import src.core.observer_actualization as api
from src.core.certify_observer_actualization import certify_observer_actualization_p1e4

logger = logging.getLogger(__name__)


def test_direct_actualization_certificate_is_narrow_and_passes():
    logger.debug("test e4 certificate entry")
    certificate = certify_observer_actualization_p1e4()
    assert certificate.name == "observer_actualization_p1e4"
    assert certificate.level == 1 and certificate.passed
    assert "history-relative HAP" in certificate.method
    assert "counterfactuals=3/3" in certificate.detail
    assert "physical_claims=0 consciousness_claims=0" in certificate.detail
    logger.debug("test e4 certificate exit")


def test_isolated_facade_exports_are_unique_and_keep_permanent_nonclaims():
    logger.debug("test e4 facade entry")
    assert len(api.__all__) == len(set(api.__all__))
    assert all(hasattr(api, name) for name in api.__all__)
    assert tuple(api.PhysicalInstantiation) == (
        api.PhysicalInstantiation.NOT_ESTABLISHED,
    )
    assert tuple(api.ConsciousnessStatus) == (
        api.ConsciousnessStatus.NOT_CLAIMED,
    )
    assert tuple(api.HistoricalActualization) == (
        api.HistoricalActualization.ESTABLISHED_RELATIVE_TO_HISTORY,
        api.HistoricalActualization.OPEN,
    )
    logger.debug("test e4 facade exit")
