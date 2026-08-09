# Sage Library Plan

## Goal

Build a SageMath library for Veyra that makes Veyra objects usable next to Sage rings, words, graphs, polynomials, finite fields, lattices, TDA, and symbolic processs.

Strategic target: **a full Veyra research laboratory for Sage, not a thin wrapper**.

The value target is 10/10 only if the package becomes a real mathematical playground: Sage-native objects, executable certificates, doctests, counterexample search, spectra, notebooks, and bridges to algebra, geometry, topology, and scientific studies.

## Difficulty

Core package wrapper: low/medium.

Real Sage-native library: high, because Sage wants coherent parents, coercions, categories, doctests, and exact algebraic semantics.

## Architecture

Package name: `veyra_sage`.

Layers:

1. `veyra_sage.core` — import/wrap current Python core.
2. `veyra_sage.parents` — Sage Parent/Element classes for modes, balances, ratios.
3. `veyra_sage.resonance` — exact/cyclic/approx/weighted/aura spectra.
4. `veyra_sage.algebra` — balance rings, ratio fields, polynomial forms.
5. `veyra_sage.certify` — executable certificate harness and doctests.
6. `veyra_sage.notebooks` — interactive school-replacement examples.

## Hard parts

- Sage coercion model.
- Multiple echo observers instead of one equality.
- Native ratio/scale operations without premature collapse to `QQ`.
- Proving operation compatibility under declared observers.
- Keeping Veyra semantics distinct from classical shadows.

## Success criterion

Sage users can run:

```python
from veyra_sage.all import *
M = VeyraModes(['a','b'])
ab = M('ab')
ab.resonance_spectrum(max_len=4)
Q = VeyraRatio(1, 2) + VeyraRatio(1, 3)
Q.certificate()
```

and get Veyra-native objects plus Sage-compatible exact shadows.

## Current implementation

Nucleus implemented in `veyra_sage`:

- `VeyraModes(alphabet)` as Sage/fallback Parent+Element for modes;
- `VeyraBalances(tact)` as Sage/fallback Parent+Element for balances;
- `VeyraRatios(tact)` as Sage/fallback Parent+Element for ratios;
- `VeyraPolynomials(tact, variable)` as Sage/fallback Parent+Element for polynomial ratio forms;
- raw ratio operations remain available before canonical shadow collapse;
- `sage_certificate_suite()` checks core certificates plus Sage mode/ratio behavior.

Detailed nucleus doc: `docs/log/sage_nucleus.md`.

## Direction statement

We are explicitly aiming for the **full research-lab version**:

- Sage-native Veyra parents/elements;
- Veyra methods preserved, not collapsed into classical Sage objects;
- exact shadows into Sage rings/fields/graphs only when declared;
- proof/certificate harness integrated with Sage doctests;
- large-scale experiment notebooks for school replacement, algebra, geometry, topology, and scientific structure discovery.

## Expansion process

We do **not** patch Sage core directly while Veyra is unstable. Expansion happens in layers:

1. `src/core` receives Veyra-native definitions and executable certificates.
2. `veyra_sage` exposes only stabilized pieces as Sage/fallback parents and elements.
3. `scripts/sage_smoke.py`, pytest, and future doctests certify behavior in the active SageMath environment.
4. Notebooks/lab examples demonstrate research studies.
5. Only mature, stable interfaces may later become a standalone Sage package or upstream Sage contribution.

Exception: if a feature is purely Sage-experimental, it may prototype first inside `veyra_sage`, but it must later be either pulled down into `src/core` or marked as Sage-only experiment.
