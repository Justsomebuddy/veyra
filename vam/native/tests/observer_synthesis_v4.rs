//! Focused exact tests for systematic representation/observer synthesis v4.

use vam_native::observer_synthesis::{
    differential_representation_observer_v4, enumerate_representation_family_v4,
    run_observer_synthesis_benchmark_suite_v4, survey_representation_family_v4,
    NativePartitionTaskId, ObserverGrammarProfileId, ObserverSynthesisBenchmarkIdV4,
    ObserverSynthesisCutoffV4, ObserverSynthesisRequestV4, ObserverSynthesisStatusV4,
    RepresentationFamilyKindV4, RepresentationTaskClassV4, ALL_REPRESENTATION_FAMILIES_V4,
    GRAMMAR_REGISTRY_DIGEST, LEGACY_REGISTRY_PREFIX_DIGEST, OBSERVER_SYNTHESIS_PIPELINE_V3_SCHEMA,
};

fn request() -> ObserverSynthesisRequestV4 {
    ObserverSynthesisRequestV4::systematic(
        NativePartitionTaskId::XorParity,
        ObserverGrammarProfileId::ParityV2,
    )
}

#[test]
fn systematic_family_is_complete_ordered_and_reproducible() {
    let first = enumerate_representation_family_v4(&ALL_REPRESENTATION_FAMILIES_V4).unwrap();
    let second = enumerate_representation_family_v4(&ALL_REPRESENTATION_FAMILIES_V4).unwrap();
    assert_eq!(first, second);
    assert_eq!(
        first.family_digest,
        "b62774bdcbd7d882f03fe86ce5a4bfec55aad5abe36aa4130db3f8cd2ce1f9b2"
    );
    assert_eq!(first.candidates.len(), 52);
    assert_eq!(
        first
            .candidates
            .iter()
            .filter(|row| row.family == RepresentationFamilyKindV4::Permutation)
            .count(),
        24
    );
    assert_eq!(
        first
            .candidates
            .iter()
            .filter(|row| row.family == RepresentationFamilyKindV4::CyclicAffine)
            .count(),
        8
    );
    assert_eq!(
        first
            .candidates
            .iter()
            .filter(|row| row.family == RepresentationFamilyKindV4::GroupingQuotient)
            .count(),
        14
    );
    assert_eq!(
        first
            .candidates
            .iter()
            .filter(|row| row.family == RepresentationFamilyKindV4::CanonicalEncoding)
            .count(),
        6
    );
    assert!(first
        .candidates
        .iter()
        .enumerate()
        .all(|(ordinal, row)| row.ordinal == ordinal));
}

#[test]
fn survey_is_an_exact_nonempty_trichotomy() {
    let survey = survey_representation_family_v4(
        NativePartitionTaskId::XorParity,
        &ALL_REPRESENTATION_FAMILIES_V4,
    )
    .unwrap();
    assert_eq!(
        survey.stable_count + survey.hidden_count + survey.destroyed_count,
        survey.rows.len()
    );
    assert!(survey.stable_count > 0);
    assert!(survey.hidden_count > 0);
    assert!(survey.destroyed_count > 0);
    assert!(survey.rows.iter().any(|row| {
        row.classification == RepresentationTaskClassV4::InformationDestroyed
            && row.first_destroyed_pair.is_some()
    }));
    assert!(survey.rows.iter().all(|row| {
        (row.classification == RepresentationTaskClassV4::InformationDestroyed)
            == row.first_destroyed_pair.is_some()
    }));
}

#[test]
fn optimized_search_matches_independent_exhaustive_oracle() {
    let differential = differential_representation_observer_v4(&request()).unwrap();
    assert!(differential.equivalent);
    assert_eq!(differential.oracle.status, ObserverSynthesisStatusV4::Found);
    let winner = differential.oracle.winner.unwrap();
    assert_eq!(
        winner.total_cost,
        winner.representation_cost
            + winner.transport_cost
            + winner.observer_cost
            + winner.explanation.explanation_cost
    );
    assert!(winner.explanation.equality_partition_exact);
    assert_eq!(winner.explanation.pair_obligations, 6);
    assert_eq!(winner.explanation.response_classes, 2);
    assert_eq!(winner.explanation.target_classes, 2);
}

