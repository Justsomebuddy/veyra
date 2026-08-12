//! Public integration tests for Linux worker custody and portable replay authentication.

use std::io::Write;
use std::path::Path;
use std::process::{Command, Stdio};
use std::sync::{Mutex, MutexGuard, OnceLock};
use std::time::{Duration, Instant};
use vam_native::observer_worker::{
    build_portable_replay_package, decode_portable_replay_package, decode_worker_receipt,
    encode_portable_replay_package, encode_request_frame, encode_worker_receipt_frame,
    replay_portable_package, supervise_current_executable, validate_portable_replay_package,
    IsolationProfile, NativeWorkerRequestV1, NativeWorkerStatus,
};

const KEY: &[u8] = b"0123456789abcdef0123456789abcdef";

fn worker_path() -> &'static Path {
    Path::new(env!("CARGO_BIN_EXE_vam-observer-worker"))
}

fn legacy_child_process_lock() -> MutexGuard<'static, ()> {
    static LOCK: OnceLock<Mutex<()>> = OnceLock::new();
    LOCK.get_or_init(|| Mutex::new(())).lock().unwrap()
}

#[test]
fn linux_worker_enforces_resources_and_replay_keeps_exact_receipt() {
    if !cfg!(target_os = "linux") {
        return;
    }
    let _guard = legacy_child_process_lock();
    let request = NativeWorkerRequestV1::default();
    let receipt = supervise_current_executable(worker_path(), &request).unwrap();
    assert_eq!(receipt.status, NativeWorkerStatus::Ready);
    assert!(receipt.wall_clock_enforced);
    assert!(receipt.cpu_rlimit_enforced);
    assert!(receipt.process_as_enforced);
    assert!(receipt.core_dump_disabled);
    assert!(receipt.process_group_custody);
    let receipt_bytes = encode_worker_receipt_frame(&receipt).unwrap();
    assert_eq!(decode_worker_receipt(&receipt_bytes).unwrap(), receipt);

    let request_bytes = encode_request_frame(&request).unwrap();
    let package =
        build_portable_replay_package(&request_bytes, &receipt_bytes, "test-signer", KEY).unwrap();
    assert!(validate_portable_replay_package(&package, KEY));
    assert!(!validate_portable_replay_package(
        &package,
        b"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    ));
    let encoded = encode_portable_replay_package(&package, KEY).unwrap();
    let decoded = decode_portable_replay_package(&encoded).unwrap();
    assert_eq!(decoded, package);
    assert_eq!(
        replay_portable_package(worker_path(), &decoded, KEY).unwrap(),
        receipt
    );
    assert!(!encoded.windows(KEY.len()).any(|window| window == KEY));
}

#[test]
fn strict_profile_and_tampering_fail_closed() {
    let strict = NativeWorkerRequestV1 {
        isolation_profile: IsolationProfile::Strict,
        ..NativeWorkerRequestV1::default()
    };
    assert_eq!(
        supervise_current_executable(worker_path(), &strict)
            .unwrap_err()
            .reason,
        "strict-isolation-unsupported"
    );
    if !cfg!(target_os = "linux") {
        return;
    }
    let _guard = legacy_child_process_lock();
    let request = NativeWorkerRequestV1::default();
    let receipt = supervise_current_executable(worker_path(), &request).unwrap();
    let receipt_bytes = encode_worker_receipt_frame(&receipt).unwrap();
    let request_bytes = encode_request_frame(&request).unwrap();
    let package =
        build_portable_replay_package(&request_bytes, &receipt_bytes, "test-signer", KEY).unwrap();
    let mut encoded = encode_portable_replay_package(&package, KEY).unwrap();
    let last = encoded.len() - 1;
    encoded[last] ^= 1;
    let decoded = decode_portable_replay_package(&encoded).unwrap();
    assert!(!validate_portable_replay_package(&decoded, KEY));

    let mut receipt_tamper = receipt_bytes;
    let receipt_last = receipt_tamper.len() - 1;
    receipt_tamper[receipt_last] ^= 1;
    assert!(decode_worker_receipt(&receipt_tamper).is_err());

    let mut unbound_receipt = encode_worker_receipt_frame(&receipt).unwrap();
    let digest_start = unbound_receipt.len() - 32;
    unbound_receipt[digest_start..].fill(0);
    assert!(decode_worker_receipt(&unbound_receipt).is_err());
}

#[test]
fn directly_invoked_child_cannot_mint_parent_custody() {
    if !cfg!(target_os = "linux") {
        return;
    }
    let _guard = legacy_child_process_lock();
    let request = NativeWorkerRequestV1::default();
    let request_bytes = encode_request_frame(&request).unwrap();
    let mut child = Command::new(worker_path())
        .arg("--child")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
        .unwrap();
    child
        .stdin
        .as_mut()
        .unwrap()
        .write_all(&request_bytes)
        .unwrap();
    child.stdin.take();
    let output = child.wait_with_output().unwrap();
    assert!(output.status.success());
    let pending = decode_worker_receipt(&output.stdout).unwrap();
    assert_eq!(pending.status, NativeWorkerStatus::CustodyPending);
    assert!(!pending.wall_clock_enforced);
    assert!(!pending.process_group_custody);
    assert_eq!(
        build_portable_replay_package(&request_bytes, &output.stdout, "test-signer", KEY)
            .unwrap_err(),
        "replay-worker-not-ready"
    );
}

#[test]
#[cfg(target_os = "linux")]
fn wall_timeout_kills_the_owned_descendant_group() {
    use std::fs;
    use std::os::unix::fs::PermissionsExt;

    let _guard = legacy_child_process_lock();

    let target = Path::new(env!("CARGO_MANIFEST_DIR")).join("target");
    let suffix = std::process::id();
    let helper = target.join(format!("observer-worker-timeout-{suffix}.sh"));
    let pid_file = target.join(format!("observer-worker-timeout-{suffix}.pid"));
    let script = format!(
        "#!/bin/sh\nexec /usr/bin/setsid /bin/sh -c 'sleep 30 & echo $! > \"{}\"; wait'\n",
        pid_file.display()
    );
    fs::write(&helper, script).unwrap();
    let mut permissions = fs::metadata(&helper).unwrap().permissions();
    permissions.set_mode(0o700);
    fs::set_permissions(&helper, permissions).unwrap();

    let request = NativeWorkerRequestV1 {
        wall_timeout_ms: 500,
        max_response_bytes: 1024,
        ..NativeWorkerRequestV1::default()
    };
    assert_eq!(
        supervise_current_executable(&helper, &request)
            .unwrap_err()
            .reason,
        "worker-wall-timeout"
    );
    let descendant = fs::read_to_string(&pid_file).unwrap();
    let proc_path = Path::new("/proc").join(descendant.trim());
    let deadline = Instant::now() + Duration::from_secs(1);
    while proc_path.exists() && Instant::now() < deadline {
        std::thread::sleep(Duration::from_millis(10));
    }
    assert!(
        !proc_path.exists(),
        "descendant survived process-group timeout"
    );
    let _ = fs::remove_file(helper);
    let _ = fs::remove_file(pid_file);
}

#[test]
fn fixed_worker_rejects_invalid_physical_limits() {
    let request = NativeWorkerRequestV1 {
        wall_timeout_ms: 0,
        ..NativeWorkerRequestV1::default()
    };
    assert_eq!(
        encode_request_frame(&request).unwrap_err(),
        "worker-request-limits"
    );
}

#[test]
fn decoder_rejects_partial_trailing_and_oversized_packages() {
    assert!(decode_portable_replay_package(&[]).is_err());
    let mut oversized = vec![0u8; vam_native::observer_worker::MAX_PORTABLE_REPLAY_BYTES + 1];
    assert!(decode_portable_replay_package(&oversized).is_err());
    oversized.clear();
    if !cfg!(target_os = "linux") {
        return;
    }
    let _guard = legacy_child_process_lock();
    let request = NativeWorkerRequestV1::default();
    let receipt = supervise_current_executable(worker_path(), &request).unwrap();
    let request_bytes = encode_request_frame(&request).unwrap();
    let receipt_bytes = encode_worker_receipt_frame(&receipt).unwrap();
    let package =
        build_portable_replay_package(&request_bytes, &receipt_bytes, "test-signer", KEY).unwrap();
    let encoded = encode_portable_replay_package(&package, KEY).unwrap();
    assert!(decode_portable_replay_package(&encoded[..encoded.len() - 1]).is_err());
    let mut trailing = encoded;
    trailing.push(0);
    assert!(decode_portable_replay_package(&trailing).is_err());
}
