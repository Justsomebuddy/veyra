//! Truthful worker-v2 capability and child-control evidence.
//!
//! A control is reported as `Enforced` only after local kernel readback.  The
//! baseline child can apply Linux no-new-privileges, the existing resource
//! limits and an owned process group, then audit inherited file descriptors.
//! Parent-owned wall/output custody remains `Available`/`CustodyPending` here.
//! Strict-only cgroup/seccomp/namespace controls block when no independently
//! verifiable implementation is present; availability is never promoted into
//! enforcement.

use std::fmt;
use std::path::{Path, PathBuf};

use super::event;
use super::linux::{apply_child_limits, enter_owned_process_group};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum WorkerV2Policy {
    Baseline,
    Strict,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum WorkerControlStateV2 {
    Enforced,
    Available,
    NotRequested,
    Unavailable,
    UnsupportedPlatform,
    Failed,
}

impl WorkerControlStateV2 {
    pub fn as_str(self) -> &'static str {
        event("WORKER_V2_STATE_STRING", "rendering control state");
        match self {
            Self::Enforced => "enforced",
            Self::Available => "available",
            Self::NotRequested => "not-requested",
            Self::Unavailable => "unavailable",
            Self::UnsupportedPlatform => "unsupported-platform",
            Self::Failed => "failed",
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct WorkerControlEvidenceV2 {
    pub state: WorkerControlStateV2,
    pub reason: String,
}

impl WorkerControlEvidenceV2 {
    fn new(state: WorkerControlStateV2, reason: impl Into<String>) -> Self {
        event("WORKER_V2_CONTROL", "recording control evidence");
        Self {
            state,
            reason: reason.into(),
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum WorkerV2Admission {
    ReadyToLaunch,
    CustodyPending,
    Blocked,
}

impl WorkerV2Admission {
    pub fn as_str(self) -> &'static str {
        event("WORKER_V2_ADMISSION_STRING", "rendering admission state");
        match self {
            Self::ReadyToLaunch => "ready-to-launch",
            Self::CustodyPending => "custody-pending",
            Self::Blocked => "blocked",
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct WorkerV2CapabilityReport {
    pub policy: WorkerV2Policy,
    pub admission: WorkerV2Admission,
    pub no_new_privileges: WorkerControlEvidenceV2,
    pub resource_limits: WorkerControlEvidenceV2,
    pub process_group: WorkerControlEvidenceV2,
    pub wall_clock_limit: WorkerControlEvidenceV2,
    pub output_limit: WorkerControlEvidenceV2,
    pub inherited_fd_boundary: WorkerControlEvidenceV2,
    pub cgroup_v2: WorkerControlEvidenceV2,
    pub seccomp: WorkerControlEvidenceV2,
    pub namespaces: WorkerControlEvidenceV2,
    pub obstruction: String,
}

impl WorkerV2CapabilityReport {
    pub fn canonical_text(&self) -> String {
        event(
            "WORKER_V2_REPORT_ENTER",
            "encoding canonical capability report",
        );
        let text = format!(
            "schema=veyra.native-observer-worker.capability.v2\npolicy={}\nadmission={}\nno_new_privileges={}\nresource_limits={}\nprocess_group={}\nwall_clock_limit={}\noutput_limit={}\ninherited_fd_boundary={}\ncgroup_v2={}\nseccomp={}\nnamespaces={}\nobstruction={}\n",
            match self.policy {
                WorkerV2Policy::Baseline => "baseline",
                WorkerV2Policy::Strict => "strict",
            },
            self.admission.as_str(),
            self.no_new_privileges.state.as_str(),
            self.resource_limits.state.as_str(),
            self.process_group.state.as_str(),
            self.wall_clock_limit.state.as_str(),
            self.output_limit.state.as_str(),
            self.inherited_fd_boundary.state.as_str(),
            self.cgroup_v2.state.as_str(),
            self.seccomp.state.as_str(),
            self.namespaces.state.as_str(),
            self.obstruction,
        );
        event(
            "WORKER_V2_REPORT_EXIT",
            "canonical capability report encoded",
        );
        text
    }
}

/// Trusted launch-time input, intentionally absent from every replay/wire
/// schema.  A caller may name a pre-created delegated cgroup, but the worker
/// only attests it after canonical-path and membership readback.
#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct WorkerV2LaunchOptions {
    pub delegated_cgroup: Option<PathBuf>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct WorkerV2Limits {
    pub cpu_seconds: u32,
    pub address_space_bytes: u64,
}

impl Default for WorkerV2Limits {
    fn default() -> Self {
        event("WORKER_V2_LIMITS_DEFAULT", "constructing default limits");
        Self {
            cpu_seconds: 10,
            address_space_bytes: 512 * 1024 * 1024,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct WorkerV2Error(pub &'static str);

impl fmt::Display for WorkerV2Error {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        event("WORKER_V2_ERROR_DISPLAY", "rendering worker-v2 error");
        formatter.write_str(self.0)
    }
}

impl std::error::Error for WorkerV2Error {}

pub fn inspect_worker_v2_capabilities(
    policy: WorkerV2Policy,
    options: &WorkerV2LaunchOptions,
) -> WorkerV2CapabilityReport {
    event(
        "WORKER_V2_INSPECT_ENTER",
        "inspecting worker-v2 capabilities",
    );
    #[cfg(target_os = "linux")]
    let mut report = linux_preflight(policy, options);
    #[cfg(not(target_os = "linux"))]
    let mut report = unsupported_preflight(policy);

    if policy == WorkerV2Policy::Strict {
        let strict_ready = report.cgroup_v2.state == WorkerControlStateV2::Enforced
            && report.seccomp.state == WorkerControlStateV2::Enforced
            && report.namespaces.state == WorkerControlStateV2::Enforced;
        if !strict_ready {
            report.admission = WorkerV2Admission::Blocked;
            report.obstruction =
                "strict policy requires verified cgroup-v2, pinned seccomp, and namespaces"
                    .to_owned();
        }
    }
    event("WORKER_V2_INSPECT_EXIT", "worker-v2 capabilities inspected");
    report
}

/// Apply child-local baseline controls.  This function is intentionally for a
/// newly spawned worker: rlimits and no-new-privileges are irreversible for
/// the process.  It never claims parent-owned wall/output custody.
pub fn apply_worker_v2_child_controls(
    policy: WorkerV2Policy,
    limits: WorkerV2Limits,
    options: &WorkerV2LaunchOptions,
) -> Result<WorkerV2CapabilityReport, WorkerV2Error> {
    event(
        "WORKER_V2_APPLY_ENTER",
        "applying child-local worker-v2 controls",
    );
    validate_limits(limits)?;
    if policy == WorkerV2Policy::Strict {
        let report = inspect_worker_v2_capabilities(policy, options);
        event(
            "WORKER_V2_APPLY_BLOCKED",
            "strict controls are not fully enforced",
        );
        return Ok(report);
    }
    #[cfg(not(target_os = "linux"))]
    {
        let _ = (limits, options);
        event(
            "WORKER_V2_APPLY_REJECT",
            "worker-v2 Linux controls unavailable",
        );
        return Err(WorkerV2Error("worker-v2-linux-controls-unavailable"));
    }
    #[cfg(target_os = "linux")]
    {
        let no_new_privileges = apply_and_read_no_new_privileges();
        let resource_limits =
            match apply_child_limits(limits.cpu_seconds, limits.address_space_bytes) {
                Ok(true) => WorkerControlEvidenceV2::new(
                    WorkerControlStateV2::Enforced,
                    "RLIMIT_CPU/RLIMIT_AS/RLIMIT_CORE set and read back exactly",
                ),
                Ok(false) => WorkerControlEvidenceV2::new(
                    WorkerControlStateV2::Failed,
                    "resource-limit readback differed from the request",
                ),
                Err(_) => WorkerControlEvidenceV2::new(
                    WorkerControlStateV2::Failed,
                    "resource-limit syscall failed",
                ),
            };
        let process_group = match enter_owned_process_group() {
            Ok(true) if process_group_is_owned() => WorkerControlEvidenceV2::new(
                WorkerControlStateV2::Enforced,
                "setpgid succeeded and getpgrp equals getpid",
            ),
            Ok(_) => WorkerControlEvidenceV2::new(
                WorkerControlStateV2::Failed,
                "owned process-group readback failed",
            ),
            Err(_) => WorkerControlEvidenceV2::new(WorkerControlStateV2::Failed, "setpgid failed"),
        };
        let inherited_fd_boundary = inherited_fd_audit();
        let local_enforced = [
            &no_new_privileges,
            &resource_limits,
            &process_group,
            &inherited_fd_boundary,
        ]
        .iter()
        .all(|control| control.state == WorkerControlStateV2::Enforced);
        let report = WorkerV2CapabilityReport {
            policy,
            admission: if local_enforced {
                WorkerV2Admission::CustodyPending
            } else {
                WorkerV2Admission::Blocked
            },
            no_new_privileges,
            resource_limits,
            process_group,
            wall_clock_limit: WorkerControlEvidenceV2::new(
                WorkerControlStateV2::Available,
                "requires supervising-parent deadline evidence",
            ),
            output_limit: WorkerControlEvidenceV2::new(
                WorkerControlStateV2::Available,
                "requires supervising-parent bounded drain evidence",
            ),
            inherited_fd_boundary,
            cgroup_v2: not_requested("baseline does not request cgroup-v2"),
            seccomp: not_requested("baseline does not request seccomp"),
            namespaces: not_requested("baseline does not request namespaces"),
            obstruction: if local_enforced {
                String::new()
            } else {
                "one or more child-local baseline controls failed readback".to_owned()
            },
        };
        event(
            "WORKER_V2_APPLY_EXIT",
            "child-local worker-v2 controls applied",
        );
        Ok(report)
    }
}

fn validate_limits(limits: WorkerV2Limits) -> Result<(), WorkerV2Error> {
    event("WORKER_V2_LIMITS_ENTER", "validating worker-v2 limits");
    if !(1..=10).contains(&limits.cpu_seconds)
        || !(128 * 1024 * 1024..=2 * 1024 * 1024 * 1024).contains(&limits.address_space_bytes)
    {
        event("WORKER_V2_LIMITS_REJECT", "invalid worker-v2 limits");
        return Err(WorkerV2Error("worker-v2-invalid-limits"));
    }
    event("WORKER_V2_LIMITS_EXIT", "worker-v2 limits validated");
    Ok(())
}

#[cfg(target_os = "linux")]
fn linux_preflight(
    policy: WorkerV2Policy,
    options: &WorkerV2LaunchOptions,
) -> WorkerV2CapabilityReport {
    event("WORKER_V2_LINUX_PREFLIGHT_ENTER", "probing Linux controls");
    let no_new_privileges = match read_no_new_privileges() {
        Ok(true) => enforced("PR_GET_NO_NEW_PRIVS readback is one"),
        Ok(false) => available("PR_SET_NO_NEW_PRIVS is available but not yet applied"),
        Err(_) => failed("PR_GET_NO_NEW_PRIVS failed"),
    };
    let process_group = if process_group_is_owned() {
        enforced("getpgrp equals getpid")
    } else {
        available("owned process group will be created in the child")
    };
    let strict = policy == WorkerV2Policy::Strict;
    let report = WorkerV2CapabilityReport {
        policy,
        admission: WorkerV2Admission::ReadyToLaunch,
        no_new_privileges,
        resource_limits: available("Linux setrlimit/getrlimit implementation is present"),
        process_group,
        wall_clock_limit: available("supervising parent owns a monotonic deadline"),
        output_limit: available("supervising parent owns a bounded concurrent drain"),
        inherited_fd_boundary: available("new child must pass the post-spawn descriptor audit"),
        cgroup_v2: if strict {
            inspect_delegated_cgroup(options.delegated_cgroup.as_deref())
        } else {
            not_requested("baseline does not request cgroup-v2")
        },
        seccomp: if strict {
            unavailable("no pinned seccomp filter manifest and readback are implemented")
        } else {
            not_requested("baseline does not request seccomp")
        },
        namespaces: if strict {
            unavailable(
                "request-scoped namespace creation and identity readback are not implemented",
            )
        } else {
            not_requested("baseline does not request namespaces")
        },
        obstruction: String::new(),
    };
    event("WORKER_V2_LINUX_PREFLIGHT_EXIT", "Linux controls probed");
    report
}

#[cfg(not(target_os = "linux"))]
fn unsupported_preflight(policy: WorkerV2Policy) -> WorkerV2CapabilityReport {
    event(
        "WORKER_V2_UNSUPPORTED_ENTER",
        "reporting unsupported platform",
    );
    let unsupported = || {
        WorkerControlEvidenceV2::new(
            WorkerControlStateV2::UnsupportedPlatform,
            "worker-v2 controls currently require Linux",
        )
    };
    WorkerV2CapabilityReport {
        policy,
        admission: WorkerV2Admission::Blocked,
        no_new_privileges: unsupported(),
        resource_limits: unsupported(),
        process_group: unsupported(),
        wall_clock_limit: unsupported(),
        output_limit: unsupported(),
        inherited_fd_boundary: unsupported(),
        cgroup_v2: unsupported(),
        seccomp: unsupported(),
        namespaces: unsupported(),
        obstruction: "worker-v2 controls currently require Linux".to_owned(),
    }
}

#[cfg(target_os = "linux")]
fn inspect_delegated_cgroup(path: Option<&Path>) -> WorkerControlEvidenceV2 {
    event(
        "WORKER_V2_CGROUP_ENTER",
        "checking external delegated cgroup evidence",
    );
    let Some(path) = path else {
        return unavailable("no request-scoped delegated cgroup path was supplied");
    };
    let Ok(canonical) = path.canonicalize() else {
        return failed("delegated cgroup path cannot be canonicalized");
    };
    if !canonical.starts_with("/sys/fs/cgroup") || !canonical.join("cgroup.procs").is_file() {
        return failed("delegated path is not a cgroup-v2 directory");
    }
    let Ok(members) = std::fs::read_to_string(canonical.join("cgroup.procs")) else {
        return failed("delegated cgroup membership cannot be read");
    };
    let pid = std::process::id().to_string();
    if !members.lines().any(|line| line == pid) {
        return available(
            "delegated cgroup exists, but current-process membership is not enforced",
        );
    }
    // Membership is real, but delegation ownership and limit files have not
    // been pinned by this layer.  Do not turn mere placement into strict proof.
    available("membership read back; delegated limit ownership remains externally unverified")
}

#[cfg(target_os = "linux")]
fn apply_and_read_no_new_privileges() -> WorkerControlEvidenceV2 {
    event("WORKER_V2_NNP_ENTER", "setting Linux no-new-privileges");
    // SAFETY: fixed prctl operation, zero unused scalar arguments.
    let applied = unsafe { linux_ffi::prctl(linux_ffi::PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) } == 0;
    let evidence = if applied && matches!(read_no_new_privileges(), Ok(true)) {
        enforced("PR_SET_NO_NEW_PRIVS succeeded and PR_GET_NO_NEW_PRIVS read back one")
    } else {
        failed("no-new-privileges set/readback failed")
    };
    event("WORKER_V2_NNP_EXIT", "Linux no-new-privileges processed");
    evidence
}

#[cfg(target_os = "linux")]
fn read_no_new_privileges() -> std::io::Result<bool> {
    event(
        "WORKER_V2_NNP_READ_ENTER",
        "reading Linux no-new-privileges",
    );
    // SAFETY: fixed read-only prctl operation, zero unused scalar arguments.
    let result = unsafe { linux_ffi::prctl(linux_ffi::PR_GET_NO_NEW_PRIVS, 0, 0, 0, 0) };
    if result < 0 {
        return Err(std::io::Error::last_os_error());
    }
    event("WORKER_V2_NNP_READ_EXIT", "Linux no-new-privileges read");
    Ok(result == 1)
}

#[cfg(target_os = "linux")]
fn process_group_is_owned() -> bool {
    event("WORKER_V2_PGRP_READ", "reading process-group identity");
    // SAFETY: getpid/getpgrp take no pointers and have no preconditions.
    unsafe { linux_ffi::getpid() == linux_ffi::getpgrp() }
}

#[cfg(target_os = "linux")]
fn inherited_fd_audit() -> WorkerControlEvidenceV2 {
    event("WORKER_V2_FD_ENTER", "auditing inherited file descriptors");
    let entries = match std::fs::read_dir("/proc/self/fd") {
        Ok(entries) => entries,
        Err(_) => return failed("cannot enumerate the Linux process descriptor table"),
    };
    let mut candidates = Vec::new();
    for entry in entries {
        let Ok(entry) = entry else {
            return failed("cannot read one Linux process descriptor entry");
        };
        let Some(name) = entry.file_name().to_str().map(str::to_owned) else {
            return failed("Linux process descriptor entry is not numeric UTF-8");
        };
        let Ok(fd) = name.parse::<i32>() else {
            return failed("Linux process descriptor entry is not numeric");
        };
        if fd >= 3 {
            candidates.push(fd);
        }
    }
    // `read_dir` temporarily owns a descriptor that appears in its own
    // listing. It is dropped above; F_GETFD below distinguishes that closed
    // scanner descriptor from descriptors actually inherited by the child.
    let mut open = Vec::new();
    candidates.sort_unstable();
    candidates.dedup();
    for fd in candidates {
        // SAFETY: F_GETFD is a read-only query for an integer descriptor.
        if unsafe { linux_ffi::fcntl(fd, linux_ffi::F_GETFD) } >= 0 {
            open.push(fd);
            if open.len() == 8 {
                break;
            }
        }
    }
    let evidence = if open.is_empty() {
        enforced("complete /proc/self/fd inventory found no inherited descriptors above stderr")
    } else {
        failed(format!("unexpected inherited file descriptors: {open:?}"))
    };
    event("WORKER_V2_FD_EXIT", "inherited file descriptors audited");
    evidence
}

fn enforced(reason: impl Into<String>) -> WorkerControlEvidenceV2 {
    event("WORKER_V2_STATE", "control enforced");
    WorkerControlEvidenceV2::new(WorkerControlStateV2::Enforced, reason)
}

fn available(reason: impl Into<String>) -> WorkerControlEvidenceV2 {
    event("WORKER_V2_STATE", "control available");
    WorkerControlEvidenceV2::new(WorkerControlStateV2::Available, reason)
}

fn not_requested(reason: impl Into<String>) -> WorkerControlEvidenceV2 {
    event("WORKER_V2_STATE", "control not requested");
    WorkerControlEvidenceV2::new(WorkerControlStateV2::NotRequested, reason)
}

fn unavailable(reason: impl Into<String>) -> WorkerControlEvidenceV2 {
    event("WORKER_V2_STATE", "control unavailable");
    WorkerControlEvidenceV2::new(WorkerControlStateV2::Unavailable, reason)
}

fn failed(reason: impl Into<String>) -> WorkerControlEvidenceV2 {
    event("WORKER_V2_STATE", "control failed");
    WorkerControlEvidenceV2::new(WorkerControlStateV2::Failed, reason)
}

#[cfg(target_os = "linux")]
mod linux_ffi {
    use std::os::raw::{c_int, c_ulong};

    pub const PR_SET_NO_NEW_PRIVS: c_int = 38;
    pub const PR_GET_NO_NEW_PRIVS: c_int = 39;
    pub const F_GETFD: c_int = 1;

    unsafe extern "C" {
        pub fn prctl(
            option: c_int,
            arg2: c_ulong,
            arg3: c_ulong,
            arg4: c_ulong,
            arg5: c_ulong,
        ) -> c_int;
        pub fn getpid() -> c_int;
        pub fn getpgrp() -> c_int;
        pub fn fcntl(fd: c_int, command: c_int, ...) -> c_int;
    }
}
