"""Exact representation transports for strict Phase-III discovery inputs."""

from .protocol import (
    apply_representation_transport,
    validate_representation_transport_result,
)
from .observer import (
    check_observer_representation_transport,
    validate_observer_transport_result,
)
from .observer_types import (
    OBSERVER_TRANSPORT_BLOCKED,
    OBSERVER_TRANSPORT_BOUNDARY,
    OBSERVER_TRANSPORT_REFUTED,
    OBSERVER_TRANSPORT_VERIFIED,
    ObserverTransportReceipt,
    ObserverTransportResult,
)
from .types import (
    TRANSPORT_APPLIED,
    TRANSPORT_BLOCKED,
    TRANSPORT_BOUNDARY,
    CategoryBijection,
    RepresentationObstruction,
    RepresentationTransportReceipt,
    RepresentationTransportResult,
    RepresentationTransportSpec,
)

__all__ = (
    "TRANSPORT_APPLIED",
    "TRANSPORT_BLOCKED",
    "TRANSPORT_BOUNDARY",
    "CategoryBijection",
    "RepresentationObstruction",
    "RepresentationTransportReceipt",
    "RepresentationTransportResult",
    "RepresentationTransportSpec",
    "apply_representation_transport",
    "validate_representation_transport_result",
    "OBSERVER_TRANSPORT_BLOCKED",
    "OBSERVER_TRANSPORT_BOUNDARY",
    "OBSERVER_TRANSPORT_REFUTED",
    "OBSERVER_TRANSPORT_VERIFIED",
    "ObserverTransportReceipt",
    "ObserverTransportResult",
    "check_observer_representation_transport",
    "validate_observer_transport_result",
)
