//! Public-crate checks for versioned grammar, transport survey, and joint search.

use vam_native::observer_synthesis::{
    enumerate_observer_grammar, enumerate_observer_grammar_profile, grammar_config_for_profile,
    survey_representation_family, synthesize_transform_and_observer, GrammarConfig,
    JointBudgetCutoff, JointSynthesisLimits, JointSynthesisStatus, NativePartitionTaskId,
    ObserverExpr, ObserverGrammarProfileId, PrimitiveId, DEFAULT_CATALOG_DIGEST,
    PARITY_INPUT_DIGEST, PARITY_V2_CANDIDATES, PARITY_V2_CATALOG_DIGEST,
    PARITY_XOR_PRESERVING_TRANSFORMS, PARITY_XOR_SURVEY_CLASSES, PARITY_XOR_SURVEY_DIGEST,
    REPRESENTATION_TRANSFORMS,
};

#[test]
fn public_profiles_preserve_legacy_and_separate_parity() {
    let legacy = enumerate_observer_grammar(GrammarConfig::default()).unwrap();
    assert_eq!(legacy.catalog_digest, DEFAULT_CATALOG_DIGEST);
    assert_eq!(legacy.candidates.len(), 1_565);
    assert!(!legacy.candidates.iter().any(|row| {
        matches!(
            row.observer,
            ObserverExpr::Apply {
                primitive: PrimitiveId::Parity,
                ..
            }
        )
    }));

    let parity = enumerate_observer_grammar_profile(
        ObserverGrammarProfileId::ParityV2,
        grammar_config_for_profile(ObserverGrammarProfileId::ParityV2),
    )
    .unwrap();
    assert_eq!(parity.enumeration.candidates.len(), PARITY_V2_CANDIDATES);
    assert_eq!(parity.enumeration.catalog_digest, PARITY_V2_CATALOG_DIGEST);
    assert_ne!(parity.enumeration.catalog_digest, legacy.catalog_digest);
}

#[test]
fn public_transport_survey_covers_the_complete_declared_family() {
    let survey =
        survey_representation_family(ObserverGrammarProfileId::ParityV2, 2, [0, 1, 1, 0]).unwrap();
    assert_eq!(survey.transform_count, REPRESENTATION_TRANSFORMS);
    assert_eq!(survey.equivalence_classes.len(), PARITY_XOR_SURVEY_CLASSES);
    assert_eq!(
        survey.preserving_transform_count,
        PARITY_XOR_PRESERVING_TRANSFORMS
    );
    assert_eq!(survey.survey_digest, PARITY_XOR_SURVEY_DIGEST);
    assert_eq!(
        survey
            .equivalence_classes
            .iter()
            .map(|row| row.transform_ordinals.len())
            .sum::<usize>(),
        REPRESENTATION_TRANSFORMS
    );
}

#[test]
fn public_joint_search_separates_winner_exhaustion_and_cutoff() {
    let parity = synthesize_transform_and_observer(
        NativePartitionTaskId::XorParity,
        ObserverGrammarProfileId::ParityV2,
        JointSynthesisLimits::default(),
    )
    .unwrap();
    assert_eq!(parity.status, JointSynthesisStatus::Found);
    let winner = parity.winner.unwrap();
    assert_eq!(winner.joint_cost, 2);
    assert_eq!(winner.transform_ordinal, 1);
    assert_eq!(winner.observer_digest, PARITY_INPUT_DIGEST);

    let legacy = synthesize_transform_and_observer(
        NativePartitionTaskId::XorParity,
        ObserverGrammarProfileId::LegacyV1,
        JointSynthesisLimits::default(),
    )
    .unwrap();
    assert_eq!(legacy.status, JointSynthesisStatus::Exhausted);
    assert!(legacy.winner.is_none());

    let cutoff = synthesize_transform_and_observer(
        NativePartitionTaskId::XorParity,
        ObserverGrammarProfileId::ParityV2,
        JointSynthesisLimits {
            relation_evaluation_limit: 1,
            ..JointSynthesisLimits::default()
        },
    )
    .unwrap();
    assert_eq!(cutoff.status, JointSynthesisStatus::Incomplete);
    assert_eq!(
        cutoff.ledger.cutoff,
        Some(JointBudgetCutoff::RelationEvaluations)
    );
    assert!(cutoff.winner.is_none());
}

#[test]
fn public_joint_budget_boundaries_are_atomic_and_exact() {
    for limits in [
        JointSynthesisLimits {
            transform_limit: 119,
            ..JointSynthesisLimits::default()
        },
        JointSynthesisLimits {
            candidate_limit: PARITY_V2_CANDIDATES - 1,
            ..JointSynthesisLimits::default()
        },
        JointSynthesisLimits {
            relation_evaluation_limit: 131,
            ..JointSynthesisLimits::default()
        },
    ] {
        let report = synthesize_transform_and_observer(
            NativePartitionTaskId::XorParity,
            ObserverGrammarProfileId::ParityV2,
            limits,
        )
        .unwrap();
        assert_eq!(report.status, JointSynthesisStatus::Incomplete);
        assert!(report.winner.is_none());
    }
    let exact = synthesize_transform_and_observer(
        NativePartitionTaskId::XorParity,
        ObserverGrammarProfileId::ParityV2,
        JointSynthesisLimits {
            transform_limit: REPRESENTATION_TRANSFORMS,
            candidate_limit: PARITY_V2_CANDIDATES,
            relation_evaluation_limit: 132,
        },
    )
    .unwrap();
    assert_eq!(exact.status, JointSynthesisStatus::Found);
    assert_eq!(exact.ledger.relation_evaluations, 132);

    for limits in [
        JointSynthesisLimits {
            transform_limit: 0,
            ..JointSynthesisLimits::default()
        },
        JointSynthesisLimits {
            candidate_limit: 0,
            ..JointSynthesisLimits::default()
        },
        JointSynthesisLimits {
            relation_evaluation_limit: 0,
            ..JointSynthesisLimits::default()
        },
    ] {
        assert!(synthesize_transform_and_observer(
            NativePartitionTaskId::XorParity,
            ObserverGrammarProfileId::ParityV2,
            limits,
        )
        .is_err());
    }
}
