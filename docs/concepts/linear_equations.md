# Linear Equation Constraints

## 1. Purpose

School algebra begins when an unknown is constrained by an equation.

Veyra treats a linear equation as a **resonance constraint** between two transformers of an unknown ratio mode.

## 2. Linear form

**DEF-055 — Linear ratio form.**

A linear form is:

`F(x)=A·x ⊕ B`

where `A` and `B` are ratio modes.

## 3. Linear equation

**DEF-056 — Linear constraint.**

A linear equation is a pair of forms:

`F(x) ⇔ G(x)`.

Solving means finding a ratio mode `x` whose residual vanishes:

`Res(x)=F(x)-G(x)=0`.

## 4. Obstructions

**DEF-057 — Equation obstruction.**

The current linear solver returns:

- `none` — unique solution;
- `identity` — infinitely many solutions;
- `parallel-obstruction` — no solution because coefficients match but offsets conflict.

## 5. Shadow theorem

In the one-tact rational length shadow, this recovers ordinary school linear equations:

`ax+b=cx+d`.

But Veyra keeps the obstruction as first-class output, not an exception.
