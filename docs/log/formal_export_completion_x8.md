# Formal Export Completion X8

**Date:** 2026-08-06
**Status:** all nineteen X7 `prep-ready` theorem-card candidates now have checked Lean artifacts.
**Implementation:** `src/core/formal/{catalog,geometry_data,remaining_data,completion,remaining_completion}.py`, `src/core/certificates/formal_completion.py`.
**Certificate:** `formal_export_completion_x8`.

## Promoted candidates

X8 promotes all nineteen rows from the X7 stable-card preparation ledger. The prior fifteen retain their exact order; the final four append after `plane-relabel-composition`:

| Field | Value |
|---|---|
| theorem card | `cyclic-period` |
| source hook | `trig.cyclic_period` |
| backend | Lean |
| proof file | `proofs/lean/VeyraCyclic.lean` |
| Lean symbol | `THM_C001_cyclic_period` |
| status | `completed` |

| Field | Value |
|---|---|
| theorem card | `pythagorean-separation` |
| source hook | `geometry.pythagorean` |
| backend | Lean |
| proof file | `proofs/lean/VeyraGeometry.lean` |
| Lean symbol | `THM_G001_pythagorean_3_4_5` |
| status | `completed` |

| Field | Value |
|---|---|
| theorem card | `polynomial-identity` |
| source hook | `algebra.polynomial_identity` |
| backend | Lean |
| proof file | `proofs/lean/VeyraAlgebra.lean` |
| Lean symbol | `THM_A001_polynomial_identity_coeffs` |
| status | `completed` |

| Field | Value |
|---|---|
| theorem card | `polynomial-evaluation` |
| source hook | `algebra.polynomial_eval` |
| backend | Lean |
| proof file | `proofs/lean/VeyraAlgebra.lean` |
| Lean symbol | `THM_A002_polynomial_eval_at_3` |
| status | `completed` |

| Field | Value |
|---|---|
| theorem card | `linear-equation-solution` |
| source hook | `algebra.linear_solution` |
| backend | Lean |
| proof file | `proofs/lean/VeyraAlgebra.lean` |
| Lean symbol | `THM_A003_linear_equation_unique_solution` |
| status | `completed` |

| Field | Value |
|---|---|
| theorem card | `probability-complement` |
| source hook | `probability.complement` |
| backend | Lean |
| proof file | `proofs/lean/VeyraProbability.lean` |
| Lean symbol | `THM_P001_probability_complement_counts` |
| status | `completed` |

| Field | Value |
|---|---|
| theorem card | `probability-union` |
| source hook | `probability.union` |
| backend | Lean |
| proof file | `proofs/lean/VeyraProbability.lean` |
| Lean symbol | `THM_P002_probability_union_counts` |
| status | `completed` |

| Field | Value |
|---|---|
| theorem card | `probability-independence` |
| source hook | `probability.independence` |
| backend | Lean |
| proof file | `proofs/lean/VeyraProbability.lean` |
| Lean symbol | `THM_P003_probability_independence_counts` |
| status | `completed` |

| Field | Value |
|---|---|
| theorem card | `mean-balance` |
| source hook | `statistics.mean_balance` |
| backend | Lean |
| proof file | `proofs/lean/VeyraStatistics.lean` |
| Lean symbol | `THM_S001_mean_balance_1_3_5` |
| status | `completed` |

| Field | Value |
|---|---|
| theorem card | `binomial-symmetry` |
| source hook | `combinatorics.binomial_symmetry` |
| backend | Lean |
| proof file | `proofs/lean/VeyraCombinatorics.lean` |
| Lean symbol | `THM_B001_binomial_symmetry_6_2` |
| status | `completed` |

| Field | Value |
|---|---|
| theorem card | `variance-shift` |
| source hook | `statistics.variance_shift` |
| backend | Lean |
| proof file | `proofs/lean/VeyraStatistics.lean` |
| Lean symbol | `THM_S002_variance_shift_1_3_5_plus_10` |
| status | `completed` |

| Field | Value |
|---|---|
| theorem card | `sss-triangle` |
| source hook | `geometry.sss` |
| backend | Lean |
| proof file | `proofs/lean/VeyraGeometry.lean` |
| Lean symbol | `THM_G002_sss_side_squares_shift_10` |
| status | `completed` |

