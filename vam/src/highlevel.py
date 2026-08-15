"""Tiny high-level VAM source seed.

This module is intentionally not a real language.  It accepts two small,
process-first source shapes and lowers them to the existing finite Core source
compiler:

- ``process NAME { echo(EXPR,EXPR) under OBSERVER }``
- ``claim NAME := echo(EXPR,EXPR) under OBSERVER``

Theorem-like cards remain unsupported and produce diagnostics, never claims.
"""
from __future__ import annotations

from dataclasses import dataclass
import logging
import re

from .compiler import CompileResult
from .diagnostics import VamDiagnostic, compile_source_with_diagnostics

logger = logging.getLogger(__name__)

NO_OVERCLAIM = "high-level seed lowering is syntax transport only; it proves no theorem"
_IDENT = r"[A-Za-z_][A-Za-z0-9_-]*"
_PROCESS_RE = re.compile(rf"\A\s*process\s+(?P<name>{_IDENT})\s*\{{(?P<body>.*)\}}\s*\Z", re.DOTALL)
_CLAIM_RE = re.compile(rf"\A\s*claim\s+(?P<name>{_IDENT})\s*:=\s*(?P<body>.*?)\s*\Z", re.DOTALL)
_ECHO_HEAD = "echo("


@dataclass(frozen=True)
class HighLevelDiagnostic:
    """Structured diagnostic for the tiny high-level seed parser."""

    error_class: str
    severity: str
    message: str
    line: int
    column: int
    offset: int
    compile_phase: str
    expected: str | None = None
    found: str | None = None
    suggestion: str | None = None
    no_overclaim_note: str = NO_OVERCLAIM
    core_diagnostic: VamDiagnostic | None = None


@dataclass(frozen=True)
class HighLevelLowering:
    """Successful lowering from tiny high-level syntax to Core source."""

    source_kind: str
    name: str
    core_source: str
    boundary: str = "high-level seed lowering; no theorem acceptance"


@dataclass(frozen=True)
class HighLevelCompileResult:
    """Either a compiled VAM result or one high-level/core diagnostic."""

    lowering: HighLevelLowering | None = None
    compile_result: CompileResult | None = None
    diagnostic: HighLevelDiagnostic | None = None

    @property
    def ok(self) -> bool:
        """True only when high-level source produced VAM IR."""
        return self.compile_result is not None and self.diagnostic is None

    @property
    def core_source(self) -> str | None:
        """Return lowered Core source when available."""
        return self.lowering.core_source if self.lowering is not None else None


def lower_highlevel_source(source: str) -> HighLevelLowering | HighLevelDiagnostic:
    """Lower the tiny high-level seed syntax to one Core ``echo`` expression."""
    logger.debug("lower_highlevel_source entry chars=%d", len(source))
    stripped = source.lstrip()
    offset = len(source) - len(stripped)
    if stripped.startswith(("theorem", "lemma")):
        return _diag(source, offset, "hl.unsupported_theorem", "theorem-like high-level cards are not supported by this seed", "process/claim echo seed", stripped.split(None, 1)[0], "use theorem carriers explicitly; this parser will not infer proof status")

    match = _PROCESS_RE.match(source)
    kind = "process"
    if match is None:
        match = _CLAIM_RE.match(source)
        kind = "claim"
    if match is None:
        return _diag(source, offset, "hl.syntax", "expected a tiny process or claim seed", "process NAME { ... } or claim NAME := ...", stripped[:24] or "<empty>", "write: process demo { echo(nod:a,nod:a) under length }")

    name = match.group("name")
    body = match.group("body").strip()
    lowered = _lower_echo_body(source, body, source.find(body), name, kind)
    if isinstance(lowered, HighLevelDiagnostic):
        return lowered
    logger.debug("lower_highlevel_source exit kind=%s core_chars=%d", kind, len(lowered.core_source))
    return lowered


