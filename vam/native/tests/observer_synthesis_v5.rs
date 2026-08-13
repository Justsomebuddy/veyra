//! Focused exact tests for generated discovery and branch-and-bound v5.

use vam_native::observer_synthesis::{
    canonical_discovery_benchmark_v5_bytes, canonical_discovery_request_v5_bytes,
    canonical_discovery_result_v5_bytes, decode_discovery_request_v5_bytes,
    decode_discovery_result_v5_bytes, differential_discovery_v5, discovery_benchmark_family_v5,
    discovery_grammar_extension_v5, enumerate_discovery_grammar_v5, run_discovery_benchmark_v5,
    synthesize_discovery_v5, verify_branch_bound_proof_v5, DiscoveryBenchmarkIdV5,
    DiscoveryBenchmarkSplitV5, DiscoveryGrammarProfileIdV5, DiscoverySearchRequestV5,
    DiscoverySearchStatusV5, ALL_DISCOVERY_BENCHMARKS_V5, CALIBRATION_DISCOVERY_BENCHMARKS_V5,
    DISCOVERY_BENCHMARK_RUN_V5_DIGEST, DISCOVERY_BENCHMARK_V5_FAMILY_DIGEST,
    DISCOVERY_GRAMMAR_V5_CATALOG_DIGEST, DISCOVERY_GRAMMAR_V5_EXTENSION_DIGEST,
    DISCOVERY_GRAMMAR_V5_PROFILE_DIGEST, GRAMMAR_REGISTRY_DIGEST, HELD_OUT_DISCOVERY_BENCHMARKS_V5,
    LEGACY_REGISTRY_PREFIX_DIGEST,
};

fn same_partition(left: &[u8; 16], right: &[u8; 16]) -> bool {
    (0..16).all(|a| (a + 1..16).all(|b| (left[a] == left[b]) == (right[a] == right[b])))
}

#[test]
fn append_only_v5_grammar_is_deterministic_and_preserves_frozen_roots() {
    let first =
        enumerate_discovery_grammar_v5(DiscoveryGrammarProfileIdV5::AffineParityReflectionV5)
            .unwrap();
    let second =
        enumerate_discovery_grammar_v5(DiscoveryGrammarProfileIdV5::AffineParityReflectionV5)
            .unwrap();
    assert_eq!(first, second);
    assert_eq!(first.candidates.len(), 2_048);
    assert_eq!(
        first.profile.profile_digest,
        DISCOVERY_GRAMMAR_V5_PROFILE_DIGEST
    );
    assert_eq!(first.catalog_digest, DISCOVERY_GRAMMAR_V5_CATALOG_DIGEST);
    assert!(first
        .candidates
        .windows(2)
        .all(|pair| (pair[0].cost, pair[0].ordinal) <= (pair[1].cost, pair[1].ordinal)));
    assert!(first
        .candidates
        .iter()
        .enumerate()
        .all(|(ordinal, candidate)| candidate.ordinal == ordinal));
    let extension = discovery_grammar_extension_v5().unwrap();
    assert_eq!(extension.extension_ordinal, 2);
    assert_eq!(
        extension.extension_digest,
        DISCOVERY_GRAMMAR_V5_EXTENSION_DIGEST
    );
    assert_eq!(extension.frozen_registry_digest, GRAMMAR_REGISTRY_DIGEST);
    assert_eq!(
        LEGACY_REGISTRY_PREFIX_DIGEST,
        "6ea628f5924b82a2cb89b402beb08d762c4716ae2d4044ade3ceb21062bfdc0c"
    );
    assert_eq!(
        GRAMMAR_REGISTRY_DIGEST,
        "f937c322be2fd20933a32993d5549009fbac6c23f80cae16964cdaaf653af8b5"
    );
}

