# Weighted Tact-Specific Defect Costs

## 1. Why weighted defects?

Bounded-defect resonance counted all mismatches equally. That is too crude.

In many systems, not all substitutions are equally disruptive:

- a chemically similar mutation may be cheap;
- a phase-compatible tact change may be mild;
- a structurally incompatible tact may be expensive.

So Veyra adds directed defect costs.

## 2. Definition

**DEF-041 — Weighted defect cost map.**

A cost map `κ` assigns a nonnegative cost to a directed mismatch:

`κ(expected, actual) -> cost`

If `expected = actual`, cost is always `0`.

If a mismatch is not listed in `κ`, a default mismatch cost is used.

**DEF-042 — Weighted defect.**

A weighted defect is:

`Def_w(i, expected, actual, cost)`

**DEF-043 — Weighted approximate resonance.**

`part ▹_{cyc,κ≤B} whole` iff some phase rotation of `whole` differs from `part^k` with total defect cost at most budget `B`.

## 3. Example

Let:

- `part = ab`
- `whole = abac`
- expected repetition = `abab`

There is one mismatch:

- index `3`: expected `b`, actual `c`.

If:

`κ(b,c)=0.25`

then total weighted defect cost is `0.25`.

If default uniform cost were `1`, the same structural mismatch would be four times more expensive.

## 4. Interpretation

Weighted resonance separates two ideas:

- **defect count** — how many positions differ;
- **defect severity** — how damaging each difference is.

This enables richer scientific analogies:

- similar amino-acid substitutions vs radical mutations;
- low-energy vs high-energy lattice defects;
- tolerable vs destructive signal errors;
- semantic closeness between symbols.

## 5. Current limitations

The cost map is still externally assigned. Veyra does not yet derive costs from internal structure.

Future layers should derive `κ` from:

- tact similarity;
- transition compatibility;
- observed co-occurrence;
- compression benefit;
- physical or semantic embedding.
