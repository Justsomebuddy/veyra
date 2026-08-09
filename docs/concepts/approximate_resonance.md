# Approximate Resonance with Bounded Defects

## 1. Why approximate resonance?

Exact phase resonance requires:

`rot(whole,r) = part^k`

Real structures often do not behave that cleanly. They may contain:

- noise,
- mutation,
- local defect,
- missing or shifted phase,
- a broken tact in an otherwise stable rhythm.

So Veyra needs a controlled notion of **near-resonance**.

## 2. First bounded-defect relation

This first version is intentionally conservative. It only allows Hamming-style tact mismatches after length compatibility is satisfied.

**DEF-032 — Defect.**

Given equal-length modes `x` and `y`, a defect is a position `i` where `x_i != y_i`.

**DEF-033 — Defect count.**

`δ(x,y)` is the number of defect positions between equal-length modes.

**DEF-034 — Approximate cyclic resonance.**

`part ▹_{cyc,≤d} whole` iff:

1. `part` is non-silent;
2. `len(whole)` is divisible by `len(part)`;
3. for some phase offset `r`, `δ(rot(whole,r), part^k) ≤ d`, where `k=len(whole)/len(part)`.

## 3. Example

Let:

- `part = ab`
- `whole = abac`

Expected exact repetition:

`part^2 = abab`

Compare:

`whole = abac`

Defect:

- position 3: expected `b`, actual `c`.

So:

- exact cyclic resonance: false;
- approximate resonance with `d=1`: true.

## 4. Obstruction taxonomy extension

Approximate resonance profiles now distinguish:

- `none` — exact resonance;
- `bounded-defect` — within defect budget;
- `over-budget` — length fits but every phase has too many defects;
- `length-obstruction` — length does not tile;
- `silent-part` — part is silent and cannot define a rhythm.

## 5. Why this matters

This is the first Veyra bridge toward scientific reality:

- crystals with defects,
- biological motifs with mutations,
- noisy signals,
- approximate periodicity,
- resonance under perturbation.

The deeper future object is not just a boolean relation, but a **resonance spectrum**: for each candidate part, record best phase, defect count, and obstruction.

## 6. Current limitation

This version does not allow insertions/deletions or time-warp drift. It is only equal-length mismatch resonance after phase rotation.

Next versions may add:

- edit-distance resonance,
- weighted defect costs,
- phase drift,
- local repair operations,
- probabilistic resonance scores.