#[test]
fn exhausted_means_the_complete_cost_admitted_product_was_checked() {
    let mut request = request();
    request.maximum_total_cost = 1;
    let differential = differential_representation_observer_v4(&request).unwrap();
    assert!(differential.equivalent);
    assert_eq!(
        differential.oracle.status,
        ObserverSynthesisStatusV4::Exhausted
    );
    assert_eq!(differential.oracle.ledger.admissible_pairs, 0);
    assert_eq!(differential.oracle.ledger.cutoff, None);
    assert!(differential.oracle.winner.is_none());
}

#[test]
fn every_physical_counter_cutoff_is_distinct_from_exhaustion() {
    let mut representation = request();
    representation.limits.representation_limit = 51;
    let result = differential_representation_observer_v4(&representation).unwrap();
    assert!(result.equivalent);
    assert_eq!(result.oracle.status, ObserverSynthesisStatusV4::Cutoff);
    assert_eq!(
        result.oracle.ledger.cutoff,
        Some(ObserverSynthesisCutoffV4::Representations)
    );

    let mut observers = request();
    observers.limits.observer_limit = 229;
    let result = differential_representation_observer_v4(&observers).unwrap();
    assert!(result.equivalent);
    assert_eq!(
        result.oracle.ledger.cutoff,
        Some(ObserverSynthesisCutoffV4::Observers)
    );

    let mut evaluations = request();
    evaluations.limits.relation_evaluation_limit = 1;
    let result = differential_representation_observer_v4(&evaluations).unwrap();
    assert!(result.equivalent);
    assert_eq!(
        result.oracle.ledger.cutoff,
        Some(ObserverSynthesisCutoffV4::RelationEvaluations)
    );
    assert!(result.oracle.winner.is_none());
}

#[test]
fn family_selection_is_declared_sorted_and_v3_roots_remain_unchanged() {
    let invalid = [
        RepresentationFamilyKindV4::GroupingQuotient,
        RepresentationFamilyKindV4::Permutation,
    ];
    assert!(enumerate_representation_family_v4(&invalid).is_err());
    assert_eq!(
        LEGACY_REGISTRY_PREFIX_DIGEST,
        "6ea628f5924b82a2cb89b402beb08d762c4716ae2d4044ade3ceb21062bfdc0c"
    );
    assert_eq!(
        GRAMMAR_REGISTRY_DIGEST,
        "f937c322be2fd20933a32993d5549009fbac6c23f80cae16964cdaaf653af8b5"
    );
    assert_eq!(
        OBSERVER_SYNTHESIS_PIPELINE_V3_SCHEMA,
        "veyra.observer-synthesis.atomic-pipeline.v3"
    );
}

#[test]
fn public_six_case_benchmark_suite_is_deterministic_and_green() {
    let first = run_observer_synthesis_benchmark_suite_v4().unwrap();
    let second = run_observer_synthesis_benchmark_suite_v4().unwrap();
    assert_eq!(first, second);
    assert_eq!(first.rows.len(), 6);
    assert_eq!(first.passed, 6);
    assert_eq!(first.failed, 0);
    assert_eq!(
        first.suite_digest,
        "55fb30d48d761ea66733db802598d9b4a161ca3feaf811de89108664f30dfe71"
    );
    assert!(first.rows.iter().all(|row| row.passed));
    assert!(first.rows.iter().any(|row| {
        row.id == ObserverSynthesisBenchmarkIdV4::PositiveHidden
            && row.winner_class == Some(RepresentationTaskClassV4::RepresentationHidden)
    }));
    assert!(first.rows.iter().any(|row| {
        row.id == ObserverSynthesisBenchmarkIdV4::NegativeControl
            && row.status == ObserverSynthesisStatusV4::Exhausted
            && row.admissible_pairs > 0
            && row.pair_attempts == row.admissible_pairs
    }));
    assert!(first.rows.iter().any(|row| {
        row.id == ObserverSynthesisBenchmarkIdV4::RepresentationTrap
            && row.hidden_count > 0
            && row.status == ObserverSynthesisStatusV4::Exhausted
    }));
    assert!(first.rows.iter().any(|row| {
        row.id == ObserverSynthesisBenchmarkIdV4::LossyInformationDestroyed
            && row.destroyed_count > 0
    }));
}

