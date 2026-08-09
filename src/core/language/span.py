"""Span-aware Veyra Core Language parsing diagnostics."""
from __future__ import annotations
from dataclasses import dataclass
import logging
from ..language import VeyraExpr, normal_text
logger = logging.getLogger(__name__)
@dataclass(frozen=True)
class SourceSpan:
    """Half-open source range with line/column start."""
    start: int
    end: int
    line: int
    column: int
@dataclass(frozen=True)
class VeyraToken:
    """One token with original source span."""
    kind: str
    text: str
    span: SourceSpan
@dataclass(frozen=True)
class SpannedExpr:
    """Expression node that preserves source span."""
    head: str
    args: tuple["SpannedExpr", ...]
    label: str | None
    span: SourceSpan
@dataclass(frozen=True)
class ParseDiagnostic:
    """Structured parse diagnostic."""
    message: str
    span: SourceSpan
    expected: str
    found: str
@dataclass(frozen=True)
class SpannedParseResult:
    """Non-throwing parse result."""
    ok: bool
    expr: SpannedExpr | None
    diagnostic: ParseDiagnostic | None
    tokens: tuple[VeyraToken, ...]
PUNCT = {"(": "LPAREN", ")": "RPAREN", ",": "COMMA", ":": "COLON"}
def lex_veyra(source: str) -> tuple[VeyraToken, ...]:
    """Lex source into tokens carrying exact source spans."""
    logger.debug("lex_veyra entry len=%d", len(source))
    tokens: list[VeyraToken] = []
    i = 0; line = 1; col = 1
    while i < len(source):
        ch = source[i]
        if ch.isspace():
            line, col = (line + 1, 1) if ch == "\n" else (line, col + 1); i += 1; continue
        span = SourceSpan(i, i + 1, line, col)
        if ch in PUNCT:
            tokens.append(VeyraToken(PUNCT[ch], ch, span)); i += 1; col += 1; continue
        if ch.isalnum() or ch in "_-τ":
            start, scol = i, col
            while i < len(source) and (source[i].isalnum() or source[i] in "_-τ"):
                i += 1; col += 1
            tokens.append(VeyraToken("NAME", source[start:i], SourceSpan(start, i, line, scol))); continue
        tokens.append(VeyraToken("ERROR", ch, span)); i += 1; col += 1
    tokens.append(VeyraToken("EOF", "", SourceSpan(len(source), len(source), line, col)))
    logger.debug("lex_veyra exit count=%d", len(tokens))
    return tuple(tokens)
def parse_veyra_spanned(source: str) -> SpannedParseResult:
    """Parse source into span-aware AST without throwing."""
    logger.debug("parse_veyra_spanned entry source=%r", source)
    tokens = lex_veyra(source)
    parser = _SpanParser(tokens)
    expr, diagnostic = parser.parse()
    result = SpannedParseResult(diagnostic is None, expr, diagnostic, tokens)
    logger.debug("parse_veyra_spanned exit ok=%s diagnostic=%r", result.ok, diagnostic)
    return result
