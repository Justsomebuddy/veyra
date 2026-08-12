//! Public checks for optimized search, finite gap scoring, and atomic aggregation.

use vam_native::observer_synthesis::{
    differential_joint_search, differential_transport_observer_search,
    enumerate_representation_family, observer_gap_calibration_requests, run_observer_gap_lab,
    run_observer_synthesis_pipeline_v3, FiniteDomainV1, JointBudgetCutoff,
    JointDifferentialVerdictV1, JointSynthesisLimits, JointSynthesisStatus,
    NamedObserverBaselineV1, NativePartitionTaskId, ObserverGapPolicyV1, ObserverGapRequestV1,
    ObserverGapStatusV1, ObserverGrammarProfileId, ObserverSynthesisPipelineRequestV3,
    PipelineStageV3, PipelineStatusV3, TransportOpV1, TransportTermV1,
};

#[test]
fn direct_declared_search_has_exact_cutoff_and_exhaustion_terminals() {
    let identity = TransportTermV1 {
        source: FiniteDomainV1::new("direct-four", 4).unwrap(),
        target: FiniteDomainV1::new("direct-four", 4).unwrap(),
        op: TransportOpV1::Identity,
    };
    let exhausted = differential_transport_observer_search(
        NativePartitionTaskId::XorParity,
        ObserverGrammarProfileId::LegacyV1,
        std::slice::from_ref(&identity),
        JointSynthesisLimits::default(),
    )
    .unwrap();
    assert!(exhausted.equivalent);
    assert_eq!(exhausted.oracle.status, JointSynthesisStatus::Exhausted);

    for (limits, cutoff) in [
        (
            JointSynthesisLimits {
                transform_limit: 1,
                ..JointSynthesisLimits::default()
            },
            JointBudgetCutoff::Transforms,
        ),
        (
            JointSynthesisLimits {
                candidate_limit: 1,
                ..JointSynthesisLimits::default()
            },
            JointBudgetCutoff::Candidates,
        ),
        (
            JointSynthesisLimits {
                relation_evaluation_limit: 5,
                ..JointSynthesisLimits::default()
            },
            JointBudgetCutoff::RelationEvaluations,
        ),
    ] {
        let terms = if cutoff == JointBudgetCutoff::Transforms {
            vec![identity.clone(), identity.clone()]
        } else {
            vec![identity.clone()]
        };
        let report = differential_transport_observer_search(
            NativePartitionTaskId::XorParity,
            ObserverGrammarProfileId::ParityV2,
            &terms,
            limits,
        )
        .unwrap();
        assert!(report.equivalent);
        assert_eq!(report.oracle.status, JointSynthesisStatus::Incomplete);
        assert_eq!(report.oracle.ledger.cutoff, Some(cutoff));
    }
}

fn gap_request(limits: JointSynthesisLimits) -> ObserverGapRequestV1 {
    ObserverGapRequestV1 {
        task_id: NativePartitionTaskId::XorParity,
        grammar_profile_id: ObserverGrammarProfileId::ParityV2,
        joint_limits: limits,
        baselines: vec![NamedObserverBaselineV1 {
            name: "input".to_owned(),
            observer_ordinal: 0,
        }],
        policy: ObserverGapPolicyV1::default(),
        information_loss_penalty: 0,
    }
}

fn pipeline_request(limits: JointSynthesisLimits) -> ObserverSynthesisPipelineRequestV3 {
    let differential = differential_joint_search(
        NativePartitionTaskId::XorParity,
        ObserverGrammarProfileId::ParityV2,
        JointSynthesisLimits::default(),
    )
    .unwrap();
    let ordinal = differential.oracle.winner.unwrap().transform_ordinal;
    let family = enumerate_representation_family().unwrap();
    let transform = &family.transforms[ordinal];
    ObserverSynthesisPipelineRequestV3 {
        gap_request: gap_request(limits),
        transports: vec![TransportTermV1 {
            source: FiniteDomainV1::new("legacy-four-abstract-states-v1", 4).unwrap(),
            target: FiniteDomainV1::new("bounded-recurrence-encoding-0-8-v1", 9).unwrap(),
            op: TransportOpV1::CanonicalEncode(
                transform
                    .permutation()
                    .into_iter()
                    .map(|value| u16::from(value) + u16::from(transform.shift()))
                    .collect(),
            ),
        }],
    }
}

#[test]
fn optimized_search_matches_reference_across_registered_matrix_and_cutoffs() {
    for task in [
        NativePartitionTaskId::OneVsThree,
        NativePartitionTaskId::XorParity,
    ] {
        for profile in [
            ObserverGrammarProfileId::LegacyV1,
            ObserverGrammarProfileId::ParityV2,
        ] {
            for limits in [
                JointSynthesisLimits::default(),
                JointSynthesisLimits {
                    relation_evaluation_limit: 131,
                    ..JointSynthesisLimits::default()
                },
            ] {
                let report = differential_joint_search(task, profile, limits).unwrap();
                assert_eq!(report.verdict, JointDifferentialVerdictV1::Equivalent);
                assert_eq!(
                    report.optimized.observation_cache,
                    "exact-four-state-response-vector"
                );
                if report.optimized.winner.is_some() {
                    assert!(report.optimized.pruned_higher_cost_pairs > 0);
                } else {
                    assert_eq!(report.optimized.pruned_higher_cost_pairs, 0);
                }
            }
        }
    }
}

