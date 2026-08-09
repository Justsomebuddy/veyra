# Balance Modes

## 1. Purpose

School arithmetic needs negative numbers. Veyra should not import “minus” as a primitive mark on a number.

Core 1.6 introduces **balance modes**: a signed shadow is a tension between arising recurrence and fading recurrence.

## 2. Definition

**DEF-047 — Balance mode.**

A balance mode is a pair:

`B = (B⁺, B⁻)`

where `B⁺` is the arising mode and `B⁻` is the fading mode.

The length shadow is:

`len±(B)=len(B⁺)-len(B⁻)`.

## 3. Opposite

**DEF-048 — Opposite balance.**

The opposite of a balance swaps its poles:

`opp(B⁺,B⁻)=(B⁻,B⁺)`.

This replaces the school unary minus sign.

## 4. Balance stitch

Balances add by stitching same-polarity sides:

`(A⁺,A⁻) ⊞ (B⁺,B⁻) = (A⁺⊙B⁺, A⁻⊙B⁻)`.

Subtraction is stitching with the opposite.

## 5. Canonical length shadow

Under the one-tact length observer, a balance can be collapsed to a canonical one-tact form:

- positive net → `(τ^n, ε)`;
- negative net → `(ε, τ^n)`;
- zero net → `(ε, ε)`.

This is only a shadow. Rich multi-tact balances may be length-equal but not echo-equal under stronger tests.

## 6. Why this is deeper than signed integers

Traditional `-3` stores a sign and a magnitude.

Veyra stores an unresolved opposition: what arose, what faded, and under which observer they cancel.
