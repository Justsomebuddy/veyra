# Cyclic Weave

## 1. Why another weave?

A mode is closed. A closed recurrence should not depend on where a human cuts the loop to write it as a word.

Ordered substitution treats a mode as a linear word:

`substitute(ab) = σ(a)σ(b)`

But for a closed mode, `ab` and `ba` are the same cycle under `T_cycle`. The operation should either:

1. return only a cyclic echo-class, or
2. choose a canonical cut before substituting.

Core-0.6 implements option 2 as a computable shadow.

## 2. Definition

**DEF-027 — Cyclic representative.**

`canon_cyc(w)` is the lexicographically least rotation of `w` in the external word shadow.

Examples:

- `canon_cyc(ab) = ab`
- `canon_cyc(ba) = ab`
- `canon_cyc(baba) = abab`

**DEF-028 — Cyclic weave.**

Given a driver mode `d` and substitution map `σ`, define:

`cyc_weave_σ(d) = canon_cyc(substitute(canon_cyc(d), σ))`

This is not a metaphysical claim that nature chooses lexicographic order. It is a computational representative of the cyclic echo-class.

## 3. Comparison with ordered substitution

Let:

- `σ(a)=x`
- `σ(b)=yy`

Then:

- ordered `substitute(ab)=xyy`
- ordered `substitute(ba)=yyx`

These differ under `T_word`.

But they are the same under `T_cycle`:

`xyy ≈_{T_cycle} yyx`

Cyclic weave canonicalizes both:

- `cyc_weave(ab)=xyy`
- `cyc_weave(ba)=xyy`

So cyclic weave respects `(T_cycle,T_word)` as a representative-picking operation, and ordered substitution respects only `(T_cycle,T_cycle)`.

## 4. Compatibility claims

On finite word shadows with fixed substitution map:

- ordered substitution respects `(T_word,T_word)`;
- ordered substitution respects `(T_cycle,T_cycle)`;
- ordered substitution generally does **not** respect `(T_cycle,T_word)`;
- cyclic weave respects `(T_cycle,T_word)` by canonicalization;
- cyclic weave respects `(T_cycle,T_cycle)` trivially if it respects `(T_cycle,T_word)`.

## 5. Caveat

Cyclic representative selection remains an external display computation. `docs/log/native_cycle_echo_number_theory.md` adds `CycleEcho` and `cyclic_weave_echo()` so native cyclic weave can return the full orbit instead of a lexicographic word.
