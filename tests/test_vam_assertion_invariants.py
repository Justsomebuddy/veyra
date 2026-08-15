"""Optimized-Python-stable invariants for the bounded VAM assertion wave."""

from __future__ import annotations

import ast
from hashlib import sha256
import json
import logging
from pathlib import Path
import subprocess
import sys
from unittest.mock import Mock

import pytest

from src.core.language_span import SpannedParseResult
import vam.intrinsic as intrinsic
import vam.intrinsic.runtime as runtime_module
import vam.src as legacy_vam
import vam.src.diagnostics as diagnostics_module
from vam.src.diagnostics import NO_OVERCLAIM as CORE_NO_OVERCLAIM
from vam.src.diagnostics import VamDiagnosticResult
import vam.src.highlevel as highlevel_module
from vam.src.intrinsic_ir_types import IntrinsicAnchorIR

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    ROOT / "vam/intrinsic/runtime.py",
    ROOT / "vam/src/diagnostics.py",
    ROOT / "vam/src/highlevel.py",
)


def _expect_codec_error(call: object, kind: str, message: str) -> None:
    logger.debug("_expect_codec_error entry kind=%s", kind)
    if not callable(call):
        raise TypeError("expected callable")
    with pytest.raises(intrinsic.IntrinsicCodecError) as caught:
        call()
    assert caught.value.kind == kind
    assert str(caught.value) == message
    logger.debug("_expect_codec_error exit kind=%s", kind)


