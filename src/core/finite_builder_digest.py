"""Compatibility module alias for the relocated finite-builder digests."""

from __future__ import annotations

from importlib import import_module as _import_module
import sys as _sys

_sys.modules[__name__] = _import_module(
    ".construction.finite_builder.digest", __package__
)
