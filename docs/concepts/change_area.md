# Veyra change and area layer

## Aim

This layer extends completion into the first analysis tools: continuity, local change, and finite area.  The primitive is not a human graph curve.  The primitive is a **tremor test**: perturb an input mode and observe whether the output shadow jumps, drifts, or accumulates.

## Definitions

### Input tremor

An input tremor around anchor `a` is a symmetric finite sample family:

```text
Tremor(a,r,n) = { a + (i/n)·r | -n ≤ i ≤ n }
```

Here `r` is a rational radius and `n` is a finite observer budget.

### Echo-continuity certificate

A rule `F` is echo-continuous at anchor `a` under `(r, ε, n)` when every sampled tremor output remains within `ε` of `F(a)`.

```text
max_i |F(a+(i/n)r)-F(a)| ≤ ε
```

This is deliberately a certificate, not a full theorem of continuity.  It is a Veyra no-jump witness.

### Drift quotient

A local change shadow divides output drift by input drift:

```text
DQ⁺(F,a,h) = (F(a+h)-F(a))/h
DQ±(F,a,h) = (F(a+h)-F(a-h))/(2h)
```

As `h` refines, a stable drift family becomes the Veyra bridge to derivative.

### Area braid

Area is accumulated from equal-width strips:

```text
Area(F,[l,u],N) = Σ F(sample_i)·((u-l)/N)
```

The strip sample can be left, right, or midpoint.  Later layers will replace finite strips by completion certificates.

## School-program coverage

| School concept | Veyra abstraction | Status |
|---|---|---|
| continuity | sampled echo-continuity / no-jump certificate | executable finite certificate |
| derivative | drift quotient refinement family | executable seed |
| slope of line | drift quotient of affine transformer | exact |
| tangent estimate | symmetric drift quotient | executable seed |
| definite integral | finite area braid | executable finite shadow |
| rectangle/midpoint sums | strip accumulation observers | exact finite implementation |

## Why this is Veyra-native

Traditional calculus starts from ideal points on a curve.  Veyra starts from observer-limited tremors and asks what survives refinement.  A derivative is not first a limit formula; it is a stable drift signature.  An integral is not first a region under a curve; it is a stable accumulation signature.

## Executable layer

Implemented in `src/core/shadows/change.py`:

- `tremor_points()` — finite symmetric input perturbation family.
- `sampled_continuity()` — no-jump certificate.
- `difference_quotient()` — forward drift quotient.
- `symmetric_difference_quotient()` — symmetric drift quotient.
- `riemann_area()` — finite strip area shadow.

Tests in `tests/shadows/test_change.py` verify:

1. affine transformer has stable sampled continuity;
2. jump rule is detected as `echo-jump`;
3. square transformer has forward and symmetric drift quotients;
4. midpoint area of identity on `[0,1]` equals `1/2`.

## Current limitation

This is still finite-observer analysis.  The next step is a completion theorem layer: when a refinement family of certificates becomes stable, Veyra may promote it into a stronger continuity/change/area theorem.

## Next layer

Build geometry from the same primitives:

1. point = anchored observation event;
2. segment = bounded tremor corridor;
3. angle/shape = invariant under allowed transformer families;
4. coordinate geometry = secondary shadow, not primitive ontology.