def test_rendered_exact_dict_gate_precedes_hostile_mapping_callbacks(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger.debug("test rendered exact dict gate entry")

    class HostileDict(dict[str, object]):
        def get(self, *_args: object, **_kwargs: object) -> object:
            raise RuntimeError("private-hostile-get")

        def __getitem__(self, _key: str) -> object:
            raise RuntimeError("private-hostile-item")

    hostile = HostileDict(tag="anchor")
    monkeypatch.setattr(runtime_module, "intrinsic_ir_data", lambda _value: {"value": hostile})
    caplog.set_level(logging.DEBUG, logger=runtime_module.__name__)
    _expect_codec_error(
        lambda: runtime_module.execute_intrinsic_ir(object()),
        "payload",
        "intrinsic runtime value must be exact dict",
    )
    assert "reason=rendered-value-not-exact-dict" in caplog.text
    assert "private-hostile" not in caplog.text
    logger.debug("test rendered exact dict gate exit")


def test_frame_exact_bytes_gate_precedes_decoder(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger.debug("test frame exact bytes gate entry")

    class PrivateDecoderBytes(bytes):
        pass

    decoder = Mock(side_effect=RuntimeError("private-decoder-callback"))
    monkeypatch.setattr(runtime_module, "decode_intrinsic_frame", decoder)
    caplog.set_level(logging.DEBUG, logger=runtime_module.__name__)
    _expect_codec_error(
        lambda: runtime_module.inspect_intrinsic_frame(PrivateDecoderBytes(b"VAMI")),
        "payload",
        "VAMI frame must be exact bytes",
    )
    decoder.assert_not_called()
    assert "reason=frame-not-exact-bytes" in caplog.text
    assert "private-decoder-callback" not in caplog.text
    assert "PrivateDecoderBytes" not in caplog.text
    logger.debug("test frame exact bytes gate exit")


def test_missing_parser_diagnostic_returns_conservative_internal_row(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger.debug("test missing parser diagnostic entry")
    sensitive = "private-parser-source"
    monkeypatch.setattr(
        diagnostics_module,
        "parse_veyra_spanned",
        lambda _source: SpannedParseResult(False, None, None, ()),
    )
    caplog.set_level(logging.DEBUG, logger=diagnostics_module.__name__)
    result = diagnostics_module.compile_source_with_diagnostics(sensitive)
    assert not result.ok
    assert result.compile_result is None
    assert result.diagnostic is not None
    assert result.diagnostic.error_class == "internal.compiler_bug"
    assert result.diagnostic.severity == "error"
    assert result.diagnostic.message == "internal VAM parser failure: missing diagnostic"
    assert result.diagnostic.compile_phase == "internal"
    assert result.diagnostic.source_span is None
    assert result.diagnostic.normalized_text is None
    assert result.diagnostic.expected is None
    assert result.diagnostic.found is None
    assert result.diagnostic.suggestion == "file a compiler bug with the minimized source"
    assert result.diagnostic.no_overclaim_note == CORE_NO_OVERCLAIM
    assert result.diagnostic.excerpt is None
    assert "reason=missing-parser-diagnostic" in caplog.text
    assert sensitive not in caplog.text
    logger.debug("test missing parser diagnostic exit")


def test_missing_core_diagnostic_returns_wrapped_internal_row(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger.debug("test missing core diagnostic entry")
    sensitive_name = "private_name"
    sensitive_atom = "private_atom"
    sensitive = f"claim {sensitive_name} := echo(nod:{sensitive_atom},nod:{sensitive_atom}) under length"
    core = Mock(return_value=VamDiagnosticResult())
    monkeypatch.setattr(highlevel_module, "compile_source_with_diagnostics", core)
    caplog.set_level(logging.DEBUG, logger=highlevel_module.__name__)
    result = highlevel_module.compile_highlevel_source(sensitive)
    assert not result.ok
    assert result.lowering is not None
    assert result.lowering.name == sensitive_name
    assert result.lowering.core_source == (f"echo(nod:{sensitive_atom},nod:{sensitive_atom},observer:length)")
    assert result.compile_result is None
    assert result.diagnostic is not None
    assert result.diagnostic.error_class == "core.internal.compiler_bug"
    assert result.diagnostic.severity == "error"
    assert result.diagnostic.message == "internal VAM compiler failure: missing diagnostic"
    assert (result.diagnostic.line, result.diagnostic.column, result.diagnostic.offset) == (1, 1, 0)
    assert result.diagnostic.compile_phase == "internal"
    assert result.diagnostic.expected is None
    assert result.diagnostic.found is None
    assert result.diagnostic.suggestion == "file a compiler bug with the minimized source"
    assert result.diagnostic.core_diagnostic is None
    assert result.diagnostic.no_overclaim_note == highlevel_module.NO_OVERCLAIM
    assert "reason=missing-core-diagnostic" in caplog.text
    assert sensitive not in caplog.text
    assert sensitive_name not in caplog.text
    assert sensitive_atom not in caplog.text
    logger.debug("test missing core diagnostic exit")


def test_valid_vami_frame_report_exports_and_highlevel_compile_remain_pinned() -> None:
    logger.debug("test valid VAM compatibility pins entry")
    frame = intrinsic.encode_intrinsic_frame(IntrinsicAnchorIR())
    report_json = intrinsic.canonical_intrinsic_report_json(frame).encode()
    report = intrinsic.inspect_intrinsic_frame(frame)
    assert (len(frame), sha256(frame).hexdigest()) == (
        15,
        "ff61ae63916a02f85a7790d981f2bb7ff908fc0da5e9c19756f17d59e765898f",
    )
    assert report["profile"] == "veyra.vami.intrinsic-r12.4.v1"
    assert (len(report_json), sha256(report_json).hexdigest()) == (
        345,
        "f7fecdca3f7be0a51b96cf41a7469326d9b9a4449a671beb3d6335634af50d0b",
    )
    assert intrinsic.__all__ == [
        "INTRINSIC_PROFILE",
        "IntrinsicCodecError",
        "canonical_intrinsic_report_json",
        "decode_intrinsic_frame",
        "encode_intrinsic_frame",
        "execute_intrinsic_ir",
        "inspect_intrinsic_frame",
        "intrinsic_error_data",
    ]
    legacy_exports = json.dumps(legacy_vam.__all__, separators=(",", ":")).encode()
    assert (len(legacy_vam.__all__), sha256(legacy_exports).hexdigest()) == (
        144,
        "ad64fbd89515ffe1e8d49930f09f70d68b35d2a2821b8ee365a5d33dd6e22573",
    )
    compiled = highlevel_module.compile_highlevel_source("claim same := echo(nod:a,nod:a) under observer:length")
    assert compiled.ok and compiled.compile_result is not None
    program = json.dumps(
        [instruction.comparable() for instruction in compiled.compile_result.program],
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    assert (len(program), sha256(program).hexdigest()) == (
        247,
        "f9cbfdcdc9dbde949843de89e7ce5fe7e469ecfe1bd8cbedbed3b7d90a2b18a9",
    )
    logger.debug("test valid VAM compatibility pins exit")


def test_scoped_production_files_have_no_assert_statements() -> None:
    logger.debug("test scoped VAM AST assertion inventory entry")
    rows = []
    for path in TARGETS:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        rows.extend((path, node.lineno) for node in ast.walk(tree) if isinstance(node, ast.Assert))
    assert rows == []
    logger.debug("test scoped VAM AST assertion inventory exit files=%d", len(TARGETS))


def test_all_four_guards_remain_active_under_optimized_python() -> None:
    logger.debug("test optimized VAM invariant probe entry")
    script = r"""
import vam.intrinsic.runtime as runtime
import vam.src.diagnostics as diagnostics
import vam.src.highlevel as highlevel
from src.core.language_span import SpannedParseResult
from vam.intrinsic import IntrinsicCodecError
from vam.src.diagnostics import VamDiagnosticResult
from vam.src.highlevel import HighLevelLowering

def fail(code):
    raise SystemExit(code)

class HostileDict(dict):
    def get(self, *args, **kwargs):
        fail(11)
    def __getitem__(self, key):
        fail(12)

runtime.intrinsic_ir_data = lambda value: {"value": HostileDict(tag="anchor")}
try:
    runtime.execute_intrinsic_ir(object())
except IntrinsicCodecError as error:
    if error.kind != "payload" or str(error) != "intrinsic runtime value must be exact dict":
        fail(13)
else:
    fail(14)

class BytesSubclass(bytes):
    pass
runtime.decode_intrinsic_frame = lambda blob: fail(21)
try:
    runtime.inspect_intrinsic_frame(BytesSubclass(b"VAMI"))
except IntrinsicCodecError as error:
    if error.kind != "payload" or str(error) != "VAMI frame must be exact bytes":
        fail(22)
else:
    fail(23)

diagnostics.parse_veyra_spanned = lambda source: SpannedParseResult(False, None, None, ())
parsed = diagnostics.compile_source_with_diagnostics("private-optimized-parser-source")
if parsed.diagnostic is None or parsed.diagnostic.error_class != "internal.compiler_bug":
    fail(31)

lowering = HighLevelLowering("claim", "same", "echo(nod:a,nod:a,observer:length)")
highlevel.lower_highlevel_source = lambda source: lowering
highlevel.compile_source_with_diagnostics = lambda *args, **kwargs: VamDiagnosticResult()
compiled = highlevel.compile_highlevel_source("private-optimized-highlevel-source")
if compiled.diagnostic is None or compiled.diagnostic.error_class != "core.internal.compiler_bug":
    fail(41)
if compiled.lowering != lowering or compiled.diagnostic.core_diagnostic is not None:
    fail(42)
"""
    completed = subprocess.run(
        (sys.executable, "-O", "-c", script),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, (completed.stdout, completed.stderr)
    assert "private-optimized" not in completed.stdout + completed.stderr
    logger.debug("test optimized VAM invariant probe exit rc=%d", completed.returncode)
