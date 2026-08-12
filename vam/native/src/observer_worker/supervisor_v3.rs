//! Physically bounded parent/child execution for canonical observer pipelines.
//!
//! The child can attest only controls that it applies and reads back.  The
//! supervising parent alone promotes wall-clock, output-drain and process-group
//! custody after it has drained, killed if necessary, and reaped the owned
//! group.  Strict mode remains blocked until its cgroup/seccomp/namespace
//! controls have real implementations.

use std::fmt;
use std::io::{Read, Write};
use std::path::Path;
use std::process::{Child, Command, ExitStatus, Stdio};
use std::sync::mpsc::{self, TryRecvError};
use std::thread;
use std::time::{Duration, Instant};

#[cfg(target_os = "linux")]
use std::os::unix::process::CommandExt;

use crate::observer_synthesis::{
    run_observer_synthesis_pipeline_v3, ObserverSynthesisPipelineResultV3,
};

use super::digest::domain_sha256;
use super::event;
use super::linux::signal_process_group;
use super::pipeline_replay_v3::{
    canonical_observer_pipeline_result_v3_bytes, decode_observer_pipeline_request_v3,
    encode_observer_pipeline_request_v3, MAX_PIPELINE_REQUEST_V3_BYTES,
    MAX_PIPELINE_RESULT_V3_BYTES,
};
use super::worker_v2::{
    apply_worker_v2_child_controls, WorkerControlStateV2, WorkerV2Admission, WorkerV2LaunchOptions,
    WorkerV2Limits, WorkerV2Policy,
};

const WIRE_MAGIC: &[u8; 4] = b"VOW3";
const WIRE_VERSION: u16 = 3;
const REQUEST_DOMAIN: &[u8] = b"veyra.native-observer-worker.v3.request";
const RESULT_DOMAIN: &[u8] = b"veyra.native-observer-worker.v3.result";
const RECEIPT_DOMAIN: &[u8] = b"veyra.native-observer-worker.v3.receipt";
const FIXED_CHILD_NAME: &str = "vam-observer-pipeline-worker";
const WIRE_FIXED_BYTES: usize = 122;
const MAX_WORKER_V3_RESPONSE_BYTES: usize = MAX_PIPELINE_RESULT_V3_BYTES + WIRE_FIXED_BYTES;
const POLL_INTERVAL: Duration = Duration::from_millis(5);
const TERM_GRACE: Duration = Duration::from_millis(200);

