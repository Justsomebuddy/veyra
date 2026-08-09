# Veyra Core Language v0.2 — Spans and Diagnostics

**Status:** executable hardening layer.
**Implementation:** `src/core/language/span.py`.
**Tests:** `tests/language/test_core_language_spans.py`.

## Purpose

Core Language v0.1 proved that Veyra expressions can be parsed, typed,
normalized, inferred, and projected into semantic shadows. v0.2 makes the
language usable as a real laboratory surface: every token and expression now
carries source position, and parse failures return structured diagnostics.

This matters because future proof objects, editors, notebooks, and fuzzers need
to point to **where** an obstruction was born, not only say that something was
blocked.

## New artifacts

| Artifact | Meaning |
|---|---|
| `SourceSpan` | half-open source range plus line/column start |
| `VeyraToken` | token kind/text/span |
| `SpannedExpr` | AST node with source span |
| `ParseDiagnostic` | message, span, expected token, found token |
| `SpannedParseResult` | non-throwing parser output |
| `span_to_plain()` | bridge from span AST to v0.1 `VeyraExpr` |

## Lexer

`lex_veyra(source)` emits tokens for names, punctuation, errors, and EOF. Each
token carries a `SourceSpan(start, end, line, column)`.

Example:

```text
nod:a
```

becomes:

```text
NAME(nod)[0:3], COLON(:)[3:4], NAME(a)[4:5], EOF[5:5]
```

## Non-throwing parser

`parse_veyra_spanned(source)` returns `SpannedParseResult`:

- `ok=True`, `expr=SpannedExpr(...)` on success;
- `ok=False`, `diagnostic=ParseDiagnostic(...)` on failure.

This lets experiments, fuzzers, and notebooks collect grammar failures as data
instead of crashing the run.

## Diagnostic excerpt

`diagnostic_excerpt(source, diagnostic)` renders a one-line caret report:

```text
echo(nod:a,nod:b,observer:length
                                  ^
expected ')', found EOF: unexpected token
```

## Bridge to v0.1

`span_to_plain(spanned)` drops spans and returns the existing `VeyraExpr`, so the
new parser can reuse `expr_kind()`, `infer_veyra()`, `normal_text()`, and the
semantic shadow pipeline.

This is deliberately conservative: v0.2 hardens the input surface without
rewriting the already-tested inference layer.

## Verification

Targeted command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/language/test_core_language_spans.py tests/language/test_core_language.py tests/shadows/test_certify.py
```

Current verification: targeted `16 passed`; full suite `228 passed`; doctest 41/41; smoke ok; line hygiene 0 files >300.

## Next step

Use spans to build proof objects: every inference step should record the source
span, rule name, input kinds, output kind/status, and obstruction if blocked.
