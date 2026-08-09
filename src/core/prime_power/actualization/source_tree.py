"""Bounded exact-tree comparison for canonical P3-N0 source envelopes."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
import logging

from .common import exact_shape, reject

logger = logging.getLogger(__name__)
MAX_SOURCE_TREE_NODES = 250_000
MAX_SOURCE_TUPLE_ITEMS = 100_000
MAX_SOURCE_TEXT_BYTES = 4 * 1024 * 1024
MAX_SOURCE_INT_BITS = 8192


def _text_equal(actual, expected, label) -> None:
    """Compare exact bounded UTF-8 strings without foreign equality."""
    logger.debug("_text_equal entry label=%s", label)
    if type(actual) is not str:
        reject(f"{label}-exact-text-required")
    try:
        encoded = actual.encode("utf-8")
    except UnicodeError:
        reject(f"{label}-text-encoding-invalid")
    if len(encoded) > MAX_SOURCE_TEXT_BYTES or actual != expected:
        reject(f"{label}-text-drift")
    logger.debug("_text_equal exit label=%s", label)


def validate_exact_source_tree(actual, expected) -> None:
    """Compare every dataclass, tuple, enum, scalar, and digest leaf exactly."""
    logger.debug("validate_exact_source_tree entry")
    stack = [("source", actual, expected)]
    nodes = 0
    while stack:
        label, current, canonical = stack.pop()
        nodes += 1
        if nodes > MAX_SOURCE_TREE_NODES:
            reject("n0-source-tree-node-limit")
        canonical_type = type(canonical)
        if type(current) is not canonical_type:
            reject(f"{label}-exact-type-drift")
        if is_dataclass(canonical) and not isinstance(canonical, type):
            raw = exact_shape(current, canonical_type, label)
            for field in reversed(fields(canonical_type)):
                stack.append((f"{label}-{field.name}", raw[field.name],
                              object.__getattribute__(canonical, field.name)))
        elif canonical_type is tuple:
            if (len(current) != len(canonical)
                    or len(current) > MAX_SOURCE_TUPLE_ITEMS):
                reject(f"{label}-tuple-drift")
            stack.extend((f"{label}-{index}", left, right)
                         for index, (left, right) in reversed(tuple(enumerate(
                             zip(current, canonical, strict=True)))))
        elif isinstance(canonical, Enum):
            if current is not canonical:
                reject(f"{label}-enum-drift")
        elif canonical_type is str:
            _text_equal(current, canonical, label)
        elif canonical_type is int:
            if abs(current).bit_length() > MAX_SOURCE_INT_BITS or current != canonical:
                reject(f"{label}-int-drift")
        elif canonical_type is bool:
            if current is not canonical:
                reject(f"{label}-bool-drift")
        elif canonical is None:
            pass
        elif canonical_type is bytes:
            if len(current) > MAX_SOURCE_TEXT_BYTES or current != canonical:
                reject(f"{label}-bytes-drift")
        else:
            reject(f"{label}-unsupported-source-leaf")
    logger.debug("validate_exact_source_tree exit nodes=%d", nodes)