#[test]
fn adversarial_exact_cost_and_charge_boundaries_match_independent_engines() {
    let baseline = differential_representation_observer_v4(&request()).unwrap();
    assert!(baseline.equivalent);
    assert!(!baseline.oracle.optimized);
    assert!(baseline.optimized.optimized);
    assert_ne!(
        baseline.oracle.result_digest,
        baseline.optimized.result_digest
    );
    let winner = baseline.oracle.winner.as_ref().unwrap();

    let mut below_cost = request();
    below_cost.maximum_total_cost = winner.total_cost - 1;
    let below = differential_representation_observer_v4(&below_cost).unwrap();
    assert!(below.equivalent);
    assert_eq!(below.oracle.status, ObserverSynthesisStatusV4::Exhausted);
    assert!(below.oracle.winner.is_none());

    let mut exact_cost = request();
    exact_cost.maximum_total_cost = winner.total_cost;
    let exact = differential_representation_observer_v4(&exact_cost).unwrap();
    assert!(exact.equivalent);
    assert_eq!(exact.oracle.status, ObserverSynthesisStatusV4::Found);
    assert_eq!(exact.oracle.winner, baseline.oracle.winner);

    let exact_charge = baseline.oracle.ledger.relation_evaluations;
    assert!(exact_charge >= 6);
    let mut below_charge = request();
    below_charge.limits.relation_evaluation_limit = exact_charge - 1;
    let cutoff = differential_representation_observer_v4(&below_charge).unwrap();
    assert!(cutoff.equivalent);
    assert_eq!(cutoff.oracle.status, ObserverSynthesisStatusV4::Cutoff);
    assert_eq!(
        cutoff.oracle.ledger.cutoff,
        Some(ObserverSynthesisCutoffV4::RelationEvaluations)
    );

    let mut exact_charge_request = request();
    exact_charge_request.limits.relation_evaluation_limit = exact_charge;
    let exact = differential_representation_observer_v4(&exact_charge_request).unwrap();
    assert!(exact.equivalent);
    assert_eq!(exact.oracle.status, ObserverSynthesisStatusV4::Found);
    assert_eq!(exact.oracle.winner, baseline.oracle.winner);
}

#[test]
fn adversarial_family_admission_has_identical_terminal_semantics() {
    for family in ALL_REPRESENTATION_FAMILIES_V4 {
        let mut exhausted = request();
        exhausted.families = vec![family];
        exhausted.maximum_total_cost = 1;
        let differential = differential_representation_observer_v4(&exhausted).unwrap();
        assert!(differential.equivalent, "family={family:?}");
        assert_eq!(
            differential.oracle.status,
            ObserverSynthesisStatusV4::Exhausted
        );
        assert_eq!(differential.oracle.ledger.admissible_pairs, 0);

        let mut cutoff = request();
        cutoff.families = vec![family];
        cutoff.limits.relation_evaluation_limit = 1;
        let differential = differential_representation_observer_v4(&cutoff).unwrap();
        assert!(differential.equivalent, "family={family:?}");
        assert_eq!(
            differential.oracle.status,
            ObserverSynthesisStatusV4::Cutoff
        );
        assert_eq!(
            differential.oracle.ledger.cutoff,
            Some(ObserverSynthesisCutoffV4::RelationEvaluations)
        );
    }
}
