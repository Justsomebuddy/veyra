"""Compatibility checks for the finite-builder package migration."""

import importlib
import logging
from pathlib import Path
import pickle
import subprocess
import sys

import src.core.construction.finite_builder.codec as canonical_codec
import src.core.construction.finite_builder.digest as canonical_digest
import src.core.construction.finite_builder.runtime as canonical_runtime
import src.core.construction.finite_builder.validation as canonical_validation
import src.core.finite_builder_codec as compatibility_codec
import src.core.finite_builder_digest as compatibility_digest
import src.core.finite_builder_runtime as compatibility_runtime
import src.core.finite_builder_validation as compatibility_validation

logger = logging.getLogger(__name__)

CODEC_SYMBOLS = (
    "annotations",
    "logging",
    "FiniteBuilderExpr",
    "PulseStep",
    "SeedRef",
    "PositiveOntologyValidationError",
    "snapshot_recurrence",
    "CoreTerm",
    "Pulse",
    "Silence",
    "logger",
    "BUILDER_MAGIC",
    "RECURRENCE_MAGIC",
    "MAX_FINITE_BUILDER_NODES",
    "FiniteBuilderCodecError",
    "_canonical_builder_bytes",
    "_decode_builder",
    "_canonical_recurrence_bytes",
    "_decode_recurrence",
)
DIGEST_SYMBOLS = (
    "annotations",
    "sha256",
    "logging",
    "logger",
    "_digest_tokens",
    "_seed_digest",
    "_program_digest",
    "_source_digest",
    "_trace_digest",
)
CODEC_DEFINED_SYMBOLS = (
    "FiniteBuilderCodecError",
    "_canonical_builder_bytes",
    "_decode_builder",
    "_canonical_recurrence_bytes",
    "_decode_recurrence",
)
DIGEST_DEFINED_SYMBOLS = (
    "_digest_tokens",
    "_seed_digest",
    "_program_digest",
    "_source_digest",
    "_trace_digest",
)
RUNTIME_DEFINED_SYMBOLS = (
    "FiniteBuilderReplayError",
    "_recurrence_depth",
    "_output_recurrence_commitment",
    "replay_finite_builder",
    "snapshot_replay_artifact",
)
VALIDATION_DEFINED_SYMBOLS = (
    "FiniteBuilderValidationError",
    "_reject",
    "_identifier",
    "_hex_digest",
    "_snapshot_doctrine",
    "_snapshot_builder_expr",
    "_builder_shape",
    "_snapshot_seed",
    "_snapshot_program",
    "_snapshot_source",
    "_snapshot_target_stage",
)
RUNTIME_CONSUMERS = (
    "src/core/__init__.py",
    "src/core/certify_finite_construction.py",
    "src/core/finite_construction.py",
)
VALIDATION_CONSUMERS = (
    "src/core/__init__.py",
    "src/core/finite_construction.py",
    "src/core/scoped_formation_preflight.py",
    "src/core/scoped_formation_result_validation.py",
    "src/core/scoped_formation_scope.py",
)


def test_flat_compatibility_modules_reexport_identical_symbols():
    """Every name formerly bound by the flat modules aliases its new binding."""
    logger.debug("test_flat_compatibility_modules_reexport_identical_symbols entry")
    assert {
        name for name in vars(canonical_codec) if not name.startswith("__")
    } == set(CODEC_SYMBOLS)
    assert {
        name for name in vars(canonical_digest) if not name.startswith("__")
    } == set(DIGEST_SYMBOLS)
    for name in CODEC_SYMBOLS:
        assert getattr(compatibility_codec, name) is getattr(canonical_codec, name)
    for name in DIGEST_SYMBOLS:
        assert getattr(compatibility_digest, name) is getattr(canonical_digest, name)
    logger.debug("test_flat_compatibility_modules_reexport_identical_symbols exit")