def compile_highlevel_source(source: str, *, certify: bool = True) -> HighLevelCompileResult:
    """Compile tiny high-level source to VAM IR via the existing Core compiler."""
    logger.debug("compile_highlevel_source entry chars=%d certify=%s", len(source), certify)
    lowering = lower_highlevel_source(source)
    if isinstance(lowering, HighLevelDiagnostic):
        return HighLevelCompileResult(diagnostic=lowering)

    core = compile_source_with_diagnostics(
        lowering.core_source,
        certify=certify,
        claim=f"hl:{lowering.source_kind}:{lowering.name}",
        boundary=lowering.boundary,
    )
    if not core.ok or core.compile_result is None:
        diag = core.diagnostic
        if diag is None:
            logger.error("compile_highlevel_source blocked reason=missing-core-diagnostic")
            result = HighLevelCompileResult(
                lowering=lowering,
                diagnostic=HighLevelDiagnostic(
                    error_class="core.internal.compiler_bug",
                    severity="error",
                    message="internal VAM compiler failure: missing diagnostic",
                    line=1,
                    column=1,
                    offset=0,
                    compile_phase="internal",
                    suggestion="file a compiler bug with the minimized source",
                    core_diagnostic=None,
                ),
            )
            logger.debug("compile_highlevel_source exit diagnostic=core.internal.compiler_bug")
            return result
        logger.debug("compile_highlevel_source exit diagnostic=core.%s", diag.error_class)
        return HighLevelCompileResult(
            lowering=lowering,
            diagnostic=HighLevelDiagnostic(
                error_class=f"core.{diag.error_class}",
                severity=diag.severity,
                message=diag.message,
                line=1,
                column=1,
                offset=0,
                compile_phase=diag.compile_phase,
                expected=diag.expected,
                found=diag.found,
                suggestion=diag.suggestion,
                core_diagnostic=diag,
            ),
        )
    result = HighLevelCompileResult(lowering=lowering, compile_result=core.compile_result)
    logger.debug("compile_highlevel_source exit ok instructions=%d", len(core.compile_result.program))
    return result


def _lower_echo_body(source: str, body: str, offset: int, name: str, kind: str) -> HighLevelLowering | HighLevelDiagnostic:
    logger.debug("lower echo body entry kind=%s chars=%d", kind, len(body))
    if not body.startswith(_ECHO_HEAD):
        return _diag(source, offset, "hl.unsupported_body", "only echo(EXPR,EXPR) under OBSERVER bodies are supported", "echo(EXPR,EXPR) under length", body[:24] or "<empty>", "keep this seed to one echo under one supported observer")
    close = _matching_paren(body, len(_ECHO_HEAD) - 1)
    if close is None:
        return _diag(source, offset + len(body) - 1, "hl.syntax", "missing ')' after echo operands", ")", body[-1:] or "<empty>", "close echo(EXPR,EXPR) before the under clause")
    operands = body[len(_ECHO_HEAD) : close]
    tail = body[close + 1 :].strip()
    if not tail.startswith("under "):
        return _diag(source, offset + close + 1, "hl.syntax", "missing observer clause", "under OBSERVER", tail[:24] or "<empty>", "append: under length")
    parts = _split_top_level_comma(operands)
    if parts is None:
        return _diag(source, offset + len(_ECHO_HEAD), "hl.syntax", "echo seed expects exactly two top-level operands", "LEFT,RIGHT", operands, "use Core expressions without extra top-level commas")
    observer = _observer_atom(tail.removeprefix("under ").strip())
    if observer is None:
        return _diag(source, source.rfind("under") + 6, "hl.syntax", "observer must be a bare name or observer:NAME", "length or observer:length", tail, "supported compiler observers include length, kind, label, trace, boundary")
    core_source = f"echo({parts[0]},{parts[1]},{observer})"
    return HighLevelLowering(kind, name, core_source)


def _matching_paren(text: str, open_index: int) -> int | None:
    depth = 0
    for index in range(open_index, len(text)):
        char = text[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index
    return None


def _split_top_level_comma(text: str) -> tuple[str, str] | None:
    depth = 0
    split_at: int | None = None
    for index, char in enumerate(text):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                return None
        elif char == "," and depth == 0:
            if split_at is not None:
                return None
            split_at = index
    if split_at is None or depth != 0:
        return None
    left, right = text[:split_at].strip(), text[split_at + 1 :].strip()
    return (left, right) if left and right else None


def _observer_atom(text: str) -> str | None:
    if re.fullmatch(_IDENT, text):
        return "observer" if text == "kind" else f"observer:{text.lower()}"
    if re.fullmatch(rf"observer:{_IDENT}", text):
        return text.lower()
    return None


def _diag(source: str, offset: int, error_class: str, message: str, expected: str, found: str, suggestion: str) -> HighLevelDiagnostic:
    line, column = _line_column(source, max(0, offset))
    logger.debug("highlevel diagnostic class=%s line=%d column=%d", error_class, line, column)
    return HighLevelDiagnostic(error_class, "error", message, line, column, max(0, offset), "highlevel-parse", expected, found, suggestion)


def _line_column(source: str, offset: int) -> tuple[int, int]:
    prefix = source[:offset]
    return prefix.count("\n") + 1, len(prefix.rsplit("\n", 1)[-1]) + 1
