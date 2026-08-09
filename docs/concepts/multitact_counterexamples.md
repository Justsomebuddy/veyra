# Multi-Tact Counterexamples: Where Human Arithmetic Splits

## 1. Purpose

The one-tact layer recovers ordinary natural numbers. That is useful, but not yet new.

The first genuinely Veyra-like behavior appears when there are at least two tact kinds, e.g. `a` and `b`. Then identity, multiplication, and primality no longer have one obvious meaning.

This file records the first controlled counterexamples.

## 2. Counterexample CE-001: length identity is too coarse

Let:

- `x = ab`
- `y = aa`

Under `T_len`, both have length 2, so:

`ab ≈_{T_len} aa`

But under `T_bag` they differ:

- `bag(ab) = {a:1,b:1}`
- `bag(aa) = {a:2}`

So:

`ab ≉_{T_bag} aa`

Lesson: tact-count alone destroys internal recurrence content.

## 3. Counterexample CE-002: bag identity loses order

Let:

- `x = ab`
- `y = ba`

Under `T_bag`:

`ab ≈_{T_bag} ba`

But under `T_word`:

`ab ≉_{T_word} ba`

Lesson: multiplicity is not rhythm. A world with order-sensitive transitions cannot use bag identity as full identity.

## 4. Counterexample CE-003: cyclic closure forgets starting cut

Let:

- `x = ab`
- `y = ba`

Under `T_cycle`, closed recurrence ignores the arbitrary starting cut, so:

`ab ≈_{T_cycle} ba`

But `T_word` distinguishes them.

Lesson: closed modes naturally suggest cyclic rather than linear identity.

## 5. Counterexample CE-004: stitch is noncommutative before coarse collapse

Let:

- `a = a`
- `b = b`

Then:

- `a ⊙ b = ab`
- `b ⊙ a = ba`

Under `T_word`, `ab ≉ ba`.  
Under `T_cycle`, `ab ≈ ba`.

Lesson: commutativity is not absolute. It is a property of a chosen echo layer.

## 6. Counterexample CE-005: weave is not well-defined over coarse echo

Let a coarse test family be `T_len`.

Driver modes:

- `d1 = ab`
- `d2 = aa`

They echo by length:

`d1 ≈_{T_len} d2`

Choose substitution map:

- `σ(a) = x`
- `σ(b) = yy`

Then:

- `weave_σ(ab) = xyy`
- `weave_σ(aa) = xx`

These outputs do not even have the same length.

Lesson: a weave schema must declare which echo relation it respects. Coarse driver equivalence is unsafe for symbol-sensitive substitution.

## 7. First structural rule

A theorem using weave must specify:

1. driver test family,
2. output test family,
3. substitution constraints,
4. whether rotations are allowed.

Without this, the theorem is incomplete.

## 8. First new direction

Multi-tact Veyra should study **schema compatibility**:

> A weave schema `W` is compatible with echo pair `(T_in, T_out)` if `x ≈_{T_in} y` implies `W(x) ≈_{T_out} W(y)`.

This replaces the human habit of assuming operations are automatically well-defined on equivalence classes.
