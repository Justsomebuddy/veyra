# Lean proof inventory

This directory contains 45 Lean source modules. The table is exhaustive: status refers to the public claim supported by the source, not merely to the presence of compilable declarations. Exact released declaration locations and dependencies are listed in `../../THEOREMS.md`.

## Status vocabulary

- `FORMALLY_PROVED` — the listed theorem or lemma has a Lean proof in this tree.
- `FORMAL_CONSTRUCTION` — the module defines formal objects used by proved declarations.
- `FORMALLY_PROVED + PUBLICLY_VALIDATED` — the proof is also exposed by the public certificate and release bundle.
- `INTERNAL_RESEARCH_CANDIDATE` — the Lean source is evidence for research, but no public theorem release follows.

## Complete source inventory

| Source | Mathematical role | Public status | Named `THM_*` declarations |
|---|---|---|---|
| `VeyraAlgebra.lean` | bounded algebra and finite analysis cards | `FORMALLY_PROVED` | `THM_A001_polynomial_identity_coeffs`, `THM_A002_polynomial_eval_at_3`, `THM_A003_linear_equation_unique_solution`, `THM_A004_sampled_continuity_double_0_five_points`, `THM_A005_square_symmetric_drift_3_steps_1_2_3`, `THM_A006_identity_midpoint_area_4_4_8` |
| `VeyraAllDepthFamily.lean` | periodic all-depth family and restriction laws | `FORMALLY_PROVED` | `THM_D3_LEAN_001_coordinate_total`, `THM_D3_LEAN_002_coordinate_member`, `THM_D3_LEAN_003_restriction_compatible`, `THM_D3_LEAN_004_relation_reflexive`, `THM_D3_LEAN_005_relation_symmetric`, `THM_D3_LEAN_006_relation_transitive`, `THM_D3_LEAN_007_restriction_identity`, `THM_D3_LEAN_008_restriction_composition`, `THM_D3_LEAN_009_restriction_congruence`, `THM_D3_LEAN_010_family_equivalence`, `THM_D3_LEAN_011_constructor_deterministic` |
| `VeyraClaimComposition.lean` | abstract exact finite-conjunction preservation, permutation, append, and explicit non-upgrade laws | `INTERNAL_RESEARCH_CANDIDATE` | none; intentionally not registered as a public `THM_*` claim |
| `VeyraCoherentTowers.lean` | conditional all-depth prefix recovery and uniqueness | `FORMALLY_PROVED` | `THM_I1_001_prefix_tower_recovers_stream`, `THM_I1_002_prefix_observers_determine_stream`, `THM_I1_003_prefix_conflict_blocks_global_stream`, `THM_I1_004_modular_addition_preserves_refinement` |
| `VeyraCombinatorics.lean` | fixed finite binomial card | `FORMALLY_PROVED` | `THM_B001_binomial_symmetry_6_2` |
| `VeyraCyclic.lean` | finite cyclic and chord cards | `FORMALLY_PROVED` | `THM_C001_cyclic_period`, `THM_C002_chord_symmetry_12_0_3_9` |
| `VeyraEcho.lean` | observer-indexed echo laws | `FORMALLY_PROVED` | `THM_F001_echo_reflexive`, `THM_F002_euclid_escape_mod` |
| `VeyraElaborationSemantics.lean` | R10 elaboration semantics | `FORMALLY_PROVED` | `THM_R10_001_image_semantics_equivalent`, `THM_R10_002_checked_elaboration_image_sound` |
| `VeyraGeneratedConfluence.lean` | ranked finite generated confluence | `FORMALLY_PROVED` | `THM_P3C1_001_ranked_local_to_generated_confluence` |
| `VeyraGeometry.lean` | finite geometry cards | `FORMALLY_PROVED` | `THM_G001_pythagorean_3_4_5`, `THM_G002_sss_side_squares_shift_10`, `THM_G003_sas_anchor_3_4_dot_0`, `THM_G004_diameter_shell_scaled_roots`, `THM_G005_quarter_turn_after_translation` |
| `VeyraIntrinsicObserverEcho.lean` | bounded R13 observer/echo bridge | `FORMALLY_PROVED` | `THM_R13_001_captured_unit_weave_accepted`, `THM_R13_002_unit_weave_semantics_and_image`, `THM_R13_003_ready_intrinsic_unit_weave_echo`, `THM_R13_004_tail_silence_two_sided_domain_blocked`, `THM_R13_005_crest_nonreflection` |
| `VeyraIntrinsicRuntime.lean` | fixed-anchor intrinsic runtime semantics | `FORMAL_CONSTRUCTION` | none |
| `VeyraIntrinsicVamBridge.lean` | bounded intrinsic VAM preservation bridge | `FORMALLY_PROVED` | `THM_R12_001_lower_recurrence_preserves_image`, `THM_R12_002_decode_lower_recurrence`, `THM_R12_003_lower_recurrence_injective`, `THM_R12_004_prefix_obstruction_transport`, `THM_R12_005_runPrimitive_transport`, `THM_R12_006_runObserver_transport`, `THM_R12_007_observe_transport`, `THM_R12_008_echo_transport`, `THM_R12_009_tail_silence_obstruction_transport` |
| `VeyraNativeArithmetic.lean` | native recurrence arithmetic | `FORMALLY_PROVED` | `THM_R3_001_stitch_associative`, `THM_R3_002_single_pulse_resonance` |
| `VeyraNativeSemantics.lean` | native constructor semantics | `FORMALLY_PROVED` | `THM_R4_001_empty_breath_blocks`, `THM_R4_002_closed_tact_is_mode`, `THM_R4_003_open_tact_blocks`, `THM_R4_004_two_tact_cycle_is_mode`, `THM_R4_005_kind_echoes_closed_modes`, `THM_R4_006_boundary_mismatch_blocks`, `THM_R4_007_anchored_silence_is_mode` |
| `VeyraObserverCore.lean` | typed observer calculus | `FORMAL_CONSTRUCTION` | none |
| `VeyraObserverDescent.lean` | conditional observer-descent partition spine | `FORMALLY_PROVED` | `THM_R16_001_residual_chain_partition`, `THM_R16_002_residual_synergy_disjoint`, `THM_R16_003_zero_synergy_chain_rule` |
| `VeyraObserverPatchAtlas.lean` | finite patch atlas/gluing criterion plus two nonpromoted uniqueness helpers | `FORMALLY_PROVED` | `THM_G4_001_exact_gluing_exists_iff_no_local_contradiction`, `THM_G4_002_triangle_singleton_overlaps_pass`, `THM_G4_003_triangle_exact_gluing_impossible` |
| `VeyraObserverProof.lean` | proof-grade observer laws | `FORMALLY_PROVED` | `THM_R11_001_ready_echo_characterization`, `THM_R11_002_ready_domain_reflexivity`, `THM_R11_003_r7_equality_implies_ready_echo`, `THM_R11_004_tail_silence_obstruction`, `THM_R11_005_both_side_echo_domain_obstruction`, `THM_R11_006_crest_noncollapse_witness` |
| `VeyraObserverSynthesis.lean` | observer-class closure and separation laws | `FORMALLY_PROVED` | `THM_R6_001_factor_blind`, `THM_R6_002_extension_separates` |
| `VeyraObserverSynthesisReplay.lean` | abstract deterministic replay, bijective task relabeling, and finite-catalog exhaustion boundary | `INTERNAL_RESEARCH_CANDIDATE` | none; abstract helpers only, with no concrete Rust theorem or public theorem-card registration |
| `VeyraObserverSynthesisV3.lean` | abstract canonical rebuild acceptance, explicit bijective task transport, and optimized/reference equivalence consequences | `INTERNAL_RESEARCH_CANDIDATE` | none; does not formalize Rust, cryptography, custody, concrete catalogs, or benchmark outcomes |
| `VeyraOptimizer.lean` | bounded local optimizer laws | `FORMAL_CONSTRUCTION` | none |
| `VeyraPadicAllDepthEquality.lean` | N4 all-projection scoped equality | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | `THM_P3N4_PREMISE_001_same_integer_coordinates` |
| `VeyraPadicCompletion.lean` | PΩ2 prime-power compatible-family completion | `FORMALLY_PROVED` | `THM_POMEGA2_001_prime_lower_bound`, `THM_POMEGA2_002_stage_modulus_divisibility`, `THM_POMEGA2_003_reduction_well_formed_congruence`, `THM_POMEGA2_004_reduction_identity`, `THM_POMEGA2_005_reduction_composition`, `THM_POMEGA2_006_carrier_presentation_compatible`, `THM_POMEGA2_007_universal_realization`, `THM_POMEGA2_008_coordinate_agreement`, `THM_POMEGA2_009_joint_separation`, `THM_POMEGA2_010_relative_uniqueness`, `THM_POMEGA2_011_zero_family_nonvacuity`, `THM_POMEGA2_012_one_family_formation`, `THM_POMEGA2_013_addition_closure`, `THM_POMEGA2_014_negation_additive_inverse`, `THM_POMEGA2_015_multiplication_closure`, `THM_POMEGA2_016_full_commutative_ring`, `THM_POMEGA2_017_ppcp_introduction` |
| `VeyraPadicFamilyIntroduction.lean` | N1 integer residue family | `FORMALLY_PROVED` | `THM_P3N1_001_integer_residue_total`, `THM_P3N1_002_integer_residue_reduction`, `THM_P3N1_003_integer_family_introduction` |
| `VeyraPadicLocalRealization.lean` | N3 local carrier realization | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | `THM_P3N3_001_realize_integer_family`, `THM_P3N3_002_realized_integer_family_coordinate`, `THM_P3N4_001_scoped_joint_separation` |
| `VeyraPrimePowerInformation.lean` | N6-W late-witness construction | `INTERNAL_RESEARCH_CANDIDATE` | `THM_P3N6W_001_exact_shape`, `THM_P3N6W_002_prefix`, `THM_P3N6W_003_later`, `THM_P3N6W_004_uniform` |
| `VeyraPrimePowerObserverActualization.lean` | N0 finite arithmetic actualization kernel | `INTERNAL_RESEARCH_CANDIDATE` | `THM_P3N0_001_zero_one_discrimination`, `THM_P3N0_002_strict_pair_coarse`, `THM_P3N0_003_strict_pair_next` |
| `VeyraPrimePowerProductiveBridge.lean` | A1b exact productive-family bridge | `FORMALLY_PROVED` | `THM_P3A1B_001_total`, `THM_P3A1B_002_deterministic`, `THM_P3A1B_003_process_coherent`, `THM_P3A1B_004_commutes` |
| `VeyraPrimePowerProductiveBridgePressure.lean` | countermodel pressure for generic productive bridges | `FORMALLY_PROVED` | `THM_P3A1B_PRESSURE_001_total`, `THM_P3A1B_PRESSURE_002_coherent` |
| `VeyraPrimePowerReductionNetwork.lean` | N2 prime-power reduction coherence | `FORMALLY_PROVED` | `THM_P3N2_001_reduction_identity`, `THM_P3N2_002_reduction_composition`, `THM_P3N2_003_reduction_witness_independent`, `THM_P3N2_004_path_equality`, `THM_P3N2_005_rho_square`, `THM_P3N2_006_separator_coarse`, `THM_P3N2_007_separator_fine` |
| `VeyraPrimePowerUnbounded.lean` | N6 finite-prefix invisibility and natural-power injection | `INTERNAL_RESEARCH_CANDIDATE` | `THM_P3N6_001_prefix_indistinguishable`, `THM_P3N6_002_next_depth_distinguishes`, `THM_P3N6_003_power_carrier_injective`, `THM_P3N6_004_power_carrier_eqc_injective`, `THM_P3N6_005_carrier_equality_adapter` |
| `VeyraProbability.lean` | fixed finite probability cards | `FORMALLY_PROVED` | `THM_P001_probability_complement_counts`, `THM_P002_probability_union_counts`, `THM_P003_probability_independence_counts` |
| `VeyraProductivityCounterpressure.lean` | finite-to-universal countermodels | `FORMALLY_PROVED` | `THM_D2_LEAN_001_finite_strict_descent`, `THM_D2_LEAN_002_no_infinite_nat_descent`, `THM_D2_LEAN_003a_self_mem`, `THM_D2_LEAN_003b_succ_subset`, `THM_D2_LEAN_003c_diagonal_absence` |
| `VeyraProofElaboration.lean` | source-bound R10 elaboration artifact | `FORMALLY_PROVED` | `THM_R10_003_elaborated_proof_accepted`, `THM_R10_004_elaborated_image_sound`, `THM_R10_005_structural_support_matches` |
| `VeyraProofKernel.lean` | R7 typed proof calculus | `FORMAL_CONSTRUCTION` | none |
| `VeyraProofModeTransport.lean` | R9 proof-to-mode transport | `FORMALLY_PROVED` | `THM_R9_008_R7_reflexive_resonance_transport` |
| `VeyraProofResonance.lean` | R7 resonance proof artifact | `FORMALLY_PROVED` | `THM_R7_002_resonance_proof_accepted`, `THM_R7_003_checked_reflexive_resonance`, `THM_R7_004_every_recurrence_resonates_with_itself` |
| `VeyraProofSoundness.lean` | R7 inference soundness | `FORMALLY_PROVED` | `THM_R7_001_check_sound` |
| `VeyraQuantumTensor.lean` | exact finite tensor and unitary laws | `FORMALLY_PROVED` | `THM_Q11_001_born_rule_normalized`, `THM_Q11_002_tensor_born_normalized`, `THM_Q11_003_tensor_unitary`, `THM_Q11_004_compose_unitary` |
| `VeyraRecurrenceModeBridge.lean` | recurrence/mode image bridge | `FORMALLY_PROVED` | `THM_R9_002_decode_encode`, `THM_R9_003_encode_decode`, `THM_R9_004_encode_injective`, `THM_R9_001_encode_mode_ready`, `THM_R9_005_stitch_preserved`, `THM_R9_006_weave_preserved`, `THM_R9_007_resonance_transport` |
| `VeyraStatistics.lean` | fixed finite statistics cards | `FORMALLY_PROVED` | `THM_S001_mean_balance_1_3_5`, `THM_S002_variance_shift_1_3_5_plus_10` |
| `VeyraStreamCompletion.lean` | PΩ1 stream completion relative to an explicit ledger | `FORMALLY_PROVED` | `THM_POMEGA1_001_truncation_identity`, `THM_POMEGA1_002_truncation_composition`, `THM_POMEGA1_003_rho_formation_congruence`, `THM_POMEGA1_004_stream_restriction_compatible`, `THM_POMEGA1_005_diagonal_realization_depth`, `THM_POMEGA1_006_universal_realization`, `THM_POMEGA1_007_coordinate_agreement`, `THM_POMEGA1_008_joint_separation`, `THM_POMEGA1_009_relative_uniqueness`, `THM_POMEGA1_010_nonvacuity_inhabitance`, `THM_POMEGA1_011_scp_introduction` |
| `VeyraTransportCoherence.lean` | P3-C2 typed-setoid transport coherence | `FORMALLY_PROVED` | `THM_P3C2_001_ranked_local_to_generated_transport`, `THM_P3C2_002_natop_reduction_identity`, `THM_P3C2_003_natop_reduction_composition` |

