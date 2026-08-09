"""Compatibility checks for the finite-builder package migration."""

import importlib
import logging
import pickle
import subprocess
import sys

import src.core.construction.finite_builder.codec as canonical_codec
import src.core.construction.finite_builder.digest as canonical_digest
import src.core.finite_builder_codec as compatibility_codec
import src.core.finite_builder_digest as compatibility_digest

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
_MISSING = object()


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


def test_pickle_triggers_legacy_adapters_from_canonical_only_interpreter():
    """Legacy-qualified pickle globals load adapters on first demand."""
    logger.debug("test_pickle_triggers_legacy_adapters entry")
    script = "\n".join((
        "import importlib, pickle, sys",
        "codec_old = 'src.core.finite_builder_codec'",
        "digest_old = 'src.core.finite_builder_digest'",
        "codec = importlib.import_module(",
        "    'src.core.construction.finite_builder.codec')",
        "digest = importlib.import_module(",
        "    'src.core.construction.finite_builder.digest')",
        "assert codec_old not in sys.modules",
        "assert digest_old not in sys.modules",
        "print('[1/2] pickling legacy-qualified globals')",
        "assert pickle.loads(pickle.dumps(codec._decode_builder)) is codec._decode_builder",
        "assert pickle.loads(pickle.dumps(digest._digest_tokens)) is digest._digest_tokens",
        "print('[2/2] checking adapter-created parent attributes')",
        "import src.core",
        "assert src.core.finite_builder_codec is codec",
        "assert src.core.finite_builder_digest is digest",
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


def test_legacy_monkeypatch_precedes_fresh_canonical_consumer_import(monkeypatch):
    """A legacy seam patch is visible to a newly imported canonical consumer."""
    logger.debug("test_legacy_monkeypatch_before_fresh_consumer entry")
    module_name = "src.core.finite_builder_runtime"
    package = importlib.import_module("src.core")
    original_module = sys.modules.get(module_name, _MISSING)
    original_attribute = getattr(package, "finite_builder_runtime", _MISSING)
    original_decode = canonical_codec._decode_builder

    def intercepted_decode(value):
        logger.debug("intercepted_decode entry")
        result = original_decode(value)
        logger.debug("intercepted_decode exit")
        return result

    with monkeypatch.context() as patch:
        patch.setattr(compatibility_codec, "_decode_builder", intercepted_decode)
        try:
            sys.modules.pop(module_name, None)
            if hasattr(package, "finite_builder_runtime"):
                delattr(package, "finite_builder_runtime")
            fresh = importlib.import_module(module_name)
            assert fresh._decode_builder is intercepted_decode
        finally:
            sys.modules.pop(module_name, None)
            if original_module is not _MISSING:
                sys.modules[module_name] = original_module
            if original_attribute is _MISSING:
                if hasattr(package, "finite_builder_runtime"):
                    delattr(package, "finite_builder_runtime")
            else:
                package.finite_builder_runtime = original_attribute
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
