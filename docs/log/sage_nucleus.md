# Sage Nucleus

## Status

Implemented as the first executable nucleus of the Veyra Sage research laboratory.

This is not a thin conversion to classical Sage objects. The package keeps Veyra-native objects first, then exposes exact shadows only through explicit methods.

## Package

`veyra_sage` currently exports:

- `VeyraModes(alphabet)` — Sage/fallback parent for closed modes.
- `VeyraBalances(tact='τ')` — Sage/fallback parent for balance modes.
- `VeyraRatios(tact='τ')` — Sage/fallback parent for ratio modes.
- `VeyraPolynomials(tact='τ', variable='x')` — Sage/fallback parent for polynomial ratio forms.
- `sage_certificate_suite()` — core certificate summary plus Sage parent checks.

## Mode parent

```python
from veyra_sage.all import VeyraModes
M = VeyraModes('abc')
ab = M('ab')
ab.cyclic_resonates(M('baba'))
ab.weighted_resonates(M('abac'), budget=0.5)
```

Mode elements preserve Veyra methods:

- echo keys by observer family;
- cyclic resonance;
- resonance profiles;
- aura-derived costs;
- weighted resonance.

## Balance parent

```python
from veyra_sage.all import VeyraBalances
B = VeyraBalances('τ')
(B(3) + B(-2)).net_length()  # 1
(B(3) - B(5)).net_length()   # -2
```

Balance elements preserve arising/fading signed structure and expose explicit length shadows through `.net_length()`.

## Ratio parent

```python
from fractions import Fraction
from veyra_sage.all import VeyraRatios
Q = VeyraRatios('τ')
half = Q(1, 2)
third = Q(Fraction(1, 3))
(half + third).shadow()      # 5/6
half.raw_add(third).word     # uncollapsed cross-scale structure
(half * third).shadow()      # 1/6
```

Ratio elements expose two layers:

1. native/raw operations preserving balance/scale structure;
2. canonical exact shadows through declared length observer.

## Polynomial parent

```python
from veyra_sage.all import VeyraPolynomials
P = VeyraPolynomials('τ', 'x')
product = P([1, 1]) * P([-1, 1])
product.coefficient_shadows()  # [-1, 0, 1]
product.evaluate(3).shadow()   # 8
product.derivative().coefficient_shadows()  # [0, 2]
```

Polynomial elements preserve Veyra ratio coefficients and expose exact coefficient/value shadows only through explicit methods.

## Certificate

The Sage certificate passes when:

- all core Veyra certificates pass;
- mode parent methods recover cyclic and weighted resonance;
- balance parent arithmetic recovers `3 + (-2) = 1` through balance stitch/opposition;
- ratio parent arithmetic recovers `1/2 + 1/3 = 5/6` and `1/2 * 1/3 = 1/6` through Veyra ratio methods;
- polynomial parent arithmetic recovers `(x+1)(x-1)=x²-1`, evaluation at `x=3`, and derivative shadow.

## Verification

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/sage/test_veyra_sage.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/sage_smoke.py
PYTHONDONTWRITEBYTECODE=1 python scripts/sage_smoke.py
```

Expected current result: full tests pass 104/104, Python smoke passes, SageMath 10.7 smoke passes, and `sage_available=True`.

## Next

- Add Sage doctests and notebook examples.
- Add bridges into Sage graphs/words/rings only as declared shadows.

## Doctest examples

`veyra_sage/examples.py` contains executable examples for modes, balances, ratios, and polynomials.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/sage_doctest.py
PYTHONDONTWRITEBYTECODE=1 python scripts/sage_doctest.py
```

Current expected result: 15 attempted, 0 failed.