## Scope boundaries

- N3 and N4 are `FORMALLY_PROVED + PUBLICLY_VALIDATED`: their Lean modules, aliases, certificates, and release-bundle inclusion are present in this tree.
- N0, N6, and N6-W remain `INTERNAL_RESEARCH_CANDIDATE`. In particular, the four N6-W declarations do not establish a released unbounded-depth or cardinality theorem.
- PΩ1 and PΩ2 establish completed carriers only relative to their explicit formation rules and assumption ledgers; they do not establish physical, metaphysical, or foundation-independent infinity.
- A declaration stated under hypotheses proves the conditional implication only; it does not construct the hypotheses.

## Registry rules

1. Stable definition and theorem IDs must match `../../THEOREMS.md`.
2. New symbols must match `../../NOTATION.md`.
3. A source file must not be described as a public theorem unless its public status is recorded in the theorem registry.
4. A single bridge theorem does not imply a complete formalization of the surrounding prose theory.

## Whole-source compilation

Install `elan` and the exact reviewed toolchain, then compile the complete
45-source local import graph from the repository root:

```bash
elan toolchain install leanprover/lean4:v4.30.0-rc2
python scripts/check_lean_sources.py --jobs 8
```

The harness checks the exact Lean version, validates the 45-file inventory,
builds dependency layers, and writes temporary `.olean` files only under the
ignored `data/tmp/` tree. Independent modules in each layer compile in parallel.

This portable source-compilation check is not the same contract as renewing a
content-bound public certificate. Certificate renewal additionally binds exact
source bytes, the reviewed Linux x86_64 Lean binary/runtime closure, and the
Linux `inotify` guard; those hardened paths are intentionally unsupported on
macOS and Windows.
