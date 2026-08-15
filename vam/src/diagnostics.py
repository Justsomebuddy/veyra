"""Conservative diagnostics front door for VAM Core lowering."""
from __future__ import annotations

from dataclasses import dataclass
import logging

from src.core.language import normal_text
from src.core.language_span import (
    SourceSpan,
    SpannedExpr,
    parse_veyra_spanned,
    span_to_plain,
    spanned_normal_text,
)

from .compiler import CompileResult, SUPPORTED_OBSERVERS, VamCompileError, compile_expr

logger = logging.getLogger(__name__)

NO_OVERCLAIM = "this Core expression was parsed but not compiled or certified by VAM"
SUPPORTED_HEADS = {"rez", "nod", "tact", "breath", "mode", "observer", "echo", "shell"}


@dataclass(frozen=True)
class VamDiagnostic:
    """One stable diagnostic row for blocked VAM compilation."""

    error_class: str
    severity: str
    message: str
    source_span: SourceSpan | None
    normalized_text: str | None
    compile_phase: str
    expected: str | None = None
    found: str | None = None
    suggestion: str | None = None
    no_overclaim_note: str | None = None
    excerpt: str | None = None


@dataclass(frozen=True)
class VamDiagnosticResult:
    """Either a successful compile result or one diagnostic."""

    compile_result: CompileResult | None = None
    diagnostic: VamDiagnostic | None = None

    @property
    def ok(self) -> bool:
        """True when VAM compilation produced IR."""
        return self.compile_result is not None and self.diagnostic is None


def compile_source_with_diagnostics(
    source: str,
    *,
    certify: bool = True,
    claim: str = "core-echo",
    boundary: str = "finite Core lowering",
) -> VamDiagnosticResult:
    """Compile Core source or return a conservative VAM diagnostic.

    This front door only reports current parser/lowering support.  A diagnostic
    result never carries a VAM certificate.
    """
    logger.debug("compile_source_with_diagnostics entry chars=%d", len(source))
    parsed = parse_veyra_spanned(source)
    if not parsed.ok or parsed.expr is None or parsed.diagnostic is not None:
        diag = parsed.diagnostic
        if diag is None:
            logger.error("compile_source_with_diagnostics rejected reason=missing-parser-diagnostic")
            diagnostic_result = VamDiagnosticResult(
                diagnostic=VamDiagnostic(
                    error_class="internal.compiler_bug",
                    severity="error",
                    message="internal VAM parser failure: missing diagnostic",
                    source_span=None,
                    normalized_text=None,
                    compile_phase="internal",
                    suggestion="file a compiler bug with the minimized source",
                    no_overclaim_note=NO_OVERCLAIM,
                )
            )
            logger.debug("compile_source_with_diagnostics exit diagnostic=internal.compiler_bug")
            return diagnostic_result
        logger.debug("compile_source_with_diagnostics exit diagnostic=parse.syntax")
        return VamDiagnosticResult(
            diagnostic=VamDiagnostic(
                error_class="parse.syntax",
                severity="error",
                message=diag.message,
                source_span=diag.span,
                normalized_text=None,
                compile_phase="parse",
                expected=diag.expected,
                found=diag.found,
                suggestion="fix Core syntax before VAM lowering",
                no_overclaim_note=None,
                excerpt=_excerpt(source, diag.span),
            )
        )

    preflight = _preflight_lowering_diagnostic(source, parsed.expr)
    if preflight is not None:
        logger.debug("compile_source_with_diagnostics exit preflight=%s", preflight.error_class)
        return VamDiagnosticResult(diagnostic=preflight)

    try:
        result = compile_expr(span_to_plain(parsed.expr), certify=certify, claim=claim, boundary=boundary)
        logger.debug("compile_source_with_diagnostics exit ok instructions=%d", len(result.program))
        return VamDiagnosticResult(compile_result=result)
    except VamCompileError as exc:
        diagnostic = _diagnose_lowering_failure(source, parsed.expr, str(exc))
        logger.debug("compile_source_with_diagnostics exit diagnostic=%s", diagnostic.error_class)
        return VamDiagnosticResult(diagnostic=diagnostic)
    except Exception as exc:  # pragma: no cover - defensive front-door boundary
        logger.exception("compile_source_with_diagnostics internal failure")
        return VamDiagnosticResult(
            diagnostic=VamDiagnostic(
                error_class="internal.compiler_bug",
                severity="error",
                message=f"internal VAM compiler failure: {type(exc).__name__}",
                source_span=parsed.expr.span,
                normalized_text=spanned_normal_text(parsed.expr),
                compile_phase="internal",
                suggestion="file a compiler bug with the minimized source",
                no_overclaim_note=NO_OVERCLAIM,
                excerpt=_excerpt(source, parsed.expr.span),
            )
        )


