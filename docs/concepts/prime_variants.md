# Prime Variants in Veyra

## 1. Why prime splits

In ordinary arithmetic, "prime" means one thing because there is one dominant multiplication and one dominant equality.

In Veyra, identity and weave are test/schema-indexed, so primality splits.

## 2. Variant P1: one-tact numeric prime

A one-tact mode `τ^n` is **numeric-prime** if `n` is an ordinary prime number.

Examples:

- `τ²`, `τ³`, `τ⁵` are numeric-prime.
- `τ⁴` is not.

This is the shadow of classical prime numbers.

## 3. Variant P2: ordered primitive rhythm

A mode word `w` is **ordered-primitive** if it is not a repetition of a shorter non-silent word.

Examples:

- `ab` is ordered-primitive.
- `abab` is not: `(ab)^2`.
- `aaaa` is not: `a^4`.

Important divergence:

- `τ²` is numeric-prime, but not ordered-primitive because `τ² = ττ`.

Thus numeric prime and primitive rhythm are different axes.

## 4. Variant P3: cyclic primitive rhythm

A closed mode is **cyclic-primitive** if its cyclic rotation class is not a repetition of a shorter cycle.

Examples:

- `ab`, `ba` are the same cyclic primitive class under `T_cycle`.
- `abab`, `baba` are not cyclic-primitive because they repeat cycle `ab`.

## 5. Variant P4: resonance-prime

A mode is **resonance-prime relative to a resonance relation `R`** if it has no non-unit proper resonant submode under `R`.

For the first ordered repetition relation:

- `ab` is resonance-prime.
- `abab` is not, because `ab` resonates inside it.

This is not final. Richer resonance relations may include cyclic resonance, phase obstruction, or schema-compatible weave decomposition.

## 6. First insight

Classical primes are not abolished. They are revealed as a narrow one-tact shadow.

The larger Veyra landscape has at least three independent notions:

1. **quantity indecomposability** — numeric prime;
2. **rhythm indecomposability** — primitive word/cycle;
3. **resonance indecomposability** — no admitted tiling/decomposition.

## 7. Research task

Build tables of small modes showing where these notions agree and disagree.

Expected first divergence table:

| Mode | Numeric-prime | Ordered-primitive | Cyclic-primitive | Ordered resonance-prime |
|---|---:|---:|---:|---:|
| `τ²` | yes | no | no | no/depends unit convention |
| `ab` | no | yes | yes | yes |
| `abab` | no | no | no | no |
| `aba` | no | yes | yes | yes |
