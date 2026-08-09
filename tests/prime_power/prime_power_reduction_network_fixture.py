"""Fresh raw-only P3-N2 fixture."""

import logging

from src.core.prime_power_reduction_network import exact_reduction_network_package

logger = logging.getLogger(__name__)


def exact_n2_package(**caps):
    """Build the canonical small arithmetic scope."""
    logger.debug("exact_n2_package entry")
    result = exact_reduction_network_package(**caps)
    logger.debug("exact_n2_package exit")
    return result
