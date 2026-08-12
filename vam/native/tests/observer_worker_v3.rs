//! Focused physical-custody tests for the observer pipeline worker.

use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::{Mutex, MutexGuard, OnceLock};

#[cfg(target_os = "linux")]
use std::os::fd::AsRawFd;
#[cfg(target_os = "linux")]
use std::os::unix::fs::PermissionsExt;
#[cfg(target_os = "linux")]
use std::os::unix::process::CommandExt;

use vam_native::observer_synthesis::{
    differential_joint_search, enumerate_representation_family, FiniteDomainV1,
    JointSynthesisLimits, NamedObserverBaselineV1, NativePartitionTaskId, ObserverGapPolicyV1,
    ObserverGapRequestV1, ObserverGrammarProfileId, ObserverSynthesisPipelineRequestV3,
    TransportOpV1, TransportTermV1,
};
use vam_native::observer_worker::{
    encode_observer_pipeline_request_v3, supervise_observer_pipeline_v3, ObserverWorkerLimitsV3,
    ObserverWorkerStatusV3, WorkerV2Policy,
};

fn worker_path() -> &'static Path {
    Path::new(env!("CARGO_BIN_EXE_vam-observer-pipeline-worker"))
}

fn clean_worker_command() -> Command {
    let mut command = Command::new(worker_path());
    #[cfg(target_os = "linux")]
    unsafe {
        command.pre_exec(|| {
            if close_range(3, u32::MAX, CLOSE_RANGE_CLOEXEC) == 0 {
                Ok(())
            } else {
                Err(std::io::Error::last_os_error())
            }
        });
    }
    command
}

fn child_process_lock() -> MutexGuard<'static, ()> {
    static LOCK: OnceLock<Mutex<()>> = OnceLock::new();
    LOCK.get_or_init(|| Mutex::new(())).lock().unwrap()
}

