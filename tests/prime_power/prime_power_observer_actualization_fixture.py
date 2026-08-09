"""Dedicated raw-only fixtures for P3-N0 tests."""

from src.core.prime_power_observer_actualization import exact_n0_source


def exact_p3n0_source(**kwargs):
    """Build one canonical three-N1/two-N2-F source."""
    return exact_n0_source(**kwargs)
