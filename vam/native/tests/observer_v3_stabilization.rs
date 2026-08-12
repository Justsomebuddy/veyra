//! Stable behavioral contracts for the bounded observer-synthesis v3 surface.
//!
//! These tests intentionally use only public APIs. They pin finite vectors and
//! metamorphic properties without treating a passing executable test as a
//! theorem or as evidence beyond the declared four-state catalogs.

use std::collections::BTreeSet;
#[cfg(target_os = "linux")]
use std::io::Write;
use std::path::Path;
#[cfg(target_os = "linux")]
use std::process::{Command, Stdio};

#[cfg(target_os = "linux")]
use std::os::unix::process::CommandExt;

use vam_native::observer_synthesis::{
    apply_transport, compile_legacy_representation_transform, compile_transport, compose_transport,
    differential_joint_search, differential_transport_observer_search,
    enumerate_representation_family, run_observer_synthesis_pipeline_v3, FiniteDomainV1,
    JointDifferentialVerdictV1, JointSynthesisLimits, NamedObserverBaselineV1,
    NativePartitionTaskId, ObserverGapPolicyV1, ObserverGapRequestV1, ObserverGrammarProfileId,
    ObserverSynthesisPipelineRequestV3, PipelineStatusV3, TransportInformationClassV1,
    TransportOpV1, TransportTermV1, MAX_TRANSPORT_COMPOSITION_COST, MAX_TRANSPORT_DEPTH,
    MAX_TRANSPORT_NODES,
};
use vam_native::observer_worker::{
    build_hmac_observer_pipeline_bundle_v3, decode_observer_pipeline_request_v3,
    encode_observer_pipeline_request_v3, supervise_observer_pipeline_v3, HmacReplayTrustV2,
    ObserverWorkerLimitsV3, ObserverWorkerStatusV3, ReplayTrustPolicyV2, WorkerV2Policy,
    MAX_PIPELINE_REQUEST_V3_BYTES,
};

const HMAC_KEY: &[u8] = b"observer-v3-stabilization-key-0001";
const HMAC_KEY_ID: [u8; 32] = [0xa7; 32];

#[cfg(target_os = "linux")]
const CLOSE_RANGE_CLOEXEC: u32 = 4;

#[cfg(target_os = "linux")]
unsafe extern "C" {
    fn close_range(first: u32, last: u32, flags: u32) -> i32;
}

fn four(id: &str) -> FiniteDomainV1 {
    FiniteDomainV1::new(id, 4).unwrap()
}

fn explicit_request() -> ObserverSynthesisPipelineRequestV3 {
    ObserverSynthesisPipelineRequestV3 {
        gap_request: ObserverGapRequestV1 {
            task_id: NativePartitionTaskId::XorParity,
            grammar_profile_id: ObserverGrammarProfileId::ParityV2,
            joint_limits: JointSynthesisLimits::default(),
            baselines: vec![NamedObserverBaselineV1 {
                name: "input".to_owned(),
                observer_ordinal: 0,
            }],
            policy: ObserverGapPolicyV1::default(),
            information_loss_penalty: 0,
        },
        transports: vec![TransportTermV1 {
            source: four("legacy-four-abstract-states-v1"),
            target: FiniteDomainV1::new("bounded-recurrence-encoding-0-8-v1", 9).unwrap(),
            op: TransportOpV1::CanonicalEncode(vec![0, 1, 3, 2]),
        }],
    }
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}

#[test]
fn explicit_v3_request_result_and_hmac_envelope_match_golden_vectors() {
    let request = explicit_request();
    let encoded = encode_observer_pipeline_request_v3(&request).unwrap();
    let result = run_observer_synthesis_pipeline_v3(&request).unwrap();
    let bundle =
        build_hmac_observer_pipeline_bundle_v3(&request, "v3-stabilization", HMAC_KEY_ID, HMAC_KEY)
            .unwrap();
    assert_eq!(
        hex(&encoded),
        concat!(
            "56505233000102020000007800000800001e848000010005696e70757400000000",
            "00000001000000010000001000000000000001001e6c65676163792d666f7572",
            "2d61627374726163742d7374617465732d763100040022626f756e6465642d72",
            "6563757272656e63652d656e636f64696e672d302d382d763100090600040000",
            "000100030002"
        )
    );
    assert_eq!(result.status, PipelineStatusV3::Ready);
    assert_eq!(
        result.audit_digest,
        "fd80d14287c11ea4ac24d20ee18cb7145f2011afe60dabca34ef3d8ea228736d"
    );
    assert_eq!(
        result.evidence.unwrap().evidence_digest,
        "2c8f7a79e2aecf1f3e1d47928f8abe73ead49e70c19b9af4686cb88c81e0a4be"
    );
    assert_eq!(bundle.worker_request, encoded);
    assert_eq!(bundle.worker_receipt.len(), 1_956);
    assert_eq!(
        hex(&bundle.payload_digest),
        "b2a03d5149dc7dba1c02c7940ea774047e70cf6a2216658273d857fa37fb5d30"
    );
    assert_eq!(
        hex(&bundle.authentication),
        "f910c99b1cd2c5cea68858757791287375cddee93f17a72815e08a19b3c3db76"
    );
}