#[test]
fn generated_family_covers_declared_scientific_controls_without_answer_tables() {
    let first = discovery_benchmark_family_v5().unwrap();
    let second = discovery_benchmark_family_v5().unwrap();
    assert_eq!(first, second);
    assert_eq!(first.family_digest, DISCOVERY_BENCHMARK_V5_FAMILY_DIGEST);
    assert_eq!(first.tasks.len(), 5);
    assert!(first.tasks[0].hidden_variable);
    assert!(first.tasks[1].symmetry);
    assert!(first.tasks[2].misrepresentation);
    assert!(first.tasks[3].negative_control);
    assert_eq!(first.tasks[3].split, DiscoveryBenchmarkSplitV5::Calibration);
    assert_eq!(
        first.tasks[4].split,
        DiscoveryBenchmarkSplitV5::SyntheticHeldOut
    );
    assert!(!first.tasks[4].negative_control);
    assert_eq!(CALIBRATION_DISCOVERY_BENCHMARKS_V5.len(), 4);
    assert_eq!(
        HELD_OUT_DISCOVERY_BENCHMARKS_V5,
        [DiscoveryBenchmarkIdV5::HeldOutAffine]
    );
    assert!(CALIBRATION_DISCOVERY_BENCHMARKS_V5
        .iter()
        .all(|id| !HELD_OUT_DISCOVERY_BENCHMARKS_V5.contains(id)));
    let identity_surface = std::array::from_fn(|state| state as u8);
    let hidden = &first.tasks[0];
    let misrepresentation = &first.tasks[2];
    assert_eq!(hidden.surface_states, identity_surface);
    assert_ne!(misrepresentation.surface_states, identity_surface);
    assert_ne!(hidden.surface_states, misrepresentation.surface_states);
    assert_ne!(
        (hidden.surface_states, hidden.target_classes),
        (
            misrepresentation.surface_states,
            misrepresentation.target_classes
        )
    );
    assert!(first.tasks[..4].iter().all(|calibration| {
        !same_partition(&calibration.target_classes, &first.tasks[4].target_classes)
    }));
    for task in &first.tasks {
        let mut sorted_surface = task.surface_states;
        sorted_surface.sort_unstable();
        assert_eq!(sorted_surface, identity_surface);
        assert!(task
            .target_classes
            .windows(2)
            .any(|pair| pair[0] != pair[1]));
        assert_eq!(
            canonical_discovery_benchmark_v5_bytes(task).unwrap(),
            canonical_discovery_benchmark_v5_bytes(task).unwrap()
        );
    }
}

#[test]
fn branch_and_bound_proof_matches_genuinely_exhaustive_reference() {
    let catalog =
        enumerate_discovery_grammar_v5(DiscoveryGrammarProfileIdV5::AffineParityReflectionV5)
            .unwrap();
    for benchmark_id in ALL_DISCOVERY_BENCHMARKS_V5 {
        let request = DiscoverySearchRequestV5::systematic(benchmark_id);
        let differential = differential_discovery_v5(&request).unwrap();
        assert!(differential.equivalent);
        assert_eq!(
            differential.optimized.benchmark_split,
            if benchmark_id == DiscoveryBenchmarkIdV5::HeldOutAffine {
                DiscoveryBenchmarkSplitV5::SyntheticHeldOut
            } else {
                DiscoveryBenchmarkSplitV5::Calibration
            }
        );
        assert!(verify_branch_bound_proof_v5(&request, &differential.optimized).unwrap());
        assert!(differential.optimized.ledger.bound_admissible);
        assert_eq!(
            differential.optimized.ledger.evaluated_pairs
                + differential.optimized.ledger.pruned_pairs,
            differential.optimized.ledger.admissible_pairs
        );
        if benchmark_id == DiscoveryBenchmarkIdV5::DiagonalNegativeControl {
            assert_eq!(
                differential.optimized.status,
                DiscoverySearchStatusV5::Exhausted
            );
            assert_eq!(differential.optimized.ledger.pruned_pairs, 0);
            assert!(differential.optimized.winner.is_none());
        } else {
            assert_eq!(
                differential.optimized.status,
                DiscoverySearchStatusV5::Found
            );
            assert!(differential.optimized.ledger.pruned_pairs > 0);
            let winner = differential.optimized.winner.as_ref().unwrap();
            let expected_evaluated = catalog
                .candidates
                .iter()
                .filter(|candidate| candidate.cost <= winner.total_cost)
                .count();
            assert_eq!(
                differential.optimized.ledger.evaluated_pairs,
                expected_evaluated * 120
            );
            assert!(
                differential
                    .optimized
                    .ledger
                    .first_pruned_cost_lower_bound
                    .unwrap()
                    > winner.total_cost
            );
            assert_eq!(
                differential.reference.ledger.evaluated_pairs,
                differential.reference.ledger.admissible_pairs
            );
        }
    }

    let hidden = differential_discovery_v5(&DiscoverySearchRequestV5::systematic(
        DiscoveryBenchmarkIdV5::HiddenAffine,
    ))
    .unwrap();
    let recovered = differential_discovery_v5(&DiscoverySearchRequestV5::systematic(
        DiscoveryBenchmarkIdV5::MisrepresentationRecovery,
    ))
    .unwrap();
    assert_ne!(
        hidden.optimized.winner.unwrap().candidate_digest,
        recovered.optimized.winner.unwrap().candidate_digest
    );
}

