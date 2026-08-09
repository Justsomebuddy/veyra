# Weave and the One-Tact Natural Shadow

## 1. Decision

`⊗` is **not primitive** in Core-0.

It is a derived **weave schema** built from stitch plus a choice of driver/test structure.

Reason: in one-tact arithmetic, multiplication is unambiguous; in multi-tact mode theory, many inequivalent weave operations become possible. Making one of them primitive too early would smuggle human arithmetic back into the system.

## 2. General substitution weave

A mode shadow is externally represented as a tact word.

Given:

- a driver mode `d = t_1 t_2 ... t_n`,
- a substitution map `σ` that sends every tact `t_i` to a mode,

we define:

`weave_σ(d) = σ(t_1) ⊙ σ(t_2) ⊙ ... ⊙ σ(t_n)`.

This is the most honest multi-tact weave: the driver pattern matters.

## 3. Binary length-weave

For the one-tact natural shadow, binary multiplication can be recovered by a coarse constant substitution:

`a ⊗_len b = a` repeated `len(b)` times.

Equivalently, `b` acts as the driver telling how many copies of `a` to stitch.

Human shadow:

If `a = τ^m` and `b = τ^n`, then:

`a ⊗_len b = (τ^m)^n = τ^(mn)`.

## 4. Why not primitive?

Because multi-tact worlds split multiplication into several possible operations:

1. **length-weave** — ignores driver symbols, keeps only driver length;
2. **ordered substitution** — driver symbols choose different replacement modes;
3. **cyclic weave** — driver is closed and rotations may be equivalent;
4. **bag weave** — driver order is ignored, only tact multiplicities matter;
5. **resonance weave** — only replacements preserving phase closure are admitted.

The alien part begins where these choices diverge.

## 5. One-tact theorem

**Theorem W-001 / THM-001.** In the one-nod one-tact shadow, Veyra modes with stitch and length-weave are isomorphic to natural numbers with addition and multiplication.

Map:

`Φ(τ^n) = n`.

Then:

- `Φ(0_V) = 0`,
- `Φ(1_V) = 1`,
- `Φ(a ⊕ b) = Φ(a) + Φ(b)`,
- `Φ(a ⊗_len b) = Φ(a) · Φ(b)`.

## 6. Proof sketch

Every one-tact mode is a finite word over a one-symbol alphabet `{τ}`. Such a word is uniquely `τ^n` for exactly one `n ∈ N`, including `n=0` for the silent word.

Stitch concatenates words, so:

`τ^m ⊙ τ^n = τ^(m+n)`.

Length-weave repeats `τ^m` exactly `n` times when driven by `τ^n`, so:

`τ^m ⊗_len τ^n = (τ^m)^n = τ^(mn)`.

Thus `Φ` preserves zero, one, addition, and multiplication.

## 7. New opening

The ordinary natural numbers are the collapsed one-tact case. Multi-tact mode theory is not merely arithmetic with colors; it is arithmetic after identity, multiplication, and primality split according to test family and weave schema.
