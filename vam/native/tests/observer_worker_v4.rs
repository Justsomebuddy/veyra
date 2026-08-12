//! Focused profile, custody and fail-closed tests for observer worker v4.

use std::path::Path;
use std::sync::{Mutex, MutexGuard, OnceLock};

use ed25519_dalek::SigningKey;

use vam_native::observer_synthesis::{
    differential_joint_search, enumerate_representation_family, FiniteDomainV1,
    JointSynthesisLimits, NamedObserverBaselineV1, NativePartitionTaskId, ObserverGapPolicyV1,
    ObserverGapRequestV1, ObserverGrammarProfileId, ObserverSynthesisPipelineRequestV3,
    TransportOpV1, TransportTermV1,
};
use vam_native::observer_worker::{
    build_autonomous_replay_package_from_worker_v4, encode_observer_pipeline_request_v3,
    supervise_observer_pipeline_v4, IsolationProfileV4, ManifestEntryV4, ManifestKindV4,
    ObserverWorkerLaunchV4, ObserverWorkerLimitsV4, WorkerPolicyManifestV4,
    WorkerProfileEvidenceV4,
};

fn worker_path() -> &'static Path {
    Path::new(env!("CARGO_BIN_EXE_vam-observer-pipeline-worker"))
}

fn child_process_lock() -> MutexGuard<'static, ()> {
    static LOCK: OnceLock<Mutex<()>> = OnceLock::new();
    LOCK.get_or_init(|| Mutex::new(())).lock().unwrap()
}