#[test]
fn cutoff_is_preflight_and_never_masquerades_as_exhaustion() {
    let mut request = DiscoverySearchRequestV5::systematic(DiscoveryBenchmarkIdV5::HiddenAffine);
    request.limits.candidate_limit -= 1;
    let differential = differential_discovery_v5(&request).unwrap();
    assert!(differential.equivalent);
    assert_eq!(
        differential.optimized.status,
        DiscoverySearchStatusV5::Cutoff
    );
    assert!(differential.optimized.ledger.cutoff);
    assert_eq!(differential.optimized.ledger.evaluated_pairs, 0);
    assert_eq!(differential.optimized.ledger.pruned_pairs, 0);
    assert!(differential.optimized.winner.is_none());
}

fn resign_result(result: &mut vam_native::observer_synthesis::DiscoverySearchResultV5) {
    result.result_digest =
        vam_native::observer_synthesis::discovery_result_v5_root(result).unwrap();
}

#[test]
fn independent_prune_verifier_rejects_hostile_ledger_winner_status_and_digests() {
    let request = DiscoverySearchRequestV5::systematic(DiscoveryBenchmarkIdV5::HeldOutAffine);
    let valid = synthesize_discovery_v5(&request).unwrap();
    assert!(verify_branch_bound_proof_v5(&request, &valid).unwrap());

    type ResultMutation = Box<dyn Fn(&mut vam_native::observer_synthesis::DiscoverySearchResultV5)>;
    let mut mutations: Vec<ResultMutation> = vec![
        Box::new(|row| row.ledger.candidates -= 1),
        Box::new(|row| row.ledger.admissible_pairs -= 120),
        Box::new(|row| row.ledger.evaluated_pairs += 120),
        Box::new(|row| row.ledger.pruned_pairs -= 120),
        Box::new(|row| row.ledger.cutoff = true),
        Box::new(|row| row.ledger.incumbent_cost = Some(usize::MAX)),
        Box::new(|row| row.ledger.first_pruned_cost_lower_bound = Some(0)),
        Box::new(|row| row.ledger.bound_admissible = false),
        Box::new(|row| row.ledger.lower_bound_digest.replace_range(0..1, "0")),
        Box::new(|row| row.ledger.prune_proof_digest.replace_range(0..1, "0")),
        Box::new(|row| row.status = DiscoverySearchStatusV5::Exhausted),
        Box::new(|row| row.detail = "complete-cost-admitted-catalog-exhausted"),
        Box::new(|row| row.benchmark_digest.replace_range(0..1, "0")),
        Box::new(|row| row.catalog_digest.replace_range(0..1, "0")),
    ];
    for mutation in mutations.drain(..) {
        let mut hostile = valid.clone();
        mutation(&mut hostile);
        resign_result(&mut hostile);
        assert!(!verify_branch_bound_proof_v5(&request, &hostile).unwrap());
    }

    let winner_mutations: Vec<Box<dyn Fn(&mut vam_native::observer_synthesis::DiscoveryWinnerV5)>> = vec![
        Box::new(|row| row.candidate_ordinal += 1),
        Box::new(|row| row.total_cost += 1),
        Box::new(|row| row.observer_gap += 1),
        Box::new(|row| row.alternatives_at_same_cost += 1),
        Box::new(|row| row.candidate_digest.replace_range(0..1, "0")),
        Box::new(|row| row.representation_digest.replace_range(0..1, "0")),
        Box::new(|row| row.explanation_digest.replace_range(0..1, "0")),
        Box::new(|row| row.witness_digest.replace_range(0..1, "0")),
    ];
    for mutation in winner_mutations {
        let mut hostile = valid.clone();
        mutation(hostile.winner.as_mut().unwrap());
        resign_result(&mut hostile);
        assert!(!verify_branch_bound_proof_v5(&request, &hostile).unwrap());
    }
}

