# 012 — VAM Diagnostics and Theorem Carriers v0.7

## Status

Implemented as a bounded v0.7 bridge:

- `vam/src/diagnostics.py` adds a span-aware diagnostic front door.
- `vam/src/theorem.py` adds theorem/obligation carrier records plus v1.0 finite theorem-case rows.
- `src/core/certify_vam.py` folds both into `vam_reference_v1`.
- v0.8 adds `vam/src/obligation.py` for explicit non-certificate obligation IR rows.

This is a compiler boundary improvement, not a proof-assistant upgrade.

## Diagnostics front door

`compile_source_with_diagnostics(source)` returns either:

- `VamDiagnosticResult(compile_result=...)` for the current finite Core subset; or
- `VamDiagnosticResult(diagnostic=...)` for parse/lowering failures.

Stable classes currently include:

- `parse.syntax`;
- `lower.unsupported_observer`;
- `lower.unsupported_arity`;
- `lower.unsupported_nod_form`;
- `lower.unsupported_head`;
- `normalize.span_gap`;
- `internal.compiler_bug`.

A diagnostic result never carries a VAM certificate.

## Span boundary

Diagnostics use `src/core/language_span.py` before lowering. Exact spans are kept for parse and direct lowering failures. If normalization makes exact ownership unclear, VAM reports `normalize.span_gap` and points to the enclosing expression.

This means VAM can locate current compiler boundaries, but it does not yet preserve full source maps through VAM0.

## Theorem carriers

`lower_theorem_source(...)` and `lower_theorem_statement(...)` transport existing Core theorem-language finite obligation checks into VAM data:

- theorem id;
- binders;
- assumptions;
- claims;
- finite environments;
- obligations;
- proof status;
- trust boundary.

Records can be exported as `VamObject("Theorem", ...)` for transport. `VamObligationRow` also exposes per-obligation rows with `accepted_certificate=False` so status metadata cannot be mistaken for accepted proof evidence.

## Status vocabulary

The carrier uses explicit statuses:

- `verified` — all finite Core obligations are ready under the declared trust boundary;
- `blocked` — at least one finite obligation fails;
- `open` — missing environment, unknown semantics, or unsupported requested status;
- `imported` — external proof boundary is named;
- `conjectural` — no finite environment or explicitly conjectural request.

## Non-claims

VAM v0.7 does not:

- lower quantified theorem semantics into executable VAM instructions;
- prove theorem cards internally;
- prove shell/conjunction semantics internally, even though finite shell carrier transport now exists;
- preserve full source maps in VAM0;
- turn diagnostics into mathematical refutations.

## Verification

Focused tests:

```bash
PYTHONPATH=. pytest -q tests/vam/test_vam_diagnostics.py tests/vam/test_vam_theorem.py
```

Global certificate hook:

```text
vam_reference_v1 includes diag=True, blocked unsupported-observer diagnostics, one verified finite theorem-case row, obligation IR status checks, shell transported/blocked carrier checks, and fixture boundary checks.
```
