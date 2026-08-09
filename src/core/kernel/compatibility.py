"""Schema compatibility checks for Veyra mode operations."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Callable, Iterable

from ..numbers.modes import Mode, TEST_FAMILIES, echo_key

logger = logging.getLogger(__name__)

UnarySchema = Callable[[Mode], Mode]
BinarySchema = Callable[[Mode, Mode], Mode]


@dataclass(frozen=True)
class UnaryCompatibilityFailure:
    """Witness that a unary schema does not respect input/output tests."""

    left: Mode
    right: Mode
    output_left: Mode
    output_right: Mode
    input_test: str
    output_test: str
    schema_name: str


@dataclass(frozen=True)
class BinaryCompatibilityFailure:
    """Witness that a binary schema does not respect declared tests."""

    left_a: Mode
    left_b: Mode
    right_a: Mode
    right_b: Mode
    output_left: Mode
    output_right: Mode
    left_test: str
    right_test: str
    output_test: str
    schema_name: str


def unary_compatibility_failures(
    modes: Iterable[Mode],
    schema: UnarySchema,
    input_test: str,
    output_test: str,
    schema_name: str = "W",
    limit: int = 20,
) -> list[UnaryCompatibilityFailure]:
    """Return finite witnesses where schema fails `(input_test, output_test)`."""
    logger.debug(
        "unary_compatibility_failures entry input=%s output=%s name=%s limit=%d",
        input_test,
        output_test,
        schema_name,
        limit,
    )
    items = list(modes)
    in_tests = TEST_FAMILIES[input_test]
    out_tests = TEST_FAMILIES[output_test]
    failures: list[UnaryCompatibilityFailure] = []
    for i, left in enumerate(items):
        for right in items[i + 1 :]:
            if echo_key(left, in_tests) != echo_key(right, in_tests):
                continue
            left_out = schema(left)
            right_out = schema(right)
            if echo_key(left_out, out_tests) == echo_key(right_out, out_tests):
                continue
            failures.append(
                UnaryCompatibilityFailure(left, right, left_out, right_out, input_test, output_test, schema_name)
            )
            if len(failures) >= limit:
                logger.debug("unary_compatibility_failures exit limit count=%d", len(failures))
                return failures
    logger.debug("unary_compatibility_failures exit count=%d", len(failures))
    return failures


def unary_respects(
    modes: Iterable[Mode],
    schema: UnarySchema,
    input_test: str,
    output_test: str,
    schema_name: str = "W",
) -> bool:
    """Return True iff no finite unary compatibility failure is found."""
    logger.debug("unary_respects entry name=%s input=%s output=%s", schema_name, input_test, output_test)
    result = not unary_compatibility_failures(modes, schema, input_test, output_test, schema_name, limit=1)
    logger.debug("unary_respects exit result=%s", result)
    return result


def binary_compatibility_failures(
    modes: Iterable[Mode],
    schema: BinarySchema,
    left_test: str,
    right_test: str,
    output_test: str,
    schema_name: str = "B",
    limit: int = 20,
) -> list[BinaryCompatibilityFailure]:
    """Return finite witnesses where binary schema fails declared tests."""
    logger.debug(
        "binary_compatibility_failures entry left=%s right=%s output=%s name=%s limit=%d",
        left_test,
        right_test,
        output_test,
        schema_name,
        limit,
    )
    items = list(modes)
    left_tests = TEST_FAMILIES[left_test]
    right_tests = TEST_FAMILIES[right_test]
    out_tests = TEST_FAMILIES[output_test]
    failures: list[BinaryCompatibilityFailure] = []
    for left_a in items:
        for left_b in items:
            if echo_key(left_a, left_tests) != echo_key(left_b, left_tests):
                continue
            for right_a in items:
                for right_b in items:
                    if echo_key(right_a, right_tests) != echo_key(right_b, right_tests):
                        continue
                    out_a = schema(left_a, right_a)
                    out_b = schema(left_b, right_b)
                    if echo_key(out_a, out_tests) == echo_key(out_b, out_tests):
                        continue
                    failures.append(
                        BinaryCompatibilityFailure(
                            left_a,
                            left_b,
                            right_a,
                            right_b,
                            out_a,
                            out_b,
                            left_test,
                            right_test,
                            output_test,
                            schema_name,
                        )
                    )
                    if len(failures) >= limit:
                        logger.debug("binary_compatibility_failures exit limit count=%d", len(failures))
                        return failures
    logger.debug("binary_compatibility_failures exit count=%d", len(failures))
    return failures
