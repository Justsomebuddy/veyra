//! Strict closed-rootfs observer worker v5.

use std::fmt;
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::mpsc::{self, TryRecvError};
use std::thread;
use std::time::{Duration, Instant};

#[cfg(target_os = "linux")]
use std::os::unix::process::CommandExt;

use crate::observer_synthesis::{
    canonical_discovery_request_v5_bytes, canonical_discovery_result_v5_bytes,
    decode_discovery_request_v5_bytes, discovery_request_v5_root, discovery_result_v5_root,
    synthesize_discovery_v5, DiscoverySearchRequestV5, DiscoverySearchResultV5,
};

use super::digest::domain_sha256;
use super::event;
#[cfg(all(target_os = "linux", target_arch = "x86_64"))]
use super::isolation_v4::apply_and_verify_seccomp;
#[cfg(target_os = "linux")]
use super::isolation_v4::{apply_and_verify_namespaces, namespace_links};
#[cfg(target_os = "linux")]
use super::isolation_v5::{
    apply_closed_rootfs_v5, parent_closed_rootfs_readback, verify_current_cgroup_v5, CgroupLeafV5,
    RootfsMountpointV5,
};
use super::linux::signal_process_group;
use super::worker_v2::{
    apply_worker_v2_child_controls, WorkerControlStateV2, WorkerV2Admission, WorkerV2LaunchOptions,
    WorkerV2Limits, WorkerV2Policy,
};

const MAGIC: &[u8; 4] = b"VOW5";
const VERSION: u16 = 5;
const GO: u8 = 0xa5;
const SETUP: u8 = 0x5a;
const FIXED_CHILD: &str = "vam-observer-pipeline-worker";
const REQUEST_DOMAIN: &[u8] = b"veyra.native-observer-worker.v5.request";
const RESULT_DOMAIN: &[u8] = b"veyra.native-observer-worker.v5.result";
const CHILD_DOMAIN: &[u8] = b"veyra.native-observer-worker.v5.child";
const RECEIPT_DOMAIN: &[u8] = b"veyra.native-observer-worker.v5.receipt";
const POLICY_DOMAIN: &[u8] = b"veyra.native-observer-worker.v5.policy";
const MAX_DISCOVERY_REQUEST_BYTES: usize = 1_024;
const MAX_DISCOVERY_RESULT_BYTES: usize = 8 * 1_024;
// header + length + worker digests + discovery roots + child digest
const WIRE_FIXED: usize = 174;
const POLL: Duration = Duration::from_millis(5);

pub const OBSERVER_WORKER_V5_BOUNDARY: &str = "Linux x86-64 only and fail closed: strict-v5 executes only canonical DiscoverySearchRequestV5 -> synthesize_discovery_v5 -> canonical DiscoverySearchResultV5 and binds both worker digests and discovery roots; it requires fresh user/mount/network/IPC/UTS namespaces, private propagation, a size-bounded empty tmpfs pivot_root with detached old root, the pinned v4 seccomp allowlist, and a caller-owned delegated cgroup-v2 root with exact cpu.max, memory.max and pids.max; parent and child independently read back isolation, parent owns deadline/output/process-group custody, and success additionally binds empty cgroup and rootfs-mountpoint cleanup";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObserverWorkerLimitsV5 {
    pub cpu_seconds: u32,
    pub address_space_bytes: u64,
    pub wall_timeout_ms: u32,
    pub max_response_bytes: u32,
    pub cpu_quota_us: u32,
    pub cpu_period_us: u32,
    pub memory_bytes: u64,
    pub pids: u32,
    pub rootfs_bytes: u64,
}

impl Default for ObserverWorkerLimitsV5 {
    fn default() -> Self {
        event("WORKER_V5_LIMITS_DEFAULT_ENTER", "constructing v5 limits");
        let result = Self {
            cpu_seconds: 10,
            address_space_bytes: 512 * 1024 * 1024,
            wall_timeout_ms: 10_000,
            max_response_bytes: (MAX_DISCOVERY_RESULT_BYTES + WIRE_FIXED) as u32,
            cpu_quota_us: 100_000,
            cpu_period_us: 100_000,
            memory_bytes: 512 * 1024 * 1024,
            pids: 1,
            rootfs_bytes: 16 * 1024 * 1024,
        };
        event("WORKER_V5_LIMITS_DEFAULT_EXIT", "v5 limits constructed");
        result
    }
}