fn request_model() -> ObserverSynthesisPipelineRequestV3 {
    let limits = JointSynthesisLimits::default();
    let winner = differential_joint_search(
        NativePartitionTaskId::XorParity,
        ObserverGrammarProfileId::ParityV2,
        limits,
    )
    .unwrap()
    .oracle
    .winner
    .unwrap();
    let transform =
        &enumerate_representation_family().unwrap().transforms[winner.transform_ordinal];
    ObserverSynthesisPipelineRequestV3 {
        gap_request: ObserverGapRequestV1 {
            task_id: NativePartitionTaskId::XorParity,
            grammar_profile_id: ObserverGrammarProfileId::ParityV2,
            joint_limits: limits,
            baselines: vec![NamedObserverBaselineV1 {
                name: "input".to_owned(),
                observer_ordinal: 0,
            }],
            policy: ObserverGapPolicyV1::default(),
            information_loss_penalty: 0,
        },
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

fn request() -> Vec<u8> {
    encode_observer_pipeline_request_v3(&request_model()).unwrap()
}

#[test]
fn replay_package_rejects_a_receipt_for_a_distinct_valid_request() {
    if !cfg!(target_os = "linux") {
        return;
    }
    let _guard = child_process_lock();
    let receipt = supervise_observer_pipeline_v4(
        worker_path(),
        &request(),
        IsolationProfileV4::Baseline,
        ObserverWorkerLimitsV4::default(),
        &ObserverWorkerLaunchV4::default(),
    )
    .unwrap();
    let worker = WorkerPolicyManifestV4::bind_worker_receipt(&receipt).unwrap();
    let mut distinct = request_model();
    distinct.gap_request.baselines[0].name = "distinct-input".to_owned();
    let manifests = vec![
        ManifestEntryV4 {
            kind: ManifestKindV4::Source,
            name: "vam/native/src/observer_synthesis/pipeline_v3.rs".to_owned(),
            digest: [0x11; 32],
        },
        ManifestEntryV4 {
            kind: ManifestKindV4::Toolchain,
            name: "rustc-1.83.0".to_owned(),
            digest: [0x22; 32],
        },
    ];
    let error = build_autonomous_replay_package_from_worker_v4(
        &distinct,
        "wrong-request-v4",
        manifests,
        worker,
        &SigningKey::from_bytes(&[0x51; 32]),
    )
    .unwrap_err();
    assert_eq!(error.0, "replay-v4-worker-request-binding");
}

#[test]
fn baseline_preserves_v3_custody_without_claiming_isolation() {
    if !cfg!(target_os = "linux") {
        return;
    }
    let _guard = child_process_lock();
    let receipt = supervise_observer_pipeline_v4(
        worker_path(),
        &request(),
        IsolationProfileV4::Baseline,
        ObserverWorkerLimitsV4::default(),
        &ObserverWorkerLaunchV4::default(),
    )
    .unwrap();
    assert!(receipt.controls().no_new_privileges);
    assert!(receipt.controls().resource_limits);
    assert!(receipt.controls().wall_clock_limit);
    assert!(receipt.controls().output_limit);
    assert!(receipt.controls().process_group_custody);
    assert!(receipt.controls().parent_control_readback);
    assert!(!receipt.controls().namespaces);
    assert!(!receipt.controls().seccomp_allowlist);
    assert!(!receipt.controls().filesystem_closed);
    assert!(!receipt.controls().cgroup_limits);
    assert!(!receipt.controls().cgroup_membership);
    assert!(!receipt.controls().cgroup_cleanup);
    assert_ne!(receipt.isolation_policy_digest(), [0; 32]);
    let policy = WorkerPolicyManifestV4::from_worker_receipt(&receipt).unwrap();
    assert_eq!(policy.profile(), WorkerProfileEvidenceV4::Baseline);
    assert_eq!(policy.receipt_digest(), receipt.receipt_digest());
    assert!(policy.custody_ready());
}

#[test]
fn receipt_binds_declared_physical_limits() {
    if !cfg!(target_os = "linux") {
        return;
    }
    let _guard = child_process_lock();
    let request = request();
    let first = supervise_observer_pipeline_v4(
        worker_path(),
        &request,
        IsolationProfileV4::Baseline,
        ObserverWorkerLimitsV4::default(),
        &ObserverWorkerLaunchV4::default(),
    )
    .unwrap();
    let second = supervise_observer_pipeline_v4(
        worker_path(),
        &request,
        IsolationProfileV4::Baseline,
        ObserverWorkerLimitsV4 {
            cgroup_cpu_quota_us: 50_000,
            ..ObserverWorkerLimitsV4::default()
        },
        &ObserverWorkerLaunchV4::default(),
    )
    .unwrap();
    assert_eq!(first.canonical_result(), second.canonical_result());
    assert_ne!(first.receipt_digest(), second.receipt_digest());
}

#[test]
fn strict_rejects_missing_or_false_delegation_before_launch() {
    let request = request();
    let missing = supervise_observer_pipeline_v4(
        worker_path(),
        &request,
        IsolationProfileV4::Strict,
        ObserverWorkerLimitsV4::default(),
        &ObserverWorkerLaunchV4::default(),
    )
    .unwrap_err();
    if cfg!(all(target_os = "linux", target_arch = "x86_64")) {
        assert_eq!(missing.0, "worker-v4-delegation-required");
    } else {
        assert!(missing.0.contains("unavailable") || missing.0.contains("unsupported"));
    }

    if cfg!(all(target_os = "linux", target_arch = "x86_64")) {
        let false_root = supervise_observer_pipeline_v4(
            worker_path(),
            &request,
            IsolationProfileV4::Strict,
            ObserverWorkerLimitsV4::default(),
            &ObserverWorkerLaunchV4 {
                delegated_cgroup_root: Some(std::env::temp_dir()),
            },
        )
        .unwrap_err();
        assert_eq!(false_root.0, "worker-v4-cgroup-delegation-invalid");
    }
}

#[test]
fn isolated_is_enforced_or_truthfully_blocked_by_the_host_kernel() {
    if !cfg!(all(target_os = "linux", target_arch = "x86_64")) {
        return;
    }
    let _guard = child_process_lock();
    let result = supervise_observer_pipeline_v4(
        worker_path(),
        &request(),
        IsolationProfileV4::Isolated,
        ObserverWorkerLimitsV4::default(),
        &ObserverWorkerLaunchV4::default(),
    );
    match result {
        Ok(receipt) => {
            assert_eq!(receipt.profile(), IsolationProfileV4::Isolated);
            assert!(receipt.controls().no_new_privileges);
            assert!(receipt.controls().resource_limits);
            assert!(receipt.controls().child_owned_process_group);
            assert!(receipt.controls().inherited_fd_boundary);
            assert!(receipt.controls().namespaces);
            assert!(receipt.controls().seccomp_allowlist);
            assert!(receipt.controls().parent_control_readback);
            assert!(!receipt.controls().filesystem_closed);
            assert!(!receipt.controls().cgroup_limits);
            assert!(!receipt.controls().cgroup_membership);
            assert!(!receipt.controls().cgroup_cleanup);
            assert!(receipt.controls().wall_clock_limit);
            assert!(receipt.controls().output_limit);
            assert!(receipt.controls().process_group_custody);
        }
        Err(error) => assert!(matches!(
            error.0,
            "worker-v4-child-setup-exit" | "worker-v4-control-readback-timeout"
        )),
    }
}