class _SpanParser:
    """Token parser for span-aware Veyra syntax."""
    def __init__(self, tokens: tuple[VeyraToken, ...]) -> None:
        logger.debug("_SpanParser.__init__ entry count=%d", len(tokens))
        self.tokens = tokens; self.index = 0
        logger.debug("_SpanParser.__init__ exit")
    def parse(self) -> tuple[SpannedExpr | None, ParseDiagnostic | None]:
        """Parse a complete expression."""
        logger.debug("_SpanParser.parse entry")
        try:
            expr = self.expr(); tail = self.peek()
            if tail.kind != "EOF":
                return None, self.diag("trailing source", "EOF", tail)
            logger.debug("_SpanParser.parse exit expr=%r", expr)
            return expr, None
        except _ParseStop as stop:
            logger.debug("_SpanParser.parse exit diagnostic=%r", stop.diagnostic)
            return None, stop.diagnostic
    def expr(self) -> SpannedExpr:
        """Parse expression node."""
        logger.debug("_SpanParser.expr entry index=%d", self.index)
        head = self.expect("NAME", "constructor name")
        token = self.peek()
        if token.kind == "COLON":
            self.index += 1; label = self.expect("NAME", "atom label")
            result = SpannedExpr(head.text.lower(), (), label.text.lower(), merge_span(head.span, label.span))
        elif token.kind == "LPAREN":
            self.index += 1; args: list[SpannedExpr] = []
            if self.peek().kind != "RPAREN":
                while True:
                    args.append(self.expr())
                    if self.peek().kind != "COMMA":
                        break
                    self.index += 1
            close = self.expect("RPAREN", "')'")
            result = SpannedExpr(head.text.lower(), tuple(args), None, merge_span(head.span, close.span))
        else:
            result = SpannedExpr(head.text.lower(), (), None, head.span)
        logger.debug("_SpanParser.expr exit result=%r", result)
        return result
    def expect(self, kind: str, expected: str) -> VeyraToken:
        """Consume token of kind or stop with diagnostic."""
        logger.debug("_SpanParser.expect entry kind=%s index=%d", kind, self.index)
        token = self.peek()
        if token.kind == kind:
            self.index += 1; logger.debug("_SpanParser.expect exit token=%r", token); return token
        raise _ParseStop(self.diag("unexpected token", expected, token))
    def peek(self) -> VeyraToken:
        """Return current token."""
        logger.debug("_SpanParser.peek entry index=%d", self.index)
        result = self.tokens[self.index]
        logger.debug("_SpanParser.peek exit token=%r", result)
        return result
    def diag(self, message: str, expected: str, token: VeyraToken) -> ParseDiagnostic:
        """Build diagnostic at token."""
        logger.debug("_SpanParser.diag entry message=%s expected=%s token=%r", message, expected, token)
        result = ParseDiagnostic(message, token.span, expected, token.kind if token.kind != "ERROR" else token.text)
        logger.debug("_SpanParser.diag exit result=%r", result)
        return result
class _ParseStop(Exception):
    """Internal parse stop carrying structured diagnostic."""
    def __init__(self, diagnostic: ParseDiagnostic) -> None:
        logger.debug("_ParseStop.__init__ entry diagnostic=%r", diagnostic)
        super().__init__(diagnostic.message); self.diagnostic = diagnostic
        logger.debug("_ParseStop.__init__ exit")
def merge_span(left: SourceSpan, right: SourceSpan) -> SourceSpan:
    """Merge two spans."""
    logger.debug("merge_span entry left=%r right=%r", left, right)
    result = SourceSpan(left.start, right.end, left.line, left.column)
    logger.debug("merge_span exit result=%r", result)
    return result
def span_to_plain(expr: SpannedExpr) -> VeyraExpr:
    """Drop spans and return the v0.1 plain AST."""
    logger.debug("span_to_plain entry expr=%r", expr)
    result = VeyraExpr(expr.head, tuple(span_to_plain(arg) for arg in expr.args), expr.label)
    logger.debug("span_to_plain exit result=%s", normal_text(result))
    return result
def spanned_normal_text(expr: SpannedExpr) -> str:
    """Render spanned expression through the canonical plain renderer."""
    logger.debug("spanned_normal_text entry expr=%r", expr)
    result = normal_text(span_to_plain(expr))
    logger.debug("spanned_normal_text exit result=%s", result)
    return result
def diagnostic_excerpt(source: str, diagnostic: ParseDiagnostic) -> str:
    """Render one-line parse diagnostic with caret position."""
    logger.debug("diagnostic_excerpt entry diagnostic=%r", diagnostic)
    line_text = source.splitlines()[diagnostic.span.line - 1] if source.splitlines() else source
    caret = " " * max(diagnostic.span.column - 1, 0) + "^"
    result = f"{line_text}\n{caret}\nexpected {diagnostic.expected}, found {diagnostic.found}: {diagnostic.message}"
    logger.debug("diagnostic_excerpt exit result=%r", result)
    return result
def span_language_checklist() -> tuple[str, ...]:
    """Return v0.2 span-language capabilities."""
    logger.debug("span_language_checklist entry")
    result = ("tokens", "source-spans", "spanned-ast", "nonthrowing-parse", "structured-diagnostic", "plain-ast-bridge")
    logger.debug("span_language_checklist exit count=%d", len(result))
    return result
