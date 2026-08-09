"""Fresh raw P3-C2 fixtures without prior judgments or P3-T adapters."""

from src.core.transport_coherence import positive_example


def exact_transport_package(**caps):
    """Return one exact finite total-setoid transport package."""
    return positive_example(**caps).package
