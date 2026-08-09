from src.core.language import VeyraKind, expr_kind, normal_text
from src.core.language_span import (
    diagnostic_excerpt,
    lex_veyra,
    parse_veyra_spanned,
    span_language_checklist,
    span_to_plain,
    spanned_normal_text,
)


def test_lexer_emits_source_spans():
    tokens = lex_veyra("nod:a")
    assert [(t.kind, t.text, t.span.start, t.span.end) for t in tokens[:3]] == [
        ("NAME", "nod", 0, 3),
        ("COLON", ":", 3, 4),
        ("NAME", "a", 4, 5),
    ]


def test_spanned_parser_returns_ast_and_span():
    result = parse_veyra_spanned("tact(nod:a,nod:b)")
    assert result.ok
    assert result.expr is not None
    assert result.expr.span.start == 0
    assert result.expr.span.end == len("tact(nod:a,nod:b)")
    assert spanned_normal_text(result.expr) == "tact(nod:a,nod:b)"


def test_spanned_ast_bridges_to_plain_typechecker():
    result = parse_veyra_spanned("mode(breath(tact(nod:a,nod:b),tact(nod:b,nod:a)))")
    assert result.expr is not None
    plain = span_to_plain(result.expr)
    assert normal_text(plain) == "mode(breath(tact(nod:a,nod:b),tact(nod:b,nod:a)))"
    assert expr_kind(plain).kind == VeyraKind.MODE


def test_parse_diagnostic_points_to_missing_close():
    source = "echo(nod:a,nod:b,observer:length"
    result = parse_veyra_spanned(source)
    assert not result.ok
    assert result.diagnostic is not None
    assert result.diagnostic.expected == "')'"
    excerpt = diagnostic_excerpt(source, result.diagnostic)
    assert "expected ')'" in excerpt
    assert "^" in excerpt


def test_invalid_character_is_structured_diagnostic():
    result = parse_veyra_spanned("nod:!")
    assert not result.ok
    assert result.diagnostic is not None
    assert result.diagnostic.found == "!"


def test_span_language_checklist_has_v02_capabilities():
    assert span_language_checklist() == (
        "tokens",
        "source-spans",
        "spanned-ast",
        "nonthrowing-parse",
        "structured-diagnostic",
        "plain-ast-bridge",
    )
