//! Focused fail-closed and delegated-host tests for strict observer worker v5.

use std::path::{Path, PathBuf};

use vam_native::observer_synthesis::{
    canonical_discovery_request_v5_bytes, DiscoveryBenchmarkIdV5, DiscoverySearchRequestV5,
};
#[cfg(target_os = "linux")]
use vam_native::observer_worker::{run_cgroup_v5_e2e_harness, CgroupHarnessStatusV5};
use vam_native::observer_worker::{
    supervise_discovery_v5, ObserverWorkerLaunchV5, ObserverWorkerLimitsV5,
};

fn worker_path() -> &'static Path {
    Path::new(env!("CARGO_BIN_EXE_vam-observer-pipeline-worker"))
}

fn request() -> Vec<u8> {
    canonical_discovery_request_v5_bytes(&DiscoverySearchRequestV5::systematic(
        DiscoveryBenchmarkIdV5::HiddenAffine,
    ))
    .unwrap()
}

#[test]
fn v5_accepts_only_canonical_discovery_requests_before_launch() {
    let error = supervise_discovery_v5(
        worker_path(),
        b"not-a-discovery-v5-request",
        ObserverWorkerLimitsV5::default(),
        &ObserverWorkerLaunchV5::default(),
    )
    .unwrap_err();
    if cfg!(all(target_os = "linux", target_arch = "x86_64")) {
        assert_eq!(error.0, "worker-v5-request-decode");
    } else {
        assert_eq!(error.0, "worker-v5-platform-unsupported");
    }
}

#[test]
fn v5_rejects_missing_cgroup_delegation_and_rootfs_base() {
    let missing_delegation = supervise_discovery_v5(
        worker_path(),
        &request(),
        ObserverWorkerLimitsV5::default(),
        &ObserverWorkerLaunchV5::default(),
    )
    .unwrap_err();
    if cfg!(all(target_os = "linux", target_arch = "x86_64")) {
        assert_eq!(missing_delegation.0, "worker-v5-delegation-required");
        let missing_rootfs = supervise_discovery_v5(
            worker_path(),
            &request(),
            ObserverWorkerLimitsV5::default(),
            &ObserverWorkerLaunchV5 {
                delegated_cgroup_root: Some(PathBuf::from("/sys/fs/cgroup")),
                rootfs_mount_base: None,
            },
        )
        .unwrap_err();
        assert_eq!(missing_rootfs.0, "worker-v5-rootfs-base-required");
    } else {
        assert_eq!(missing_delegation.0, "worker-v5-platform-unsupported");
    }
}

#[test]
fn v5_rejects_invalid_limits_and_false_delegation() {
    let invalid = supervise_discovery_v5(
        worker_path(),
        &request(),
        ObserverWorkerLimitsV5 {
            pids: 0,
            ..ObserverWorkerLimitsV5::default()
        },
        &ObserverWorkerLaunchV5::default(),
    )
    .unwrap_err();
    if cfg!(all(target_os = "linux", target_arch = "x86_64")) {
        assert_eq!(invalid.0, "worker-v5-invalid-limits");
        let false_root = supervise_discovery_v5(
            worker_path(),
            &request(),
            ObserverWorkerLimitsV5::default(),
            &ObserverWorkerLaunchV5 {
                delegated_cgroup_root: Some(std::env::temp_dir()),
                rootfs_mount_base: Some(std::env::current_dir().unwrap()),
            },
        )
        .unwrap_err();
        assert_eq!(false_root.0, "worker-v5-cgroup-delegation-invalid");
    } else {
        assert_eq!(invalid.0, "worker-v5-platform-unsupported");
    }
}

#[cfg(target_os = "linux")]
#[test]
fn delegated_cgroup_harness_is_explicitly_passed_or_unavailable() {
    let root = std::env::var_os("VEYRA_V5_CGROUP_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("/sys/fs/cgroup/veyra-not-delegated"));
    let report = run_cgroup_v5_e2e_harness(&root, ObserverWorkerLimitsV5::default()).unwrap();
    match report.status() {
        CgroupHarnessStatusV5::Passed => {
            assert!(report.controls_readback());
            assert!(report.cpu_limit_readback());
            assert!(report.memory_limit_readback());
            assert!(report.pids_limit_readback());
            assert!(report.normal_cleanup());
            assert!(report.sigkill_cleanup());
            assert!(report.crash_cleanup());
        }
        CgroupHarnessStatusV5::Unavailable => {
            assert_ne!(report.reason(), "passed");
            assert!(!report.controls_readback());
        }
    }
}

#[cfg(target_os = "linux")]
#[test]
fn cgroup_harness_rejects_invalid_limits_before_host_probe() {
    let error = run_cgroup_v5_e2e_harness(
        Path::new("/sys/fs/cgroup/veyra-not-delegated"),
        ObserverWorkerLimitsV5 {
            memory_bytes: 1,
            ..ObserverWorkerLimitsV5::default()
        },
    )
    .unwrap_err();
    assert_eq!(error.0, "worker-v5-invalid-limits");
}