def test_flat_and_canonical_imports_are_true_module_aliases_with_legacy_provenance():
    """The canonical layout must not change module, pickle, or logger identity."""
    logger.debug("test_true_module_aliases_with_legacy_provenance entry")
    assert compatibility_codec is canonical_codec
    assert compatibility_digest is canonical_digest
    assert sys.modules["src.core.finite_builder_codec"] is canonical_codec
    assert sys.modules["src.core.finite_builder_digest"] is canonical_digest
    for name in CODEC_DEFINED_SYMBOLS:
        assert getattr(canonical_codec, name).__module__ == (
            "src.core.finite_builder_codec"
        )
    for name in DIGEST_DEFINED_SYMBOLS:
        assert getattr(canonical_digest, name).__module__ == (
            "src.core.finite_builder_digest"
        )
    assert canonical_codec.logger.name == "src.core.finite_builder_codec"
    assert canonical_digest.logger.name == "src.core.finite_builder_digest"
    logger.debug("test_true_module_aliases_with_legacy_provenance exit")


def test_runtime_and_validation_are_true_aliases_with_legacy_provenance():
    """Relocated execution modules retain module, symbol, and logger identity."""
    logger.debug("test_runtime_validation_true_aliases entry")
    assert compatibility_runtime is canonical_runtime
    assert compatibility_validation is canonical_validation
    assert sys.modules["src.core.finite_builder_runtime"] is canonical_runtime
    assert sys.modules["src.core.finite_builder_validation"] is canonical_validation
    for name in RUNTIME_DEFINED_SYMBOLS:
        assert getattr(compatibility_runtime, name) is getattr(canonical_runtime, name)
        assert getattr(canonical_runtime, name).__module__ == (
            "src.core.finite_builder_runtime"
        )
    for name in VALIDATION_DEFINED_SYMBOLS:
        assert getattr(compatibility_validation, name) is getattr(
            canonical_validation, name
        )
        assert getattr(canonical_validation, name).__module__ == (
            "src.core.finite_builder_validation"
        )
    assert canonical_runtime.logger.name == "src.core.finite_builder_runtime"
    assert canonical_validation.logger.name == "src.core.finite_builder_validation"
    logger.debug("test_runtime_validation_true_aliases exit")


def test_runtime_validation_root_exports_remain_compatible():
    """Stable root API bindings point at the canonical execution modules."""
    logger.debug("test_runtime_validation_root_exports entry")
    core = importlib.import_module("src.core")
    for name in (
        "FiniteBuilderReplayError",
        "replay_finite_builder",
        "snapshot_replay_artifact",
    ):
        assert getattr(core, name) is getattr(canonical_runtime, name)
    assert core.FiniteBuilderValidationError is (
        canonical_validation.FiniteBuilderValidationError
    )
    logger.debug("test_runtime_validation_root_exports exit")


def test_known_production_consumers_use_canonical_execution_paths():
    """The reviewed production ledger no longer depends on flat adapters."""
    logger.debug("test_canonical_execution_consumer_ledger entry")
    root = Path(__file__).resolve().parents[1]
    for relative_path in RUNTIME_CONSUMERS:
        source = (root / relative_path).read_text(encoding="utf-8")
        assert "from .finite_builder_runtime import" not in source, relative_path
        assert "construction.finite_builder.runtime import" in source, relative_path
    for relative_path in VALIDATION_CONSUMERS:
        source = (root / relative_path).read_text(encoding="utf-8")
        assert "from .finite_builder_validation import" not in source, relative_path
        assert "construction.finite_builder.validation import" in source, relative_path
    runtime_source = (
        root / "src/core/construction/finite_builder/runtime.py"
    ).read_text(encoding="utf-8")
    assert "from .validation import" in runtime_source
    logger.debug("test_canonical_execution_consumer_ledger exit")