fn request() -> ObserverSynthesisPipelineRequestV3 {
    let limits = JointSynthesisLimits::default();
    let differential = differential_joint_search(
        NativePartitionTaskId::XorParity,
        ObserverGrammarProfileId::ParityV2,
        limits,
    )
    .unwrap();
    let winner = differential.oracle.winner.unwrap();
    let family = enumerate_representation_family().unwrap();
    let transform = &family.transforms[winner.transform_ordinal];
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

#[test]
fn parent_promotes_only_parent_owned_controls_after_exact_fresh_replay() {
    if !cfg!(target_os = "linux") {
        return;
    }
    let _guard = child_process_lock();
    let request = encode_observer_pipeline_request_v3(&request()).unwrap();
    let receipt = supervise_observer_pipeline_v3(
        worker_path(),
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
    assert!(!receipt.canonical_result.is_empty());

    let alternate = supervise_observer_pipeline_v3(
        worker_path(),
        &request,
        WorkerV2Policy::Baseline,
        ObserverWorkerLimitsV3 {
            wall_timeout_ms: 9_999,
            ..ObserverWorkerLimitsV3::default()
        },
    )
    .unwrap();
    assert_eq!(receipt.canonical_result, alternate.canonical_result);
    assert_ne!(
        receipt.receipt_digest, alternate.receipt_digest,
        "parent receipt must bind its wall/output custody limits"
    );
}

#[test]
fn directly_invoked_child_can_emit_only_custody_pending() {
    if !cfg!(target_os = "linux") {
        return;
    }
    let _guard = child_process_lock();
    let request = encode_observer_pipeline_request_v3(&request()).unwrap();
    let mut command = clean_worker_command();
    command
        .arg("--child")
        .arg("10")
        .arg((512_u64 * 1024 * 1024).to_string())
        .env_clear()
        .stdin(Stdio::piped())
        .stdout(Stdio::piped());
    #[cfg(target_os = "linux")]
    command.process_group(0);
    let mut child = command.spawn().unwrap();
    child.stdin.take().unwrap().write_all(&request).unwrap();
    let output = child.wait_with_output().unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(&output.stdout[..4], b"VOW3");
    assert_eq!(output.stdout[6], 0, "child status must be custody-pending");
    assert_eq!(output.stdout[7], 0x0f, "all child controls are enforced");
    assert_eq!(output.stdout[8], 0, "no parent control may be promoted");
}

#[test]
fn strict_policy_blocks_before_launching_the_child() {
    let request = encode_observer_pipeline_request_v3(&request()).unwrap();
    let error = supervise_observer_pipeline_v3(
        worker_path(),
        &request,
        WorkerV2Policy::Strict,
        ObserverWorkerLimitsV3::default(),
    )
    .unwrap_err();
    assert_eq!(error.0, "worker-v3-strict-controls-unavailable");
}

#[test]
fn parent_enforces_output_limit() {
    if !cfg!(target_os = "linux") {
        return;
    }
    let _guard = child_process_lock();
    let fake = FakeWorker::new("printf '%02048d' 0");
    let request = encode_observer_pipeline_request_v3(&request()).unwrap();
    let error = supervise_observer_pipeline_v3(
        &fake.path,
        &request,
        WorkerV2Policy::Baseline,
        ObserverWorkerLimitsV3 {
            max_response_bytes: 128,
            ..ObserverWorkerLimitsV3::default()
        },
    )
    .unwrap_err();
    assert_eq!(error.0, "worker-v3-output-limit");
}

#[test]
fn parent_enforces_wall_deadline_and_reaps_owned_group() {
    if !cfg!(target_os = "linux") {
        return;
    }
    let _guard = child_process_lock();
    let fake = FakeWorker::new("sleep 5");
    let request = encode_observer_pipeline_request_v3(&request()).unwrap();
    let error = supervise_observer_pipeline_v3(
        &fake.path,
        &request,
        WorkerV2Policy::Baseline,
        ObserverWorkerLimitsV3 {
            wall_timeout_ms: 20,
            ..ObserverWorkerLimitsV3::default()
        },
    )
    .unwrap_err();
    assert_eq!(error.0, "worker-v3-wall-timeout");
}

#[test]
fn child_rejects_an_inherited_descriptor_above_the_old_scan_window() {
    if !cfg!(target_os = "linux") {
        return;
    }
    let _guard = child_process_lock();
    #[cfg(target_os = "linux")]
    {
        let request = encode_observer_pipeline_request_v3(&request()).unwrap();
        let source = std::fs::File::open("/dev/null").unwrap();
        // SAFETY: duplicates a valid descriptor into this test process.  The
        // returned descriptor is explicitly closed after the child exits.
        let inherited = unsafe { fcntl(source.as_raw_fd(), F_DUPFD, 4096) };
        assert!(inherited >= 4096);
        let mut child = Command::new(worker_path())
            .arg("--child")
            .arg("10")
            .arg((512_u64 * 1024 * 1024).to_string())
            .env_clear()
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .unwrap();
        child.stdin.take().unwrap().write_all(&request).unwrap();
        let output = child.wait_with_output().unwrap();
        // SAFETY: `inherited` is the successful F_DUPFD result owned here.
        assert_eq!(unsafe { close(inherited) }, 0);
        assert!(!output.status.success());
        assert!(output.stdout.is_empty());
        assert!(String::from_utf8(output.stderr)
            .unwrap()
            .contains("worker-v3-child-controls-blocked"));
    }
}

#[test]
fn parent_removes_inherited_descriptor_before_child_audit() {
    if !cfg!(target_os = "linux") {
        return;
    }
    let _guard = child_process_lock();
    #[cfg(target_os = "linux")]
    {
        let request = encode_observer_pipeline_request_v3(&request()).unwrap();
        let source = std::fs::File::open("/dev/null").unwrap();
        // SAFETY: duplicates a valid descriptor into this test process. The
        // parent launch boundary must mark it close-on-exec for the worker.
        let inherited = unsafe { fcntl(source.as_raw_fd(), F_DUPFD, 4096) };
        assert!(inherited >= 4096);
        let result = supervise_observer_pipeline_v3(
            worker_path(),
            &request,
            WorkerV2Policy::Baseline,
            ObserverWorkerLimitsV3::default(),
        );
        // SAFETY: `inherited` is the successful F_DUPFD result owned here.
        assert_eq!(unsafe { close(inherited) }, 0);
        let receipt = result.unwrap();
        assert_eq!(receipt.status, ObserverWorkerStatusV3::Ready);
        assert!(receipt.controls.inherited_fd_boundary);
    }
}

struct FakeWorker {
    directory: PathBuf,
    path: PathBuf,
}

impl FakeWorker {
    fn new(body: &str) -> Self {
        let directory = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("target")
            .join(format!(
                "worker-v3-test-{}-{}",
                std::process::id(),
                body.len()
            ));
        std::fs::create_dir_all(&directory).unwrap();
        let path = directory.join("vam-observer-pipeline-worker");
        std::fs::write(&path, format!("#!/bin/sh\n{body}\n")).unwrap();
        #[cfg(target_os = "linux")]
        std::fs::set_permissions(&path, std::fs::Permissions::from_mode(0o700)).unwrap();
        Self { directory, path }
    }
}

impl Drop for FakeWorker {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.directory);
    }
}

#[cfg(target_os = "linux")]
const F_DUPFD: std::os::raw::c_int = 0;

#[cfg(target_os = "linux")]
const CLOSE_RANGE_CLOEXEC: std::os::raw::c_uint = 1 << 2;

#[cfg(target_os = "linux")]
unsafe extern "C" {
    fn fcntl(fd: std::os::raw::c_int, command: std::os::raw::c_int, ...) -> std::os::raw::c_int;
    fn close(fd: std::os::raw::c_int) -> std::os::raw::c_int;
    fn close_range(
        first: std::os::raw::c_uint,
        last: std::os::raw::c_uint,
        flags: std::os::raw::c_uint,
    ) -> std::os::raw::c_int;
}
