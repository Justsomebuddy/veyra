# 176 — Core Runtime Invariants

**Status:** implemented bounded correctness/security hardening  
**Scope:** seven maintained production assertions in five core files  
**Issue:** #67

## Boundary

This wave replaces seven control-flow assertions whose removal under
`python -O` could otherwise erase type narrowing, a complete-join precondition,
or subprocess-pipe cleanup. It does not change any public DTO, export, digest,
receipt, formal artifact, output byte, proof status, theorem, or mathematical
claim.

The five owned files are:

- `src/core/confluence_runtime.py`;
- `src/core/intrinsic_observer_echo_source.py`;
- `src/core/observer_provenance.py`;
- `src/core/stream_completion_formal_process.py`; and
- `src/core/translated_confluence_cell.py`.

Certificate-result assertions were handled in the preceding independent wave.
VAM, tests, generated/vendor code and the wider repository quality backlog are
not part of this change.

## Runtime behavior

### C1 confluence

The public `fork_confluence_judgment()` remains total for a validated plan with
no join paths: it returns `OPEN`, constructs no transport cell, and retains the
`missing-required-joins` obstruction. A one-sided partial join is not such a
plan: public construction rejects it earlier with the existing
`ConfluenceValidationError("partial-join-plan")`. The private `_transport_cell()` instead
requires both separate join IDs and raises the stable
`transport-cell-requires-complete-separate-joins` runtime error before history
lookup if that internal precondition is violated.

### R13 and provenance

`verify_intrinsic_observer_echo_source_artifact()` performs an exact built-in
artifact-type gate before calling the shape helper. A wrong type therefore
returns only `invalid-r13-source-artifact-type`, even when the helper has been
hostilely replaced. Exceptions from validation of an exact artifact are closed
into `invalid-r13-source-artifact-shape`; the verifier remains nonthrowing.

The provenance `_exact_digest()` gate likewise rejects a non-built-in string
through the existing `ProvenanceDiagnosticError` before calling its digest
predicate. This preserves the public error taxonomy without allowing a hostile
value to reach helper logic.

### Formal process capture

A spawned process whose requested pipe is unexpectedly absent is killed as one
process group, reaped exactly once, and returned as
`COMPILE_ERROR / -1 / b""`. No selector or file-descriptor operation is
attempted. Capture logs no longer interpolate any command element or spawn
exception payload: they retain only fixed stage names and numeric argument
count, cap, return code, and byte count. Normal stdout bytes, output-limit
prefixes, deadlines, return codes and receipts are unchanged.

### Translated C3

The internal side resolver now returns both complete occurrence histories and
the two narrowed join IDs. Missing joins raise the existing
`TranslatedConfluenceValidationError` with
`translated-cell-requires-complete-separate-joins`; downstream history binding
uses the narrowed IDs without assertion-only type assumptions. Exact
`ResponseTranslation` and `OntologyStage` annotations record the already
validated runtime contract without changing values.

## Verification and residual debt

The permanent regression covers both one-sided private C1 failures, public
both-absent totality, public one-sided early rejection, hostile R13 shape and
pin helpers, provenance helper isolation, missing-pipe kill/reap accounting
before selector construction, log privacy, positive and negative C3 side
resolution, AST absence of assertions in all five files, and representative
optimized-Python behavior. It is admitted to the portable hosted matrix.
The same optimized probe exits `12` against the exact pre-wave `fe66e07`
source tree because both assertion-only gates disappear, proving that the
regression distinguishes this change rather than merely exercising old code.

The bounded target is strict-Mypy-clean and has zero production Bandit B101
findings. `stream_completion_formal_process.py` still carries the inherited LOW
B404/B603 findings for its intentionally direct `subprocess` use. Ruff's
formatter still reports the same five legacy files as needing formatting; they
were deliberately not mass-formatted in this semantic wave. These residuals,
and the wider Ruff/Mypy/Bandit backlog, are not reclassified as green. Full
`make verify` was not run for this bounded change.
