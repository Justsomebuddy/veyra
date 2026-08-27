# Number Theory as Resonance of Modes

## 1. Number analogue

A Veyra-number is a **mode**: a closed breath, a recurrence that returns to its own nod-boundary.

The ordinary natural number `n` is only the shadow of the mode:

`n_V = close(τ stitched with itself n times)`.

Special cases:

- `0_V` = silent closed breath.
- `1_V` = one-tact closed breath.
- `S(x)` = stitch `x` with `1_V`.

Native boundary: a silent breath requires an anchor nod, so `0_V` is
anchor-relative natively — one zero per nod, echoed together by the length
observer but separated by the boundary observer
(`native_runtime.silent_breath`, `intrinsic_arithmetic.zero`). "The" zero is a
shadow-level convention.

## 2. Addition

Addition is **stitching of recurrences**.

`a ⊕ b := a ⊙ b`

Human shadow: if `a = τ^m` and `b = τ^n`, then `a ⊕ b = τ^(m+n)`.

## 3. Multiplication

Multiplication is **weaving**: replace each tact of one mode by a full copy of another mode.

`a ⊗ b := b-fold weave of a`

Human shadow: `τ^m ⊗ τ^n = τ^(mn)`.

## 4. Divisibility

A mode `a` **resonates inside** mode `b`, written `a ▹ b`, if `b` can be echo-built by stitching copies of `a` without leftover phase.

Human shadow: `a` divides `b`.

## 5. Prime analogue

A **first-mode** (prime analogue) is a non-silent mode whose only resonant submodes are `1_V` and itself.

Human shadow: prime number.

Veyra interpretation: a prime is a recurrence that cannot be decomposed into smaller stable recurrences under the admitted resonance tests.

## 6. Congruence analogue

Modes `x` and `y` are **phase-congruent modulo** mode `m`, written:

`x ≡_m y`

if their difference of emitted tacts leaves the same phase obstruction after maximal `m`-resonance extraction.

Human shadow: `x mod m = y mod m`.

Boundary: "difference" and "maximal extraction" are shadow-level wording —
they presuppose host subtraction and ordering. The executable native
counterpart is structural division with obstruction rows (`structural_divide`,
`cycle_divisibility_row`); a fully native definition of phase congruence is an
open research task, not an established primitive.

## 7. First non-human shift

The key shift is that arithmetic is not about quantities but about **stable recurrence and decomposition of recurrence**.

This makes number theory look closer to physics:

- divisibility = resonance,
- primality = indecomposable rhythm,
- modularity = phase obstruction,
- gcd = strongest shared echo,
- lcm = smallest shared closure.
