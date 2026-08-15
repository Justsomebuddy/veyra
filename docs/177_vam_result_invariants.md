# 177 — VAM Result Invariants

**Status:** implemented bounded correctness/security hardening  
**Scope:** four maintained production assertions in three VAM files  
**Issue:** #69

## Boundary

This wave replaces exactly four control-flow assertions whose removal under
`python -O` could otherwise expose helper callbacks or turn malformed internal
results into unrelated exceptions. The owned positions are:

- the exact rendered-value gate in `vam/intrinsic/runtime.py`;
- the exact VAMI-frame bytes gate in `vam/intrinsic/runtime.py`;
- the parser-result diagnostic narrowing in `vam/src/diagnostics.py`; and
- the Core-result diagnostic narrowing in `vam/src/highlevel.py`.

No VAM instruction, IR DTO, codec tag, profile, report field, legacy VAM0/VAMD
wire value, public export, compiler success path, certificate boundary, proof
status, theorem or mathematical claim changes. Assertions in tests,
experimental/generated/vendor code and other production modules remain outside
this independently reversible wave.

## Runtime behavior

### Intrinsic runtime

`execute_intrinsic_ir()` now requires the producer's rendered `value` to be an
exact built-in `dict` before metrics or tag lookup. A subclass or other value
raises `IntrinsicCodecError("payload", "intrinsic runtime value must be exact
dict")`. Its fixed rejection log contains no value, representation, dynamic
type name or callback payload.

`inspect_intrinsic_frame()` now requires exact built-in `bytes` before calling
the decoder. This preserves the codec's existing
`IntrinsicCodecError("payload", "VAMI frame must be exact bytes")` taxonomy,
but makes the predecoder invariant explicit and optimization-independent. Its
entry and rejection logs are fixed and value-free, so a hostile subclass name
cannot enter logs.

### Conservative diagnostics

An impossible parser result that is unsuccessful or lacks an expression while
also carrying no parser diagnostic now returns one conservative diagnostic:

- class `internal.compiler_bug`, severity `error`, phase `internal`;
- fixed message `internal VAM parser failure: missing diagnostic`;
- no span, normalized text, expected/found value or excerpt;
- the existing no-overclaim boundary and minimized-source bug-report advice.

An impossible unsuccessful Core result with neither compile result nor
diagnostic now retains the completed high-level lowering and returns
`core.internal.compiler_bug`. The row uses fixed line/column `1/1`, offset `0`,
phase `internal`, no nested Core diagnostic and the existing high-level
no-theorem boundary. Both paths emit only fixed reason/state logs; source text
and callback or exception payloads are excluded.

## Compatibility pins and verification contract

The permanent regression exercises hostile rendered-dict and bytes subclasses,
a decoder bomb that must remain uncalled, missing parser/Core diagnostics,
privacy-safe logs, all diagnostic fields, exact public exports and absence of
AST assertions in the three owned production files. One explicit
`python -O` child reaches all four paths and uses ordinary `if`/`raise` checks,
so the regression itself does not disappear in optimized mode.

Valid behavior is pinned to the pre-change baseline:

- canonical anchor VAMI frame: 15 bytes,
  SHA-256 `ff61ae63916a02f85a7790d981f2bb7ff908fc0da5e9c19756f17d59e765898f`;
- profile: `veyra.vami.intrinsic-r12.4.v1`;
- canonical anchor report: 345 bytes,
  SHA-256 `f7fecdca3f7be0a51b96cf41a7469326d9b9a4449a671beb3d6335634af50d0b`;
- legacy `vam.src` export vector: 144 entries with its pre-change digest; and
- representative valid high-level compile: the unchanged seven-instruction
  comparable program with its pre-change digest.

The bounded verification lane includes focused and broader VAM tests, the
portable admission pin, Ruff lint for touched Python, byte compilation, strict
target-only Mypy, Bandit B101 inventory, privacy/hygiene/diff checks and native
Python/Rust VAMI parity when the pinned Rust toolchain is available. The three
owned legacy production files already fail Ruff format and remain deliberately
unformatted to avoid mixing a semantic fix with mass formatting. Wider
repository Ruff/Mypy/Bandit debt is neither modified nor reclassified. Full
`make verify` is not part of this bounded wave.

Local final evidence passes the focused invariant suite `7/7`, the broader
portable-capability VAM lane `320/320` with 183 capability deselections, native
Python/Rust VAMI parity `27/27`, and the configured portable Pytest stage
`667/667` with 12 capability deselections. Ruff lint, new-test formatting,
byte compilation, strict target-only Mypy, Bandit B101 `0`, repository hygiene
`1831/0` and diff integrity pass. The exact pre-wave `5ae42ef` tree exits `11`
under the same optimized probe because its rendered-dict assertion disappears,
while current code reaches all four guards and exits zero. The complete
portable runner passes Ruff and Pytest, then truthfully stops at the inherited
local setuptools 80.10.2 versus declared `>=83,<84` package-build floor;
package smoke is therefore unavailable locally, not green.