#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct ObserverWorkerLaunchV5 {
    pub delegated_cgroup_root: Option<PathBuf>,
    pub rootfs_mount_base: Option<PathBuf>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObserverWorkerControlsV5 {
    pub no_new_privileges: bool,
    pub resource_limits: bool,
    pub child_owned_process_group: bool,
    pub inherited_fd_boundary: bool,
    pub namespaces: bool,
    pub seccomp_allowlist: bool,
    pub private_mount_propagation: bool,
    pub tmpfs_root: bool,
    pub old_root_detached: bool,
    pub filesystem_closed: bool,
    pub cgroup_limits: bool,
    pub cgroup_membership: bool,
    pub parent_control_readback: bool,
    pub wall_clock_limit: bool,
    pub output_limit: bool,
    pub process_group_custody: bool,
    pub cgroup_cleanup: bool,
    pub rootfs_cleanup: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ObserverWorkerReceiptV5 {
    controls: ObserverWorkerControlsV5,
    limits: ObserverWorkerLimitsV5,
    request_digest: [u8; 32],
    result_digest: [u8; 32],
    request_root: [u8; 32],
    result_root: [u8; 32],
    isolation_policy_digest: [u8; 32],
    canonical_request: Vec<u8>,
    canonical_result: Vec<u8>,
    request: DiscoverySearchRequestV5,
    result: DiscoverySearchResultV5,
    receipt_digest: [u8; 32],
    boundary: &'static str,
}

impl ObserverWorkerReceiptV5 {
    pub fn controls(&self) -> ObserverWorkerControlsV5 {
        event("WORKER_V5_RECEIPT_CONTROLS", "reading v5 controls");
        self.controls
    }
    pub fn limits(&self) -> ObserverWorkerLimitsV5 {
        event("WORKER_V5_RECEIPT_LIMITS", "reading v5 limits");
        self.limits
    }
    pub fn request_digest(&self) -> [u8; 32] {
        event("WORKER_V5_RECEIPT_REQUEST", "reading v5 request digest");
        self.request_digest
    }
    pub fn result_digest(&self) -> [u8; 32] {
        event("WORKER_V5_RECEIPT_RESULT", "reading v5 result digest");
        self.result_digest
    }
    pub fn request_root(&self) -> [u8; 32] {
        event("WORKER_V5_RECEIPT_REQUEST_ROOT", "reading v5 request root");
        self.request_root
    }
    pub fn result_root(&self) -> [u8; 32] {
        event("WORKER_V5_RECEIPT_RESULT_ROOT", "reading v5 result root");
        self.result_root
    }
    pub fn isolation_policy_digest(&self) -> [u8; 32] {
        event("WORKER_V5_RECEIPT_POLICY", "reading v5 policy digest");
        self.isolation_policy_digest
    }
    pub fn canonical_request(&self) -> &[u8] {
        event(
            "WORKER_V5_RECEIPT_REQUEST_BYTES",
            "borrowing v5 request bytes",
        );
        &self.canonical_request
    }
    pub fn canonical_result(&self) -> &[u8] {
        event("WORKER_V5_RECEIPT_BYTES", "borrowing v5 result bytes");
        &self.canonical_result
    }
    pub fn request(&self) -> &DiscoverySearchRequestV5 {
        event(
            "WORKER_V5_RECEIPT_REQUEST_VALUE",
            "borrowing v5 typed request",
        );
        &self.request
    }
    pub fn result(&self) -> &DiscoverySearchResultV5 {
        event("WORKER_V5_RECEIPT_VALUE", "borrowing v5 typed result");
        &self.result
    }
    pub fn receipt_digest(&self) -> [u8; 32] {
        event("WORKER_V5_RECEIPT_DIGEST", "reading v5 receipt digest");
        self.receipt_digest
    }
    pub fn boundary(&self) -> &'static str {
        event("WORKER_V5_RECEIPT_BOUNDARY", "reading v5 boundary");
        self.boundary
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObserverWorkerV5Error(pub &'static str);

impl fmt::Display for ObserverWorkerV5Error {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        event("WORKER_V5_ERROR_ENTER", "rendering v5 error");
        let result = formatter.write_str(self.0);
        event("WORKER_V5_ERROR_EXIT", "v5 error rendered");
        result
    }
}

impl std::error::Error for ObserverWorkerV5Error {}

#[derive(Clone, Debug, Eq, PartialEq)]
struct ChildWireV5 {
    flags: u32,
    request_digest: [u8; 32],
    result_digest: [u8; 32],
    request_root: [u8; 32],
    result_root: [u8; 32],
    result: Vec<u8>,
    digest: [u8; 32],
}

fn reject(reason: &'static str) -> ObserverWorkerV5Error {
    event("WORKER_V5_REJECT", reason);
    ObserverWorkerV5Error(reason)
}

fn discovery_root(value: &str) -> Result<[u8; 32], ObserverWorkerV5Error> {
    event("WORKER_V5_ROOT_DECODE_ENTER", "decoding discovery root");
    if value.len() != 64 {
        return Err(reject("worker-v5-discovery-root"));
    }
    let mut root = [0; 32];
    for (index, pair) in value.as_bytes().chunks_exact(2).enumerate() {
        let text = std::str::from_utf8(pair).map_err(|_| reject("worker-v5-discovery-root"))?;
        root[index] =
            u8::from_str_radix(text, 16).map_err(|_| reject("worker-v5-discovery-root"))?;
    }
    event("WORKER_V5_ROOT_DECODE_EXIT", "discovery root decoded");
    Ok(root)
}

pub(super) fn validate_limits(limits: ObserverWorkerLimitsV5) -> Result<(), ObserverWorkerV5Error> {
    event("WORKER_V5_LIMITS_ENTER", "validating v5 limits");
    if !(1..=10).contains(&limits.cpu_seconds)
        || !(128 * 1024 * 1024..=2 * 1024 * 1024 * 1024).contains(&limits.address_space_bytes)
        || !(1..=30_000).contains(&limits.wall_timeout_ms)
        || !(WIRE_FIXED as u32..=(MAX_DISCOVERY_RESULT_BYTES + WIRE_FIXED) as u32)
            .contains(&limits.max_response_bytes)
        || !(1_000..=1_000_000).contains(&limits.cpu_period_us)
        || !(1_000..=limits.cpu_period_us.saturating_mul(64)).contains(&limits.cpu_quota_us)
        || !(128 * 1024 * 1024..=2 * 1024 * 1024 * 1024).contains(&limits.memory_bytes)
        || limits.memory_bytes > limits.address_space_bytes
        || !(1..=64).contains(&limits.pids)
        || !(1024 * 1024..=64 * 1024 * 1024).contains(&limits.rootfs_bytes)
    {
        return Err(reject("worker-v5-invalid-limits"));
    }
    event("WORKER_V5_LIMITS_EXIT", "v5 limits validated");
    Ok(())
}

fn child_flags(controls: ObserverWorkerControlsV5) -> u32 {
    event("WORKER_V5_FLAGS_ENTER", "encoding v5 child flags");
    let result = u32::from(controls.no_new_privileges)
        | (u32::from(controls.resource_limits) << 1)
        | (u32::from(controls.child_owned_process_group) << 2)
        | (u32::from(controls.inherited_fd_boundary) << 3)
        | (u32::from(controls.namespaces) << 4)
        | (u32::from(controls.seccomp_allowlist) << 5)
        | (u32::from(controls.private_mount_propagation) << 6)
        | (u32::from(controls.tmpfs_root) << 7)
        | (u32::from(controls.old_root_detached) << 8)
        | (u32::from(controls.filesystem_closed) << 9)
        | (u32::from(controls.cgroup_limits) << 10)
        | (u32::from(controls.cgroup_membership) << 11);
    event("WORKER_V5_FLAGS_EXIT", "v5 child flags encoded");
    result
}

fn child_digest(wire: &ChildWireV5) -> [u8; 32] {
    event("WORKER_V5_CHILD_BIND_ENTER", "binding v5 child evidence");
    let mut body = Vec::new();
    body.extend_from_slice(&wire.flags.to_be_bytes());
    body.extend_from_slice(&wire.request_digest);
    body.extend_from_slice(&wire.result_digest);
    body.extend_from_slice(&wire.request_root);
    body.extend_from_slice(&wire.result_root);
    let result = domain_sha256(CHILD_DOMAIN, &body);
    event("WORKER_V5_CHILD_BIND_EXIT", "v5 child evidence bound");
    result
}

fn policy_digest() -> [u8; 32] {
    event("WORKER_V5_POLICY_ENTER", "binding v5 isolation policy");
    let result = domain_sha256(POLICY_DOMAIN, OBSERVER_WORKER_V5_BOUNDARY.as_bytes());
    event("WORKER_V5_POLICY_EXIT", "v5 isolation policy bound");
    result
}

fn receipt_digest(
    controls: ObserverWorkerControlsV5,
    limits: ObserverWorkerLimitsV5,
    request_digest: [u8; 32],
    result_digest: [u8; 32],
    request_root: [u8; 32],
    result_root: [u8; 32],
    child_root: [u8; 32],
) -> [u8; 32] {
    event("WORKER_V5_RECEIPT_BIND_ENTER", "binding v5 receipt");
    let mut body = Vec::new();
    body.extend_from_slice(&child_flags(controls).to_be_bytes());
    let parent = u32::from(controls.parent_control_readback)
        | (u32::from(controls.wall_clock_limit) << 1)
        | (u32::from(controls.output_limit) << 2)
        | (u32::from(controls.process_group_custody) << 3)
        | (u32::from(controls.cgroup_cleanup) << 4)
        | (u32::from(controls.rootfs_cleanup) << 5);
    body.extend_from_slice(&parent.to_be_bytes());
    body.extend_from_slice(&limits.cpu_seconds.to_be_bytes());
    body.extend_from_slice(&limits.address_space_bytes.to_be_bytes());
    body.extend_from_slice(&limits.wall_timeout_ms.to_be_bytes());
    body.extend_from_slice(&limits.max_response_bytes.to_be_bytes());
    body.extend_from_slice(&limits.cpu_quota_us.to_be_bytes());
    body.extend_from_slice(&limits.cpu_period_us.to_be_bytes());
    body.extend_from_slice(&limits.memory_bytes.to_be_bytes());
    body.extend_from_slice(&limits.pids.to_be_bytes());
    body.extend_from_slice(&limits.rootfs_bytes.to_be_bytes());
    body.extend_from_slice(&request_digest);
    body.extend_from_slice(&result_digest);
    body.extend_from_slice(&request_root);
    body.extend_from_slice(&result_root);
    body.extend_from_slice(&child_root);
    body.extend_from_slice(&policy_digest());
    let result = domain_sha256(RECEIPT_DOMAIN, &body);
    event("WORKER_V5_RECEIPT_BIND_EXIT", "v5 receipt bound");
    result
}

fn encode_wire(wire: &ChildWireV5) -> Result<Vec<u8>, ObserverWorkerV5Error> {
    event("WORKER_V5_WIRE_ENCODE_ENTER", "encoding v5 child wire");
    if wire.flags != 0x0fff
        || wire.result.len() > MAX_DISCOVERY_RESULT_BYTES
        || wire.digest != child_digest(wire)
    {
        return Err(reject("worker-v5-invalid-child-wire"));
    }
    let mut bytes = Vec::with_capacity(WIRE_FIXED + wire.result.len());
    bytes.extend_from_slice(MAGIC);
    bytes.extend_from_slice(&VERSION.to_be_bytes());
    bytes.extend_from_slice(&wire.flags.to_be_bytes());
    bytes.extend_from_slice(&(wire.result.len() as u32).to_be_bytes());
    bytes.extend_from_slice(&wire.request_digest);
    bytes.extend_from_slice(&wire.result_digest);
    bytes.extend_from_slice(&wire.request_root);
    bytes.extend_from_slice(&wire.result_root);
    bytes.extend_from_slice(&wire.result);
    bytes.extend_from_slice(&wire.digest);
    event("WORKER_V5_WIRE_ENCODE_EXIT", "v5 child wire encoded");
    Ok(bytes)
}

fn take<const N: usize>(
    bytes: &[u8],
    cursor: &mut usize,
) -> Result<[u8; N], ObserverWorkerV5Error> {
    event("WORKER_V5_WIRE_TAKE_ENTER", "reading v5 wire field");
    let end = cursor
        .checked_add(N)
        .ok_or_else(|| reject("worker-v5-wire-overflow"))?;
    let result = bytes
        .get(*cursor..end)
        .ok_or_else(|| reject("worker-v5-truncated"))?
        .try_into()
        .map_err(|_| reject("worker-v5-truncated"))?;
    *cursor = end;
    event("WORKER_V5_WIRE_TAKE_EXIT", "v5 wire field read");
    Ok(result)
}

fn decode_wire(bytes: &[u8]) -> Result<ChildWireV5, ObserverWorkerV5Error> {
    event("WORKER_V5_WIRE_DECODE_ENTER", "decoding v5 child wire");
    if bytes.len() < WIRE_FIXED || bytes.len() > WIRE_FIXED + MAX_DISCOVERY_RESULT_BYTES {
        return Err(reject("worker-v5-response-size"));
    }
    let mut cursor = 0;
    if &take::<4>(bytes, &mut cursor)? != MAGIC
        || u16::from_be_bytes(take(bytes, &mut cursor)?) != VERSION
    {
        return Err(reject("worker-v5-wire-header"));
    }
    let flags = u32::from_be_bytes(take(bytes, &mut cursor)?);
    let result_len = u32::from_be_bytes(take(bytes, &mut cursor)?) as usize;
    if flags != 0x0fff || result_len > MAX_DISCOVERY_RESULT_BYTES {
        return Err(reject("worker-v5-wire-shape"));
    }
    let request_digest = take(bytes, &mut cursor)?;
    let result_digest = take(bytes, &mut cursor)?;
    let request_root = take(bytes, &mut cursor)?;
    let result_root = take(bytes, &mut cursor)?;
    let end = cursor
        .checked_add(result_len)
        .ok_or_else(|| reject("worker-v5-wire-overflow"))?;
    let result = bytes
        .get(cursor..end)
        .ok_or_else(|| reject("worker-v5-truncated"))?
        .to_vec();
    cursor = end;
    let digest = take(bytes, &mut cursor)?;
    if cursor != bytes.len() {
        return Err(reject("worker-v5-trailing"));
    }
    let wire = ChildWireV5 {
        flags,
        request_digest,
        result_digest,
        request_root,
        result_root,
        result,
        digest,
    };
    if wire.digest != child_digest(&wire) {
        return Err(reject("worker-v5-child-digest"));
    }
    event("WORKER_V5_WIRE_DECODE_EXIT", "v5 child wire decoded");
    Ok(wire)
}

#[cfg(all(target_os = "linux", target_arch = "x86_64"))]
pub fn run_discovery_child_v5<R: Read, W: Write>(
    mut input: R,
    mut output: W,
    limits: ObserverWorkerLimitsV5,
    cgroup_leaf: &Path,
    rootfs_mountpoint: &Path,
) -> Result<(), ObserverWorkerV5Error> {
    event(
        "WORKER_V5_CHILD_ENTER",
        "starting strict discovery v5 child",
    );
    validate_limits(limits)?;
    let mut setup = [0];
    input
        .read_exact(&mut setup)
        .map_err(|_| reject("worker-v5-setup-read"))?;
    if setup[0] != SETUP {
        return Err(reject("worker-v5-setup-marker"));
    }
    let report = apply_worker_v2_child_controls(
        WorkerV2Policy::Baseline,
        WorkerV2Limits {
            cpu_seconds: limits.cpu_seconds,
            address_space_bytes: limits.address_space_bytes,
        },
        &WorkerV2LaunchOptions::default(),
    )
    .map_err(|_| reject("worker-v5-baseline-controls"))?;
    if report.admission != WorkerV2Admission::CustodyPending {
        return Err(reject("worker-v5-baseline-controls-blocked"));
    }
    let controls = {
        let cgroup_membership = verify_current_cgroup_v5(cgroup_leaf, limits)?;
        let namespaces =
            apply_and_verify_namespaces().map_err(|_| reject("worker-v5-namespace-setup"))?;
        let filesystem_closed = apply_closed_rootfs_v5(rootfs_mountpoint, limits.rootfs_bytes)?;
        let seccomp_allowlist =
            apply_and_verify_seccomp().map_err(|_| reject("worker-v5-seccomp-setup"))?;
        ObserverWorkerControlsV5 {
            no_new_privileges: report.no_new_privileges.state == WorkerControlStateV2::Enforced,
            resource_limits: report.resource_limits.state == WorkerControlStateV2::Enforced,
            child_owned_process_group: report.process_group.state == WorkerControlStateV2::Enforced,
            inherited_fd_boundary: report.inherited_fd_boundary.state
                == WorkerControlStateV2::Enforced,
            namespaces,
            seccomp_allowlist,
            private_mount_propagation: namespaces,
            tmpfs_root: filesystem_closed,
            old_root_detached: filesystem_closed,
            filesystem_closed,
            cgroup_limits: cgroup_membership,
            cgroup_membership,
            parent_control_readback: false,
            wall_clock_limit: false,
            output_limit: false,
            process_group_custody: false,
            cgroup_cleanup: false,
            rootfs_cleanup: false,
        }
    };
    if child_flags(controls) != 0x0fff {
        return Err(reject("worker-v5-child-control-readback"));
    }
    let mut go = [0];
    input
        .read_exact(&mut go)
        .map_err(|_| reject("worker-v5-go-read"))?;
    if go[0] != GO {
        return Err(reject("worker-v5-go-marker"));
    }
    let mut request_bytes = Vec::new();
    input
        .take((MAX_DISCOVERY_REQUEST_BYTES + 1) as u64)
        .read_to_end(&mut request_bytes)
        .map_err(|_| reject("worker-v5-request-read"))?;
    if request_bytes.len() > MAX_DISCOVERY_REQUEST_BYTES {
        return Err(reject("worker-v5-request-size"));
    }
    let request = decode_discovery_request_v5_bytes(&request_bytes)
        .map_err(|_| reject("worker-v5-request-decode"))?;
    if canonical_discovery_request_v5_bytes(&request)
        .map_err(|_| reject("worker-v5-request-encode"))?
        != request_bytes
    {
        return Err(reject("worker-v5-request-noncanonical"));
    }
    let result =
        synthesize_discovery_v5(&request).map_err(|_| reject("worker-v5-discovery-execution"))?;
    let request_root = discovery_root(
        &discovery_request_v5_root(&request).map_err(|_| reject("worker-v5-request-root"))?,
    )?;
    let result_root = discovery_root(
        &discovery_result_v5_root(&result).map_err(|_| reject("worker-v5-result-root"))?,
    )?;
    let result = canonical_discovery_result_v5_bytes(&result)
        .map_err(|_| reject("worker-v5-result-encode"))?;
    let mut wire = ChildWireV5 {
        flags: child_flags(controls),
        request_digest: domain_sha256(REQUEST_DOMAIN, &request_bytes),
        result_digest: domain_sha256(RESULT_DOMAIN, &result),
        request_root,
        result_root,
        result,
        digest: [0; 32],
    };
    wire.digest = child_digest(&wire);
    output
        .write_all(&encode_wire(&wire)?)
        .map_err(|_| reject("worker-v5-response-write"))?;
    output
        .flush()
        .map_err(|_| reject("worker-v5-response-flush"))?;
    event(
        "WORKER_V5_CHILD_EXIT",
        "strict discovery v5 child completed",
    );
    Ok(())
}

#[cfg(not(all(target_os = "linux", target_arch = "x86_64")))]
pub fn run_discovery_child_v5<R: Read, W: Write>(
    _input: R,
    _output: W,
    _limits: ObserverWorkerLimitsV5,
    _cgroup_leaf: &Path,
    _rootfs_mountpoint: &Path,
) -> Result<(), ObserverWorkerV5Error> {
    Err(reject("worker-v5-platform-unsupported"))
}

#[cfg(all(target_os = "linux", target_arch = "x86_64"))]
pub fn supervise_discovery_v5(
    executable: &Path,
    canonical_request: &[u8],
    limits: ObserverWorkerLimitsV5,
    launch: &ObserverWorkerLaunchV5,
) -> Result<ObserverWorkerReceiptV5, ObserverWorkerV5Error> {
    event(
        "WORKER_V5_PARENT_ENTER",
        "starting strict discovery v5 supervisor",
    );
    let expected = if cfg!(windows) {
        "vam-observer-pipeline-worker.exe"
    } else {
        FIXED_CHILD
    };
    if executable.file_name().and_then(|value| value.to_str()) != Some(expected) {
        return Err(reject("worker-v5-not-fixed-child"));
    }
    validate_limits(limits)?;
    let request = decode_discovery_request_v5_bytes(canonical_request)
        .map_err(|_| reject("worker-v5-request-decode"))?;
    if canonical_request.len() > MAX_DISCOVERY_REQUEST_BYTES
        || canonical_discovery_request_v5_bytes(&request)
            .map_err(|_| reject("worker-v5-request-encode"))?
            != canonical_request
    {
        return Err(reject("worker-v5-request-noncanonical"));
    }
    #[cfg(all(target_os = "linux", target_arch = "x86_64"))]
    {
        let cgroup_root = launch
            .delegated_cgroup_root
            .as_deref()
            .ok_or_else(|| reject("worker-v5-delegation-required"))?;
        let rootfs_base = launch
            .rootfs_mount_base
            .as_deref()
            .ok_or_else(|| reject("worker-v5-rootfs-base-required"))?;
        let mut rootfs = RootfsMountpointV5::create(rootfs_base)?;
        let mut cgroup = match CgroupLeafV5::create(cgroup_root, limits) {
            Ok(value) => value,
            Err(error) => {
                let _ = rootfs.cleanup();
                return Err(error);
            }
        };
        let parent_namespaces = namespace_links(std::process::id())
            .map_err(|_| reject("worker-v5-parent-namespace-read"))?;
        let mut command = Command::new(executable);
        command
            .arg("--child-v5")
            .arg(limits.cpu_seconds.to_string())
            .arg(limits.address_space_bytes.to_string())
            .arg(limits.wall_timeout_ms.to_string())
            .arg(limits.max_response_bytes.to_string())
            .arg(limits.cpu_quota_us.to_string())
            .arg(limits.cpu_period_us.to_string())
            .arg(limits.memory_bytes.to_string())
            .arg(limits.pids.to_string())
            .arg(limits.rootfs_bytes.to_string())
            .arg(&cgroup.path)
            .arg(&rootfs.path)
            .env_clear()
            .env("LANG", "C.UTF-8")
            .env("LC_ALL", "C.UTF-8")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .process_group(0);
        configure_fd_boundary(&mut command);
        let mut child = match command.spawn() {
            Ok(value) => value,
            Err(_) => {
                let _ = cgroup.cleanup();
                let _ = rootfs.cleanup();
                return Err(reject("worker-v5-spawn"));
            }
        };
        if let Err(error) = cgroup.attach(child.id()) {
            terminate_and_reap(&mut child);
            let _ = cgroup.cleanup();
            let _ = rootfs.cleanup();
            return Err(error);
        }
        if release_setup(&mut child).is_err() {
            terminate_and_reap(&mut child);
            cleanup_after_child(&mut cgroup, &mut rootfs)?;
            return Err(reject("worker-v5-setup-write"));
        }
        let deadline = Instant::now() + Duration::from_millis(limits.wall_timeout_ms as u64);
        if let Err(error) = wait_for_readback(&mut child, &cgroup, &parent_namespaces, deadline) {
            terminate_and_reap(&mut child);
            cleanup_after_child(&mut cgroup, &mut rootfs)?;
            return Err(error);
        }
        if write_request(&mut child, canonical_request).is_err() {
            terminate_and_reap(&mut child);
            cleanup_after_child(&mut cgroup, &mut rootfs)?;
            return Err(reject("worker-v5-request-write"));
        }
        let bytes = match collect_output(&mut child, limits.max_response_bytes as usize, deadline) {
            Ok(value) => value,
            Err(error) => {
                terminate_and_reap(&mut child);
                cleanup_after_child(&mut cgroup, &mut rootfs)?;
                return Err(error);
            }
        };
        let status = match child.wait() {
            Ok(value) => value,
            Err(_) => {
                terminate_and_reap(&mut child);
                cleanup_after_child(&mut cgroup, &mut rootfs)?;
                return Err(reject("worker-v5-wait"));
            }
        };
        if !status.success() {
            cleanup_after_child(&mut cgroup, &mut rootfs)?;
            return Err(reject("worker-v5-child-exit"));
        }
        let validation = (|| {
            signal_process_group(child.id(), true)
                .map_err(|_| reject("worker-v5-process-group-reap"))?;
            let wire = decode_wire(&bytes)?;
            let request_root = discovery_root(
                &discovery_request_v5_root(&request)
                    .map_err(|_| reject("worker-v5-request-root"))?,
            )?;
            if wire.flags != 0x0fff
                || wire.request_digest != domain_sha256(REQUEST_DOMAIN, canonical_request)
                || wire.result_digest != domain_sha256(RESULT_DOMAIN, &wire.result)
                || wire.request_root != request_root
            {
                return Err(reject("worker-v5-custody-binding"));
            }
            let fresh = synthesize_discovery_v5(&request)
                .map_err(|_| reject("worker-v5-fresh-discovery-execution"))?;
            let fresh_bytes = canonical_discovery_result_v5_bytes(&fresh)
                .map_err(|_| reject("worker-v5-fresh-encode"))?;
            let result_root = discovery_root(
                &discovery_result_v5_root(&fresh).map_err(|_| reject("worker-v5-result-root"))?,
            )?;
            if fresh_bytes != wire.result || wire.result_root != result_root {
                return Err(reject("worker-v5-fresh-result-mismatch"));
            }
            Ok((wire, fresh))
        })();
        let (cgroup_cleanup, rootfs_cleanup) = cleanup_after_child(&mut cgroup, &mut rootfs)?;
        let (wire, fresh) = validation?;
        let controls = ObserverWorkerControlsV5 {
            no_new_privileges: true,
            resource_limits: true,
            child_owned_process_group: true,
            inherited_fd_boundary: true,
            namespaces: true,
            seccomp_allowlist: true,
            private_mount_propagation: true,
            tmpfs_root: true,
            old_root_detached: true,
            filesystem_closed: true,
            cgroup_limits: true,
            cgroup_membership: true,
            parent_control_readback: true,
            wall_clock_limit: true,
            output_limit: true,
            process_group_custody: true,
            cgroup_cleanup,
            rootfs_cleanup,
        };
        let receipt_digest = receipt_digest(
            controls,
            limits,
            wire.request_digest,
            wire.result_digest,
            wire.request_root,
            wire.result_root,
            wire.digest,
        );
        let receipt = ObserverWorkerReceiptV5 {
            controls,
            limits,
            request_digest: wire.request_digest,
            result_digest: wire.result_digest,
            request_root: wire.request_root,
            result_root: wire.result_root,
            isolation_policy_digest: policy_digest(),
            canonical_request: canonical_request.to_vec(),
            canonical_result: wire.result,
            request,
            result: fresh,
            receipt_digest,
            boundary: OBSERVER_WORKER_V5_BOUNDARY,
        };
        event(
            "WORKER_V5_PARENT_EXIT",
            "strict discovery v5 supervisor completed",
        );
        Ok(receipt)
    }
}

#[cfg(not(all(target_os = "linux", target_arch = "x86_64")))]
pub fn supervise_discovery_v5(
    _executable: &Path,
    _canonical_request: &[u8],
    _limits: ObserverWorkerLimitsV5,
    _launch: &ObserverWorkerLaunchV5,
) -> Result<ObserverWorkerReceiptV5, ObserverWorkerV5Error> {
    Err(reject("worker-v5-platform-unsupported"))
}

#[cfg(target_os = "linux")]
fn configure_fd_boundary(command: &mut Command) {
    event("WORKER_V5_FD_ENTER", "configuring close-on-exec boundary");
    unsafe {
        command.pre_exec(|| {
            if ffi::close_range(3, u32::MAX, ffi::CLOSE_RANGE_CLOEXEC) == 0 {
                Ok(())
            } else {
                Err(std::io::Error::last_os_error())
            }
        });
    }
    event("WORKER_V5_FD_EXIT", "close-on-exec boundary configured");
}

#[cfg(all(target_os = "linux", target_arch = "x86_64"))]
fn wait_for_readback(
    child: &mut Child,
    cgroup: &CgroupLeafV5,
    parent_namespaces: &[String],
    deadline: Instant,
) -> Result<(), ObserverWorkerV5Error> {
    event("WORKER_V5_READBACK_ENTER", "waiting for parent readback");
    loop {
        if Instant::now() >= deadline {
            return Err(reject("worker-v5-control-readback-timeout"));
        }
        if child
            .try_wait()
            .map_err(|_| reject("worker-v5-wait"))?
            .is_some()
        {
            return Err(reject("worker-v5-child-setup-exit"));
        }
        let pid = child.id();
        let status = std::fs::read_to_string(format!("/proc/{pid}/status")).unwrap_or_default();
        let nnp = status.lines().any(|line| line == "NoNewPrivs:\t1");
        let seccomp = status.lines().any(|line| line == "Seccomp:\t2");
        let namespaces = namespace_links(pid)
            .map(|links| {
                links
                    .iter()
                    .zip(parent_namespaces)
                    .all(|(left, right)| left != right)
            })
            .unwrap_or(false);
        let rootfs = parent_closed_rootfs_readback(pid).unwrap_or(false);
        if nnp && seccomp && namespaces && rootfs && cgroup.verify().is_ok() && cgroup.contains(pid)
        {
            event("WORKER_V5_READBACK_EXIT", "parent readback completed");
            return Ok(());
        }
        thread::sleep(POLL);
    }
}

fn write_request(child: &mut Child, request: &[u8]) -> std::io::Result<()> {
    event("WORKER_V5_WRITE_ENTER", "releasing v5 child");
    let mut stdin = child.stdin.take().ok_or_else(|| {
        std::io::Error::new(std::io::ErrorKind::BrokenPipe, "missing child stdin")
    })?;
    stdin.write_all(&[GO])?;
    stdin.write_all(request)?;
    drop(stdin);
    event("WORKER_V5_WRITE_EXIT", "v5 child released");
    Ok(())
}

fn release_setup(child: &mut Child) -> std::io::Result<()> {
    event("WORKER_V5_SETUP_ENTER", "releasing v5 setup");
    let stdin = child.stdin.as_mut().ok_or_else(|| {
        std::io::Error::new(std::io::ErrorKind::BrokenPipe, "missing child stdin")
    })?;
    stdin.write_all(&[SETUP])?;
    stdin.flush()?;
    event("WORKER_V5_SETUP_EXIT", "v5 setup released");
    Ok(())
}

fn collect_output(
    child: &mut Child,
    limit: usize,
    deadline: Instant,
) -> Result<Vec<u8>, ObserverWorkerV5Error> {
    event("WORKER_V5_DRAIN_ENTER", "draining bounded v5 output");
    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| reject("worker-v5-output-pipe"))?;
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
            return Err(reject("worker-v5-wall-timeout"));
        }
        if !exited {
            match child.try_wait() {
                Ok(Some(_)) => exited = true,
                Ok(None) => {}
                Err(_) => {
                    terminate_and_reap(child);
                    let _ = reader.join();
                    return Err(reject("worker-v5-wait"));
                }
            }
        }
        if output.is_none() {
            match receiver.try_recv() {
                Ok(Ok(bytes)) if bytes.len() <= limit => output = Some(bytes),
                Ok(Ok(_)) => {
                    terminate_and_reap(child);
                    let _ = reader.join();
                    return Err(reject("worker-v5-output-limit"));
                }
                Ok(Err(_)) | Err(TryRecvError::Disconnected) => {
                    terminate_and_reap(child);
                    let _ = reader.join();
                    return Err(reject("worker-v5-output-read"));
                }
                Err(TryRecvError::Empty) => {}
            }
        }
        if exited && output.is_some() {
            break;
        }
        thread::sleep(POLL);
    }
    reader
        .join()
        .map_err(|_| reject("worker-v5-output-reader"))?;
    event("WORKER_V5_DRAIN_EXIT", "bounded v5 output drained");
    output.ok_or_else(|| reject("worker-v5-missing-output"))
}