#[test]
fn optimized_and_reference_terminals_are_identical_across_complete_and_cutoff_cases() {
    let cases = [
        JointSynthesisLimits::default(),
        JointSynthesisLimits {
            transform_limit: 1,
            ..JointSynthesisLimits::default()
        },
        JointSynthesisLimits {
            candidate_limit: 1,
            ..JointSynthesisLimits::default()
        },
        JointSynthesisLimits {
            relation_evaluation_limit: 131,
            ..JointSynthesisLimits::default()
        },
    ];
    for task in [
        NativePartitionTaskId::OneVsThree,
        NativePartitionTaskId::XorParity,
    ] {
        for profile in [
            ObserverGrammarProfileId::LegacyV1,
            ObserverGrammarProfileId::ParityV2,
        ] {
            for limits in cases {
                let report = differential_joint_search(task, profile, limits).unwrap();
                assert_eq!(report.verdict, JointDifferentialVerdictV1::Equivalent);
                assert_eq!(report.oracle.status, report.optimized.status);
                assert_eq!(report.oracle.detail, report.optimized.detail);
                assert_eq!(report.oracle.ledger, report.optimized.ledger);
                assert_eq!(report.oracle.winner, report.optimized.winner);
                assert_eq!(
                    report.oracle.grammar_profile_digest,
                    report.optimized.grammar_profile_digest
                );
                assert_eq!(
                    report.oracle.catalog_digest,
                    report.optimized.catalog_digest
                );
                assert_eq!(
                    report.oracle.representation_family_digest,
                    report.optimized.representation_family_digest
                );
            }
        }
    }
}

#[test]
fn direct_search_terminal_is_invariant_under_declared_transport_permutation() {
    let domain = four("metamorphic-four");
    let mut transports = vec![
        TransportTermV1 {
            source: domain.clone(),
            target: domain.clone(),
            op: TransportOpV1::Identity,
        },
        TransportTermV1 {
            source: domain.clone(),
            target: domain,
            op: TransportOpV1::Relabel(vec![1, 0, 3, 2]),
        },
    ];
    let forward = differential_transport_observer_search(
        NativePartitionTaskId::XorParity,
        ObserverGrammarProfileId::ParityV2,
        &transports,
        JointSynthesisLimits::default(),
    )
    .unwrap();
    transports.reverse();
    let reverse = differential_transport_observer_search(
        NativePartitionTaskId::XorParity,
        ObserverGrammarProfileId::ParityV2,
        &transports,
        JointSynthesisLimits::default(),
    )
    .unwrap();
    assert!(forward.equivalent && reverse.equivalent);
    assert_eq!(forward.oracle.status, reverse.oracle.status);
    assert_eq!(
        forward.oracle.winner.as_ref().map(|row| row.joint_cost),
        reverse.oracle.winner.as_ref().map(|row| row.joint_cost)
    );
    assert_eq!(
        forward
            .oracle
            .winner
            .as_ref()
            .map(|row| row.observer_digest.as_str()),
        reverse
            .oracle
            .winner
            .as_ref()
            .map(|row| row.observer_digest.as_str())
    );
}

#[test]
fn all_twenty_four_permutations_cancel_with_their_inverse() {
    let family = enumerate_representation_family().unwrap();
    let permutations = family
        .transforms
        .iter()
        .map(|row| row.permutation())
        .collect::<BTreeSet<_>>();
    assert_eq!(permutations.len(), 24);

    let domain = four("permutation-four");
    for permutation in permutations {
        let mut inverse = vec![0; 4];
        for (source, target) in permutation.into_iter().enumerate() {
            inverse[target as usize] = source as u16;
        }
        let forward = compile_transport(&TransportTermV1 {
            source: domain.clone(),
            target: domain.clone(),
            op: TransportOpV1::Relabel(permutation.into_iter().map(u16::from).collect()),
        })
        .unwrap();
        let backward = compile_transport(&TransportTermV1 {
            source: domain.clone(),
            target: domain.clone(),
            op: TransportOpV1::Relabel(inverse),
        })
        .unwrap();
        let cancelled = compose_transport(&forward, &backward).unwrap();
        assert_eq!(cancelled.image(), &[0, 1, 2, 3]);
        assert_eq!(
            cancelled.information_class(),
            TransportInformationClassV1::Bijection
        );
        assert_eq!(cancelled.cost(), 2);
    }
}

