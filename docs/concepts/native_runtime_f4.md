# Native Runtime F4 — rez/nod/tact/breath/mode objects

**Date:** 2026-07-07  
**Status:** first executable native runtime, not a completed ontology.  
**Implements:** F4 native `rez/nod/tact/breath/mode` objects and observer-derived shadow rows.

## Scope boundary

This closes the narrow F4 blocker from `../concepts/foundational_gap_audit.md`: native Veyra objects now exist as Python runtime objects before school/classical shadows are derived.

It does **not** prove that all prior geometry, topology, algebra, or statistics are deduced from this runtime. Those layers still need dependency proofs or explicit non-derivation boundaries.

## Runtime objects

Implemented in `src/core/native_runtime.py`.

| Object | Native role | Key behavior |
|---|---|---|
| `Rez` | residue of distinction | carries a native residue name |
| `Nod` | address into a residue | observer key is residue plus mark |
| `Tact` | directed contact | links start/end nods with a mark |
| `Breath` | finite run of tacts | requires contiguous tact boundaries |
| `Mode` | recurrent breath | only wraps closed recurrence |

The public constructors are lower-case behavior functions:

```python
from src.core.native_runtime import breath, mode, nod, rez, tact

a = nod(rez("a"))
b = nod(rez("b"))
run = breath(tact(a, b, "rise"), tact(b, a, "fall"))
wrapped = mode(run)
```

`breath()` and `mode()` retain blocked cases as `NativeObstruction` values instead of throwing away the failure.

## Observer-derived shadows

School-readable rows are downstream observations:

- `native_observers()` returns `boundary`, `length`, `shape`, and `residue` observers;
- `observe_native(obj, observer)` derives one response;
- `echo_native(left, right, observer)` performs observer-indexed echo;
- `native_shadow_rows(obj)` returns `NativeShadowRow` rows whose boundary is explicitly `observer-derived; not primary ontology`.

This is the key F4 distinction: shadows are not the object layer. They are measurements of native objects.

## Certificate

`native_runtime_f4` checks:

1. native objects assemble without the Core Language parser;
2. non-contiguous breaths become obstructions;
3. open breaths cannot become modes;
4. observer echo works over native responses;
5. shadow rows are observer-derived and not primary ontology.

The Essence/Core ledger now has `35` execution-ready layers after R7; `native-runtime` remains a witness-only row, while only `intrinsic-resonance` is theorem-derived.

## Remaining blockers

- F5 now has a first paired benchmark ledger in `../concepts/classical_benchmark_ledger_f5.md`; expand it before claiming advantage.
- Later foundational work must derive more layers from native runtime semantics rather than merely listing axiom dependencies.
