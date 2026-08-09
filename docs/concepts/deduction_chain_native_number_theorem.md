# Deduction Chain and Native Number Theorem N1

**Date:** 2026-08-04
**Status:** five-row deduction-chain ledger with executable proof rows plus native Mode-length, finite right-corner, and benchmark-verdict rows.
**Implements:** explicit derivation boundaries, `THM-F002`, and non-claim pressure for number theory.

## Scope boundary

This does not complete a unified deductive foundation. It creates three narrow upgrades:

1. `src/core/formal/deduction_chain.py` names boundary-derived links and executes a proof row for each link.
2. `src/core/numbers/native_number_theorems.py` adds product-plus-one escape construction whose finite source periods can be observed from native `Mode` objects, plus N2 finite Fermat phase rows over native Mode/Breath length observers.
3. `src/core/geometry/native_derivations.py` adds finite right-corner rows whose leg lengths are observed from native `Breath` objects.

The number construction is derived for finite Mode-length rows, and `THM-G001` is derived for finite right-corner Breath lengths. Neither is a complete number or geometry theorem.

## Deduction-chain statuses

| Status | Meaning |
|---|---|
| `derived` | currently checked from kernel/runtime/proof anchors |
| `blocked` | intentionally not claimed |

Current rows:

| ID | Target | Status | Anchor |
|---|---|---|---|
| `DC-001` | echo | derived | `THM-F001` |
| `DC-002` | native-runtime | derived | `native_runtime_f4` |
| `DC-003` | native-number-theorem | derived | `THM-F002` + native Mode lengths |
| `DC-004` | classical-benchmark | derived | eight active benchmark rows + scoped verdict rules |
| `DC-005` | geometry-theorems | derived | `THM-G001` + native Breath lengths |

The important invariant is that `all_derived=True` means every active boundary row has an executable derivation, not that Veyra gained every mathematical capability. Current proof rows verify all five boundaries.

## Executable proof rows

`deduction_proof_rows()` checks every ledger row:

- `DC-001`: internal `THM-F001` certificate plus Lean bridge check.
- `DC-002`: native runtime smoke: closed mode, shape echo, and four shadow observers.
- `DC-003`: three native Mode-length Euclid rows plus Lean `THM-F002`.
- `DC-004`: eight benchmark verdicts derive from named rules: equivalent boundaries, finite-vs-general weaker rows, obstruction clarity, and one strict observer-class separation.
- `DC-005`: three finite native right-corner rows derive 3-4-5, 5-12-13, and 8-15-17 from Breath lengths.

## `THM-F002` bridge

`proofs/lean/VeyraEcho.lean` includes:

```lean
theorem THM_F002_euclid_escape_mod (n k : Nat) : (n * k + 1) % n = 1 % n
```

This is the arithmetic core of the Euclid-style escape: for a listed factor `n`, product-plus-one has remainder one modulo `n`.

## Number-theory rows

`euclid_escape_row((2,3,5,7))` returns witness `211` and remainders `(1,1,1,1)`. `native_euclid_mode_row((2,3,5))` builds native closed Modes, observes lengths `(2,3,5)`, and derives witness `31` with remainders `(1,1,1)`. The certificate checks three increasing finite observer lists and three native Mode-length rows, then keeps these gaps open:

- native infinite resonance-prime theorem;
- unbounded native Fermat theorem beyond finite prime-period rows;
- quadratic-reciprocity analogue.

N2 adds `native_fermat_phase_row(p)`: it builds a native closed period Mode, derives every unit `1..p-1` from native unit Breath lengths, checks `u^(p-1) mod p = 1` for every unit, and requires multiplicative orbit coverage of all nonzero residues. Canonical rows derive periods `2,3,5,7` and block invalid/composite periods `1,4,6`. This is stronger than a single fixture, but remains finite and observer-indexed.

## Benchmark verdict row

`benchmark_derivation_rows()` derives verdicts for the eight active benchmark rows from explicit rules. This makes the ledger verdicts derived, but it does not derive the compared target mathematics. `stronger=1` requires the Lean laws plus executable proper-subset class inclusion and exact `histogram(xor-rows(input))` membership; unsupported/global stronger claims remain zero.

## Native geometry row

`native_right_corner_row(3,4)` builds two native open `Breath` legs, observes lengths `(3,4)`, and derives `hypotenuse=5` because `3²+4²=5²`. The canonical rows also include `(5,12,13)` and `(8,15,17)`.

This promotes `DC-005` only for finite right-corner Breath-length rows. It does not claim full Euclidean geometry, topology, congruence, or coordinate-free geometry.

## Next work

- Convert the finite Mode-length derivation into intrinsic `Mode`/`Breath` divisibility and resonance-prime theorems.
- Extend N2 beyond canonical prime periods or move it into a checked proof bridge before claiming an unbounded Fermat theorem.
- Convert finite `THM-G001` right-corner rows into a reusable native geometry theorem, not only Pythagorean triples.
- Add proof-language exports for more than echo reflexivity and product-plus-one modularity.
