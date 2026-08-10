"""Recent release certificates split from the root registry for cohesion."""

from __future__ import annotations

import logging

from .certify_all_depth_family import certify_all_depth_family_p1d3
from .certify_generated_confluence import certify_generated_confluence_p3c1
from .certify_observer_actualization import certify_observer_actualization_p1e4
from .certify_observer_network import certify_observer_network_p3t
from .certify_padic_completion import certify_padic_completion_pomega2
from .certify_padic_family_introduction import certify_padic_family_introduction_p3n1
from .certify_padic_local_realization import certify_padic_local_realization
from .certify_prime_power_productive_bridge import certify_prime_power_productive_bridge_p3a1b
from .certify_prime_power_reduction_network import certify_prime_power_reduction_network
from .certify_scoped_formation import certify_scoped_formation
from .certify_status_promotion import certify_status_promotion_p2s
from .certify_stream_completion import certify_stream_completion_pomega1
from .certify_transport_coherence import certify_transport_coherence_p3c2
from .certify_types import Certificate

logger = logging.getLogger(__name__)


def certify_d3_pomega_p2s_bundle() -> tuple[Certificate, ...]:
    """Return thirteen independently scoped recent release certificates."""
    logger.debug("certify_d3_pomega_p2s_bundle entry")
    result = (
        certify_all_depth_family_p1d3(),
        certify_stream_completion_pomega1(),
        certify_status_promotion_p2s(),
        certify_scoped_formation(),
        certify_observer_actualization_p1e4(),
        certify_generated_confluence_p3c1(),
        certify_padic_completion_pomega2(),
        certify_padic_family_introduction_p3n1(),
        certify_observer_network_p3t(),
        certify_prime_power_productive_bridge_p3a1b(),
        certify_transport_coherence_p3c2(),
        certify_prime_power_reduction_network(),
        certify_padic_local_realization(),
    )
    logger.debug(
        "certify_d3_pomega_p2s_bundle exit count=%d passed=%d",
        len(result), sum(item.passed for item in result),
    )
    return result
