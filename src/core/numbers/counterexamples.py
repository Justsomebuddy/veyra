"""Counterexample search helpers for multi-tact Veyra mode shadows."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import logging
from typing import Iterable

from .modes import Mode, TEST_FAMILIES, echo_key, substitute_mode

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EchoSplit:
    """A pair equivalent under one test family but separated by another."""

    left: Mode
    right: Mode
    coarse_test: str
    fine_test: str
    coarse_key: tuple[object, ...]
    left_fine_key: tuple[object, ...]
    right_fine_key: tuple[object, ...]


@dataclass(frozen=True)
class StitchCommutator:
    """A pair whose two stitch orders diverge under a test family."""

    left: Mode
    right: Mode
    left_then_right: Mode
    right_then_left: Mode
    test_name: str


@dataclass(frozen=True)
class WeaveIncompatibility:
    """A driver echo destroyed by symbol-sensitive substitution weave."""

    driver_left: Mode
    driver_right: Mode
    output_left: Mode
    output_right: Mode
    driver_test: str
    output_test: str
    mapping: dict[str, Mode]


def group_by_test(modes: Iterable[Mode], test_name: str) -> dict[tuple[object, ...], list[Mode]]:
    """Group modes by echo key for a named test family."""
    logger.debug("group_by_test entry test=%s", test_name)
    tests = TEST_FAMILIES[test_name]
    groups: dict[tuple[object, ...], list[Mode]] = defaultdict(list)
    for mode in modes:
        groups[echo_key(mode, tests)].append(mode)
    logger.debug("group_by_test exit groups=%d", len(groups))
    return dict(groups)


def find_echo_splits(modes: Iterable[Mode], coarse_test: str, fine_test: str, limit: int = 20) -> list[EchoSplit]:
    """Find pairs equivalent under coarse_test but distinct under fine_test."""
    logger.debug(
        "find_echo_splits entry coarse=%s fine=%s limit=%d",
        coarse_test,
        fine_test,
        limit,
    )
    fine = TEST_FAMILIES[fine_test]
    splits: list[EchoSplit] = []
    for coarse_key, members in group_by_test(modes, coarse_test).items():
        for i, left in enumerate(members):
            for right in members[i + 1 :]:
                left_key = echo_key(left, fine)
                right_key = echo_key(right, fine)
                if left_key == right_key:
                    continue
                splits.append(EchoSplit(left, right, coarse_test, fine_test, coarse_key, left_key, right_key))
                if len(splits) >= limit:
                    logger.debug("find_echo_splits exit limit count=%d", len(splits))
                    return splits
    logger.debug("find_echo_splits exit count=%d", len(splits))
    return splits


def find_stitch_commutators(modes: Iterable[Mode], test_name: str, limit: int = 20) -> list[StitchCommutator]:
    """Find modes a,b where a stitched b differs from b stitched a under test_name."""
    logger.debug("find_stitch_commutators entry test=%s limit=%d", test_name, limit)
    tests = TEST_FAMILIES[test_name]
    items = [mode for mode in modes if mode.length > 0]
    found: list[StitchCommutator] = []
    for left in items:
        for right in items:
            ab = left.stitch(right)
            ba = right.stitch(left)
            if echo_key(ab, tests) == echo_key(ba, tests):
                continue
            found.append(StitchCommutator(left, right, ab, ba, test_name))
            if len(found) >= limit:
                logger.debug("find_stitch_commutators exit limit count=%d", len(found))
                return found
    logger.debug("find_stitch_commutators exit count=%d", len(found))
    return found


def find_weave_incompatibilities(
    modes: Iterable[Mode],
    driver_test: str,
    output_test: str,
    mapping: dict[str, Mode],
    limit: int = 20,
) -> list[WeaveIncompatibility]:
    """Find driver echoes that substitution weave separates at output."""
    logger.debug(
        "find_weave_incompatibilities entry driver_test=%s output_test=%s limit=%d",
        driver_test,
        output_test,
        limit,
    )
    output_tests = TEST_FAMILIES[output_test]
    found: list[WeaveIncompatibility] = []
    usable = [mode for mode in modes if all(tact in mapping for tact in mode.tacts)]
    for _, members in group_by_test(usable, driver_test).items():
        for i, left in enumerate(members):
            for right in members[i + 1 :]:
                left_out = substitute_mode(left, mapping)
                right_out = substitute_mode(right, mapping)
                if echo_key(left_out, output_tests) == echo_key(right_out, output_tests):
                    continue
                found.append(WeaveIncompatibility(left, right, left_out, right_out, driver_test, output_test, mapping))
                if len(found) >= limit:
                    logger.debug("find_weave_incompatibilities exit limit count=%d", len(found))
                    return found
    logger.debug("find_weave_incompatibilities exit count=%d", len(found))
    return found
