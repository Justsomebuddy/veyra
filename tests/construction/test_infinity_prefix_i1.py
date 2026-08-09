"""Focused finite-prefix tests for the bounded I1 experiment."""

import logging

import src.core as core
from src.core.infinity_prefix import (
    first_prefix_obstruction,
    periodic_prefix_window,
    prefix_alphabet,
    prefix_coherence_report,
    prefix_stage,
    prefix_tower_window,
    restrict_prefix,
)

logger = logging.getLogger(__name__)


def test_periodic_prefix_window_is_exactly_coherent_at_declared_depth():
    logger.debug("test_periodic_prefix_window_is_exactly_coherent_at_declared_depth entry")
    alphabet = prefix_alphabet(("a", "b"))
    window = periodic_prefix_window(alphabet, ("a", "a", "b"), 7)
    assert tuple(stage.depth for stage in window.stages) == tuple(range(8))
    assert window.stages[-1].symbols == ("a", "a", "b", "a", "a", "b", "a")
    assert prefix_coherence_report(window) == core.PrefixCoherenceReport(7, 7, True, None)
    assert restrict_prefix(prefix_stage(alphabet, 3, ("a", "a", "b")), 2).symbols == ("a", "a")
    logger.debug("test_periodic_prefix_window_is_exactly_coherent_at_declared_depth exit")


def test_prefix_window_preserves_and_reports_first_incoherent_candidate():
    logger.debug("test_prefix_window_preserves_and_reports_first_incoherent_candidate entry")
    alphabet = prefix_alphabet(("a", "b"))
    window = prefix_tower_window(
        alphabet, ((), ("a",), ("a", "b"), ("b", "b", "a"))
    )
    obstruction = first_prefix_obstruction(window)
    assert obstruction == core.PrefixRestrictionObstruction(2, 3, 0, "a", "b")
    assert prefix_coherence_report(window) == core.PrefixCoherenceReport(3, 3, False, obstruction)
    logger.debug("test_prefix_window_preserves_and_reports_first_incoherent_candidate exit")


def test_i1_prefix_public_api_is_exactly_exported():
    logger.debug("test_i1_prefix_public_api_is_exactly_exported entry")
    expected = {
        "PrefixAlphabet", "PrefixStage", "PrefixTowerWindow",
        "PrefixRestrictionObstruction", "PrefixCoherenceReport", "prefix_alphabet",
        "prefix_tower_window", "periodic_prefix_window",
        "first_prefix_obstruction", "prefix_coherence_report", "prefix_stage", "restrict_prefix",
    }
    assert expected <= set(core.__all__)
    for name in expected:
        assert getattr(core, name) is not None
    logger.debug("test_i1_prefix_public_api_is_exactly_exported exit")