#[test]
fn gap_and_pipeline_have_exact_positive_and_atomic_incomplete_terminals() {
    let (positive, negative) =
        observer_gap_calibration_requests(JointSynthesisLimits::default()).unwrap();
    let gap = run_observer_gap_lab(&positive).unwrap();
    assert_eq!(gap.status, ObserverGapStatusV1::Positive);
    let vector = gap.witness.unwrap().vector;
    assert_eq!((vector.fit_gain, vector.class_saving_gain), (2, 2));
    assert_eq!(
        run_observer_gap_lab(&negative).unwrap().status,
        ObserverGapStatusV1::NoGap
    );

    let ready =
        run_observer_synthesis_pipeline_v3(&pipeline_request(JointSynthesisLimits::default()))
            .unwrap();
    assert_eq!(ready.status, PipelineStatusV3::Ready);
    let evidence = ready.evidence.unwrap();
    assert_eq!(evidence.selected_transport_ordinal, 0);
    assert_eq!(
        evidence
            .stages
            .iter()
            .map(|row| row.stage)
            .collect::<Vec<_>>(),
        vec![
            PipelineStageV3::Normalize,
            PipelineStageV3::Transport,
            PipelineStageV3::Observer,
            PipelineStageV3::Explanation,
            PipelineStageV3::Aggregate,
        ]
    );
    for ordinal in 1..evidence.stages.len() {
        assert_eq!(
            evidence.stages[ordinal].predecessor_digest.as_deref(),
            Some(evidence.stages[ordinal - 1].stage_digest.as_str())
        );
    }

    let incomplete = run_observer_synthesis_pipeline_v3(&pipeline_request(JointSynthesisLimits {
        relation_evaluation_limit: 5,
        ..JointSynthesisLimits::default()
    }))
    .unwrap();
    assert_eq!(incomplete.status, PipelineStatusV3::Incomplete);
    assert!(incomplete.evidence.is_none());

    let mut mismatch = pipeline_request(JointSynthesisLimits::default());
    mismatch.transports = vec![TransportTermV1 {
        source: FiniteDomainV1::new("mismatch", 4).unwrap(),
        target: FiniteDomainV1::new("mismatch", 4).unwrap(),
        op: TransportOpV1::Identity,
    }];
    let blocked = run_observer_synthesis_pipeline_v3(&mismatch).unwrap();
    assert_eq!(blocked.status, PipelineStatusV3::Blocked);
    assert_eq!(blocked.failed_stage, Some(PipelineStageV3::Observer));
    assert!(blocked.evidence.is_none());

    let mut untrusted = pipeline_request(JointSynthesisLimits::default());
    untrusted.gap_request.information_loss_penalty = 1;
    assert!(run_observer_synthesis_pipeline_v3(&untrusted).is_err());
}

#[test]
fn lossy_declared_transport_is_actually_searched_and_penalized() {
    let mut request = pipeline_request(JointSynthesisLimits::default());
    request.transports = vec![TransportTermV1 {
        source: FiniteDomainV1::new("lossy-four", 4).unwrap(),
        target: FiniteDomainV1::new("lossy-two", 2).unwrap(),
        op: TransportOpV1::Group(vec![0, 1, 1, 0]),
    }];
    let report = run_observer_synthesis_pipeline_v3(&request).unwrap();
    assert_eq!(report.status, PipelineStatusV3::Ready);
    let evidence = report.evidence.unwrap();
    assert_eq!(evidence.selected_transport_ordinal, 0);
    assert!(evidence.transports[0].collision_count > 0);
    assert_eq!(
        evidence.selected_transport_collision_count,
        evidence.transports[0].collision_count
    );
    assert_eq!(evidence.selected_joint_cost, 1);
    assert_eq!(evidence.observer_gap_status, ObserverGapStatusV1::NoGap);

    request.gap_request.policy = ObserverGapPolicyV1 {
        minimum_fit_gain: 0,
        minimum_class_saving_gain: 0,
        maximum_cost_delta: 16,
        permit_information_loss: true,
    };
    let opted_in = run_observer_synthesis_pipeline_v3(&request).unwrap();
    assert_eq!(opted_in.status, PipelineStatusV3::Ready);
    assert_eq!(
        opted_in.evidence.unwrap().observer_gap_status,
        ObserverGapStatusV1::NoGap,
        "loss acknowledgement must not mint a positive observer gap"
    );
}
