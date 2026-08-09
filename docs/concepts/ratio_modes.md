# Ratio Modes

## 1. Purpose

School arithmetic needs fractions and rational numbers. Veyra treats a fraction as a balance measured against a scale, not as “two integers with a bar.”

## 2. Definition

**DEF-049 — Ratio mode.**

A ratio mode is:

`Q = B / S`

where `B` is a balance mode and `S` is a non-silent scale mode.

The length shadow is:

`shadow(Q)=len±(B)/len(S)`.

## 3. Canonical ratio

**DEF-050 — Canonical ratio shadow.**

Under the one-tact length observer, `Q` reduces to the ordinary rational number represented by:

`(τ^p, ε)/τ^q` or `(ε, τ^p)/τ^q`

with `p/q` in lowest terms.

## 4. Operations

Addition uses cross-scaling:

`B₁/S₁ + B₂/S₂ = (B₁·len(S₂) ⊞ B₂·len(S₁)) / (S₁S₂)`.

Multiplication and inverse are currently implemented in the length-shadow rational layer.

## 5. Caveat

This is enough to recover school fractions as a shadow, but not yet enough for full Veyra-native ratio geometry.

Future work: define scale composition without collapsing to length, and let ratios preserve multi-tact structure.
