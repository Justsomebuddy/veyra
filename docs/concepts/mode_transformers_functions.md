# Mode Transformers: Veyra Functions

## Purpose

School mathematics treats a function as a rule `y=f(x)`. Veyra treats a function as a **transformer**: a rule that sends one trace or shadow to another while preserving, distorting, or hiding structure.

This is the bridge from arithmetic/algebra into graphs, powers, roots, exponentials, logarithms, geometry, and analysis.

## Definition

**DEF-059 — Mode transformer.**

A mode transformer is a rule:

```text
F : Shadow_A -> Shadow_B
```

that carries a declared observer context. Two transformers are not equal absolutely; they are echo-equivalent under a chosen family of input observers and output observers.

## Polynomial-backed transformer

The first executable school bridge uses ratio-polynomial schemas:

```text
F(x)=a0 ⊕ a1 x ⊕ ... ⊕ an x^n
```

This covers constant, affine, linear, quadratic, and higher polynomial school functions in the rational length-shadow layer.

## Composition

**DEF-060 — Transformer composition.**

Given transformers `F` and `G`, their composition is:

```text
(F∘G)(x)=F(G(x))
```

In Veyra terms, this is transformer nesting: the output shadow of `G` becomes the input trace for `F`.

Composition is the first function-level form of controlled observer chaining.

## Inverse transformer

**DEF-061 — Affine lift.**

For an affine transformer:

```text
F(x)=ax+b
```

with nonzero `a`, the inverse is:

```text
F^-1(y)=(y-b)/a
```

Veyra interprets this as a successful lift: the output shadow contains enough information to reconstruct the input shadow.

Constant functions have no inverse because they are hiding observers.

## Fixed point

**DEF-062 — Fixed residue.**

A fixed point is a ratio mode `x` such that:

```text
F(x) ⇔ x
```

For affine transformers this becomes a linear resonance constraint. A fixed point is a residue that survives transformation unchanged under the chosen observer.

## Graph shadow

**DEF-063 — Graph shadow.**

A graph is not primitive geometry. It is a finite observer table:

```text
{(x, F(x))}
```

under a chosen sample family. Continuous graph geometry is a later completion of this finite shadow.

## School concepts recovered

| School concept | Veyra view |
|---|---|
| function | mode transformer |
| graph | sampled observer table |
| composition | chained transformer |
| inverse | lift through non-hiding transformer |
| fixed point | stable residue under transformation |
| linear function | affine ratio transformer |
| polynomial function | ratio-polynomial transformer |

## Executable layer

Implemented in:

- `src/core/shadows/transformer.py`
- `src/core/shadows/category_like.py` for bounded object/morphism translation rows over transformer schemas
- `tests/shadows/test_transformer.py`
- `tests/shadows/test_category_like.py`

Current executable coverage:

- affine application;
- composition;
- affine inverse;
- affine fixed point;
- graph shadows;
- finite echo-equivalence of transformers.
- finite category-like object/morphism/invariant/universal-shadow rows.

## Next theory step

After transformers, the next school layers can be rebuilt as:

1. powers: repeated transformer/weave;
2. roots: inverse lift of power transformer;
3. exponential: self-similar transformer iteration;
4. logarithm: transition-count lift;
5. continuity: no observer jump under refinement;
6. derivative: local transition ratio;
7. integral: accumulated transition residue.
