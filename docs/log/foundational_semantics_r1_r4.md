# Foundational semantic closure R1–R4

**Status:** implemented and checked on 2026-07-14.
**Scope:** strict Core/native semantics, provenance-derived axiom use, intrinsic recurrence arithmetic, and a Lean mirror of the native constructor subset.

## R1 — one executable semantics

`src/core/kernel/semantic_kernel.py` is now the semantic front door for Core terms. It elaborates the normalized AST into the same `Rez`, `Nod`, `Tact`, `Breath`, `Mode`, `NativeObserver`, `NativeEcho`, and `NativeObstruction` values used by `src/core/native_runtime.py`.

The kernel enforces:

- tact ordering;
- breath contiguity;
- mode closure;
- the five Core observers `kind`, `label`, `length`, `trace`, and `boundary`;
- explicit blocked/unknown results instead of coercion;
- deterministic derivation receipts with premise IDs and content digests.

`infer_veyra()` consumes this result instead of maintaining a second observer evaluator. Core-to-VAM lowering performs the same strict preflight. Python VAM and Rust `vam0-ref-v1` use the aligned observer responses; tests cover every supported Core native kind and all five observer adapters. Raw hand-written VAM remains a permissive machine language, but compiled Core cannot bypass Core closure or contiguity.

## R2 — axiom dependencies from proof graphs

Each semantic rule emits a receipt. `verify_receipts()` rejects missing premises, bad rule arity, digest changes, duplicate-ID conflicts, cycles, multiple roots, disconnected extras, and graphs that do not replay exactly from their single root source. `axiom_closure()` maps only that verified graph to the exact kernel axioms used.

After R7, `src/core/kernel/layer_derivations.py` classifies all 35 registered layers without fallback:

- 1 `theorem-derived` intrinsic-resonance row carries an exact proof/Lean binding;
- 4 `receipt-backed-witness` rows carry checked witness graphs and derived closures;
- 25 `shadow` layers explicitly claim no native kernel derivation;
- 5 `meta` layers are ledgers/diagnostics and claim no theorem axioms.

Registry drift is an error. Empty primitive-axiom sets for theorem/shadow/meta rows are deliberate: R7 records its proof-rule/native-law closure separately. The former hand-written exact/fallback axiom table was removed from `axiom_kernel.py`. A witness closure is **not** a proof of the whole named layer or its certificate.

## R3 — intrinsic recurrence arithmetic

`src/core/intrinsic_arithmetic*.py` defines anchored silent zero, one pulse, successor, stitch, weave, structural power, structural quotient/residual reconstruction, zero-divisor obstruction, and product-plus-one escape witnesses directly over recurrence structure.

The theorem path does not call `int`, `%`, `pow`, `gcd`, `len`, or the length observer. Division consumes matching tact prefixes and returns a proof object containing quotient, residual, reconstruction, steps, and obstruction state. The former `native_number_theorems.py` path remains classified as a compatibility shadow.

`proofs/lean/VeyraNativeArithmetic.lean` independently defines an inductive `Recurrence`, stitch, weave, and resonance. It checks `THM-R3-001` (stitch associativity) and `THM-R3-002` (every recurrence resonates with a single pulse), with no imported `Nat` arithmetic.

## R4 — native Lean bridge

`proofs/lean/VeyraNativeSemantics.lean` mirrors native `Rez/Nod/Tact/Breath/Mode`, ready/blocked results, contiguity, boundary, mode closure, observer response, and echo. It proves:

- `THM-R4-001`: empty breath blocks;
- `THM-R4-002`: a closed tact forms a mode;
- `THM-R4-003`: an open tact blocks;
- `THM-R4-004`: a two-tact cycle forms a mode;
- `THM-R4-005`: all ready modes echo under the kind observer.
- `THM-R4-006`: unequal boundary responses block with `echo mismatch` rather than returning a ready false relation;
- `THM-R4-007`: anchored silent breath is a valid closed mode, matching intrinsic zero.

`certify_foundational.py` now requires both Lean files through `native_formal_bridge.py`.

## Honest boundary

This closes the executable native constructor subset, not every Veyra shadow module. R7 adds one proof-carrying intrinsic theorem (`docs/log/proof_carrying_core_r7.md`), while the 25 shadow layers remain explicit finite/classical models. The Lean semantics does not prove Python implementation equivalence by extraction or cover every Core observer.

## Verification surface

- `tests/language/test_core_native_semantics.py`
- `tests/proof/test_semantic_receipts.py`
- `tests/language/test_core_vam_semantic_parity.py`
- `tests/proof/test_layer_derivations.py`
- `tests/proof/test_intrinsic_arithmetic.py`
- `tests/formal/test_native_formal_bridge.py`
- `proofs/lean/VeyraNativeArithmetic.lean`
- `proofs/lean/VeyraNativeSemantics.lean`
