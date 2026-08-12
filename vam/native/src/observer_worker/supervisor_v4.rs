//! Truthful Linux isolation profiles for the observer-pipeline worker.
//!
//! `Baseline` preserves the v3 execution boundary. `Isolated` additionally
//! requires independently read-back user/mount/network/IPC/UTS namespaces and
//! an x86-64 seccomp-BPF allowlist. `Strict` adds an explicitly delegated
//! cgroup-v2 leaf whose CPU, memory and PID controls are written and read back
//! exactly, whose worker membership is checked by both processes, and whose
//! empty removal is part of successful parent custody.

use std::fmt;
use std::fs;
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
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
#[cfg(all(target_os = "linux", target_arch = "x86_64"))]
use super::isolation_v4::apply_and_verify_seccomp;
#[cfg(target_os = "linux")]
use super::isolation_v4::{
    apply_and_verify_namespaces, enter_and_verify_cgroup, namespace_links, CgroupLeaf,
};
use super::linux::signal_process_group;
use super::pipeline_replay_v3::{
    canonical_observer_pipeline_result_v3_bytes, decode_observer_pipeline_request_v3,
    encode_observer_pipeline_request_v3, MAX_PIPELINE_REQUEST_V3_BYTES,
    MAX_PIPELINE_RESULT_V3_BYTES,
};
use super::supervisor_v3::{supervise_observer_pipeline_v3, ObserverWorkerLimitsV3};
use super::worker_v2::{
    apply_worker_v2_child_controls, WorkerControlStateV2, WorkerV2Admission, WorkerV2LaunchOptions,
    WorkerV2Limits, WorkerV2Policy,
};

const MAGIC: &[u8; 4] = b"VOW4";
const VERSION: u16 = 4;
const GO: u8 = 0xa5;
const FIXED_CHILD_NAME: &str = "vam-observer-pipeline-worker";
const REQUEST_DOMAIN: &[u8] = b"veyra.native-observer-worker.v4.request";
const RESULT_DOMAIN: &[u8] = b"veyra.native-observer-worker.v4.result";
const CHILD_DOMAIN: &[u8] = b"veyra.native-observer-worker.v4.child";
const RECEIPT_DOMAIN: &[u8] = b"veyra.native-observer-worker.v4.receipt";
const POLICY_DOMAIN: &[u8] = b"veyra.native-observer-worker.v4.policy";
const WIRE_FIXED: usize = 110;
const POLL: Duration = Duration::from_millis(5);

pub(super) fn worker_v4_request_digest(canonical_request: &[u8]) -> [u8; 32] {
    event(
        "WORKER_V4_REQUEST_DIGEST_ENTER",
        "binding canonical request",
    );
    let digest = domain_sha256(REQUEST_DOMAIN, canonical_request);
    event("WORKER_V4_REQUEST_DIGEST_EXIT", "canonical request bound");
    digest
}

pub(super) fn worker_v4_result_digest(canonical_result: &[u8]) -> [u8; 32] {
    event("WORKER_V4_RESULT_DIGEST_ENTER", "binding canonical result");
    let digest = domain_sha256(RESULT_DOMAIN, canonical_result);
    event("WORKER_V4_RESULT_DIGEST_EXIT", "canonical result bound");
    digest
}

pub(super) const SECCOMP_ALLOWLIST_X86_64: &[u32] = &[
    0, 1, 3, 5, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 24, 25, 28, 32, 33, 35, 39, 60, 62,
    63, 72, 74, 79, 89, 102, 104, 107, 108, 110, 131, 157, 158, 160, 186, 202, 228, 231, 257, 262,
    273, 302, 318, 334, 436,
];

pub const OBSERVER_WORKER_V4_BOUNDARY: &str = "Linux-only: baseline retains v3 custody; isolated requires parent-and-child readback of fresh user/mount/network/IPC/UTS namespaces plus an installed x86-64 seccomp-BPF allowlist, but its private mount-propagation namespace still exposes the host filesystem and is explicitly not a closed filesystem; strict additionally requires a caller-delegated cgroup-v2 root, exact cpu.max/memory.max/pids.max readback, dual membership verification, empty-leaf readback and removal; configuration, availability, or child testimony alone never counts as enforcement";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum IsolationProfileV4 {
    Baseline,
    Isolated,
    Strict,
}

impl IsolationProfileV4 {
    fn code(self) -> u8 {
        event("WORKER_V4_PROFILE_ENTER", "encoding isolation profile");
        let code = match self {
            Self::Baseline => 0,
            Self::Isolated => 1,
            Self::Strict => 2,
        };
        event("WORKER_V4_PROFILE_EXIT", "isolation profile encoded");
        code
    }

    fn from_code(code: u8) -> Result<Self, ObserverWorkerV4Error> {
        event(
            "WORKER_V4_PROFILE_DECODE_ENTER",
            "decoding isolation profile",
        );
        let profile = match code {
            0 => Self::Baseline,
            1 => Self::Isolated,
            2 => Self::Strict,
            _ => return Err(reject("worker-v4-profile")),
        };
        event("WORKER_V4_PROFILE_DECODE_EXIT", "isolation profile decoded");
        Ok(profile)
    }
}

