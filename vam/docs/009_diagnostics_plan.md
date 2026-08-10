# 009 — VAM Diagnostics and Source-Span Plan

> **Historical plan:** `vam/src/diagnostics.py` now implements the bounded
> span-aware diagnostic result and stable error-class surface. The broader
> proposals below remain design history, not evidence of complete language or
> compiler diagnostics.

## Scope

Design the diagnostics layer for VAM Core lowering so compiler failures can point back to Core source spans without claiming semantic coverage that VAM has not implemented.

This document originally specified a plan; current behavior is defined by the
implementation and tests, while unsupported forms remain explicit boundaries.

## Goals

- Preserve Core parser diagnostics when source text is syntactically invalid.
- Attach Core source spans to VAM compile errors raised after parsing succeeds.
- Classify VAM compile failures into stable machine-readable error classes.
- Provide deterministic human messages, excerpts, and suggested next actions.
- Keep no-overclaim boundaries explicit in diagnostics, test fixtures, and user-facing summaries.

## Non-Goals

- Do not implement the diagnostics layer here.
- Do not certify unsupported Core constructs by rewording errors as warnings.
- Do not infer missing source spans from normalized text when exact spans are unavailable.
- Do not claim theorem, quantifier, proof, or opaque-symbol lowering is complete.
- Do not treat a successful parse as a successful VAM compilation.

## Current Inputs

Core already has a span-aware parser path:

```text
source -> parse_veyra_spanned -> SpannedExpr | ParseDiagnostic
```

Current VAM lowering uses the plain parser path:

```text
source -> parse_veyra -> normalize_veyra -> _Compiler.compile -> VAMCompileError | CompileResult
```

The diagnostics bridge should move VAM compilation to a conservative span-aware front door:

```text
source
  -> parse_veyra_spanned
  -> span_to_plain + span index
  -> normalize/lower
  -> VamDiagnostic | CompileResult
```

## Diagnostic Data Model

Planned public diagnostic object:

```text
VamDiagnostic {
  error_class,
  severity,
  message,
  source_span,
  normalized_text,
  compile_phase,
  expected,
  found,
  suggestion,
  no_overclaim_note,
}
```

Required fields:

- `error_class`: stable enum value from the classes below.
- `severity`: `error` for blocked compilation, `warning` for conservative degradations, `info` for trace notes.
- `source_span`: exact Core span if known; absent only for non-source internal failures.
- `compile_phase`: `parse`, `normalize`, `lower`, `cert`, or `internal`.
- `no_overclaim_note`: required when a construct is recorded but not compiled/certified.

## Error Classes

### `parse.syntax`

Use for Core parser failures from `ParseDiagnostic`.

- Phase: `parse`.
- Span source: parser diagnostic span.
- Message source: parser diagnostic message, expected, found.
- VAM action: do not enter lowering.

Examples: missing close parenthesis, trailing source, empty label, invalid character.

### `lower.unsupported_head`

Use when an expression head has no VAM lowering rule.

- Phase: `lower`.
- Span source: full span of the unsupported `SpannedExpr`.
- Message: `unsupported Core expression for VAM lowering: <normal_text>`.
- Suggestion: use the finite Core subset or add an explicit lowering rule.

Examples: theorem syntax, quantifier forms, shell relations, domain-specific operators.

### `lower.unsupported_arity`

Use when a known head is present with unsupported argument count.

- Phase: `lower`.
- Span source: full expression span.
- Message: `<head> expects <n> argument(s), found <m>`.
- Suggestion: fix Core shape before VAM lowering.

Examples: `tact(nod:a)`, `mode(nod:a,nod:b)`, malformed `echo` arity.

### `lower.unsupported_observer`

Use when `observer:<label>` is syntactically valid but not in VAM's supported observer set.

- Phase: `lower`.
- Span source: observer atom span.
- Message: `unsupported observer for VAM lowering: <label>`.
- Suggestion: use `kind`, `label`, `length`, `trace`, or `boundary`, or implement a new observer contract.

### `lower.unsupported_nod_form`

Use when `nod` is syntactically valid but not conservatively lowerable.

- Phase: `lower`.
- Span source: `nod` expression span.
- Message: `unsupported nod form: <normal_text>`.
- Suggestion: use `nod:x`, `nod(rez:x)`, or anonymous `nod` until richer residue rules exist.

### `normalize.span_gap`

Use when normalization changes expression structure and the compiler cannot map the failing normalized node back to exactly one original span.

- Phase: `normalize`.
- Span source: nearest safe enclosing span, if available.
- Message: `normalized expression has no exact source-span owner`.
- Suggestion: report the enclosing expression and keep the diagnostic conservative.

This class prevents fake precision.

### `cert.boundary_overclaim`

Use when a caller requests a certificate or verified status for a construct with open obligations.

