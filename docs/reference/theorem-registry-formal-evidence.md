# Exact formal evidence and bounded-card status

Part of the public [Theorem and Definition Registry](../../THEOREMS.md).

## Exact formal evidence index

Each row names one Lean declaration, its publication status, direct named theorem
or imported-module dependencies, and its source location. A dependency entry of
“same-module definitions only” means that the declaration invokes no other
`THM_*` declaration and imports no local Veyra module.

| Formal ID | Lean kind | Publication status | Direct theorem/module dependencies | Proof location |
|---|---|---|---|---|
| `THM_A001_polynomial_identity_coeffs` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraAlgebra.lean:7` |
| `THM_A002_polynomial_eval_at_3` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraAlgebra.lean:14` |
| `THM_A003_linear_equation_unique_solution` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraAlgebra.lean:19` |
| `THM_A004_sampled_continuity_double_0_five_points` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraAlgebra.lean:27` |
| `THM_A005_square_symmetric_drift_3_steps_1_2_3` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraAlgebra.lean:35` |
| `THM_A006_identity_midpoint_area_4_4_8` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraAlgebra.lean:44` |
| `THM_D3_LEAN_001_coordinate_total` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraAllDepthFamily.lean:30` |
| `THM_D3_LEAN_002_coordinate_member` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraAllDepthFamily.lean:35` |
| `THM_D3_LEAN_003_restriction_compatible` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraAllDepthFamily.lean:40` |
| `THM_D3_LEAN_004_relation_reflexive` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraAllDepthFamily.lean:47` |
| `THM_D3_LEAN_005_relation_symmetric` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraAllDepthFamily.lean:52` |
| `THM_D3_LEAN_006_relation_transitive` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraAllDepthFamily.lean:57` |
| `THM_D3_LEAN_007_restriction_identity` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraAllDepthFamily.lean:63` |
| `THM_D3_LEAN_008_restriction_composition` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraAllDepthFamily.lean:69` |
| `THM_D3_LEAN_009_restriction_congruence` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraAllDepthFamily.lean:75` |
| `THM_D3_LEAN_010_family_equivalence` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraAllDepthFamily.lean:81` |
| `THM_D3_LEAN_011_constructor_deterministic` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraAllDepthFamily.lean:95` |
| `THM_I1_001_prefix_tower_recovers_stream` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraCoherentTowers.lean:22` |
| `THM_I1_002_prefix_observers_determine_stream` | `theorem` | `FORMALLY_PROVED` | `THM_I1_001_prefix_tower_recovers_stream` | `proofs/lean/VeyraCoherentTowers.lean:34` |
| `THM_I1_003_prefix_conflict_blocks_global_stream` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraCoherentTowers.lean:54` |
| `THM_I1_004_modular_addition_preserves_refinement` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraCoherentTowers.lean:67` |
| `THM_B001_binomial_symmetry_6_2` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraCombinatorics.lean:11` |
| `THM_C001_cyclic_period` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraCyclic.lean:5` |
| `THM_C002_chord_symmetry_12_0_3_9` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraCyclic.lean:13` |
| `THM_F001_echo_reflexive` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraEcho.lean:9` |
| `THM_F002_euclid_escape_mod` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraEcho.lean:16` |
| `THM_R10_001_image_semantics_equivalent` | `theorem` | `FORMALLY_PROVED` | `THM_R9_007_resonance_transport` | `proofs/lean/VeyraElaborationSemantics.lean:30` |
| `THM_R10_002_checked_elaboration_image_sound` | `theorem` | `FORMALLY_PROVED` | `THM_R10_001_image_semantics_equivalent`, `THM_R7_001_check_sound` | `proofs/lean/VeyraElaborationSemantics.lean:48` |
| `THM_P3C1_001_ranked_local_to_generated_confluence` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraGeneratedConfluence.lean:38` |
| `THM_G001_pythagorean_3_4_5` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraGeometry.lean:5` |
| `THM_G002_sss_side_squares_shift_10` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraGeometry.lean:10` |
| `THM_G003_sas_anchor_3_4_dot_0` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraGeometry.lean:21` |
| `THM_G004_diameter_shell_scaled_roots` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraGeometry.lean:32` |
| `THM_G005_quarter_turn_after_translation` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraGeometry.lean:39` |
| `THM_R13_001_captured_unit_weave_accepted` | `theorem` | `FORMALLY_PROVED` | `THM_R7_001_check_sound` | `proofs/lean/VeyraIntrinsicObserverEcho.lean:29` |
| `THM_R13_002_unit_weave_semantics_and_image` | `theorem` | `FORMALLY_PROVED` | `THM_R9_006_weave_preserved` | `proofs/lean/VeyraIntrinsicObserverEcho.lean:42` |
| `THM_R13_003_ready_intrinsic_unit_weave_echo` | `theorem` | `FORMALLY_PROVED` | `THM_R13_002_unit_weave_semantics_and_image`, `THM_R12_008_echo_transport`, `THM_R11_002_ready_domain_reflexivity` | `proofs/lean/VeyraIntrinsicObserverEcho.lean:52` |
| `THM_R13_004_tail_silence_two_sided_domain_blocked` | `theorem` | `FORMALLY_PROVED` | `THM_R11_005_both_side_echo_domain_obstruction`, `THM_R13_002_unit_weave_semantics_and_image`, `THM_R12_008_echo_transport` | `proofs/lean/VeyraIntrinsicObserverEcho.lean:76` |
| `THM_R13_005_crest_nonreflection` | `theorem` | `FORMALLY_PROVED` | `THM_R11_006_crest_noncollapse_witness`, `THM_R12_008_echo_transport`, `THM_R12_003_lower_recurrence_injective` | `proofs/lean/VeyraIntrinsicObserverEcho.lean:97` |
| `THM_R12_001_lower_recurrence_preserves_image` | `theorem` | `FORMALLY_PROVED` | imports `VeyraObserverProof` | `proofs/lean/VeyraIntrinsicVamBridge.lean:273` |
| `THM_R12_002_decode_lower_recurrence` | `theorem` | `FORMALLY_PROVED` | imports `VeyraObserverProof` | `proofs/lean/VeyraIntrinsicVamBridge.lean:275` |
| `THM_R12_003_lower_recurrence_injective` | `theorem` | `FORMALLY_PROVED` | imports `VeyraObserverProof` | `proofs/lean/VeyraIntrinsicVamBridge.lean:277` |
| `THM_R12_004_prefix_obstruction_transport` | `theorem` | `FORMALLY_PROVED` | imports `VeyraObserverProof` | `proofs/lean/VeyraIntrinsicVamBridge.lean:279` |
| `THM_R12_005_runPrimitive_transport` | `theorem` | `FORMALLY_PROVED` | imports `VeyraObserverProof` | `proofs/lean/VeyraIntrinsicVamBridge.lean:282` |
| `THM_R12_006_runObserver_transport` | `theorem` | `FORMALLY_PROVED` | imports `VeyraObserverProof` | `proofs/lean/VeyraIntrinsicVamBridge.lean:286` |
| `THM_R12_007_observe_transport` | `theorem` | `FORMALLY_PROVED` | imports `VeyraObserverProof` | `proofs/lean/VeyraIntrinsicVamBridge.lean:290` |
| `THM_R12_008_echo_transport` | `theorem` | `FORMALLY_PROVED` | imports `VeyraObserverProof` | `proofs/lean/VeyraIntrinsicVamBridge.lean:294` |
| `THM_R12_009_tail_silence_obstruction_transport` | `theorem` | `FORMALLY_PROVED` | imports `VeyraObserverProof` | `proofs/lean/VeyraIntrinsicVamBridge.lean:298` |
| `THM_R3_001_stitch_associative` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraNativeArithmetic.lean:64` |
| `THM_R3_002_single_pulse_resonance` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraNativeArithmetic.lean:68` |
| `THM_R4_001_empty_breath_blocks` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraNativeSemantics.lean:108` |
| `THM_R4_002_closed_tact_is_mode` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraNativeSemantics.lean:112` |
| `THM_R4_003_open_tact_blocks` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraNativeSemantics.lean:119` |
| `THM_R4_004_two_tact_cycle_is_mode` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraNativeSemantics.lean:125` |
| `THM_R4_005_kind_echoes_closed_modes` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraNativeSemantics.lean:132` |
| `THM_R4_006_boundary_mismatch_blocks` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraNativeSemantics.lean:140` |
| `THM_R4_007_anchored_silence_is_mode` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraNativeSemantics.lean:147` |
| `THM_R16_001_residual_chain_partition` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraObserverDescent.lean:37` |
| `THM_R16_002_residual_synergy_disjoint` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraObserverDescent.lean:53` |
| `THM_R16_003_zero_synergy_chain_rule` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraObserverDescent.lean:65` |
| `THM_G4_001_exact_gluing_exists_iff_no_local_contradiction` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraObserverPatchAtlas.lean:59` |
| `THM_G4_002_triangle_singleton_overlaps_pass` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraObserverPatchAtlas.lean:106` |
| `THM_G4_003_triangle_exact_gluing_impossible` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraObserverPatchAtlas.lean:122` |
| `THM_R11_001_ready_echo_characterization` | `theorem` | `FORMALLY_PROVED` | imports `VeyraObserverCore`, `VeyraProofSoundness` | `proofs/lean/VeyraObserverProof.lean:8` |
| `THM_R11_002_ready_domain_reflexivity` | `theorem` | `FORMALLY_PROVED` | imports `VeyraObserverCore`, `VeyraProofSoundness` | `proofs/lean/VeyraObserverProof.lean:35` |
| `THM_R11_003_r7_equality_implies_ready_echo` | `theorem` | `FORMALLY_PROVED` | `THM_R7_001_check_sound`, `THM_R11_002_ready_domain_reflexivity` | `proofs/lean/VeyraObserverProof.lean:42` |
| `THM_R11_004_tail_silence_obstruction` | `theorem` | `FORMALLY_PROVED` | imports `VeyraObserverCore`, `VeyraProofSoundness` | `proofs/lean/VeyraObserverProof.lean:55` |
| `THM_R11_005_both_side_echo_domain_obstruction` | `theorem` | `FORMALLY_PROVED` | imports `VeyraObserverCore`, `VeyraProofSoundness` | `proofs/lean/VeyraObserverProof.lean:61` |
| `THM_R11_006_crest_noncollapse_witness` | `theorem` | `FORMALLY_PROVED` | imports `VeyraObserverCore`, `VeyraProofSoundness` | `proofs/lean/VeyraObserverProof.lean:69` |
| `THM_R6_001_factor_blind` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraObserverSynthesis.lean:2` |
| `THM_R6_002_extension_separates` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraObserverSynthesis.lean:10` |
| `THM_P3N4_PREMISE_001_same_integer_coordinates` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | imports `VeyraPadicLocalRealization` | `proofs/lean/VeyraPadicAllDepthEquality.lean:6` |
| `THM_POMEGA2_001_prime_lower_bound` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | imports `Std.Tactic`, `Init.GrindInstances.Ring.Fin` | `proofs/lean/VeyraPadicCompletion.lean:177` |
| `THM_POMEGA2_002_stage_modulus_divisibility` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | imports `Std.Tactic`, `Init.GrindInstances.Ring.Fin` | `proofs/lean/VeyraPadicCompletion.lean:179` |
| `THM_POMEGA2_003_reduction_well_formed_congruence` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | imports `Std.Tactic`, `Init.GrindInstances.Ring.Fin` | `proofs/lean/VeyraPadicCompletion.lean:184` |
| `THM_POMEGA2_004_reduction_identity` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | imports `Std.Tactic`, `Init.GrindInstances.Ring.Fin` | `proofs/lean/VeyraPadicCompletion.lean:190` |
| `THM_POMEGA2_005_reduction_composition` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | `THM_POMEGA2_002_stage_modulus_divisibility` | `proofs/lean/VeyraPadicCompletion.lean:195` |
| `THM_POMEGA2_006_carrier_presentation_compatible` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | imports `Std.Tactic`, `Init.GrindInstances.Ring.Fin` | `proofs/lean/VeyraPadicCompletion.lean:202` |
| `THM_POMEGA2_007_universal_realization` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | imports `Std.Tactic`, `Init.GrindInstances.Ring.Fin` | `proofs/lean/VeyraPadicCompletion.lean:206` |
| `THM_POMEGA2_008_coordinate_agreement` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | imports `Std.Tactic`, `Init.GrindInstances.Ring.Fin` | `proofs/lean/VeyraPadicCompletion.lean:210` |
| `THM_POMEGA2_009_joint_separation` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | imports `Std.Tactic`, `Init.GrindInstances.Ring.Fin` | `proofs/lean/VeyraPadicCompletion.lean:214` |
| `THM_POMEGA2_010_relative_uniqueness` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | `THM_POMEGA2_009_joint_separation` | `proofs/lean/VeyraPadicCompletion.lean:219` |
| `THM_POMEGA2_011_zero_family_nonvacuity` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | imports `Std.Tactic`, `Init.GrindInstances.Ring.Fin` | `proofs/lean/VeyraPadicCompletion.lean:225` |
| `THM_POMEGA2_012_one_family_formation` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | imports `Std.Tactic`, `Init.GrindInstances.Ring.Fin` | `proofs/lean/VeyraPadicCompletion.lean:228` |
| `THM_POMEGA2_013_addition_closure` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | imports `Std.Tactic`, `Init.GrindInstances.Ring.Fin` | `proofs/lean/VeyraPadicCompletion.lean:232` |
| `THM_POMEGA2_014_negation_additive_inverse` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | `THM_POMEGA2_009_joint_separation` | `proofs/lean/VeyraPadicCompletion.lean:237` |
| `THM_POMEGA2_015_multiplication_closure` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | imports `Std.Tactic`, `Init.GrindInstances.Ring.Fin` | `proofs/lean/VeyraPadicCompletion.lean:244` |
| `THM_POMEGA2_016_full_commutative_ring` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | `THM_POMEGA2_009_joint_separation` | `proofs/lean/VeyraPadicCompletion.lean:249` |
| `THM_POMEGA2_017_ppcp_introduction` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | `THM_POMEGA2_001_prime_lower_bound`, `THM_POMEGA2_002_stage_modulus_divisibility`, `THM_POMEGA2_003_reduction_well_formed_congruence`, `THM_POMEGA2_004_reduction_identity`, `THM_POMEGA2_005_reduction_composition`, `THM_POMEGA2_006_carrier_presentation_compatible`, `THM_POMEGA2_007_universal_realization`, `THM_POMEGA2_008_coordinate_agreement`, `THM_POMEGA2_009_joint_separation`, `THM_POMEGA2_010_relative_uniqueness`, `THM_POMEGA2_011_zero_family_nonvacuity`, `THM_POMEGA2_012_one_family_formation`, `THM_POMEGA2_013_addition_closure`, `THM_POMEGA2_014_negation_additive_inverse`, `THM_POMEGA2_015_multiplication_closure`, `THM_POMEGA2_016_full_commutative_ring` | `proofs/lean/VeyraPadicCompletion.lean:261` |
| `THM_P3N1_001_integer_residue_total` | `theorem` | `FORMALLY_PROVED` | imports `VeyraPadicCompletion` | `proofs/lean/VeyraPadicFamilyIntroduction.lean:13` |
| `THM_P3N1_002_integer_residue_reduction` | `theorem` | `FORMALLY_PROVED` | imports `VeyraPadicCompletion` | `proofs/lean/VeyraPadicFamilyIntroduction.lean:21` |
| `THM_P3N1_003_integer_family_introduction` | `theorem` | `FORMALLY_PROVED` | imports `VeyraPadicCompletion` | `proofs/lean/VeyraPadicFamilyIntroduction.lean:52` |
| `THM_P3N3_001_realize_integer_family` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | `THM_POMEGA2_007_universal_realization` | `proofs/lean/VeyraPadicLocalRealization.lean:6` |
| `THM_P3N3_002_realized_integer_family_coordinate` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | `THM_P3N3_001_realize_integer_family` | `proofs/lean/VeyraPadicLocalRealization.lean:13` |
| `THM_P3N4_001_scoped_joint_separation` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | `THM_POMEGA2_009_joint_separation` | `proofs/lean/VeyraPadicLocalRealization.lean:21` |
| `THM_P3N6W_001_exact_shape` | `theorem` | `INTERNAL_RESEARCH_CANDIDATE` | imports `VeyraPrimePowerUnbounded` | `proofs/lean/VeyraPrimePowerInformation.lean:36` |
| `THM_P3N6W_002_prefix` | `theorem` | `INTERNAL_RESEARCH_CANDIDATE` | imports `VeyraPrimePowerUnbounded` | `proofs/lean/VeyraPrimePowerInformation.lean:46` |
| `THM_P3N6W_003_later` | `theorem` | `INTERNAL_RESEARCH_CANDIDATE` | imports `VeyraPrimePowerUnbounded` | `proofs/lean/VeyraPrimePowerInformation.lean:54` |
| `THM_P3N6W_004_uniform` | `theorem` | `INTERNAL_RESEARCH_CANDIDATE` | imports `VeyraPrimePowerUnbounded` | `proofs/lean/VeyraPrimePowerInformation.lean:65` |
| `THM_P3N0_001_zero_one_discrimination` | `theorem` | `INTERNAL_RESEARCH_CANDIDATE` | imports `VeyraPrimePowerReductionNetwork` | `proofs/lean/VeyraPrimePowerObserverActualization.lean:13` |
| `THM_P3N0_002_strict_pair_coarse` | `theorem` | `INTERNAL_RESEARCH_CANDIDATE` | `THM_P3N2_006_separator_coarse` | `proofs/lean/VeyraPrimePowerObserverActualization.lean:26` |
| `THM_P3N0_003_strict_pair_next` | `theorem` | `INTERNAL_RESEARCH_CANDIDATE` | `THM_P3N2_007_separator_fine` | `proofs/lean/VeyraPrimePowerObserverActualization.lean:33` |
| `THM_P3A1B_001_total` | `theorem` | `FORMALLY_PROVED` | imports `VeyraPadicFamilyIntroduction` | `proofs/lean/VeyraPrimePowerProductiveBridge.lean:16` |
| `THM_P3A1B_002_deterministic` | `theorem` | `FORMALLY_PROVED` | imports `VeyraPadicFamilyIntroduction` | `proofs/lean/VeyraPrimePowerProductiveBridge.lean:22` |
| `THM_P3A1B_003_process_coherent` | `theorem` | `FORMALLY_PROVED` | imports `VeyraPadicFamilyIntroduction` | `proofs/lean/VeyraPrimePowerProductiveBridge.lean:31` |
| `THM_P3A1B_004_commutes` | `theorem` | `FORMALLY_PROVED` | imports `VeyraPadicFamilyIntroduction` | `proofs/lean/VeyraPrimePowerProductiveBridge.lean:59` |
| `THM_P3A1B_PRESSURE_001_total` | `theorem` | `FORMALLY_PROVED` | `THM_P3A1B_001_total` | `proofs/lean/VeyraPrimePowerProductiveBridgePressure.lean:14` |
| `THM_P3A1B_PRESSURE_002_coherent` | `theorem` | `FORMALLY_PROVED` | `THM_P3A1B_003_process_coherent` | `proofs/lean/VeyraPrimePowerProductiveBridgePressure.lean:19` |
| `THM_P3N2_001_reduction_identity` | `theorem` | `FORMALLY_PROVED` | `THM_POMEGA2_004_reduction_identity` | `proofs/lean/VeyraPrimePowerReductionNetwork.lean:45` |
| `THM_P3N2_002_reduction_composition` | `theorem` | `FORMALLY_PROVED` | `THM_POMEGA2_005_reduction_composition` | `proofs/lean/VeyraPrimePowerReductionNetwork.lean:52` |
| `THM_P3N2_003_reduction_witness_independent` | `theorem` | `FORMALLY_PROVED` | `THM_P3N2_001_reduction_identity`, `THM_P3N2_002_reduction_composition` | `proofs/lean/VeyraPrimePowerReductionNetwork.lean:61` |
| `THM_P3N2_004_path_equality` | `theorem` | `FORMALLY_PROVED` | `THM_P3N2_003_reduction_witness_independent` | `proofs/lean/VeyraPrimePowerReductionNetwork.lean:97` |
| `THM_P3N2_005_rho_square` | `theorem` | `FORMALLY_PROVED` | imports `VeyraPadicFamilyIntroduction` | `proofs/lean/VeyraPrimePowerReductionNetwork.lean:112` |
| `THM_P3N2_006_separator_coarse` | `theorem` | `FORMALLY_PROVED` | imports `VeyraPadicFamilyIntroduction` | `proofs/lean/VeyraPrimePowerReductionNetwork.lean:119` |
| `THM_P3N2_007_separator_fine` | `theorem` | `FORMALLY_PROVED` | imports `VeyraPadicFamilyIntroduction` | `proofs/lean/VeyraPrimePowerReductionNetwork.lean:127` |
| `THM_P3N6_001_prefix_indistinguishable` | `theorem` | `INTERNAL_RESEARCH_CANDIDATE` | imports `VeyraPadicFamilyIntroduction` | `proofs/lean/VeyraPrimePowerUnbounded.lean:16` |
| `THM_P3N6_002_next_depth_distinguishes` | `theorem` | `INTERNAL_RESEARCH_CANDIDATE` | imports `VeyraPadicFamilyIntroduction` | `proofs/lean/VeyraPrimePowerUnbounded.lean:31` |
| `THM_P3N6_003_power_carrier_injective` | `theorem` | `INTERNAL_RESEARCH_CANDIDATE` | imports `VeyraPadicFamilyIntroduction` | `proofs/lean/VeyraPrimePowerUnbounded.lean:52` |
| `THM_P3N6_004_power_carrier_eqc_injective` | `theorem` | `INTERNAL_RESEARCH_CANDIDATE` | `THM_P3N6_003_power_carrier_injective` | `proofs/lean/VeyraPrimePowerUnbounded.lean:80` |
| `THM_P3N6_005_carrier_equality_adapter` | `theorem` | `INTERNAL_RESEARCH_CANDIDATE` | imports `VeyraPadicFamilyIntroduction` | `proofs/lean/VeyraPrimePowerUnbounded.lean:88` |
| `THM_P001_probability_complement_counts` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraProbability.lean:5` |
| `THM_P002_probability_union_counts` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraProbability.lean:10` |
| `THM_P003_probability_independence_counts` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraProbability.lean:17` |
| `THM_D2_LEAN_001_finite_strict_descent` | `theorem` | `FORMALLY_PROVED` | imports `Lean.Elab.Tactic.Omega` | `proofs/lean/VeyraProductivityCounterpressure.lean:25` |
| `THM_D2_LEAN_002_no_infinite_nat_descent` | `theorem` | `FORMALLY_PROVED` | imports `Lean.Elab.Tactic.Omega` | `proofs/lean/VeyraProductivityCounterpressure.lean:32` |
| `THM_D2_LEAN_003a_self_mem` | `theorem` | `FORMALLY_PROVED` | imports `Lean.Elab.Tactic.Omega` | `proofs/lean/VeyraProductivityCounterpressure.lean:47` |
| `THM_D2_LEAN_003b_succ_subset` | `theorem` | `FORMALLY_PROVED` | imports `Lean.Elab.Tactic.Omega` | `proofs/lean/VeyraProductivityCounterpressure.lean:50` |
| `THM_D2_LEAN_003c_diagonal_absence` | `theorem` | `FORMALLY_PROVED` | imports `Lean.Elab.Tactic.Omega` | `proofs/lean/VeyraProductivityCounterpressure.lean:55` |
| `THM_R10_003_elaborated_proof_accepted` | `theorem` | `FORMALLY_PROVED` | imports `VeyraElaborationSemantics` | `proofs/lean/VeyraProofElaboration.lean:20` |
| `THM_R10_004_elaborated_image_sound` | `theorem` | `FORMALLY_PROVED` | `THM_R10_002_checked_elaboration_image_sound`, `THM_R10_003_elaborated_proof_accepted` | `proofs/lean/VeyraProofElaboration.lean:25` |
| `THM_R10_005_structural_support_matches` | `theorem` | `FORMALLY_PROVED` | imports `VeyraElaborationSemantics` | `proofs/lean/VeyraProofElaboration.lean:31` |
| `THM_R9_008_R7_reflexive_resonance_transport` | `theorem` | `FORMALLY_PROVED` | `THM_R9_007_resonance_transport`, `THM_R7_004_every_recurrence_resonates_with_itself` | `proofs/lean/VeyraProofModeTransport.lean:24` |
| `THM_R7_002_resonance_proof_accepted` | `theorem` | `FORMALLY_PROVED` | imports `VeyraProofSoundness` | `proofs/lean/VeyraProofResonance.lean:11` |
| `THM_R7_003_checked_reflexive_resonance` | `theorem` | `FORMALLY_PROVED` | `THM_R7_001_check_sound`, `THM_R7_002_resonance_proof_accepted` | `proofs/lean/VeyraProofResonance.lean:13` |
| `THM_R7_004_every_recurrence_resonates_with_itself` | `theorem` | `FORMALLY_PROVED` | `THM_R7_003_checked_reflexive_resonance` | `proofs/lean/VeyraProofResonance.lean:16` |
| `THM_R7_001_check_sound` | `theorem` | `FORMALLY_PROVED` | imports `VeyraProofKernel` | `proofs/lean/VeyraProofSoundness.lean:100` |
| `THM_Q11_001_born_rule_normalized` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraQuantumTensor.lean:30` |
| `THM_Q11_002_tensor_born_normalized` | `theorem` | `FORMALLY_PROVED` | `THM_Q11_001_born_rule_normalized` | `proofs/lean/VeyraQuantumTensor.lean:51` |
| `THM_Q11_003_tensor_unitary` | `def` | `FORMAL_CONSTRUCTION` | same-module definitions only | `proofs/lean/VeyraQuantumTensor.lean:86` |
| `THM_Q11_004_compose_unitary` | `def` | `FORMAL_CONSTRUCTION` | same-module definitions only | `proofs/lean/VeyraQuantumTensor.lean:112` |
| `THM_R9_002_decode_encode` | `theorem` | `FORMALLY_PROVED` | imports `VeyraNativeArithmetic`, `VeyraIntrinsicRuntime` | `proofs/lean/VeyraRecurrenceModeBridge.lean:47` |
| `THM_R9_003_encode_decode` | `theorem` | `FORMALLY_PROVED` | imports `VeyraNativeArithmetic`, `VeyraIntrinsicRuntime` | `proofs/lean/VeyraRecurrenceModeBridge.lean:72` |
| `THM_R9_004_encode_injective` | `theorem` | `FORMALLY_PROVED` | `THM_R9_002_decode_encode` | `proofs/lean/VeyraRecurrenceModeBridge.lean:104` |
| `THM_R9_001_encode_mode_ready` | `theorem` | `FORMALLY_PROVED` | imports `VeyraNativeArithmetic`, `VeyraIntrinsicRuntime` | `proofs/lean/VeyraRecurrenceModeBridge.lean:172` |
| `THM_R9_005_stitch_preserved` | `theorem` | `FORMALLY_PROVED` | imports `VeyraNativeArithmetic`, `VeyraIntrinsicRuntime` | `proofs/lean/VeyraRecurrenceModeBridge.lean:187` |
| `THM_R9_006_weave_preserved` | `theorem` | `FORMALLY_PROVED` | imports `VeyraNativeArithmetic`, `VeyraIntrinsicRuntime` | `proofs/lean/VeyraRecurrenceModeBridge.lean:208` |
| `THM_R9_007_resonance_transport` | `theorem` | `FORMALLY_PROVED` | `THM_R9_006_weave_preserved`, `THM_R9_004_encode_injective` | `proofs/lean/VeyraRecurrenceModeBridge.lean:221` |
| `THM_S001_mean_balance_1_3_5` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraStatistics.lean:5` |
| `THM_S002_variance_shift_1_3_5_plus_10` | `theorem` | `FORMALLY_PROVED` | same-module definitions only | `proofs/lean/VeyraStatistics.lean:18` |
| `THM_POMEGA1_001_truncation_identity` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | same-module definitions only | `proofs/lean/VeyraStreamCompletion.lean:20` |
| `THM_POMEGA1_002_truncation_composition` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | same-module definitions only | `proofs/lean/VeyraStreamCompletion.lean:25` |
| `THM_POMEGA1_003_rho_formation_congruence` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | same-module definitions only | `proofs/lean/VeyraStreamCompletion.lean:32` |
| `THM_POMEGA1_004_stream_restriction_compatible` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | same-module definitions only | `proofs/lean/VeyraStreamCompletion.lean:37` |
| `THM_POMEGA1_005_diagonal_realization_depth` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | same-module definitions only | `proofs/lean/VeyraStreamCompletion.lean:43` |
| `THM_POMEGA1_006_universal_realization` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | `THM_POMEGA1_005_diagonal_realization_depth` | `proofs/lean/VeyraStreamCompletion.lean:52` |
| `THM_POMEGA1_007_coordinate_agreement` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | same-module definitions only | `proofs/lean/VeyraStreamCompletion.lean:57` |
| `THM_POMEGA1_008_joint_separation` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | `THM_POMEGA1_007_coordinate_agreement` | `proofs/lean/VeyraStreamCompletion.lean:63` |
| `THM_POMEGA1_009_relative_uniqueness` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | `THM_POMEGA1_008_joint_separation` | `proofs/lean/VeyraStreamCompletion.lean:69` |
| `THM_POMEGA1_010_nonvacuity_inhabitance` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | same-module definitions only | `proofs/lean/VeyraStreamCompletion.lean:77` |
| `THM_POMEGA1_011_scp_introduction` | `theorem` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | `THM_POMEGA1_005_diagonal_realization_depth`, `THM_POMEGA1_009_relative_uniqueness`, `THM_POMEGA1_010_nonvacuity_inhabitance` | `proofs/lean/VeyraStreamCompletion.lean:85` |
| `THM_POMEGA1_012_alphabet_encode_roundtrip` | `theorem (generated)` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | generated instance of the PΩ1 SCP basis | generated at check time from `src/core/stream_completion_alphabet.py`; digest-pinned and compiled by `src/core/stream_completion_formal.py`; no repository `.lean` file |
| `THM_POMEGA1_013_alphabet_decode_roundtrip` | `theorem (generated)` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | generated instance of the PΩ1 SCP basis | generated at check time from `src/core/stream_completion_alphabet.py`; digest-pinned and compiled by `src/core/stream_completion_formal.py`; no repository `.lean` file |
| `THM_POMEGA1_014_alphabet_bijection` | `theorem (generated)` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | `THM_POMEGA1_012_alphabet_encode_roundtrip`, `THM_POMEGA1_013_alphabet_decode_roundtrip` | generated at check time from `src/core/stream_completion_alphabet.py`; digest-pinned and compiled by `src/core/stream_completion_formal.py`; no repository `.lean` file |
| `THM_POMEGA1_015_alphabet_order` | `theorem (generated)` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | generated instance of the PΩ1 SCP basis | generated at check time from `src/core/stream_completion_alphabet.py`; digest-pinned and compiled by `src/core/stream_completion_formal.py`; no repository `.lean` file |
| `THM_P3C2_001_ranked_local_to_generated_transport` | `theorem` | `FORMALLY_PROVED` | imports `Std.Tactic` | `proofs/lean/VeyraTransportCoherence.lean:73` |
| `THM_P3C2_002_natop_reduction_identity` | `theorem` | `FORMALLY_PROVED` | imports `Std.Tactic` | `proofs/lean/VeyraTransportCoherence.lean:136` |
| `THM_P3C2_003_natop_reduction_composition` | `theorem` | `FORMALLY_PROVED` | imports `Std.Tactic` | `proofs/lean/VeyraTransportCoherence.lean:141` |

## Experimental research appendix

The 65 declarations in `experimental/research_lean/manifest.json` are a
separate `INTERNAL_RESEARCH_CANDIDATE` appendix, not stable theorem rows. Their
exact digests, import graph, toolchain commit, and axiom closures are checked by
`make research-lean`; THM-001–003 and all X8 statuses below are unchanged.

## Stable nonformal and bounded theorem-card status

| ID family | Status | Dependencies | Evidence | Exact boundary |
|---|---|---|---|---|
| `THM-001`–`THM-003` | `CONJECTURE` | `AX-007`, `LEM-001`, then preceding theorem | `docs/08_weave_and_n_shadow.md` | Natural/addition/multiplication shadows; not foundations of ordinary arithmetic. |
| `THM-F003` | `EXECUTABLE_EVIDENCE` | native `Mode`/`Breath` length observer | `src/core/native_number_theorems.py`; focused tests | Finite prime-period Fermat rows only; no Lean theorem. |
| X8 fixed cards (`THM_A001`–`A006`, `B001`, `C001`–`C002`, `G001`–`G005`, `P001`–`P003`, `S001`–`S002`) | `FORMALLY_PROVED` | fixed literal fixtures | corresponding `Veyra{Algebra,Combinatorics,Cyclic,Geometry,Probability,Statistics}.lean` | The exact numerals/samples only; no general analysis, geometry, probability or statistics theorem. |
| `THM-D2-001`–`005` | `EXECUTABLE_EVIDENCE` with formal auxiliary lemmas | exact five-inference catalog | `src/core/productivity_counterpressure*.py`; `VeyraProductivityCounterpressure.lean` | Refutes only the five exact implications; no generator nonexistence. |
| `THM-D3-001`–`011` | `FORMALLY_PROVED` | exact periodic-family ledger | `VeyraAllDepthFamily.lean`; focused certificate tests | One periodic compatible family; no completed carrier or generic introduction rule. |
| `THM-POMEGA1-001`–`015` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | exact completion doctrine/ledger | `VeyraStreamCompletion.lean`; generated instance bridge; public certificate tests | `Stream(A)` relative to that doctrine; no physical or foundation-independent infinity. |
| `THM-POMEGA2-001`–`017` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | prime witness and exact 45-row ledger | `VeyraPadicCompletion.lean`; PΩ2 formal/public tests | Exact compatible prime-power carrier; not a categorical/topological p-adic equivalence. |
| `THM-P3N3-001`–`002`, `THM-P3N4-001` | `FORMALLY_PROVED + PUBLICLY_VALIDATED` | N1, PΩ2 and the explicit all-depth premise for N4 | `VeyraPadicLocalRealization.lean`; `VeyraPadicAllDepthEquality.lean`; public certificate tests | Ledger-relative realization/scoped equality only. |
| `THM-P3N0-001`–`003` | `INTERNAL_RESEARCH_CANDIDATE` | finite observer-actualization sources | `VeyraPrimePowerObserverActualization.lean`; focused candidate tests | No public release/certificate status. |
| `THM-P3N6-001`–`005` | `INTERNAL_RESEARCH_CANDIDATE` | exact PΩ2 injection sources | `VeyraPrimePowerUnbounded.lean`; focused candidate tests | No public release, ΩN or cardinality theorem. |
| `THM-P3N6W-001`–`004` | `INTERNAL_RESEARCH_CANDIDATE` | P3-N6 candidate basis | `VeyraPrimePowerInformation.lean`; focused candidate tests | Uniform late witness only; no completed indexing/cardinality/uncountability. |
