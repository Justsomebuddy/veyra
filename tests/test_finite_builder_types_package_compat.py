"""Compatibility checks for the relocated finite-builder type definitions."""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
import pickle
import subprocess
import sys

import src.core as core
import src.core.construction.finite_builder.types as canonical_types
import src.core.finite_builder_types as compatibility_types

logger = logging.getLogger(__name__)

LEGACY_MODULE = "src.core.finite_builder_types"
CANONICAL_MODULE = "src.core.construction.finite_builder.types"
DEFINED_TYPES = (
    "SeedRef",
    "PulseStep",
    "ReplayStatus",
    "FormalGenerability",
    "OnticGenesis",
    "TargetIndependence",
    "ScopedObjectFormation",
    "FiniteRecurrenceSeed",
    "FiniteBuilderProgram",
    "ConstructionSourceBinding",
    "ReplayArtifact",
    "FiniteConstructionJudgment",
)
ROOT_EXPORTS = (
    "SeedRef",
    "PulseStep",
    "ReplayStatus",
    "FormalGenerability",
    "OnticGenesis",
    "TargetIndependence",
    "ScopedObjectFormation",
    "FiniteRecurrenceSeed",
    "FiniteBuilderProgram",
    "ConstructionSourceBinding",
    "ReplayArtifact",
    "FiniteConstructionJudgment",
)
CANONICAL_CONSUMERS = (
    "src/core/__init__.py",
    "src/core/certify_finite_construction.py",
    "src/core/certify_productivity.py",
    "src/core/certify_scoped_formation.py",
    "src/core/finite_builder_runtime.py",
    "src/core/finite_builder_validation.py",
    "src/core/finite_construction.py",
    "src/core/observer_actualization.py",
    "src/core/observer_actualization_certificate_fixture.py",
    "src/core/observer_actualization_runtime.py",
    "src/core/observer_actualization_types.py",
    "src/core/observer_actualization_validation.py",
    "src/core/productivity_result_validation.py",
    "src/core/productivity_types.py",
    "src/core/scoped_formation_components.py",
    "src/core/scoped_formation_types.py",
    "src/core/status_promotion_schema_audit.py",
)


def test_flat_and_canonical_types_are_true_module_aliases():
    """The compatibility path resolves to the canonical module object."""
    logger.debug("test_flat_and_canonical_types_are_true_module_aliases entry")
    assert compatibility_types is canonical_types
    assert sys.modules[LEGACY_MODULE] is canonical_types
    assert core.finite_builder_types is canonical_types
    for name in DEFINED_TYPES:
        value = getattr(canonical_types, name)
        assert getattr(compatibility_types, name) is value
        assert value.__module__ == LEGACY_MODULE
    logger.debug("test_flat_and_canonical_types_are_true_module_aliases exit")


def test_root_exports_and_pickle_provenance_remain_compatible():
    """Root exports and representative serialized values retain old identity."""
    logger.debug("test_root_exports_and_pickle_provenance entry")
    for name in ROOT_EXPORTS:
        assert getattr(core, name) is getattr(canonical_types, name)

    seed = canonical_types.SeedRef("pickle-seed")
    expression = canonical_types.PulseStep(seed)
    values = (
        canonical_types.SeedRef,
        canonical_types.ReplayStatus,
        seed,
        expression,
        canonical_types.ReplayStatus.REPLAYED,
        canonical_types.FormalGenerability.TARGET_MISMATCH,
        canonical_types.OnticGenesis.NOT_ESTABLISHED,
        canonical_types.TargetIndependence.NOT_ESTABLISHED,
        canonical_types.ScopedObjectFormation.OPEN,
    )
    for value in values:
        restored = pickle.loads(pickle.dumps(value))
        if isinstance(value, type) or isinstance(value, canonical_types.Enum):
            assert restored is value
        else:
            assert type(restored) is type(value)
            assert restored == value
    logger.debug("test_root_exports_and_pickle_provenance exit")


def test_types_import_orders_and_module_alias_survive_reload():
    """Both import orders preserve the module alias across canonical reload."""
    logger.debug("test_types_import_orders_and_reload entry")
    prelude = "\n".join(
        (
            "import importlib, pickle, sys",
            f"old = {LEGACY_MODULE!r}",
            f"new = {CANONICAL_MODULE!r}",
            "import src.core",
        )
    )
    assertions = "\n".join(
        (
            "old_module = importlib.import_module(old)",
            "new_module = importlib.import_module(new)",
            "assert old_module is new_module",
            "assert src.core.finite_builder_types is new_module",
            "assert new_module.SeedRef.__module__ == old",
            "value = new_module.PulseStep(new_module.SeedRef('fresh'))",
            "assert pickle.loads(pickle.dumps(value)) == value",
            "assert importlib.reload(old_module) is new_module",
            "assert importlib.import_module(old) is new_module",
            "assert new_module.SeedRef.__module__ == old",
        )
    )
    scenarios = (
        prelude + "\nimportlib.import_module(new)\nassert old not in sys.modules\n" + assertions,
        prelude + "\nimportlib.import_module(old)\n" + assertions,
    )
    for scenario in scenarios:
        result = subprocess.run(
            [sys.executable, "-c", scenario],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        assert result.returncode == 0, result.stderr
    logger.debug("test_types_import_orders_and_reload exit")


def test_known_core_consumers_use_the_canonical_types_path():
    """The bounded migration updates every reviewed stable Core consumer."""
    logger.debug("test_known_core_consumers_use_canonical_path entry")
    root = Path(__file__).resolve().parents[1]
    for relative_path in CANONICAL_CONSUMERS:
        source = (root / relative_path).read_text(encoding="utf-8")
        assert "finite_builder_types" not in source, relative_path
        assert "construction.finite_builder.types" in source, relative_path
    codec_source = (root / "src/core/construction/finite_builder/codec.py").read_text(encoding="utf-8")
    assert "from .types import" in codec_source
    logger.debug("test_known_core_consumers_use_canonical_path exit")