def test_legacy_provenance_remains_pickle_resolvable():
    """Legacy-qualified functions and exceptions survive pickle resolution."""
    logger.debug("test_legacy_provenance_remains_pickle_resolvable entry")
    for name in CODEC_DEFINED_SYMBOLS[1:]:
        value = getattr(canonical_codec, name)
        assert pickle.loads(pickle.dumps(value)) is value
    for name in DIGEST_DEFINED_SYMBOLS:
        value = getattr(canonical_digest, name)
        assert pickle.loads(pickle.dumps(value)) is value
    error = canonical_codec.FiniteBuilderCodecError("pickle-boundary")
    restored = pickle.loads(pickle.dumps(error))
    assert type(restored) is canonical_codec.FiniteBuilderCodecError
    assert restored.args == ("pickle-boundary",)
    for module, names in (
        (canonical_runtime, RUNTIME_DEFINED_SYMBOLS[1:]),
        (canonical_validation, VALIDATION_DEFINED_SYMBOLS[1:]),
    ):
        for name in names:
            value = getattr(module, name)
            assert pickle.loads(pickle.dumps(value)) is value
    for error_type in (
        canonical_runtime.FiniteBuilderReplayError,
        canonical_validation.FiniteBuilderValidationError,
    ):
        restored = pickle.loads(pickle.dumps(error_type("pickle-boundary")))
        assert type(restored) is error_type
        assert restored.args == ("pickle-boundary",)
    logger.debug("test_legacy_provenance_remains_pickle_resolvable exit")


def test_standard_legacy_imports_set_parent_attributes_in_fresh_interpreters():
    """Standard and from-parent imports work in both clean import orders."""
    logger.debug("test_standard_legacy_imports_set_parent_attributes entry")
    shared = (
        "import src.core\n"
        "codec = importlib.import_module(codec_new)\n"
        "digest = importlib.import_module(digest_new)\n"
        "assert src.core.finite_builder_codec is codec\n"
        "assert src.core.finite_builder_digest is digest\n"
        "from src.core import finite_builder_codec, finite_builder_digest\n"
        "assert finite_builder_codec is codec\n"
        "assert finite_builder_digest is digest\n"
    )
    prelude = (
        "import importlib, sys\n"
        "codec_old = 'src.core.finite_builder_codec'\n"
        "codec_new = 'src.core.construction.finite_builder.codec'\n"
        "digest_old = 'src.core.finite_builder_digest'\n"
        "digest_new = 'src.core.construction.finite_builder.digest'\n"
    )
    canonical_first = prelude + (
        "print('[1/2] importing canonical modules first')\n"
        "importlib.import_module(codec_new)\n"
        "importlib.import_module(digest_new)\n"
        "assert codec_old not in sys.modules\n"
        "assert digest_old not in sys.modules\n"
        "print('[2/2] running standard legacy imports')\n"
        "import src.core.finite_builder_codec\n"
        "import src.core.finite_builder_digest\n"
    ) + shared
    legacy_first = prelude + (
        "print('[1/1] running pristine standard legacy imports')\n"
        "import src.core.finite_builder_codec\n"
        "import src.core.finite_builder_digest\n"
    ) + shared
    for scenario in (canonical_first, legacy_first):
        result = subprocess.run(
            [sys.executable, "-c", scenario],
            capture_output=True, text=True, check=False,
        )
        assert result.returncode == 0, result.stderr
    logger.debug("test_standard_legacy_imports_set_parent_attributes exit")


def test_runtime_validation_import_orders_and_reload_keep_true_aliases():
    """Both execution-module import orders preserve compatibility identity."""
    logger.debug("test_runtime_validation_import_orders entry")
    prelude = "\n".join((
        "import importlib, sys",
        "runtime_old = 'src.core.finite_builder_runtime'",
        "runtime_new = 'src.core.construction.finite_builder.runtime'",
        "validation_old = 'src.core.finite_builder_validation'",
        "validation_new = 'src.core.construction.finite_builder.validation'",
    )) + "\n"
    assertions = "\n".join((
        "old_runtime = importlib.import_module(runtime_old)",
        "new_runtime = importlib.import_module(runtime_new)",
        "old_validation = importlib.import_module(validation_old)",
        "new_validation = importlib.import_module(validation_new)",
        "assert old_runtime is new_runtime",
        "assert old_validation is new_validation",
        "import src.core",
        "assert src.core.finite_builder_runtime is new_runtime",
        "assert src.core.finite_builder_validation is new_validation",
        "assert importlib.reload(old_runtime) is new_runtime",
        "assert importlib.reload(old_validation) is new_validation",
        "assert importlib.import_module(runtime_old) is new_runtime",
        "assert importlib.import_module(validation_old) is new_validation",
        "assert new_runtime.replay_finite_builder.__module__ == runtime_old",
        "assert new_validation._snapshot_source.__module__ == validation_old",
        "assert new_runtime.logger.name == runtime_old",
        "assert new_validation.logger.name == validation_old",
    ))
    scenarios = (
        prelude + (
            "print('[1/2] canonical-first execution modules')\n"
            "importlib.import_module(runtime_new)\n"
            "importlib.import_module(validation_new)\n"
            "assert runtime_old not in sys.modules\n"
            "assert validation_old not in sys.modules\n"
            "print('[2/2] loading legacy adapters')\n"
        ) + assertions,
        prelude + (
            "print('[1/1] legacy-first execution modules')\n"
            "importlib.import_module(runtime_old)\n"
            "importlib.import_module(validation_old)\n"
        ) + assertions,
    )
    for scenario in scenarios:
        result = subprocess.run(
            [sys.executable, "-c", scenario],
            capture_output=True, text=True, check=False, timeout=60,
        )
        assert result.returncode == 0, result.stderr
    logger.debug("test_runtime_validation_import_orders exit")