fn terminate_and_reap(child: &mut Child) {
    event("WORKER_V5_TERMINATE_ENTER", "terminating v5 process group");
    let _ = signal_process_group(child.id(), false);
    thread::sleep(Duration::from_millis(50));
    let _ = signal_process_group(child.id(), true);
    let _ = child.wait();
    event("WORKER_V5_TERMINATE_EXIT", "v5 process group reaped");
}

#[cfg(target_os = "linux")]
fn cleanup_after_child(
    cgroup: &mut CgroupLeafV5,
    rootfs: &mut RootfsMountpointV5,
) -> Result<(bool, bool), ObserverWorkerV5Error> {
    event("WORKER_V5_CLEANUP_ENTER", "performing v5 cleanup");
    let cgroup_clean = cgroup.cleanup()?;
    let rootfs_clean = rootfs.cleanup()?;
    event("WORKER_V5_CLEANUP_EXIT", "v5 cleanup completed");
    Ok((cgroup_clean, rootfs_clean))
}

#[cfg(target_os = "linux")]
mod ffi {
    use std::os::raw::{c_int, c_uint};
    pub const CLOSE_RANGE_CLOEXEC: c_uint = 1 << 2;
    unsafe extern "C" {
        pub fn close_range(first: c_uint, last: c_uint, flags: c_uint) -> c_int;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn wire_binds_discovery_roots_and_has_exact_size() {
        let mut wire = ChildWireV5 {
            flags: 0x0fff,
            request_digest: [1; 32],
            result_digest: [2; 32],
            request_root: [3; 32],
            result_root: [4; 32],
            result: Vec::new(),
            digest: [0; 32],
        };
        wire.digest = child_digest(&wire);
        let encoded = encode_wire(&wire).unwrap();
        assert_eq!(encoded.len(), WIRE_FIXED);
        assert_eq!(decode_wire(&encoded).unwrap(), wire);
        let mut changed = wire.clone();
        changed.request_root[0] ^= 1;
        assert_ne!(child_digest(&changed), wire.digest);
        changed = wire.clone();
        changed.result_root[0] ^= 1;
        assert_ne!(child_digest(&changed), wire.digest);
    }

    #[test]
    fn discovery_hex_roots_decode_exactly_and_fail_closed() {
        assert_eq!(discovery_root(&"ab".repeat(32)).unwrap(), [0xab; 32]);
        assert_eq!(
            discovery_root("00").unwrap_err().0,
            "worker-v5-discovery-root"
        );
        assert_eq!(
            discovery_root(&"zz".repeat(32)).unwrap_err().0,
            "worker-v5-discovery-root"
        );
    }
}
