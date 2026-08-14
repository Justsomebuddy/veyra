# Axioms: executable F1 kernel

## Purpose

The active axiom reference now follows `docs/103_foundational_kernel_f1_f3.md`. It is a minimal executable kernel, not a completed foundation.

## Ontology boundary

These `AX-*` rows are **operational semantics**: typed construction and response
rules used by the executable kernel. They are not metaphysical axioms and do
not prove that their primitives are constituents of reality. The canonical
provisional ontological doctrine is `../149_positive_ontology_p0.md`; the nine
mixed Essence policy rows remain separately documented in
`../64_veyra_essence_core.md`.

## Kernel axioms

| Axiom | Primitive | Statement | Witness |
|---|---|---|---|
| `AX-REZ` | `rez` | distinction leaves a residue token | `rez:cut` |
| `AX-NOD` | `nod` | residue may be addressed as a nod | `nod:a` |
| `AX-TACT` | `tact` | two nods may form an ordered contact | `tact(nod:a,nod:b)` |
| `AX-BREATH` | `breath` | nonempty finite contacts assemble as breath | `breath(tact(nod:a,nod:b))` |
| `AX-MODE` | `mode` | a breath can be wrapped as recurrence mode | `mode(breath(tact(nod:a,nod:a)))` |
| `AX-OBSERVER` | observer | observer labels choose visible responses | `observer:kind` |
| `AX-ECHO` | echo | echo is observer-indexed indistinguishability | `echo(nod:a,nod:b,observer:kind)` |
| `AX-OBSTRUCTION` | obstruction | blocked inference is retained | `echo(nod:a,nod:b,observer:trace)` |

## Executable API

- `src.core.axiom_kernel.unified_axiom_kernel()` returns the axiom rows.
- `axiom_witness_rows()` checks each witness through Core Language inference.
- `layer_axiom_dependencies()` names the kernel axioms used by each current
  executable layer and preserves its `status`; a capability-blocked theorem row
  cannot be rewritten as ready merely because it claims no primitive axioms.
- `axiom_kernel_report()` reports derivation boundaries plus
  `theorem_blocked`; readiness is false until every theorem-derived row is
  actually ready.

## Current boundary

This repair names dependencies; F4 does not prove every shadow layer follows from the kernel. P1-C2/C3 and P3-T add no axiom beyond exact finite replay. P1-D2 introduces no all-depth carrier. PΩ1 exposes `Quot.sound`; PΩ2 exposes `Quot.sound`/`propext`; these are not global axioms. P3-A1b adds no choice/DC/coinduction/König axiom. P3-C2.2 derives finite transport coherence from strict rank, total setoid maps, and complete local squares; its NatOp proofs expose only `propext`, and derived cofinal reconciliation is not a 3-cell axiom. P3-N2's seven theorem rows close only through the exact ledger at `Classical.choice`, `propext`, and `Quot.sound`; these are exposed dependencies, not new global axioms, and proof-witness independence blocks map identity from depending on comparison proofs. P2-S/C4/E4 add no promotion or universal ontology.