pub const OBSERVER_WORKER_V3_BOUNDARY: &str = "the caller-trusted fixed-name child path is not executable attestation; the Linux parent marks every descriptor above stderr close-on-exec and the child independently audits the post-exec table before applying and reading back baseline controls; only the supervising parent may promote wall-clock, bounded-output, and owned-process-group custody after exact fresh request/result replay; strict execution blocks until real cgroup-v2, seccomp, and namespace controls exist";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ObserverWorkerStatusV3 {
    CustodyPending,
    Ready,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObserverWorkerControlsV3 {
    pub no_new_privileges: bool,
    pub resource_limits: bool,
    pub child_owned_process_group: bool,
    pub inherited_fd_boundary: bool,
    pub wall_clock_limit: bool,
    pub output_limit: bool,
    pub process_group_custody: bool,
}

impl ObserverWorkerControlsV3 {
    fn child_complete(self) -> bool {
        event("WORKER_V3_CONTROLS_ENTER", "checking child controls");
        let result = self.no_new_privileges
            && self.resource_limits
            && self.child_owned_process_group
            && self.inherited_fd_boundary;
        event("WORKER_V3_CONTROLS_EXIT", "child controls checked");
        result
    }

    fn parent_pending(self) -> bool {
        event("WORKER_V3_CUSTODY_ENTER", "checking pending custody");
        let result = !self.wall_clock_limit && !self.output_limit && !self.process_group_custody;
        event("WORKER_V3_CUSTODY_EXIT", "pending custody checked");
        result
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObserverWorkerLimitsV3 {
    pub cpu_seconds: u32,
    pub address_space_bytes: u64,
    pub wall_timeout_ms: u32,
    pub max_response_bytes: u32,
}

impl Default for ObserverWorkerLimitsV3 {
    fn default() -> Self {
        event("WORKER_V3_LIMITS_DEFAULT", "constructing default limits");
        Self {
            cpu_seconds: 10,
            address_space_bytes: 512 * 1024 * 1024,
            wall_timeout_ms: 10_000,
            max_response_bytes: MAX_WORKER_V3_RESPONSE_BYTES as u32,
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ObserverWorkerReceiptV3 {
    pub status: ObserverWorkerStatusV3,
    pub controls: ObserverWorkerControlsV3,
    pub limits: ObserverWorkerLimitsV3,
    pub request_digest: [u8; 32],
    pub result_digest: [u8; 32],
    pub canonical_result: Vec<u8>,
    pub result: ObserverSynthesisPipelineResultV3,
    pub receipt_digest: [u8; 32],
    pub boundary: &'static str,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObserverWorkerV3Error(pub &'static str);

impl fmt::Display for ObserverWorkerV3Error {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        event("WORKER_V3_ERROR_DISPLAY", "rendering worker-v3 error");
        formatter.write_str(self.0)
    }
}

impl std::error::Error for ObserverWorkerV3Error {}

#[derive(Clone, Debug, Eq, PartialEq)]
struct WireReceiptV3 {
    status: ObserverWorkerStatusV3,
    controls: ObserverWorkerControlsV3,
    cpu_seconds: u32,
    address_space_bytes: u64,
    request_digest: [u8; 32],
    result_digest: [u8; 32],
    result: Vec<u8>,
    receipt_digest: [u8; 32],
}

fn reject(reason: &'static str) -> ObserverWorkerV3Error {
    event("WORKER_V3_REJECT", reason);
    ObserverWorkerV3Error(reason)
}

fn validate_limits(limits: ObserverWorkerLimitsV3) -> Result<(), ObserverWorkerV3Error> {
    event("WORKER_V3_LIMITS_ENTER", "validating supervisor limits");
    if !(1..=10).contains(&limits.cpu_seconds)
        || !(128 * 1024 * 1024..=2 * 1024 * 1024 * 1024).contains(&limits.address_space_bytes)
        || !(1..=30_000).contains(&limits.wall_timeout_ms)
        || !(128..=MAX_WORKER_V3_RESPONSE_BYTES as u32).contains(&limits.max_response_bytes)
    {
        return Err(reject("worker-v3-invalid-limits"));
    }
    event("WORKER_V3_LIMITS_EXIT", "supervisor limits validated");
    Ok(())
}

fn fixed_child(executable: &Path) -> Result<(), ObserverWorkerV3Error> {
    event("WORKER_V3_PATH_ENTER", "checking fixed child path");
    let expected_name = if cfg!(target_os = "windows") {
        concat!("vam-observer-pipeline-worker", ".exe")
    } else {
        FIXED_CHILD_NAME
    };
    if executable.file_name().and_then(|name| name.to_str()) != Some(expected_name) {
        return Err(reject("worker-v3-not-fixed-child"));
    }
    event("WORKER_V3_PATH_EXIT", "fixed child path checked");
    Ok(())
}

fn receipt_digest(wire: &WireReceiptV3) -> [u8; 32] {
    event("WORKER_V3_BIND_ENTER", "binding worker-v3 receipt");
    let mut body = Vec::with_capacity(96);
    body.push(match wire.status {
        ObserverWorkerStatusV3::CustodyPending => 0,
        ObserverWorkerStatusV3::Ready => 1,
    });
    body.push(child_flags(wire.controls));
    body.push(parent_flags(wire.controls));
    body.extend_from_slice(&wire.cpu_seconds.to_be_bytes());
    body.extend_from_slice(&wire.address_space_bytes.to_be_bytes());
    body.extend_from_slice(&wire.request_digest);
    body.extend_from_slice(&wire.result_digest);
    let result = domain_sha256(RECEIPT_DOMAIN, &body);
    event("WORKER_V3_BIND_EXIT", "worker-v3 receipt bound");
    result
}

fn parent_receipt_digest(wire: &WireReceiptV3, limits: ObserverWorkerLimitsV3) -> [u8; 32] {
    event(
        "WORKER_V3_PARENT_BIND_ENTER",
        "binding complete parent-owned worker limits",
    );
    let child_root = receipt_digest(wire);
    let mut body = Vec::with_capacity(48);
    body.extend_from_slice(&child_root);
    body.extend_from_slice(&limits.wall_timeout_ms.to_be_bytes());
    body.extend_from_slice(&limits.max_response_bytes.to_be_bytes());
    let result = domain_sha256(b"veyra.native-observer-worker.v3.parent-receipt", &body);
    event(
        "WORKER_V3_PARENT_BIND_EXIT",
        "complete parent-owned worker limits bound",
    );
    result
}

fn child_flags(controls: ObserverWorkerControlsV3) -> u8 {
    event("WORKER_V3_CHILD_FLAGS", "encoding child flags");
    u8::from(controls.no_new_privileges)
        | (u8::from(controls.resource_limits) << 1)
        | (u8::from(controls.child_owned_process_group) << 2)
        | (u8::from(controls.inherited_fd_boundary) << 3)
}

fn parent_flags(controls: ObserverWorkerControlsV3) -> u8 {
    event("WORKER_V3_PARENT_FLAGS", "encoding parent flags");
    u8::from(controls.wall_clock_limit)
        | (u8::from(controls.output_limit) << 1)
        | (u8::from(controls.process_group_custody) << 2)
}

fn encode_wire(wire: &WireReceiptV3) -> Result<Vec<u8>, ObserverWorkerV3Error> {
    event("WORKER_V3_ENCODE_ENTER", "encoding worker-v3 receipt");
    if wire.result.len() > MAX_PIPELINE_RESULT_V3_BYTES
        || wire.receipt_digest != receipt_digest(wire)
    {
        return Err(reject("worker-v3-invalid-receipt"));
    }
    let mut bytes = Vec::with_capacity(WIRE_FIXED_BYTES + wire.result.len());
    bytes.extend_from_slice(WIRE_MAGIC);
    bytes.extend_from_slice(&WIRE_VERSION.to_be_bytes());
    bytes.push(match wire.status {
        ObserverWorkerStatusV3::CustodyPending => 0,
        ObserverWorkerStatusV3::Ready => 1,
    });
    bytes.push(child_flags(wire.controls));
    bytes.push(parent_flags(wire.controls));
    bytes.push(0);
    bytes.extend_from_slice(&wire.cpu_seconds.to_be_bytes());
    bytes.extend_from_slice(&wire.address_space_bytes.to_be_bytes());
    bytes.extend_from_slice(&wire.request_digest);
    bytes.extend_from_slice(&wire.result_digest);
    bytes.extend_from_slice(&(wire.result.len() as u32).to_be_bytes());
    bytes.extend_from_slice(&wire.result);
    bytes.extend_from_slice(&wire.receipt_digest);
    event("WORKER_V3_ENCODE_EXIT", "worker-v3 receipt encoded");
    Ok(bytes)
}

fn take<const N: usize>(
    bytes: &[u8],
    cursor: &mut usize,
) -> Result<[u8; N], ObserverWorkerV3Error> {
    event("WORKER_V3_TAKE_ENTER", "reading fixed wire field");
    let end = cursor
        .checked_add(N)
        .ok_or_else(|| reject("worker-v3-wire-overflow"))?;
    let value: [u8; N] = bytes
        .get(*cursor..end)
        .ok_or_else(|| reject("worker-v3-truncated"))?
        .try_into()
        .map_err(|_| reject("worker-v3-truncated"))?;
    *cursor = end;
    event("WORKER_V3_TAKE_EXIT", "fixed wire field read");
    Ok(value)
}

fn decode_wire(bytes: &[u8]) -> Result<WireReceiptV3, ObserverWorkerV3Error> {
    event("WORKER_V3_DECODE_ENTER", "decoding worker-v3 receipt");
    if bytes.len() < WIRE_FIXED_BYTES || bytes.len() > MAX_WORKER_V3_RESPONSE_BYTES {
        return Err(reject("worker-v3-response-size"));
    }
    let mut cursor = 0;
    if &take::<4>(bytes, &mut cursor)? != WIRE_MAGIC
        || u16::from_be_bytes(take(bytes, &mut cursor)?) != WIRE_VERSION
    {
        return Err(reject("worker-v3-wire-header"));
    }
    let status = match take::<1>(bytes, &mut cursor)?[0] {
        0 => ObserverWorkerStatusV3::CustodyPending,
        1 => ObserverWorkerStatusV3::Ready,
        _ => return Err(reject("worker-v3-wire-status")),
    };
    let child = take::<1>(bytes, &mut cursor)?[0];
    let parent = take::<1>(bytes, &mut cursor)?[0];
    if child & !0x0f != 0 || parent & !0x07 != 0 || take::<1>(bytes, &mut cursor)?[0] != 0 {
        return Err(reject("worker-v3-wire-flags"));
    }
    let cpu_seconds = u32::from_be_bytes(take(bytes, &mut cursor)?);
    let address_space_bytes = u64::from_be_bytes(take(bytes, &mut cursor)?);
    let request_digest = take(bytes, &mut cursor)?;
    let result_digest = take(bytes, &mut cursor)?;
    let result_len = u32::from_be_bytes(take(bytes, &mut cursor)?) as usize;
    if result_len > MAX_PIPELINE_RESULT_V3_BYTES {
        return Err(reject("worker-v3-result-size"));
    }
    let end = cursor
        .checked_add(result_len)
        .ok_or_else(|| reject("worker-v3-wire-overflow"))?;
    let result = bytes
        .get(cursor..end)
        .ok_or_else(|| reject("worker-v3-truncated"))?
        .to_vec();
    cursor = end;
    let stored_digest = take(bytes, &mut cursor)?;
    if cursor != bytes.len() {
        return Err(reject("worker-v3-trailing"));
    }
    let controls = ObserverWorkerControlsV3 {
        no_new_privileges: child & 1 != 0,
        resource_limits: child & 2 != 0,
        child_owned_process_group: child & 4 != 0,
        inherited_fd_boundary: child & 8 != 0,
        wall_clock_limit: parent & 1 != 0,
        output_limit: parent & 2 != 0,
        process_group_custody: parent & 4 != 0,
    };
    let wire = WireReceiptV3 {
        status,
        controls,
        cpu_seconds,
        address_space_bytes,
        request_digest,
        result_digest,
        result,
        receipt_digest: stored_digest,
    };
    if receipt_digest(&wire) != stored_digest {
        return Err(reject("worker-v3-receipt-digest"));
    }
    event("WORKER_V3_DECODE_EXIT", "worker-v3 receipt decoded");
    Ok(wire)
}

pub fn run_observer_pipeline_child_v3<R: Read, W: Write>(
    input: R,
    mut output: W,
    limits: WorkerV2Limits,
) -> Result<(), ObserverWorkerV3Error> {
    event("WORKER_V3_CHILD_ENTER", "starting bounded child execution");
    let report = apply_worker_v2_child_controls(
        WorkerV2Policy::Baseline,
        limits,
        &WorkerV2LaunchOptions::default(),
    )
    .map_err(|_| reject("worker-v3-child-controls"))?;
    if report.admission != WorkerV2Admission::CustodyPending {
        return Err(reject("worker-v3-child-controls-blocked"));
    }
    let controls = ObserverWorkerControlsV3 {
        no_new_privileges: report.no_new_privileges.state == WorkerControlStateV2::Enforced,
        resource_limits: report.resource_limits.state == WorkerControlStateV2::Enforced,
        child_owned_process_group: report.process_group.state == WorkerControlStateV2::Enforced,
        inherited_fd_boundary: report.inherited_fd_boundary.state == WorkerControlStateV2::Enforced,
        wall_clock_limit: false,
        output_limit: false,
        process_group_custody: false,
    };
    if !controls.child_complete() || !controls.parent_pending() {
        return Err(reject("worker-v3-child-control-readback"));
    }
    let mut request_bytes = Vec::new();
    input
        .take((MAX_PIPELINE_REQUEST_V3_BYTES + 1) as u64)
        .read_to_end(&mut request_bytes)
        .map_err(|_| reject("worker-v3-request-read"))?;
    if request_bytes.len() > MAX_PIPELINE_REQUEST_V3_BYTES {
        return Err(reject("worker-v3-request-size"));
    }
    let request = decode_observer_pipeline_request_v3(&request_bytes)
        .map_err(|_| reject("worker-v3-request-decode"))?;
    if encode_observer_pipeline_request_v3(&request)
        .map_err(|_| reject("worker-v3-request-encode"))?
        != request_bytes
    {
        return Err(reject("worker-v3-request-noncanonical"));
    }
    let result = run_observer_synthesis_pipeline_v3(&request)
        .map_err(|_| reject("worker-v3-pipeline-execution"))?;
    let result = canonical_observer_pipeline_result_v3_bytes(&result)
        .map_err(|_| reject("worker-v3-result-encode"))?;
    let mut wire = WireReceiptV3 {
        status: ObserverWorkerStatusV3::CustodyPending,
        controls,
        cpu_seconds: limits.cpu_seconds,
        address_space_bytes: limits.address_space_bytes,
        request_digest: domain_sha256(REQUEST_DOMAIN, &request_bytes),
        result_digest: domain_sha256(RESULT_DOMAIN, &result),
        result,
        receipt_digest: [0; 32],
    };
    wire.receipt_digest = receipt_digest(&wire);
    let response = encode_wire(&wire)?;
    output
        .write_all(&response)
        .map_err(|_| reject("worker-v3-response-write"))?;
    output
        .flush()
        .map_err(|_| reject("worker-v3-response-flush"))?;
    event("WORKER_V3_CHILD_EXIT", "bounded child execution completed");
    Ok(())
}

pub fn supervise_observer_pipeline_v3(
    executable: &Path,
    canonical_request: &[u8],
    policy: WorkerV2Policy,
    limits: ObserverWorkerLimitsV3,
) -> Result<ObserverWorkerReceiptV3, ObserverWorkerV3Error> {
    event("WORKER_V3_PARENT_ENTER", "starting observer supervisor");
    fixed_child(executable)?;
    validate_limits(limits)?;
    if policy == WorkerV2Policy::Strict {
        return Err(reject("worker-v3-strict-controls-unavailable"));
    }
    if !cfg!(target_os = "linux") {
        return Err(reject("worker-v3-linux-controls-unavailable"));
    }
    if canonical_request.len() > MAX_PIPELINE_REQUEST_V3_BYTES {
        return Err(reject("worker-v3-request-size"));
    }
    let request = decode_observer_pipeline_request_v3(canonical_request)
        .map_err(|_| reject("worker-v3-request-decode"))?;
    if encode_observer_pipeline_request_v3(&request)
        .map_err(|_| reject("worker-v3-request-encode"))?
        != canonical_request
    {
        return Err(reject("worker-v3-request-noncanonical"));
    }
    let mut command = Command::new(executable);
    command
        .arg("--child")
        .arg(limits.cpu_seconds.to_string())
        .arg(limits.address_space_bytes.to_string())
        .env_clear()
        .env("LANG", "C.UTF-8")
        .env("LC_ALL", "C.UTF-8")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null());
    #[cfg(target_os = "linux")]
    {
        command.process_group(0);
        configure_close_on_exec_boundary(&mut command);
    }
    let mut child = command.spawn().map_err(|_| reject("worker-v3-spawn"))?;
    let pid = child.id();
    if write_request(&mut child, canonical_request).is_err() {
        terminate_and_reap(&mut child);
        return Err(reject("worker-v3-request-write"));
    }
    let deadline = Instant::now() + Duration::from_millis(limits.wall_timeout_ms as u64);
    let (status, bytes) =
        collect_output(&mut child, limits.max_response_bytes as usize, deadline).map_err(reject)?;
    if !status.success() {
        terminate_and_reap(&mut child);
        return Err(reject("worker-v3-child-exit"));
    }
    signal_process_group(pid, true).map_err(|_| reject("worker-v3-process-group-reap"))?;
    let mut wire = decode_wire(&bytes)?;
    if wire.status != ObserverWorkerStatusV3::CustodyPending
        || !wire.controls.child_complete()
        || !wire.controls.parent_pending()
        || wire.cpu_seconds != limits.cpu_seconds
        || wire.address_space_bytes != limits.address_space_bytes
        || wire.request_digest != domain_sha256(REQUEST_DOMAIN, canonical_request)
        || wire.result_digest != domain_sha256(RESULT_DOMAIN, &wire.result)
    {
        return Err(reject("worker-v3-custody-binding"));
    }
    let fresh = run_observer_synthesis_pipeline_v3(&request)
        .map_err(|_| reject("worker-v3-fresh-execution"))?;
    let fresh_bytes = canonical_observer_pipeline_result_v3_bytes(&fresh)
        .map_err(|_| reject("worker-v3-fresh-encode"))?;
    if fresh_bytes != wire.result {
        return Err(reject("worker-v3-fresh-result-mismatch"));
    }
    wire.status = ObserverWorkerStatusV3::Ready;
    wire.controls.wall_clock_limit = true;
    wire.controls.output_limit = true;
    wire.controls.process_group_custody = true;
    wire.receipt_digest = receipt_digest(&wire);
    let complete_receipt_digest = parent_receipt_digest(&wire, limits);
    let receipt = ObserverWorkerReceiptV3 {
        status: wire.status,
        controls: wire.controls,
        limits,
        request_digest: wire.request_digest,
        result_digest: wire.result_digest,
        canonical_result: wire.result,
        result: fresh,
        receipt_digest: complete_receipt_digest,
        boundary: OBSERVER_WORKER_V3_BOUNDARY,
    };
    event("WORKER_V3_PARENT_EXIT", "observer supervisor completed");
    Ok(receipt)
}

#[cfg(target_os = "linux")]
fn configure_close_on_exec_boundary(command: &mut Command) {
    event(
        "WORKER_V3_FD_SETUP_ENTER",
        "configuring child close-on-exec descriptor boundary",
    );
    // SAFETY: the closure runs after fork and performs one async-signal-safe
    // Linux syscall. CLOEXEC preserves Rust's exec-error pipe until exec while
    // ensuring every unrelated descriptor above stderr is absent afterwards.
    unsafe {
        command.pre_exec(|| {
            if linux_fd_ffi::close_range(3, u32::MAX, linux_fd_ffi::CLOSE_RANGE_CLOEXEC) == 0 {
                Ok(())
            } else {
                Err(std::io::Error::last_os_error())
            }
        });
    }
    event(
        "WORKER_V3_FD_SETUP_EXIT",
        "child close-on-exec descriptor boundary configured",
    );
}

fn write_request(child: &mut Child, request: &[u8]) -> std::io::Result<()> {
    event("WORKER_V3_WRITE_ENTER", "writing bounded child request");
    let mut stdin = child
        .stdin
        .take()
        .ok_or_else(|| std::io::Error::new(std::io::ErrorKind::BrokenPipe, "missing stdin"))?;
    stdin.write_all(request)?;
    drop(stdin);
    event("WORKER_V3_WRITE_EXIT", "bounded child request written");
    Ok(())
}

fn collect_output(
    child: &mut Child,
    output_limit: usize,
    deadline: Instant,
) -> Result<(ExitStatus, Vec<u8>), &'static str> {
    event(
        "WORKER_V3_DRAIN_ENTER",
        "draining child output concurrently",
    );
    let stdout = match child.stdout.take() {
        Some(value) => value,
        None => return Err("worker-v3-output-pipe"),
    };
    let (sender, receiver) = mpsc::sync_channel(1);
    let reader = thread::spawn(move || {
        let mut bytes = Vec::new();
        let result = stdout
            .take((output_limit + 1) as u64)
            .read_to_end(&mut bytes)
            .map(|_| bytes);
        let _ = sender.send(result);
    });
    let mut status = None;
    let mut output = None;
    loop {
        if status.is_none() {
            match child.try_wait() {
                Ok(value) => status = value,
                Err(_) => {
                    terminate_and_reap(child);
                    let _ = reader.join();
                    return Err("worker-v3-wait");
                }
            }
        }
        if output.is_none() {
            match receiver.try_recv() {
                Ok(Ok(bytes)) if bytes.len() <= output_limit => output = Some(bytes),
                Ok(Ok(_)) => {
                    terminate_and_reap(child);
                    let _ = reader.join();
                    return Err("worker-v3-output-limit");
                }
                Ok(Err(_)) | Err(TryRecvError::Disconnected) => {
                    terminate_and_reap(child);
                    let _ = reader.join();
                    return Err("worker-v3-output-read");
                }
                Err(TryRecvError::Empty) => {}
            }
        }
        if status.is_some() && output.is_some() {
            break;
        }
        if Instant::now() >= deadline {
            terminate_and_reap(child);
            let _ = reader.join();
            return Err("worker-v3-wall-timeout");
        }
        thread::sleep(POLL_INTERVAL);
    }
    if reader.join().is_err() {
        return Err("worker-v3-output-reader");
    }
    event("WORKER_V3_DRAIN_EXIT", "bounded child output drained");
    let status = status.ok_or("worker-v3-missing-status-after-drain")?;
    let output = output.ok_or("worker-v3-missing-output-after-drain")?;
    Ok((status, output))
}

fn terminate_and_reap(child: &mut Child) {
    event(
        "WORKER_V3_TERMINATE_ENTER",
        "terminating owned process group",
    );
    let _ = signal_process_group(child.id(), false);
    let deadline = Instant::now() + TERM_GRACE;
    while Instant::now() < deadline {
        if matches!(child.try_wait(), Ok(Some(_))) {
            let _ = signal_process_group(child.id(), true);
            event("WORKER_V3_TERMINATE_EXIT", "child reaped after termination");
            return;
        }
        thread::sleep(POLL_INTERVAL);
    }
    let _ = signal_process_group(child.id(), true);
    let _ = child.wait();
    event("WORKER_V3_TERMINATE_EXIT", "child killed and reaped");
}

#[cfg(target_os = "linux")]
mod linux_fd_ffi {
    use std::os::raw::{c_int, c_uint};

    pub const CLOSE_RANGE_CLOEXEC: c_uint = 1 << 2;

    unsafe extern "C" {
        pub fn close_range(first: c_uint, last: c_uint, flags: c_uint) -> c_int;
    }
}