- Phase: `cert`.
- Span source: root expression or specific obligation span.
- Message: `cannot certify construct with unsupported or open lowering obligations`.
- Suggestion: emit an obligation/conjectural status instead of a verified certificate.

### `internal.compiler_bug`

Use for impossible states, missing spans caused by implementation bugs, or exceptions not attributable to user source.

- Phase: `internal`.
- Span source: absent or root source span.
- Message: stable generic text plus debug-safe details.
- Suggestion: file a compiler bug with the minimized source.

## Span Mapping Strategy

1. Parse with `parse_veyra_spanned(source)` first.
2. If parsing fails, return `parse.syntax` directly; do not call the VAM compiler.
3. If parsing succeeds, build a span index keyed by node identity and canonical `spanned_normal_text`.
4. Convert to plain AST only at the lowering boundary.
5. During lowering, pass both plain and spanned nodes, or a side table that maps each plain node to its spanned origin.
6. When normalization rewrites a node, preserve a provenance set of original spans.
7. If a failing normalized node has exactly one origin span, use it.
8. If it has multiple origins, use the smallest enclosing span and emit `normalize.span_gap` detail rather than inventing a single-token caret.
9. Diagnostic excerpts should use original source text, never reconstructed normalized text.
10. Serialization must preserve span start/end plus line/column.

## User-Facing Format

Recommended text rendering:

```text
error[lower.unsupported_observer] at 1:27
unsupported observer for VAM lowering: weight

  echo(nod:a,nod:b,observer:weight)
                            ^

note: VAM currently supports observer labels: kind, label, length, trace, boundary.
no-overclaim: this Core expression was parsed but not compiled or certified by VAM.
```

Rules:

- Prefix with stable `error_class`.
- Include line/column and excerpt when span exists.
- Include the no-overclaim note for every unsupported semantic construct.
- Avoid words like `proved`, `verified`, or `certified` unless the certificate path actually accepted the object.

## Test Plan

### Parser diagnostic passthrough

- Missing close parenthesis returns `parse.syntax` with the Core parser span.
- Trailing source returns `parse.syntax` and never calls lowering.
- Bad label character returns `parse.syntax` with exact found token.
- Multiline parse failure preserves line and column.

### Lowering error spans

- `observer:weight` returns `lower.unsupported_observer` at the observer atom span.
- `tact(nod:a)` returns `lower.unsupported_arity` at the `tact` expression span.
- `mode(nod:a,nod:b)` returns `lower.unsupported_arity` at the `mode` expression span.
- Unsupported head returns `lower.unsupported_head` at the unsupported node span.
- Unsupported nested node reports the nested span, not the whole source, when exact provenance exists.

### Normalization provenance

- Normalization-preserved expressions keep exact spans.
- Reordered or merged expressions with ambiguous provenance produce `normalize.span_gap` detail.
- Ambiguous provenance uses an enclosing span and does not render a misleading single-token caret.

### Certificate boundary

- `certify=True` with open lowering obligations returns or records `cert.boundary_overclaim`.
- Unsupported constructs cannot produce accepted VAM certificates.
- Diagnostics distinguish `parsed`, `compiled`, `lowered with obligations`, and `certified`.

### Regression and golden tests

- Golden diagnostic objects should assert enum class, phase, severity, span start/end, line/column, message, and no-overclaim note.
- Text snapshots should assert excerpt caret placement without depending on full debug logs.
- Existing successful finite Core lowering fixtures must remain unchanged.

## Acceptance Criteria

- Every VAM compile error from Core source has either an exact Core span or an explicit `normalize.span_gap`/`internal.compiler_bug` reason.
- Parser failures use Core parser diagnostics unchanged.
- Unsupported observer, arity, head, and nod-form failures are separate error classes.
- No unsupported construct is labeled as compiled, verified, or certified.
- Test coverage includes parse passthrough, lower-time failures, nested spans, normalization ambiguity, and certificate no-overclaim boundaries.
- Public docs state that diagnostics improve error location only; they do not expand VAM semantic coverage.

## Implementation Order

1. Add diagnostic enum/data object near the VAM compiler boundary.
2. Add a nonthrowing `compile_source_diagnostic` entrypoint that wraps parser and lowering diagnostics.
3. Thread spanned expressions or provenance through the compiler without changing existing `compile_source` behavior yet.
4. Split current `VamCompileError` sites into typed diagnostic classes.
5. Add renderer for stable CLI/test output.
6. Add golden tests before changing any user-facing success path.
7. Only after tests pass, decide whether `compile_source` should keep throwing or delegate to the new diagnostic entrypoint.

## No-Overclaim Boundary

Diagnostics only locate and classify failures. They do not prove that a rejected construct is mathematically invalid, and they do not prove that an accepted finite lowering covers theorem, quantifier, proof, shell, or opaque-symbol semantics. A successful VAM diagnostic pass means only that the compiler can report its boundary precisely.