#[test]
fn primitive_composition_matches_every_published_permutation_shift_image() {
    let source = four("legacy-four-abstract-states-v1");
    let middle = four("metamorphic-middle-four");
    let target = FiniteDomainV1::new("bounded-recurrence-encoding-0-8-v1", 9).unwrap();
    for transform in &enumerate_representation_family().unwrap().transforms {
        let permutation = compile_transport(&TransportTermV1 {
            source: source.clone(),
            target: middle.clone(),
            op: TransportOpV1::Relabel(
                transform.permutation().into_iter().map(u16::from).collect(),
            ),
        })
        .unwrap();
        let shift = compile_transport(&TransportTermV1 {
            source: middle.clone(),
            target: target.clone(),
            op: TransportOpV1::ShiftEmbed(u16::from(transform.shift())),
        })
        .unwrap();
        let composed = compose_transport(&permutation, &shift).unwrap();
        let legacy = compile_legacy_representation_transform(transform).unwrap();
        assert_eq!(composed.image(), legacy.image());
        assert_eq!(
            apply_transport(&composed, &[3, 2, 1, 0]).unwrap(),
            apply_transport(&legacy, &[3, 2, 1, 0]).unwrap()
        );
        assert_eq!(composed.cost(), 2);
        assert_eq!(legacy.cost(), 5);
    }
}

#[test]
fn transport_cost_node_and_depth_edges_are_fail_closed() {
    let domain = four("boundary-four");
    let identity = compile_transport(&TransportTermV1 {
        source: domain.clone(),
        target: domain.clone(),
        op: TransportOpV1::Identity,
    })
    .unwrap();
    let mut at_cost_limit = identity.clone();
    for _ in 1..MAX_TRANSPORT_COMPOSITION_COST {
        at_cost_limit = compose_transport(&at_cost_limit, &identity).unwrap();
    }
    assert_eq!(
        at_cost_limit.cost(),
        u32::from(MAX_TRANSPORT_COMPOSITION_COST)
    );
    assert_eq!(at_cost_limit.image(), identity.image());
    assert_eq!(
        compose_transport(&at_cost_limit, &identity).unwrap_err().0,
        "transport-classification-shape"
    );

    let leaf = TransportTermV1 {
        source: domain.clone(),
        target: domain.clone(),
        op: TransportOpV1::Identity,
    };
    let maximum_flat_tree = TransportTermV1 {
        source: domain.clone(),
        target: domain.clone(),
        op: TransportOpV1::Compose(vec![leaf.clone(); MAX_TRANSPORT_NODES as usize - 1]),
    };
    assert_eq!(
        compile_transport(&maximum_flat_tree).unwrap().cost(),
        u32::from(MAX_TRANSPORT_NODES - 1)
    );
    let over_node_limit = TransportTermV1 {
        source: domain.clone(),
        target: domain.clone(),
        op: TransportOpV1::Compose(vec![leaf.clone(); MAX_TRANSPORT_NODES as usize]),
    };
    assert_eq!(
        compile_transport(&over_node_limit).unwrap_err().0,
        "transport-node-limit"
    );

    let mut deepest_valid = leaf.clone();
    for _ in 0..MAX_TRANSPORT_DEPTH - 1 {
        deepest_valid = TransportTermV1 {
            source: domain.clone(),
            target: domain.clone(),
            op: TransportOpV1::Compose(vec![deepest_valid, leaf.clone()]),
        };
    }
    assert!(compile_transport(&deepest_valid).is_ok());
    let too_deep = TransportTermV1 {
        source: domain.clone(),
        target: domain,
        op: TransportOpV1::Compose(vec![deepest_valid, leaf]),
    };
    assert_eq!(
        compile_transport(&too_deep).unwrap_err().0,
        "transport-depth-limit"
    );
}

#[test]
fn canonical_request_decoder_rejects_hostile_framing_and_noncanonical_fields() {
    let encoded = encode_observer_pipeline_request_v3(&explicit_request()).unwrap();
    assert_eq!(
        decode_observer_pipeline_request_v3(&encoded).unwrap(),
        explicit_request()
    );

    for split in 0..encoded.len() {
        assert!(decode_observer_pipeline_request_v3(&encoded[..split]).is_err());
    }
    let mut trailing = encoded.clone();
    trailing.push(0);
    assert!(decode_observer_pipeline_request_v3(&trailing).is_err());

    for (offset, value) in [(0, b'X'), (5, 2), (6, 0), (7, 0), (45, 2)] {
        let mut mutation = encoded.clone();
        mutation[offset] = value;
        assert!(
            decode_observer_pipeline_request_v3(&mutation).is_err(),
            "mutation at byte {offset} was accepted"
        );
    }

    let oversized = vec![0; MAX_PIPELINE_REQUEST_V3_BYTES + 1];
    assert!(decode_observer_pipeline_request_v3(&oversized).is_err());
}