#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct ObserverWorkerLaunchV4 {
    /// A pre-created, caller-controlled delegation below `/sys/fs/cgroup`.
    /// The worker creates and removes only one fresh child leaf below it.
    pub delegated_cgroup_root: Option<PathBuf>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObserverWorkerLimitsV4 {
    pub cpu_seconds: u32,
    pub address_space_bytes: u64,
    pub wall_timeout_ms: u32,
    pub max_response_bytes: u32,
    pub cgroup_cpu_quota_us: u32,
    pub cgroup_cpu_period_us: u32,
    pub cgroup_memory_bytes: u64,
    pub cgroup_pids: u32,
}

impl Default for ObserverWorkerLimitsV4 {
    fn default() -> Self {
        event("WORKER_V4_LIMITS_ENTER", "constructing default v4 limits");
        let limits = Self {
            cpu_seconds: 10,
            address_space_bytes: 512 * 1024 * 1024,
            wall_timeout_ms: 10_000,
            max_response_bytes: (MAX_PIPELINE_RESULT_V3_BYTES + WIRE_FIXED) as u32,
            cgroup_cpu_quota_us: 100_000,
            cgroup_cpu_period_us: 100_000,
            cgroup_memory_bytes: 512 * 1024 * 1024,
            cgroup_pids: 1,
        };
        event("WORKER_V4_LIMITS_EXIT", "default v4 limits constructed");
        limits
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObserverWorkerControlsV4 {
    pub no_new_privileges: bool,
    pub resource_limits: bool,
    pub child_owned_process_group: bool,
    pub inherited_fd_boundary: bool,
    pub namespaces: bool,
    pub seccomp_allowlist: bool,
    /// Always false in v4: mount propagation is private but host paths remain visible.
    pub filesystem_closed: bool,
    pub cgroup_limits: bool,
    pub cgroup_membership: bool,
    pub parent_control_readback: bool,
    pub wall_clock_limit: bool,
    pub output_limit: bool,
    pub process_group_custody: bool,
    pub cgroup_cleanup: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ObserverWorkerReceiptV4 {
    profile: IsolationProfileV4,
    controls: ObserverWorkerControlsV4,
    limits: ObserverWorkerLimitsV4,
    request_digest: [u8; 32],
    result_digest: [u8; 32],
    /// Binds the named profiles, namespace set, filesystem caveat and seccomp policy.
    isolation_policy_digest: [u8; 32],
    canonical_result: Vec<u8>,
    result: ObserverSynthesisPipelineResultV3,
    receipt_digest: [u8; 32],
    boundary: &'static str,
}

impl ObserverWorkerReceiptV4 {
    pub fn profile(&self) -> IsolationProfileV4 {
        event("WORKER_V4_RECEIPT_PROFILE_ENTER", "reading receipt profile");
        let value = self.profile;
        event("WORKER_V4_RECEIPT_PROFILE_EXIT", "receipt profile read");
        value
    }
    pub fn controls(&self) -> ObserverWorkerControlsV4 {
        event(
            "WORKER_V4_RECEIPT_CONTROLS_ENTER",
            "reading receipt controls",
        );
        let value = self.controls;
        event("WORKER_V4_RECEIPT_CONTROLS_EXIT", "receipt controls read");
        value
    }
    pub fn limits(&self) -> ObserverWorkerLimitsV4 {
        event("WORKER_V4_RECEIPT_LIMITS_ENTER", "reading receipt limits");
        let value = self.limits;
        event("WORKER_V4_RECEIPT_LIMITS_EXIT", "receipt limits read");
        value
    }
    pub fn request_digest(&self) -> [u8; 32] {
        event("WORKER_V4_RECEIPT_REQUEST_ENTER", "reading request digest");
        let value = self.request_digest;
        event("WORKER_V4_RECEIPT_REQUEST_EXIT", "request digest read");
        value
    }
    pub fn result_digest(&self) -> [u8; 32] {
        event("WORKER_V4_RECEIPT_RESULT_ENTER", "reading result digest");
        let value = self.result_digest;
        event("WORKER_V4_RECEIPT_RESULT_EXIT", "result digest read");
        value
    }
    pub fn isolation_policy_digest(&self) -> [u8; 32] {
        event("WORKER_V4_RECEIPT_POLICY_ENTER", "reading policy digest");
        let value = self.isolation_policy_digest;
        event("WORKER_V4_RECEIPT_POLICY_EXIT", "policy digest read");
        value
    }
    pub fn canonical_result(&self) -> &[u8] {
        event(
            "WORKER_V4_RECEIPT_BYTES_ENTER",
            "borrowing canonical result",
        );
        let value = self.canonical_result.as_slice();
        event("WORKER_V4_RECEIPT_BYTES_EXIT", "canonical result borrowed");
        value
    }
    pub fn result(&self) -> &ObserverSynthesisPipelineResultV3 {
        event("WORKER_V4_RECEIPT_VALUE_ENTER", "borrowing typed result");
        let value = &self.result;
        event("WORKER_V4_RECEIPT_VALUE_EXIT", "typed result borrowed");
        value
    }
    pub fn receipt_digest(&self) -> [u8; 32] {
        event("WORKER_V4_RECEIPT_ROOT_ENTER", "reading receipt digest");
        let value = self.receipt_digest;
        event("WORKER_V4_RECEIPT_ROOT_EXIT", "receipt digest read");
        value
    }
    pub fn boundary(&self) -> &'static str {
        event(
            "WORKER_V4_RECEIPT_BOUNDARY_ENTER",
            "reading receipt boundary",
        );
        let value = self.boundary;
        event("WORKER_V4_RECEIPT_BOUNDARY_EXIT", "receipt boundary read");
        value
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObserverWorkerV4Error(pub &'static str);

impl fmt::Display for ObserverWorkerV4Error {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        event("WORKER_V4_ERROR_ENTER", "rendering worker-v4 error");
        let result = formatter.write_str(self.0);
        event("WORKER_V4_ERROR_EXIT", "worker-v4 error rendered");
        result
    }
}

impl std::error::Error for ObserverWorkerV4Error {}

#[derive(Clone, Debug, Eq, PartialEq)]
struct ChildWireV4 {
    profile: IsolationProfileV4,
    flags: u16,
    request_digest: [u8; 32],
    result_digest: [u8; 32],
    result: Vec<u8>,
    digest: [u8; 32],
}

pub(super) fn reject(reason: &'static str) -> ObserverWorkerV4Error {
    event("WORKER_V4_REJECT", reason);
    ObserverWorkerV4Error(reason)
}

fn validate_limits(limits: ObserverWorkerLimitsV4) -> Result<(), ObserverWorkerV4Error> {
    event(
        "WORKER_V4_LIMITS_VALIDATE_ENTER",
        "validating all v4 limits",
    );
    let max_wire = MAX_PIPELINE_RESULT_V3_BYTES + WIRE_FIXED;
    if !(1..=10).contains(&limits.cpu_seconds)
        || !(128 * 1024 * 1024..=2 * 1024 * 1024 * 1024).contains(&limits.address_space_bytes)
        || !(1..=30_000).contains(&limits.wall_timeout_ms)
        || !(WIRE_FIXED as u32..=max_wire as u32).contains(&limits.max_response_bytes)
        || !(1_000..=1_000_000).contains(&limits.cgroup_cpu_period_us)
        || !(1_000..=limits.cgroup_cpu_period_us.saturating_mul(64))
            .contains(&limits.cgroup_cpu_quota_us)
        || !(128 * 1024 * 1024..=2 * 1024 * 1024 * 1024).contains(&limits.cgroup_memory_bytes)
        || limits.cgroup_memory_bytes > limits.address_space_bytes
        || !(1..=64).contains(&limits.cgroup_pids)
    {
        return Err(reject("worker-v4-invalid-limits"));
    }
    event("WORKER_V4_LIMITS_VALIDATE_EXIT", "all v4 limits validated");
    Ok(())
}

fn fixed_child(path: &Path) -> Result<(), ObserverWorkerV4Error> {
    event("WORKER_V4_PATH_ENTER", "validating fixed child name");
    let expected = if cfg!(windows) {
        "vam-observer-pipeline-worker.exe"
    } else {
        FIXED_CHILD_NAME
    };
    if path.file_name().and_then(|value| value.to_str()) != Some(expected) {
        return Err(reject("worker-v4-not-fixed-child"));
    }
    event("WORKER_V4_PATH_EXIT", "fixed child name validated");
    Ok(())
}

fn controls_flags(controls: ObserverWorkerControlsV4) -> u16 {
    event("WORKER_V4_FLAGS_ENTER", "encoding child control flags");
    let flags = u16::from(controls.no_new_privileges)
        | (u16::from(controls.resource_limits) << 1)
        | (u16::from(controls.child_owned_process_group) << 2)
        | (u16::from(controls.inherited_fd_boundary) << 3)
        | (u16::from(controls.namespaces) << 4)
        | (u16::from(controls.seccomp_allowlist) << 5)
        | (u16::from(controls.cgroup_limits) << 6)
        | (u16::from(controls.cgroup_membership) << 7)
        | (u16::from(controls.filesystem_closed) << 8);
    event("WORKER_V4_FLAGS_EXIT", "child control flags encoded");
    flags
}

fn child_digest(wire: &ChildWireV4) -> [u8; 32] {
    event("WORKER_V4_CHILD_BIND_ENTER", "binding child evidence");
    let mut body = Vec::with_capacity(99);
    body.push(wire.profile.code());
    body.extend_from_slice(&wire.flags.to_be_bytes());
    body.extend_from_slice(&wire.request_digest);
    body.extend_from_slice(&wire.result_digest);
    let digest = domain_sha256(CHILD_DOMAIN, &body);
    event("WORKER_V4_CHILD_BIND_EXIT", "child evidence bound");
    digest
}

fn receipt_digest(
    profile: IsolationProfileV4,
    controls: ObserverWorkerControlsV4,
    limits: ObserverWorkerLimitsV4,
    request_digest: [u8; 32],
    result_digest: [u8; 32],
    child_root: [u8; 32],
) -> [u8; 32] {
    event(
        "WORKER_V4_RECEIPT_BIND_ENTER",
        "binding v4 controls and custody",
    );
    let mut body = Vec::with_capacity(160);
    body.push(profile.code());
    body.extend_from_slice(&controls_flags(controls).to_be_bytes());
    let parent_flags = u16::from(controls.parent_control_readback)
        | (u16::from(controls.wall_clock_limit) << 1)
        | (u16::from(controls.output_limit) << 2)
        | (u16::from(controls.process_group_custody) << 3)
        | (u16::from(controls.cgroup_cleanup) << 4);
    body.extend_from_slice(&parent_flags.to_be_bytes());
    body.extend_from_slice(&limits.cpu_seconds.to_be_bytes());
    body.extend_from_slice(&limits.address_space_bytes.to_be_bytes());
    body.extend_from_slice(&limits.wall_timeout_ms.to_be_bytes());
    body.extend_from_slice(&limits.max_response_bytes.to_be_bytes());
    body.extend_from_slice(&limits.cgroup_cpu_quota_us.to_be_bytes());
    body.extend_from_slice(&limits.cgroup_cpu_period_us.to_be_bytes());
    body.extend_from_slice(&limits.cgroup_memory_bytes.to_be_bytes());
    body.extend_from_slice(&limits.cgroup_pids.to_be_bytes());
    body.extend_from_slice(&request_digest);
    body.extend_from_slice(&result_digest);
    body.extend_from_slice(&child_root);
    body.extend_from_slice(&isolation_policy_digest());
    let digest = domain_sha256(RECEIPT_DOMAIN, &body);
    event(
        "WORKER_V4_RECEIPT_BIND_EXIT",
        "v4 controls and custody bound",
    );
    digest
}

fn isolation_policy_digest() -> [u8; 32] {
    event(
        "WORKER_V4_POLICY_BIND_ENTER",
        "binding fixed isolation policy",
    );
    let mut policy = OBSERVER_WORKER_V4_BOUNDARY.as_bytes().to_vec();
    for syscall in SECCOMP_ALLOWLIST_X86_64 {
        policy.extend_from_slice(&syscall.to_be_bytes());
    }
    let digest = domain_sha256(POLICY_DOMAIN, &policy);
    event("WORKER_V4_POLICY_BIND_EXIT", "fixed isolation policy bound");
    digest
}

fn encode_wire(wire: &ChildWireV4) -> Result<Vec<u8>, ObserverWorkerV4Error> {
    event("WORKER_V4_ENCODE_ENTER", "encoding v4 child wire");
    if wire.flags & !0xff != 0
        || wire.result.len() > MAX_PIPELINE_RESULT_V3_BYTES
        || wire.digest != child_digest(wire)
    {
        return Err(reject("worker-v4-invalid-child-wire"));
    }
    let mut bytes = Vec::with_capacity(WIRE_FIXED + wire.result.len());
    bytes.extend_from_slice(MAGIC);
    bytes.extend_from_slice(&VERSION.to_be_bytes());
    bytes.push(wire.profile.code());
    bytes.push(0);
    bytes.extend_from_slice(&wire.flags.to_be_bytes());
    bytes.extend_from_slice(&(wire.result.len() as u32).to_be_bytes());
    bytes.extend_from_slice(&wire.request_digest);
    bytes.extend_from_slice(&wire.result_digest);
    bytes.extend_from_slice(&wire.result);
    bytes.extend_from_slice(&wire.digest);
    event("WORKER_V4_ENCODE_EXIT", "v4 child wire encoded");
    Ok(bytes)
}

fn take<const N: usize>(
    bytes: &[u8],
    cursor: &mut usize,
) -> Result<[u8; N], ObserverWorkerV4Error> {
    event("WORKER_V4_TAKE_ENTER", "taking bounded wire field");
    let end = cursor
        .checked_add(N)
        .ok_or_else(|| reject("worker-v4-wire-overflow"))?;
    let value = bytes
        .get(*cursor..end)
        .ok_or_else(|| reject("worker-v4-truncated"))?
        .try_into()
        .map_err(|_| reject("worker-v4-truncated"))?;
    *cursor = end;
    event("WORKER_V4_TAKE_EXIT", "bounded wire field taken");
    Ok(value)
}

fn decode_wire(bytes: &[u8]) -> Result<ChildWireV4, ObserverWorkerV4Error> {
    event("WORKER_V4_DECODE_ENTER", "decoding v4 child wire");
    if bytes.len() < WIRE_FIXED || bytes.len() > MAX_PIPELINE_RESULT_V3_BYTES + WIRE_FIXED {
        return Err(reject("worker-v4-response-size"));
    }
    let mut cursor = 0;
    if &take::<4>(bytes, &mut cursor)? != MAGIC
        || u16::from_be_bytes(take(bytes, &mut cursor)?) != VERSION
    {
        return Err(reject("worker-v4-wire-header"));
    }
    let profile = IsolationProfileV4::from_code(take::<1>(bytes, &mut cursor)?[0])?;
    if take::<1>(bytes, &mut cursor)?[0] != 0 {
        return Err(reject("worker-v4-wire-reserved"));
    }
    let flags = u16::from_be_bytes(take(bytes, &mut cursor)?);
    if flags & !0xff != 0 {
        return Err(reject("worker-v4-wire-flags"));
    }
    let result_len = u32::from_be_bytes(take(bytes, &mut cursor)?) as usize;
    if result_len > MAX_PIPELINE_RESULT_V3_BYTES {
        return Err(reject("worker-v4-result-size"));
    }
    let request_digest = take(bytes, &mut cursor)?;
    let result_digest = take(bytes, &mut cursor)?;
    let end = cursor
        .checked_add(result_len)
        .ok_or_else(|| reject("worker-v4-wire-overflow"))?;
    let result = bytes
        .get(cursor..end)
        .ok_or_else(|| reject("worker-v4-truncated"))?
        .to_vec();
    cursor = end;
    let digest = take(bytes, &mut cursor)?;
    if cursor != bytes.len() {
        return Err(reject("worker-v4-trailing"));
    }
    let wire = ChildWireV4 {
        profile,
        flags,
        request_digest,
        result_digest,
        result,
        digest,
    };
    if child_digest(&wire) != wire.digest {
        return Err(reject("worker-v4-child-digest"));
    }
    event("WORKER_V4_DECODE_EXIT", "v4 child wire decoded");
    Ok(wire)
}

/// Child entry used only by the fixed-name worker binary.
pub fn run_observer_pipeline_child_v4<R: Read, W: Write>(
    mut input: R,
    mut output: W,
    profile: IsolationProfileV4,
    limits: WorkerV2Limits,
    cgroup_leaf: Option<&Path>,
) -> Result<(), ObserverWorkerV4Error> {
    event("WORKER_V4_CHILD_ENTER", "starting v4 child setup");
    if !cfg!(target_os = "linux") {
        return Err(reject("worker-v4-linux-controls-unavailable"));
    }
    let report = apply_worker_v2_child_controls(
        WorkerV2Policy::Baseline,
        limits,
        &WorkerV2LaunchOptions::default(),
    )
    .map_err(|_| reject("worker-v4-baseline-controls"))?;
    if report.admission != WorkerV2Admission::CustodyPending {
        return Err(reject("worker-v4-baseline-controls-blocked"));
    }
    let mut controls = ObserverWorkerControlsV4 {
        no_new_privileges: report.no_new_privileges.state == WorkerControlStateV2::Enforced,
        resource_limits: report.resource_limits.state == WorkerControlStateV2::Enforced,
        child_owned_process_group: report.process_group.state == WorkerControlStateV2::Enforced,
        inherited_fd_boundary: report.inherited_fd_boundary.state == WorkerControlStateV2::Enforced,
        namespaces: false,
        seccomp_allowlist: false,
        filesystem_closed: false,
        cgroup_limits: false,
        cgroup_membership: false,
        parent_control_readback: false,
        wall_clock_limit: false,
        output_limit: false,
        process_group_custody: false,
        cgroup_cleanup: false,
    };
    if profile != IsolationProfileV4::Baseline {
        #[cfg(all(target_os = "linux", not(target_arch = "x86_64")))]
        return Err(reject("worker-v4-seccomp-architecture-unsupported"));
        #[cfg(all(target_os = "linux", target_arch = "x86_64"))]
        {
            if profile == IsolationProfileV4::Strict {
                let leaf = cgroup_leaf.ok_or_else(|| reject("worker-v4-cgroup-leaf-missing"))?;
                controls.cgroup_membership = enter_and_verify_cgroup(leaf)?;
                controls.cgroup_limits = controls.cgroup_membership;
            } else if cgroup_leaf.is_some() {
                return Err(reject("worker-v4-unexpected-cgroup-leaf"));
            }
            controls.namespaces = apply_and_verify_namespaces()?;
            controls.seccomp_allowlist = apply_and_verify_seccomp()?;
        }
    }
    let expected = match profile {
        IsolationProfileV4::Baseline => 0x0f,
        IsolationProfileV4::Isolated => 0x3f,
        IsolationProfileV4::Strict => 0xff,
    };
    if controls_flags(controls) != expected {
        return Err(reject("worker-v4-child-control-readback"));
    }
    let mut go = [0u8; 1];
    input
        .read_exact(&mut go)
        .map_err(|_| reject("worker-v4-go-read"))?;
    if go[0] != GO {
        return Err(reject("worker-v4-go-marker"));
    }
    let mut request_bytes = Vec::new();
    input
        .take((MAX_PIPELINE_REQUEST_V3_BYTES + 1) as u64)
        .read_to_end(&mut request_bytes)
        .map_err(|_| reject("worker-v4-request-read"))?;
    if request_bytes.len() > MAX_PIPELINE_REQUEST_V3_BYTES {
        return Err(reject("worker-v4-request-size"));
    }
    let request = decode_observer_pipeline_request_v3(&request_bytes)
        .map_err(|_| reject("worker-v4-request-decode"))?;
    if encode_observer_pipeline_request_v3(&request)
        .map_err(|_| reject("worker-v4-request-encode"))?
        != request_bytes
    {
        return Err(reject("worker-v4-request-noncanonical"));
    }
    let result = run_observer_synthesis_pipeline_v3(&request)
        .map_err(|_| reject("worker-v4-pipeline-execution"))?;
    let result = canonical_observer_pipeline_result_v3_bytes(&result)
        .map_err(|_| reject("worker-v4-result-encode"))?;
    let mut wire = ChildWireV4 {
        profile,
        flags: controls_flags(controls),
        request_digest: worker_v4_request_digest(&request_bytes),
        result_digest: worker_v4_result_digest(&result),
        result,
        digest: [0; 32],
    };
    wire.digest = child_digest(&wire);
    output
        .write_all(&encode_wire(&wire)?)
        .map_err(|_| reject("worker-v4-response-write"))?;
    output
        .flush()
        .map_err(|_| reject("worker-v4-response-flush"))?;
    event("WORKER_V4_CHILD_EXIT", "v4 child completed");
    Ok(())
}

/// Run one observer request under the requested truthful profile.
pub fn supervise_observer_pipeline_v4(
    executable: &Path,
    canonical_request: &[u8],
    profile: IsolationProfileV4,
    limits: ObserverWorkerLimitsV4,
    launch: &ObserverWorkerLaunchV4,
) -> Result<ObserverWorkerReceiptV4, ObserverWorkerV4Error> {
    event("WORKER_V4_PARENT_ENTER", "starting v4 supervisor");
    fixed_child(executable)?;
    validate_limits(limits)?;
    if !cfg!(target_os = "linux") {
        return Err(reject("worker-v4-linux-controls-unavailable"));
    }
    let request = decode_observer_pipeline_request_v3(canonical_request)
        .map_err(|_| reject("worker-v4-request-decode"))?;
    if canonical_request.len() > MAX_PIPELINE_REQUEST_V3_BYTES
        || encode_observer_pipeline_request_v3(&request)
            .map_err(|_| reject("worker-v4-request-encode"))?
            != canonical_request
    {
        return Err(reject("worker-v4-request-noncanonical"));
    }
    if profile == IsolationProfileV4::Baseline {
        if launch.delegated_cgroup_root.is_some() {
            return Err(reject("worker-v4-baseline-cgroup-not-requested"));
        }
        let v3_limits = ObserverWorkerLimitsV3 {
            cpu_seconds: limits.cpu_seconds,
            address_space_bytes: limits.address_space_bytes,
            wall_timeout_ms: limits.wall_timeout_ms,
            max_response_bytes: limits.max_response_bytes,
        };
        let receipt = supervise_observer_pipeline_v3(
            executable,
            canonical_request,
            WorkerV2Policy::Baseline,
            v3_limits,
        )
        .map_err(|_| reject("worker-v4-baseline-execution"))?;
        let controls = ObserverWorkerControlsV4 {
            no_new_privileges: receipt.controls.no_new_privileges,
            resource_limits: receipt.controls.resource_limits,
            child_owned_process_group: receipt.controls.child_owned_process_group,
            inherited_fd_boundary: receipt.controls.inherited_fd_boundary,
            namespaces: false,
            seccomp_allowlist: false,
            filesystem_closed: false,
            cgroup_limits: false,
            cgroup_membership: false,
            parent_control_readback: true,
            wall_clock_limit: receipt.controls.wall_clock_limit,
            output_limit: receipt.controls.output_limit,
            process_group_custody: receipt.controls.process_group_custody,
            cgroup_cleanup: false,
        };
        let request_digest = worker_v4_request_digest(canonical_request);
        let result_digest = worker_v4_result_digest(&receipt.canonical_result);
        let digest = receipt_digest(
            profile,
            controls,
            limits,
            request_digest,
            result_digest,
            receipt.receipt_digest,
        );
        event("WORKER_V4_PARENT_EXIT", "baseline v4 supervisor completed");
        return Ok(ObserverWorkerReceiptV4 {
            profile,
            controls,
            limits,
            request_digest,
            result_digest,
            canonical_result: receipt.canonical_result,
            result: receipt.result,
            isolation_policy_digest: isolation_policy_digest(),
            receipt_digest: digest,
            boundary: OBSERVER_WORKER_V4_BOUNDARY,
        });
    }
    #[cfg(not(all(target_os = "linux", target_arch = "x86_64")))]
    return Err(reject("worker-v4-seccomp-architecture-unsupported"));
    #[cfg(all(target_os = "linux", target_arch = "x86_64"))]
    supervise_isolated(
        executable,
        canonical_request,
        request,
        profile,
        limits,
        launch,
    )
}

#[cfg(all(target_os = "linux", target_arch = "x86_64"))]
fn supervise_isolated(
    executable: &Path,
    canonical_request: &[u8],
    request: crate::observer_synthesis::ObserverSynthesisPipelineRequestV3,
    profile: IsolationProfileV4,
    limits: ObserverWorkerLimitsV4,
    launch: &ObserverWorkerLaunchV4,
) -> Result<ObserverWorkerReceiptV4, ObserverWorkerV4Error> {
    event("WORKER_V4_ISOLATED_ENTER", "preparing isolated child");
    let mut cgroup = if profile == IsolationProfileV4::Strict {
        Some(CgroupLeaf::create(
            launch
                .delegated_cgroup_root
                .as_deref()
                .ok_or_else(|| reject("worker-v4-delegation-required"))?,
            limits,
        )?)
    } else {
        if launch.delegated_cgroup_root.is_some() {
            return Err(reject("worker-v4-isolated-cgroup-not-requested"));
        }
        None
    };
    let parent_namespaces = namespace_links(std::process::id())?;
    let mut command = Command::new(executable);
    command
        .arg("--child-v4")
        .arg(profile.code().to_string())
        .arg(limits.cpu_seconds.to_string())
        .arg(limits.address_space_bytes.to_string());
    if let Some(leaf) = &cgroup {
        command.arg(&leaf.path);
    }
    command
        .env_clear()
        .env("LANG", "C.UTF-8")
        .env("LC_ALL", "C.UTF-8")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .process_group(0);
    configure_fd_boundary(&mut command);
    let mut child = command.spawn().map_err(|_| reject("worker-v4-spawn"))?;
    let deadline = Instant::now() + Duration::from_millis(limits.wall_timeout_ms as u64);
    if let Err(error) = wait_for_controls(
        &mut child,
        profile,
        cgroup.as_ref(),
        &parent_namespaces,
        deadline,
    ) {
        terminate_and_reap(&mut child);
        return Err(error);
    }
    if let Err(_) = write_request(&mut child, canonical_request) {
        terminate_and_reap(&mut child);
        return Err(reject("worker-v4-request-write"));
    }
    let bytes = collect_output(&mut child, limits.max_response_bytes as usize, deadline)?;
    if !child
        .wait()
        .map_err(|_| reject("worker-v4-wait"))?
        .success()
    {
        return Err(reject("worker-v4-child-exit"));
    }
    signal_process_group(child.id(), true).map_err(|_| reject("worker-v4-process-group-reap"))?;
    let wire = decode_wire(&bytes)?;
    let expected_flags = if profile == IsolationProfileV4::Strict {
        0xff
    } else {
        0x3f
    };
    if wire.profile != profile
        || wire.flags != expected_flags
        || wire.request_digest != worker_v4_request_digest(canonical_request)
        || wire.result_digest != worker_v4_result_digest(&wire.result)
    {
        return Err(reject("worker-v4-custody-binding"));
    }
    let fresh = run_observer_synthesis_pipeline_v3(&request)
        .map_err(|_| reject("worker-v4-fresh-execution"))?;
    let fresh_bytes = canonical_observer_pipeline_result_v3_bytes(&fresh)
        .map_err(|_| reject("worker-v4-fresh-encode"))?;
    if fresh_bytes != wire.result {
        return Err(reject("worker-v4-fresh-result-mismatch"));
    }
    let cgroup_cleanup = if let Some(leaf) = cgroup.as_mut() {
        leaf.cleanup()?;
        true
    } else {
        false
    };
    let controls = ObserverWorkerControlsV4 {
        no_new_privileges: true,
        resource_limits: true,
        child_owned_process_group: true,
        inherited_fd_boundary: true,
        namespaces: true,
        seccomp_allowlist: true,
        filesystem_closed: false,
        cgroup_limits: profile == IsolationProfileV4::Strict,
        cgroup_membership: profile == IsolationProfileV4::Strict,
        parent_control_readback: true,
        wall_clock_limit: true,
        output_limit: true,
        process_group_custody: true,
        cgroup_cleanup,
    };
    let digest = receipt_digest(
        profile,
        controls,
        limits,
        wire.request_digest,
        wire.result_digest,
        wire.digest,
    );
    event(
        "WORKER_V4_ISOLATED_EXIT",
        "isolated child custody completed",
    );
    Ok(ObserverWorkerReceiptV4 {
        profile,
        controls,
        limits,
        request_digest: wire.request_digest,
        result_digest: wire.result_digest,
        canonical_result: wire.result,
        result: fresh,
        isolation_policy_digest: isolation_policy_digest(),
        receipt_digest: digest,
        boundary: OBSERVER_WORKER_V4_BOUNDARY,
    })
}

#[cfg(target_os = "linux")]
fn configure_fd_boundary(command: &mut Command) {
    event("WORKER_V4_FD_ENTER", "configuring close-on-exec boundary");
    unsafe {
        command.pre_exec(|| {
            if linux_fd_ffi::close_range(3, u32::MAX, linux_fd_ffi::CLOSE_RANGE_CLOEXEC) == 0 {
                Ok(())
            } else {
                Err(std::io::Error::last_os_error())
            }
        });
    }
    event("WORKER_V4_FD_EXIT", "close-on-exec boundary configured");
}

fn write_request(child: &mut Child, request: &[u8]) -> std::io::Result<()> {
    event("WORKER_V4_WRITE_ENTER", "releasing child with request");
    let mut stdin = child
        .stdin
        .take()
        .ok_or_else(|| std::io::Error::new(std::io::ErrorKind::BrokenPipe, "missing stdin"))?;
    stdin.write_all(&[GO])?;
    stdin.write_all(request)?;
    drop(stdin);
    event("WORKER_V4_WRITE_EXIT", "child released with request");
    Ok(())
}

fn collect_output(
    child: &mut Child,
    limit: usize,
    deadline: Instant,
) -> Result<Vec<u8>, ObserverWorkerV4Error> {
    event("WORKER_V4_DRAIN_ENTER", "draining bounded v4 output");
    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| reject("worker-v4-output-pipe"))?;
    let (sender, receiver) = mpsc::sync_channel(1);
    let reader = thread::spawn(move || {
        let mut bytes = Vec::new();
        let result = stdout
            .take((limit + 1) as u64)
            .read_to_end(&mut bytes)
            .map(|_| bytes);
        let _ = sender.send(result);
    });
    let mut exited = false;
    let mut output = None;
    loop {
        if Instant::now() >= deadline {
            terminate_and_reap(child);
            let _ = reader.join();
            return Err(reject("worker-v4-wall-timeout"));
        }
        if !exited {
            match child.try_wait() {
                Ok(Some(_)) => exited = true,
                Ok(None) => {}
                Err(_) => {
                    terminate_and_reap(child);
                    let _ = reader.join();
                    return Err(reject("worker-v4-wait"));
                }
            }
        }
        if output.is_none() {
            match receiver.try_recv() {
                Ok(Ok(bytes)) if bytes.len() <= limit => output = Some(bytes),
                Ok(Ok(_)) => {
                    terminate_and_reap(child);
                    let _ = reader.join();
                    return Err(reject("worker-v4-output-limit"));
                }
                Ok(Err(_)) | Err(TryRecvError::Disconnected) => {
                    terminate_and_reap(child);
                    let _ = reader.join();
                    return Err(reject("worker-v4-output-read"));
                }
                Err(TryRecvError::Empty) => {}
            }
        }
        if exited && output.is_some() {
            break;
        }
        thread::sleep(POLL);
    }
    if reader.join().is_err() {
        return Err(reject("worker-v4-output-reader"));
    }
    event("WORKER_V4_DRAIN_EXIT", "bounded v4 output drained");
    output.ok_or_else(|| reject("worker-v4-missing-output"))
}

fn terminate_and_reap(child: &mut Child) {
    event("WORKER_V4_TERMINATE_ENTER", "terminating v4 process group");
    let _ = signal_process_group(child.id(), false);
    thread::sleep(Duration::from_millis(50));
    let _ = signal_process_group(child.id(), true);
    let _ = child.wait();
    event("WORKER_V4_TERMINATE_EXIT", "v4 process group reaped");
}

#[cfg(all(target_os = "linux", target_arch = "x86_64"))]
fn wait_for_controls(
    child: &mut Child,
    profile: IsolationProfileV4,
    cgroup: Option<&CgroupLeaf>,
    parent_ns: &[String],
    deadline: Instant,
) -> Result<(), ObserverWorkerV4Error> {
    event(
        "WORKER_V4_READBACK_ENTER",
        "waiting for independent parent readback",
    );
    loop {
        if Instant::now() >= deadline {
            return Err(reject("worker-v4-control-readback-timeout"));
        }
        if child
            .try_wait()
            .map_err(|_| reject("worker-v4-wait"))?
            .is_some()
        {
            return Err(reject("worker-v4-child-setup-exit"));
        }
        let pid = child.id();
        let status = fs::read_to_string(format!("/proc/{pid}/status")).unwrap_or_default();
        let nnp = status.lines().any(|line| line == "NoNewPrivs:\t1");
        let seccomp = status.lines().any(|line| line == "Seccomp:\t2");
        let namespaces = namespace_links(pid)
            .map(|links| links.iter().zip(parent_ns).all(|(a, b)| a != b))
            .unwrap_or(false);
        let cgroup_ok = match (profile, cgroup) {
            (IsolationProfileV4::Strict, Some(leaf)) => {
                leaf.verify_controls().is_ok() && leaf.contains(pid)
            }
            (IsolationProfileV4::Isolated, None) => true,
            _ => false,
        };
        if nnp && seccomp && namespaces && cgroup_ok {
            event(
                "WORKER_V4_READBACK_EXIT",
                "parent control readback completed",
            );
            return Ok(());
        }
        thread::sleep(POLL);
    }
}

#[cfg(target_os = "linux")]
mod linux_fd_ffi {
    use std::os::raw::{c_int, c_uint};

    pub const CLOSE_RANGE_CLOEXEC: c_uint = 1 << 2;

    unsafe extern "C" {
        pub fn close_range(first: c_uint, last: c_uint, flags: c_uint) -> c_int;
    }
}
