"""Shared exact P3-T focused fixture."""

from src.core.observer_network import example_observer_network


def network_source():
    """Return a freshly constructed source for each test."""
    return example_observer_network()