| Field | Value |
|---|---|
| theorem card | `sas-triangle` |
| source hook | `geometry.sas` |
| backend | Lean |
| proof file | `proofs/lean/VeyraGeometry.lean` |
| Lean symbol | `THM_G003_sas_anchor_3_4_dot_0` |
| status | `completed` |

| Field | Value |
|---|---|
| theorem card | `line-shell-intersection` |
| source hook | `geometry.line_shell` |
| backend | Lean |
| proof file | `proofs/lean/VeyraGeometry.lean` |
| Lean symbol | `THM_G004_diameter_shell_scaled_roots` |
| status | `completed` |

| Field | Value |
|---|---|
| theorem card | `plane-relabel-composition` |
| source hook | `geometry.relabel_compose` |
| backend | Lean |
| proof file | `proofs/lean/VeyraGeometry.lean` |
| Lean symbol | `THM_G005_quarter_turn_after_translation` |
| status | `completed` |

| theorem card | source hook | proof file | Lean symbol |
|---|---|---|---|
| `sampled-continuity` | `analysis.sampled_continuity` | `VeyraAlgebra.lean` | `THM_A004_sampled_continuity_double_0_five_points` |
| `drift-stability` | `analysis.drift_stability` | `VeyraAlgebra.lean` | `THM_A005_square_symmetric_drift_3_steps_1_2_3` |
| `area-additivity` | `analysis.area_additivity` | `VeyraAlgebra.lean` | `THM_A006_identity_midpoint_area_4_4_8` |
| `chord-symmetry` | `trig.chord_symmetry` | `VeyraCyclic.lean` | `THM_C002_chord_symmetry_12_0_3_9` |
The Lean statement is the finite phase-shadow identity:

```lean
theorem THM_C001_cyclic_period (phase modulus : Nat) :
    (phase + modulus) % modulus = phase % modulus
```

The geometry statement is the finite 3-4-5 separation identity:

```lean
theorem THM_G001_pythagorean_3_4_5 : (3 : Nat) * 3 + 4 * 4 = 5 * 5

theorem THM_G002_sss_side_squares_shift_10 :
    (((3 : Int) - 0) * (3 - 0) + (0 - 0) * (0 - 0) = 9 ∧
     (0 - 0) * (0 - 0) + (4 - 0) * (4 - 0) = 16 ∧
     ((0 : Int) - 3) * (0 - 3) + (4 - 0) * (4 - 0) = 25) ∧
    (((13 : Int) - 10) * (13 - 10) + (10 - 10) * (10 - 10) = 9 ∧
     (10 - 10) * (10 - 10) + (14 - 10) * (14 - 10) = 16 ∧
     ((10 : Int) - 13) * (10 - 13) + (14 - 10) * (14 - 10) = 25)

theorem THM_G003_sas_anchor_3_4_dot_0 :
    (((3 : Int) - 0) * (3 - 0) + (0 - 0) * (0 - 0) = 9 ∧
     (0 - 0) * (0 - 0) + (4 - 0) * (4 - 0) = 16 ∧
     (3 - 0) * (0 - 0) + (0 - 0) * (4 - 0) = 0) ∧
    (((13 : Int) - 10) * (13 - 10) + (10 - 10) * (10 - 10) = 9 ∧
     (10 - 10) * (10 - 10) + (14 - 10) * (14 - 10) = 16 ∧
     (13 - 10) * (10 - 10) + (10 - 10) * (14 - 10) = 0)

theorem THM_G004_diameter_shell_scaled_roots :
    ((-10 : Int) * 4 + 20 * 1 = (-5) * 4 ∧ (-5 : Int) * (-5) = 25) ∧
    ((-10 : Int) * 4 + 20 * 3 = 5 * 4 ∧ (5 : Int) * 5 = 25)

theorem THM_G005_quarter_turn_after_translation :
    ((-((3 : Int) - 2), 2 + 1) = (-1, 3)) ∧
    ((-(1 : Int), 3) = (-1, 3)) ∧
    ((-((3 : Int) - 2), 2 + 1) = (-(1 : Int), 3))
```

The algebra/probability statements are finite coefficient/evaluation/counting shadows:

```lean
theorem THM_A001_polynomial_identity_coeffs :
    poly_identity_left_coeffs = poly_identity_right_coeffs

theorem THM_A002_polynomial_eval_at_3 :
    ((3 : Int) + 1) * (3 - 1) = 8

theorem THM_A003_linear_equation_unique_solution :
    ∀ x : Int, 2 * x + 3 = 7 → x = 2

theorem THM_P001_probability_complement_counts :
    (1 : Nat) + 3 = 4

theorem THM_P002_probability_union_counts :
    (3 : Nat) + 1 = 2 + 2

theorem THM_P003_probability_independence_counts :
    (1 : Nat) * 4 = 2 * 2

theorem THM_S001_mean_balance_1_3_5 :
    ((1 : Int) - 3) + (3 - 3) + (5 - 3) = 0

theorem THM_B001_binomial_symmetry_6_2 :
    choose 6 2 = choose 6 4 ∧ choose 6 2 = 15 ∧ choose 6 4 = 15

theorem THM_S002_variance_shift_1_3_5_plus_10 :
    varianceNumerator135 = varianceNumerator111315 ∧
    varianceNumerator135 = 8 ∧ varianceNumerator111315 = 8

theorem THM_A004_sampled_continuity_double_0_five_points : -- fixed five points
theorem THM_A005_square_symmetric_drift_3_steps_1_2_3 : -- fixed anchor/steps
theorem THM_A006_identity_midpoint_area_4_4_8 : -- fixed three midpoint sums
theorem THM_C002_chord_symmetry_12_0_3_9 : -- fixed mod-12 mirror phases
```

## Boundary

These are formal theorem-card artifacts only. `cyclic-period` and `pythagorean-separation` retain their bounded Nat scopes. G002–G005 remain the declared closed coordinate fixtures, not general geometry. A004 is only the five displayed double-map samples; A005 is only the square-map symmetric quotients at anchor `3` and steps `1,2,3`; A006 is only the displayed identity-midpoint sums; C002 is only anchor `0 mod 12`, mirror phases `3,9`, and chord shadow `3/4`. They prove no general continuity, derivatives, integration, analysis, chord symmetry, or trigonometry. Probability rows remain canonical finite counts, S001/S002 fixed samples, and B001 only `choose 6 2 = choose 6 4 = 15`. No broader domain formalization follows.

After X8:

- X7 stable-card candidates: `19`;
- checked completed theorem-card candidates: `19`;
- unique checked Lean artifact paths: `6` (the algebra and probability rows share files);
- remaining prep-ready candidates: `0`;
- overclaim count: `0`.

Each catalog row pins the SHA-256 of the **entire Lean artifact byte content**. A readable digest mismatch is blocked before Lean is invoked. Trusted bytes are compiled from an isolated content-addressed capture, followed by canonical-path continuity recheck while reporting the canonical path. Exact declaration outside comments is also required; same-symbol `: True` and mid-check swap both block. Evaluation lookup lives in `formal_export_evaluator.py`; the public row class stays in `formal_export_completion.py`, with identical pickle identity, 13-key order, legacy imports, and caller-supplied checker patch semantics.

## Verification

```bash
elan run leanprover/lean4:v4.30.0-rc2 lean proofs/lean/VeyraCyclic.lean
elan run leanprover/lean4:v4.30.0-rc2 lean proofs/lean/VeyraGeometry.lean
elan run leanprover/lean4:v4.30.0-rc2 lean proofs/lean/VeyraAlgebra.lean
elan run leanprover/lean4:v4.30.0-rc2 lean proofs/lean/VeyraProbability.lean
elan run leanprover/lean4:v4.30.0-rc2 lean proofs/lean/VeyraStatistics.lean
elan run leanprover/lean4:v4.30.0-rc2 lean -DwarningAsError=true proofs/lean/VeyraCombinatorics.lean
PYTHONPATH=. python3 -m pytest -q tests/formal/test_formal_export_remaining_artifacts.py tests/formal/test_formal_export_remaining_completion.py tests/formal/test_formal_export_completion.py tests/formal/test_formal_export_evaluator.py tests/formal/test_formal_export_geometry_wave.py tests/formal/test_formal_export_probability_union.py tests/formal/test_formal_export_probability_independence.py tests/formal/test_formal_export_binomial_symmetry.py tests/formal/test_formal_export_variance_shift.py tests/formal/test_formal_export_prep.py
PYTHONPATH=. python3 -c 'from src.core.certificates.formal_completion import certify_formal_export_completion_x8 as c; assert c().passed'
```

Expected X8 signal: `formal_export_completion_x8` reports `completed=19 remaining=0 lean=6`; X8 still contributes one certificate, while separate G4 integration keeps the continuation suite at 76 and leaves the original frozen gate at 75.
