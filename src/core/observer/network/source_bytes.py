"""Cycle-safe canonical-byte charging for the closed P3-T source grammar."""

from __future__ import annotations

from dataclasses import fields
from enum import Enum
import logging

from ..morphism import ProjectionStep
from .common import exact_shape, reject
from .types import (
    GrammarDescriptor,
    InputSnapshot,
    ObservationRow,
    ObserverSource,
    RawObserverPairSource,
    Response,
    ResponseStatus,
    TranslationRow,
    TranslationSource,
    TriangleDemand,
    TypedValue,
)

logger = logging.getLogger(__name__)

_SOURCE_DTOS = {
    InputSnapshot,
    GrammarDescriptor,
    ObservationRow,
    ObserverSource,
    TranslationRow,
    TranslationSource,
    TriangleDemand,
    RawObserverPairSource,
    Response,
    TypedValue,
}
_SOURCE_ENUMS = {ProjectionStep, ResponseStatus}


def charge_source_bytes(value: object, remaining: int) -> int:
    """Charge one exact source value without recursion or unbounded encoding."""
    logger.debug("charge_source_bytes entry remaining=%d", remaining)
    if type(remaining) is not int or remaining < 0:
        reject("canonical-byte-hard-limit")
    stack: list[tuple[bool, object, str]] = [(False, value, "root")]
    active_paths: dict[int, str] = {}
    charged = 0
    while stack:
        leaving, current, path = stack.pop()
        current_type = type(current)
        if leaving:
            active_paths.pop(id(current), None)
            continue
        if current_type is str:
            available = remaining - charged
            if len(current) > available:
                reject("canonical-byte-hard-limit")
            try:
                encoded = current.encode("utf-8")
            except UnicodeError:
                reject("canonical-string-encoding-invalid")
            charged += len(encoded)
        elif current_type is bytes:
            charged += len(current)
        elif current_type is bool:
            charged += 8
        elif current_type is int:
            charged += 8
        elif current is None:
            charged += 8
        elif current_type in _SOURCE_ENUMS:
            stack.append((False, object.__getattribute__(current, "_value_"), f"{path}.value"))
        elif current_type is tuple or current_type in _SOURCE_DTOS:
            identity = id(current)
            if identity in active_paths:
                reject("source-byte-cycle")
            active_paths[identity] = path
            stack.append((True, current, path))
            if current_type is tuple:
                charged += 4
                stack.extend(
                    (False, item, f"{path}[{index}]")
                    for index, item in reversed(tuple(enumerate(current)))
                )
            else:
                exact_shape(current, current_type, "source-byte-dto")
                instance_dict = object.__getattribute__(current, "__dict__")
                names = tuple(item.name for item in fields(current_type))
                stack.extend(
                    (False, dict.__getitem__(instance_dict, name), f"{path}.{name}")
                    for name in reversed(names)
                )
        elif isinstance(current, Enum):
            reject("canonical-byte-value-invalid")
        else:
            reject("canonical-byte-value-invalid")
        if charged > remaining:
            reject("canonical-byte-hard-limit")
    logger.debug("charge_source_bytes exit charged=%d", charged)
    return charged
