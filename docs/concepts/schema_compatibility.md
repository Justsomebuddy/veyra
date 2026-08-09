# Schema Compatibility

## 1. Problem

Veyra replaces absolute equality with test-indexed echo:

`x ≈_T y`

Therefore an operation is not automatically well-defined on echo classes. It must declare what identity it respects.

## 2. Definition

**DEF-021 — Unary schema compatibility.**

A unary schema `W` respects `(T_in, T_out)` when:

`x ≈_{T_in} y  =>  W(x) ≈_{T_out} W(y)`.

This means `W` can safely act on `T_in`-echo classes and produce `T_out`-echo classes.

## 3. Binary version

**DEF-022 — Binary schema compatibility.**

A binary schema `B` respects `(T_left, T_right; T_out)` when:

`x₁ ≈_{T_left} x₂` and `y₁ ≈_{T_right} y₂`

imply:

`B(x₁,y₁) ≈_{T_out} B(x₂,y₂)`.

## 4. Positive examples

### Exact ordered identity

Any deterministic operation respects `(T_word, T_word)` on finite word shadows, because `T_word` distinguishes exact input words.

### Length-preserving substitution

If a substitution map sends every driver tact to an output mode of the same length, then substitution weave respects `(T_len, T_len)`.

Example:

- `σ(a)=x`
- `σ(b)=y`

Then every input tact contributes exactly one output tact, so input length determines output length.

## 5. Negative example

If:

- `σ(a)=x`
- `σ(b)=yy`

then `a ≈_{T_len} b`, but:

- `σ(a)=x`, length 1;
- `σ(b)=yy`, length 2.

So this substitution does **not** respect `(T_len,T_len)`.

## 6. Proposition

**PROP-001 — Factor-through criterion.**

A unary schema `W` respects `(T_in,T_out)` iff there exists a function `F` on `T_in` echo-keys such that:

`echo_{T_out}(W(x)) = F(echo_{T_in}(x))`

for every admitted `x`.

Interpretation: compatible operations are exactly those whose output observation depends only on the admitted input observation.

## 7. Why this matters

In ordinary algebra we often define operations on equivalence classes after checking well-definedness. Veyra makes that check central:

> A law is not only an operation; it is an operation plus a declared identity scale.

This may be useful for physics: a transformation can preserve coarse observables while breaking fine observables, or preserve cyclic phase while breaking linear order.