#[test]
fn independent_prune_verifier_rejects_hostile_cutoff_and_exhaustion_fields() {
    let mut cutoff_request =
        DiscoverySearchRequestV5::systematic(DiscoveryBenchmarkIdV5::HiddenAffine);
    cutoff_request.limits.candidate_limit -= 1;
    let cutoff = synthesize_discovery_v5(&cutoff_request).unwrap();
    for change in 0..4 {
        let mut hostile = cutoff.clone();
        match change {
            0 => hostile.ledger.evaluated_pairs = 120,
            1 => hostile.ledger.pruned_pairs = 120,
            2 => hostile.ledger.cutoff = false,
            _ => hostile.status = DiscoverySearchStatusV5::Exhausted,
        }
        resign_result(&mut hostile);
        assert!(!verify_branch_bound_proof_v5(&cutoff_request, &hostile).unwrap());
    }

    let request =
        DiscoverySearchRequestV5::systematic(DiscoveryBenchmarkIdV5::DiagonalNegativeControl);
    let exhausted = synthesize_discovery_v5(&request).unwrap();
    let mut hostile = exhausted.clone();
    hostile.ledger.pruned_pairs = 120;
    hostile.ledger.evaluated_pairs -= 120;
    resign_result(&mut hostile);
    assert!(!verify_branch_bound_proof_v5(&request, &hostile).unwrap());
}

#[test]
fn request_and_result_codecs_are_canonical_bounded_and_tamper_evident() {
    let request = DiscoverySearchRequestV5::systematic(DiscoveryBenchmarkIdV5::ReflectionSymmetry);
    let request_bytes = canonical_discovery_request_v5_bytes(&request).unwrap();
    assert_eq!(
        decode_discovery_request_v5_bytes(&request_bytes).unwrap(),
        request
    );
    let mut padded = request_bytes.clone();
    padded.extend_from_slice(b"\0junk");
    assert!(decode_discovery_request_v5_bytes(&padded).is_err());

    let result = synthesize_discovery_v5(&request).unwrap();
    let result_bytes = canonical_discovery_result_v5_bytes(&result).unwrap();
    let decoded = decode_discovery_result_v5_bytes(&result_bytes).unwrap();
    assert_eq!(decoded, result);
    let mut tampered = result_bytes;
    let index = tampered.iter().position(|byte| *byte == b'F').unwrap();
    tampered[index] = b'X';
    assert!(decode_discovery_result_v5_bytes(&tampered).is_err());

    for benchmark_id in ALL_DISCOVERY_BENCHMARKS_V5 {
        let request = DiscoverySearchRequestV5::systematic(benchmark_id);
        let bytes = canonical_discovery_request_v5_bytes(&request).unwrap();
        assert_eq!(decode_discovery_request_v5_bytes(&bytes).unwrap(), request);
        let result = synthesize_discovery_v5(&request).unwrap();
        let bytes = canonical_discovery_result_v5_bytes(&result).unwrap();
        assert_eq!(decode_discovery_result_v5_bytes(&bytes).unwrap(), result);
    }

    let mut cutoff = DiscoverySearchRequestV5::systematic(DiscoveryBenchmarkIdV5::HeldOutAffine);
    cutoff.limits.candidate_limit -= 1;
    let cutoff = synthesize_discovery_v5(&cutoff).unwrap();
    assert_eq!(cutoff.status, DiscoverySearchStatusV5::Cutoff);
    let bytes = canonical_discovery_result_v5_bytes(&cutoff).unwrap();
    assert_eq!(decode_discovery_result_v5_bytes(&bytes).unwrap(), cutoff);
}

#[test]
fn public_family_run_exposes_found_exhausted_and_no_cutoff() {
    let run = run_discovery_benchmark_v5().unwrap();
    assert_eq!(run.run_digest, DISCOVERY_BENCHMARK_RUN_V5_DIGEST);
    assert_eq!(run.rows.len(), 5);
    assert_eq!(run.found, 4);
    assert_eq!(run.exhausted, 1);
    assert_eq!(run.cutoff, 0);
    assert!(run.rows.iter().all(|row| row.equivalent));
}