def _preflight_lowering_diagnostic(source: str, root: SpannedExpr) -> VamDiagnostic | None:
    """Return known lowering-boundary diagnostics before invoking the compiler."""
    node = _find_unsupported_observer(root)
    if node is not None:
        label = node.label or node.head
        return _diag(
            source,
            "lower.unsupported_observer",
            f"unsupported observer for VAM lowering: {label}",
            node,
            "lower",
            suggestion="use kind, label, length, trace, or boundary, or implement a new observer contract",
        )
    node = _find_unsupported_arity(root)
    if node is not None:
        return _diag(source, "lower.unsupported_arity", _arity_message(node), node, "lower", suggestion="fix Core shape before VAM lowering")
    node = _find_unsupported_nod(root)
    if node is not None:
        return _diag(
            source,
            "lower.unsupported_nod_form",
            f"unsupported nod form: {spanned_normal_text(node)}",
            node,
            "lower",
            suggestion="use nod:x, nod(rez:x), or anonymous nod until richer residue rules exist",
        )
    node = _find_unsupported_head(root)
    if node is not None:
        return _diag(
            source,
            "lower.unsupported_head",
            f"unsupported Core expression for VAM lowering: {spanned_normal_text(node)}",
            node,
            "lower",
            suggestion="use the finite Core subset or add an explicit lowering rule",
        )
    return None


def compile_source_diagnostic(
    source: str,
    *,
    certify: bool = True,
    claim: str = "core-echo",
    boundary: str = "finite Core lowering",
) -> VamDiagnosticResult:
    """Short alias for :func:`compile_source_with_diagnostics`."""
    return compile_source_with_diagnostics(source, certify=certify, claim=claim, boundary=boundary)


def _diagnose_lowering_failure(source: str, root: SpannedExpr, detail: str) -> VamDiagnostic:
    logger.debug("diagnose lowering entry detail=%s", detail)
    node = _find_unsupported_observer(root)
    if node is not None:
        label = node.label or node.head
        return _diag(
            source,
            "lower.unsupported_observer",
            f"unsupported observer for VAM lowering: {label}",
            node,
            "lower",
            suggestion="use kind, label, length, trace, or boundary, or implement a new observer contract",
        )

    node = _find_unsupported_arity(root)
    if node is not None:
        return _diag(
            source,
            "lower.unsupported_arity",
            _arity_message(node),
            node,
            "lower",
            suggestion="fix Core shape before VAM lowering",
        )

    node = _find_unsupported_nod(root)
    if node is not None:
        return _diag(
            source,
            "lower.unsupported_nod_form",
            f"unsupported nod form: {spanned_normal_text(node)}",
            node,
            "lower",
            suggestion="use nod:x, nod(rez:x), or anonymous nod until richer residue rules exist",
        )

    node = _find_unsupported_head(root)
    if node is not None:
        return _diag(
            source,
            "lower.unsupported_head",
            f"unsupported Core expression for VAM lowering: {spanned_normal_text(node)}",
            node,
            "lower",
            suggestion="use the finite Core subset or add an explicit lowering rule",
        )

    return VamDiagnostic(
        error_class="normalize.span_gap",
        severity="error",
        message="normalized expression has no exact source-span owner",
        source_span=root.span,
        normalized_text=normal_text(span_to_plain(root)),
        compile_phase="normalize",
        suggestion="report the enclosing expression and keep the diagnostic conservative",
        no_overclaim_note=f"{NO_OVERCLAIM}; compiler detail: {detail}",
        excerpt=_excerpt(source, root.span),
    )


def _diag(source: str, error_class: str, message: str, node: SpannedExpr, phase: str, *, suggestion: str) -> VamDiagnostic:
    return VamDiagnostic(
        error_class=error_class,
        severity="error",
        message=message,
        source_span=node.span,
        normalized_text=spanned_normal_text(node),
        compile_phase=phase,
        suggestion=suggestion,
        no_overclaim_note=NO_OVERCLAIM,
        excerpt=_excerpt(source, node.span),
    )


def _walk(expr: SpannedExpr) -> tuple[SpannedExpr, ...]:
    return (expr,) + tuple(child for arg in expr.args for child in _walk(arg))


def _find_unsupported_observer(expr: SpannedExpr) -> SpannedExpr | None:
    return next((node for node in _walk(expr) if node.head == "observer" and (node.label or "kind") not in SUPPORTED_OBSERVERS), None)


def _find_unsupported_arity(expr: SpannedExpr) -> SpannedExpr | None:
    for node in _walk(expr):
        if node.label is not None:
            continue
        if node.head == "tact" and len(node.args) != 2:
            return node
        if node.head == "mode" and len(node.args) != 1:
            return node
        if node.head == "echo" and len(node.args) != 3:
            return node
    return None


def _arity_message(node: SpannedExpr) -> str:
    expected = {"tact": 2, "mode": 1, "echo": 3}[node.head]
    return f"{node.head} expects {expected} argument(s), found {len(node.args)}"


def _find_unsupported_nod(expr: SpannedExpr) -> SpannedExpr | None:
    for node in _walk(expr):
        if node.head == "nod" and node.label is None and node.args:
            if not (len(node.args) == 1 and node.args[0].head == "rez"):
                return node
    return None


def _find_unsupported_head(expr: SpannedExpr) -> SpannedExpr | None:
    return next((node for node in _walk(expr) if node.head not in SUPPORTED_HEADS), None)


def _excerpt(source: str, span: SourceSpan) -> str:
    lines = source.splitlines() or [source]
    line = lines[span.line - 1] if 0 <= span.line - 1 < len(lines) else ""
    width = max(1, min(span.end - span.start, max(len(line) - span.column + 1, 1)))
    return f"{line}\n{' ' * max(span.column - 1, 0)}{'^' * width}"
