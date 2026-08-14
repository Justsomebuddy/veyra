# Foundational Kernel F1–F3 — first checked repair

**Date:** 2026-07-07
**Status:** first executable repair artifact, not a completed foundation.
**Implements:** F1 unified axiom kernel, F2 theorem-grade statement objects, F3 first checked proof bridge.

## Scope boundary

This file does **not** claim that Veyra is now complete mathematics. It records the first minimal artifacts that answer the audit in `102_foundational_gap_audit.md`:

1. a shared executable axiom kernel exists;
2. current executable layers name their kernel dependencies;
3. Core Language can now carry theorem statements with quantifiers and proof obligations;
4. one tiny theorem has both an internal checked certificate and a Lean-checked external bridge.

The remaining blockers are still real: F4 native runtime is now tracked separately, while mature number theory and the classical benchmark ledger remain open.

## F1 — unified axiom kernel

Implemented in `src/core/axiom_kernel.py`.

| Axiom | Primitive | Executable witness |
|---|---|---|
| `AX-REZ` | `rez` | `rez:cut` |
| `AX-NOD` | `nod` | `nod:a` |
| `AX-TACT` | `tact` | `tact(nod:a,nod:b)` |
| `AX-BREATH` | `breath` | `breath(tact(nod:a,nod:b))` |
| `AX-MODE` | `mode` | `mode(breath(tact(nod:a,nod:a)))` |
| `AX-OBSERVER` | observer | `observer:kind` |
| `AX-ECHO` | echo | `echo(nod:a,nod:b,observer:kind)` |
| `AX-OBSTRUCTION` | obstruction | `echo(nod:a,nod:b,observer:trace)` blocks with mismatch |

`axiom_kernel_report()` now returns witness rows and layer-dependency rows. The
honest boundary is the pair of `derivation` and `status`: a theorem-derived row
whose exact proof toolchain is unavailable remains `blocked`, contributes to
`theorem_blocked`, and makes kernel readiness false rather than being promoted
by the dependency projection.

The derivation field distinguishes:

- `kernel-native` means the row is an internal rule/proof/diagnostic layer;
- `shadow-dependent` means the row uses kernel axioms through finite observer shadows and is not yet a deduction from a native ontology.

## F2 — theorem-grade Core Language

Implemented in `src/core/theorem_language.py`.

Example syntax:

```text
theorem echo_kind_reflexive forall x:nod :: ready(echo($x,$x,observer:kind))
theorem kind_sym forall x:nod,y:nod :: ready(echo($x,$y,observer:kind)) -> ready(echo($y,$x,observer:kind))
theorem kind_iff forall x:nod,y:nod :: ready(echo($x,$y,observer:kind)) <-> ready(echo($y,$x,observer:kind))
```

The parser creates `TheoremStatement` objects with:

- theorem name;
- typed `forall` quantifiers;
- status propositions: `ready(expr)`, `blocked(expr)`, `unknown(expr)`;
- assertion, implication, or equivalence connective;
- finite `ProofObligation` rows under explicit environments.

The blocked diagnostic fixture is intentional: `ready(echo(nod:a,nod:b,observer:trace))` becomes a blocked obligation with the retained echo-mismatch obstruction.

## F3 — checked formal proof bridge

Implemented in `src/core/formal_bridge.py` and `proofs/lean/VeyraEcho.lean`.

Stable theorem id:

```text
THM-F001: for every observer o and object x, echo(o,x,x)
```

Internal mini-kernel proof steps:

1. assume `AX-ECHO`;
2. apply reflexivity of observer response equality;
3. derive `THM-F001` by `echo_refl`.

Lean bridge:

```lean
def echo (o : Observer) (x y : Obj) : Prop := observe o x = observe o y

theorem THM_F001_echo_reflexive (o : Observer) (x : Obj) : echo o x x := by
  unfold echo
  rfl
```

`check_lean_echo_export()` runs the installed Lean toolchain explicitly through `elan run leanprover/lean4:v4.30.0-rc2 lean` when available, avoiding accidental toolchain download.

## Certificate

`foundational_repair_f1_f3` now joins:

- `axiom_kernel_report().ready`;
- ready theorem obligations for `echo_kind_reflexive`;
- at least one blocked theorem obligation diagnostic;
- checked internal proof certificate;
- checked Lean file.

The full certificate suite now reports `46/46` passing certificates after X7 formal export-prep integration.

## What this still does not solve

- It does not make geometry/topology/algebra deduce from arithmetic.
- It does not by itself implement native runtime behavior; F4 now lives in `104_native_runtime_f4.md`.
- It does not prove Veyra number theory theorems such as infinitude of primes.
