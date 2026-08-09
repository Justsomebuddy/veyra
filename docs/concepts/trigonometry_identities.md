# Trigonometry identities seed

**Status:** executable seed, not full transcendental trigonometry.
**Implemented:** `src/core/shadows/trigonometry_identities.py`, `src/core/certificates/trigonometry.py`.

## Native intent

The `trigonometry-identities` row now has theorem-card certification for identity algebra over rational phase shadows.  A phase is represented as a `TrigIdentityVector(cos, sin)` where both coordinates are existing ratio modes.

This is deliberately a rational unit-circle seed: it certifies identity structure without pretending to compute arbitrary `sin(x)` or `cos(x)`.

## Executable objects

- `TrigIdentityVector(cos, sin, label)` — rational cosine/sine phase shadow.
- `trig_vector_from_ints(c, s, d)` — exact rational phase builder.
- `unit_identity_gap(v)` — computes `cos²+sin²-1`.
- `pythagorean_identity_card(v)` — checks the unit identity.
- `compose_phases(a, b)` — applies sum-angle formulas.
- `sum_angle_identity_card(a, b)` — checks sum-angle composition preserves unit identity.
- `double_angle_identity_card(v)` — checks self-composition against double-angle formulas.
- `inverse_phase_identity_card(v)` — checks phase plus inverse phase gives `(1,0)`.

## Certificate

`trigonometry_identities` checks:

1. a rational unit phase from the 3-4-5 triangle;
2. sum-angle composition against a 5-12-13 phase;
3. double-angle identity;
4. inverse phase identity;
5. the four-item identity checklist.

## What is still not claimed

- no transcendental sine/cosine evaluation;
- no inverse-trig solver;
- no trig-equation normal form;
- no analytic continuation or calculus bridge.

## Tests

- `tests/shadows/test_trigonometry_identities.py`
- `tests/shadows/test_certify.py`
- `tests/registry/test_curriculum_map.py`
