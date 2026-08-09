"""Alias resolution for relocated ``src.core`` modules.

A module that moves keeps its former import path working: the alias resolves to
the module object at the canonical location, so imports, ``unittest.mock.patch``
targets, and subprocess snippets all continue to address the same object.

``legacy_modules.json`` holds the mapping. New code imports the canonical path;
this layer exists so consumers migrate one cluster at a time, as
``docs/concepts/package_boundary.md`` requires.
"""
from __future__ import annotations

import importlib
import json
import logging
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import MappingProxyType, ModuleType
from typing import Sequence

logger = logging.getLogger(__name__)

TABLE_PATH = Path(__file__).with_name("legacy_modules.json")
LEGACY_MODULES = MappingProxyType(json.loads(TABLE_PATH.read_text(encoding="utf-8")))


class LegacyModuleFinder(MetaPathFinder, Loader):
    """Resolve ``src.core.<flat_name>`` to its relocated canonical module."""

    def __init__(self, package: str, table: MappingProxyType) -> None:
        self._package = package
        self._prefix = f"{package}."
        self._table = table
        self._canonical_metadata: dict[str, tuple[object, object, object]] = {}

    def _legacy_name(self, fullname: str) -> str | None:
        if not fullname.startswith(self._prefix):
            return None
        legacy = fullname[len(self._prefix):]
        return legacy if legacy in self._table else None

    def find_spec(
        self, fullname: str, path: Sequence[str] | None = None, target: ModuleType | None = None,
    ) -> ModuleSpec | None:
        if self._legacy_name(fullname) is None:
            return None
        logger.debug("LegacyModuleFinder.find_spec alias=%s", fullname)
        return ModuleSpec(fullname, self)

    def create_module(self, spec: ModuleSpec) -> ModuleType:
        legacy = self._legacy_name(spec.name)
        if legacy is None:
            raise ImportError(f"not a legacy core module: {spec.name}")
        canonical = f"{self._package}.{self._table[legacy]}"
        logger.debug("LegacyModuleFinder alias=%s canonical=%s", spec.name, canonical)
        module = importlib.import_module(canonical)
        self._canonical_metadata[spec.name] = (
            module.__spec__, module.__loader__, module.__package__,
        )
        return module

    def exec_module(self, module: ModuleType) -> None:
        """Restore metadata overwritten while binding the legacy alias."""
        alias = module.__spec__.name if module.__spec__ is not None else ""
        metadata = self._canonical_metadata.pop(alias, None)
        if metadata is None:
            raise ImportError(f"missing canonical metadata for legacy module: {alias}")
        module.__spec__, module.__loader__, module.__package__ = metadata


def install(package: str) -> None:
    """Register the alias finder once for ``package``."""
    import sys

    for finder in sys.meta_path:
        if isinstance(finder, LegacyModuleFinder) and finder._package == package:
            return
    sys.meta_path.append(LegacyModuleFinder(package, LEGACY_MODULES))
    logger.debug("legacy alias finder installed package=%s rows=%d", package, len(LEGACY_MODULES))
