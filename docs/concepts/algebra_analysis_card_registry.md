# Algebra and analysis card registry

## Aim

The geometry registry proved that theorem cards can carry dependencies and obstructions.  This layer extends the same discipline to algebra and analysis: equations, polynomial identities, sampled continuity, drift stability, and finite area additivity.

## Algebra cards

### Linear equation solution

A linear constraint card wraps `solve_linear()`:

```text
A·x+B = C·x+D -> unique | identity | blocked
```

A unique solution is accepted only if the residual check returns zero.

### Polynomial identity

A polynomial identity is certified by coefficient echoes, not by sampled guessing:

```text
P ≡ Q iff all coefficient shadows match
```

### Polynomial evaluation

A polynomial evaluation card checks one executable value:

```text
P(a) ⇔ expected
```

This is useful for examples, counterexamples, and later Sage hooks.

## Analysis cards

### Sampled continuity

A continuity card promotes a finite tremor certificate to theorem-card shape:

```text
Echo_ε(F,a,r,n) -> stable | blocked
```

### Drift stability

A drift card compares several drift quotients across refinements:

```text
DQ_h1, DQ_h2, ... stable within tolerance
```

This is the finite-observer seed of derivative proofs.

### Area additivity

A finite area card checks adjacent interval additivity:

```text
Area([a,b]) + Area([b,c]) = Area([a,c])
```

For now this is an executable finite braid certificate.

## Registry expansion

`src/core/registry/theorem_registry.py` now includes:

- `algebra_analysis_theorem_specs()`
- `all_theorem_specs()`
- shared `SCHOOL_KNOWN_DEFS`

New specs:

1. `linear-equation-solution`
2. `polynomial-identity`
3. `polynomial-evaluation`
4. `sampled-continuity`
5. `drift-stability`
6. `area-additivity`

Together with five geometry specs, the school-core registry currently has 11 theorem/check objects.

## Executable layer

Implemented in `src/core/shadows/algebra_analysis_cards.py`:

- `linear_equation_card()`
- `polynomial_identity_card()`
- `polynomial_evaluation_card()`
- `continuity_card()`
- `drift_stability_card()`
- `area_additivity_card()`

Tests in `tests/shadows/test_algebra_analysis_cards.py` verify unique/identity/blocked equations, polynomial identity/evaluation, stable/blocked continuity, drift stability for square symmetric quotients, and midpoint area additivity.

## Why this matters

Veyra is no longer only building objects.  It is building a school replacement architecture where every theorem-like statement has:

- a named card;
- exact dependencies;
- accepted success relations;
- known obstruction modes;
- a future Sage hook.

## Next layer

Build a cross-domain curriculum map:

1. arithmetic -> algebra -> functions -> analysis -> geometry edges;
2. cards grouped by school-grade concept;
3. missing concept detector;
4. Sage export of specs and checks.