#[test]
fn custody_states_cannot_be_promoted_by_policy_or_invalid_limits() {
    let request = encode_observer_pipeline_request_v3(&explicit_request()).unwrap();
    let worker = Path::new(env!("CARGO_BIN_EXE_vam-observer-pipeline-worker"));
    let strict = supervise_observer_pipeline_v3(
        worker,
        &request,
        WorkerV2Policy::Strict,
        ObserverWorkerLimitsV3::default(),
    )
    .unwrap_err();
    assert_eq!(strict.0, "worker-v3-strict-controls-unavailable");

    for limits in [
        ObserverWorkerLimitsV3 {
            cpu_seconds: 0,
            ..ObserverWorkerLimitsV3::default()
        },
        ObserverWorkerLimitsV3 {
            address_space_bytes: 127 * 1024 * 1024,
            ..ObserverWorkerLimitsV3::default()
        },
        ObserverWorkerLimitsV3 {
            wall_timeout_ms: 0,
            ..ObserverWorkerLimitsV3::default()
        },
        ObserverWorkerLimitsV3 {
            max_response_bytes: 127,
            ..ObserverWorkerLimitsV3::default()
        },
    ] {
        assert_eq!(
            supervise_observer_pipeline_v3(worker, &request, WorkerV2Policy::Baseline, limits)
                .unwrap_err()
                .0,
            "worker-v3-invalid-limits"
        );
    }

    if cfg!(target_os = "linux") {
        let receipt = supervise_observer_pipeline_v3(
            worker,
            &request,
            WorkerV2Policy::Baseline,
            ObserverWorkerLimitsV3::default(),
        )
        .unwrap();
        assert_eq!(receipt.status, ObserverWorkerStatusV3::Ready);
        assert!(receipt.controls.no_new_privileges);
        assert!(receipt.controls.resource_limits);
        assert!(receipt.controls.child_owned_process_group);
        assert!(receipt.controls.inherited_fd_boundary);
        assert!(receipt.controls.wall_clock_limit);
        assert!(receipt.controls.output_limit);
        assert!(receipt.controls.process_group_custody);
        assert_eq!(receipt.result.status, PipelineStatusV3::Ready);
    }
}

#[test]
fn direct_child_can_report_only_pending_custody() {
    if !cfg!(target_os = "linux") {
        return;
    }
    #[cfg(target_os = "linux")]
    {
        let request = encode_observer_pipeline_request_v3(&explicit_request()).unwrap();
        let worker = Path::new(env!("CARGO_BIN_EXE_vam-observer-pipeline-worker"));
        let mut command = Command::new(worker);
        command
            .arg("--child")
            .arg("10")
            .arg((512_u64 * 1024 * 1024).to_string())
            .env_clear()
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .process_group(0);
        // SAFETY: this pre-exec closure performs one async-signal-safe Linux
        // syscall. It makes the test independent of descriptors inherited
        // from the test runner while preserving stdin/stdout/stderr.
        unsafe {
            command.pre_exec(|| {
                if close_range(3, u32::MAX, CLOSE_RANGE_CLOEXEC) == 0 {
                    Ok(())
                } else {
                    Err(std::io::Error::last_os_error())
                }
            });
        }
        let mut child = command.spawn().unwrap();
        child.stdin.take().unwrap().write_all(&request).unwrap();
        let output = child.wait_with_output().unwrap();
        assert!(
            output.status.success(),
            "{}",
            String::from_utf8_lossy(&output.stderr)
        );
        assert_eq!(&output.stdout[..4], b"VOW3");
        assert_eq!(output.stdout[6], 0, "child must remain custody-pending");
        assert_eq!(output.stdout[7], 0x0f, "child controls must be complete");
        assert_eq!(output.stdout[8], 0, "parent controls must remain unset");
    }
}

#[test]
fn hmac_bundle_is_replayable_under_the_matching_explicit_trust_root() {
    let request = explicit_request();
    let bundle =
        build_hmac_observer_pipeline_bundle_v3(&request, "v3-stabilization", HMAC_KEY_ID, HMAC_KEY)
            .unwrap();
    vam_native::observer_worker::verify_replay_bundle_v2(
        &bundle,
        &ReplayTrustPolicyV2::hmac_only(),
        &HmacReplayTrustV2::new(HMAC_KEY_ID, HMAC_KEY).unwrap(),
    )
    .unwrap();
}