def test_pickle_triggers_legacy_adapters_from_canonical_only_interpreter():
    """Legacy-qualified pickle globals load adapters on first demand."""
    logger.debug("test_pickle_triggers_legacy_adapters entry")
    script = "\n".join((
        "import importlib, pickle, sys",
        "codec_old = 'src.core.finite_builder_codec'",
        "digest_old = 'src.core.finite_builder_digest'",
        "runtime_old = 'src.core.finite_builder_runtime'",
        "validation_old = 'src.core.finite_builder_validation'",
        "codec = importlib.import_module(",
        "    'src.core.construction.finite_builder.codec')",
        "digest = importlib.import_module(",
        "    'src.core.construction.finite_builder.digest')",
        "runtime = importlib.import_module(",
        "    'src.core.construction.finite_builder.runtime')",
        "validation = importlib.import_module(",
        "    'src.core.construction.finite_builder.validation')",
        "assert codec_old not in sys.modules",
        "assert digest_old not in sys.modules",
        "assert runtime_old not in sys.modules",
        "assert validation_old not in sys.modules",
        "print('[1/2] pickling legacy-qualified globals')",
        "assert pickle.loads(pickle.dumps(codec._decode_builder)) is codec._decode_builder",
        "assert pickle.loads(pickle.dumps(digest._digest_tokens)) is digest._digest_tokens",
        "assert pickle.loads(pickle.dumps(runtime.replay_finite_builder)) is runtime.replay_finite_builder",
        "assert pickle.loads(pickle.dumps(validation._snapshot_source)) is validation._snapshot_source",
        "print('[2/2] checking adapter-created parent attributes')",
        "import src.core",
        "assert src.core.finite_builder_codec is codec",
        "assert src.core.finite_builder_digest is digest",
        "assert src.core.finite_builder_runtime is runtime",
        "assert src.core.finite_builder_validation is validation",
    ))
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert "[2/2] checking adapter-created parent attributes" in result.stdout
    logger.debug("test_pickle_triggers_legacy_adapters exit")


def test_legacy_first_import_and_reload_keep_true_aliases_in_fresh_interpreter():
    """Legacy-first loading and reload preserve alias identity in isolation."""
    logger.debug("test_legacy_first_import_and_reload entry")
    script = "\n".join((
        "import importlib, sys",
        "codec_old = 'src.core.finite_builder_codec'",
        "codec_new = 'src.core.construction.finite_builder.codec'",
        "digest_old = 'src.core.finite_builder_digest'",
        "digest_new = 'src.core.construction.finite_builder.digest'",
        "import src.core",
        "sys.modules.pop(codec_old, None)",
        "sys.modules.pop(digest_old, None)",
        "print('[1/3] executing legacy adapter paths')",
        "old_codec = importlib.import_module(codec_old)",
        "old_digest = importlib.import_module(digest_old)",
        "new_codec = importlib.import_module(codec_new)",
        "new_digest = importlib.import_module(digest_new)",
        "assert old_codec is new_codec",
        "assert old_digest is new_digest",
        "assert src.core.finite_builder_codec is new_codec",
        "assert src.core.finite_builder_digest is new_digest",
        "print('[2/3] reloading both shared modules')",
        "assert importlib.reload(old_codec) is new_codec",
        "assert importlib.reload(old_digest) is new_digest",
        "print('[3/3] checking aliases and provenance')",
        "assert importlib.import_module(codec_old) is new_codec",
        "assert importlib.import_module(digest_old) is new_digest",
        "assert new_codec._decode_builder.__module__ == codec_old",
        "assert new_digest._digest_tokens.__module__ == digest_old",
        "assert new_codec.logger.name == codec_old",
        "assert new_digest.logger.name == digest_old",
    ))
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert "[3/3] checking aliases and provenance" in result.stdout
    logger.debug("test_legacy_first_import_and_reload exit")


def test_legacy_monkeypatch_precedes_fresh_canonical_consumer_import():
    """Legacy codec and validation seams reach a fresh canonical runtime."""
    logger.debug("test_legacy_monkeypatch_before_fresh_consumer entry")
    script = "\n".join((
        "import importlib, sys",
        "import src.core",
        "codec = importlib.import_module('src.core.finite_builder_codec')",
        "validation = importlib.import_module('src.core.finite_builder_validation')",
        "runtime = importlib.import_module('src.core.finite_builder_runtime')",
        "original_decode = codec._decode_builder",
        "original_snapshot = validation._snapshot_doctrine",
        "def intercepted_decode(value):",
        "    return original_decode(value)",
        "def intercepted_snapshot(value):",
        "    return original_snapshot(value)",
        "codec._decode_builder = intercepted_decode",
        "validation._snapshot_doctrine = intercepted_snapshot",
        "runtime_old = 'src.core.finite_builder_runtime'",
        "runtime_new = 'src.core.construction.finite_builder.runtime'",
        "sys.modules.pop(runtime_old, None)",
        "sys.modules.pop(runtime_new, None)",
        "for package_name, attribute in ((",
        "    'src.core', 'finite_builder_runtime'), (",
        "    'src.core.construction.finite_builder', 'runtime')):",
        "    package = importlib.import_module(package_name)",
        "    if hasattr(package, attribute):",
        "        delattr(package, attribute)",
        "print('[1/2] importing fresh canonical runtime')",
        "fresh = importlib.import_module(runtime_new)",
        "assert fresh._decode_builder is intercepted_decode",
        "assert fresh._snapshot_doctrine is intercepted_snapshot",
        "print('[2/2] loading legacy runtime alias')",
        "assert importlib.import_module(runtime_old) is fresh",
        "assert src.core.finite_builder_runtime is fresh",
    ))
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, check=False, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "[2/2] loading legacy runtime alias" in result.stdout
    logger.debug("test_legacy_monkeypatch_before_fresh_consumer exit")


def test_flat_and_canonical_paths_share_codec_and_digest_behavior():
    """Both import paths execute the same bounded codec and digest objects."""
    logger.debug("test_flat_and_canonical_paths_share_codec_and_digest_behavior entry")
    expression = compatibility_codec.PulseStep(
        compatibility_codec.SeedRef("compatibility-seed")
    )
    encoded = compatibility_codec._canonical_builder_bytes(expression)
    assert encoded == canonical_codec._canonical_builder_bytes(expression)
    assert compatibility_codec._decode_builder(encoded) == expression
    assert canonical_codec._decode_builder(encoded) == expression

    recurrence = compatibility_codec.Pulse(compatibility_codec.Silence())
    recurrence_bytes = compatibility_codec._canonical_recurrence_bytes(recurrence)
    assert recurrence_bytes == canonical_codec._canonical_recurrence_bytes(recurrence)
    assert compatibility_codec._decode_recurrence(recurrence_bytes) == recurrence
    assert canonical_codec._decode_recurrence(recurrence_bytes) == recurrence

    tokens = (b"finite-builder", encoded, recurrence_bytes)
    assert compatibility_digest._digest_tokens(tokens) == (
        canonical_digest._digest_tokens(tokens)
    )
    logger.debug("test_flat_and_canonical_paths_share_codec_and_digest_behavior exit")
