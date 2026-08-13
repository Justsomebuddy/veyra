//! Closed-rootfs and delegated cgroup-v2 primitives for strict worker v5.

#![cfg(target_os = "linux")]

use std::fs;
use std::os::unix::fs::{MetadataExt, PermissionsExt};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};
use std::thread;
use std::time::{Duration, Instant};

use super::event;
use super::supervisor_v5::{validate_limits, ObserverWorkerLimitsV5, ObserverWorkerV5Error};

const CGROUP_MOUNT: &str = "/sys/fs/cgroup";
const TMPFS_MAGIC: i64 = 0x0102_1994;

fn reject(reason: &'static str) -> ObserverWorkerV5Error {
    event("WORKER_V5_ISOLATION_REJECT", reason);
    ObserverWorkerV5Error(reason)
}

pub(super) struct RootfsMountpointV5 {
    pub(super) path: PathBuf,
    cleaned: bool,
}

impl RootfsMountpointV5 {
    pub(super) fn create(base: &Path) -> Result<Self, ObserverWorkerV5Error> {
        event(
            "WORKER_V5_ROOTDIR_ENTER",
            "creating private rootfs mountpoint",
        );
        let base = fs::canonicalize(base).map_err(|_| reject("worker-v5-rootfs-base"))?;
        let metadata = fs::metadata(&base).map_err(|_| reject("worker-v5-rootfs-base"))?;
        if !metadata.is_dir() || metadata.uid() != unsafe { ffi::getuid() } {
            return Err(reject("worker-v5-rootfs-base-ownership"));
        }
        static NEXT: AtomicU64 = AtomicU64::new(0);
        let path = base.join(format!(
            ".veyra-worker-v5-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&path).map_err(|_| reject("worker-v5-rootfs-create"))?;
        if fs::set_permissions(&path, fs::Permissions::from_mode(0o700)).is_err() {
            let _ = fs::remove_dir(&path);
            return Err(reject("worker-v5-rootfs-mode"));
        }
        event(
            "WORKER_V5_ROOTDIR_EXIT",
            "private rootfs mountpoint created",
        );
        Ok(Self {
            path,
            cleaned: false,
        })
    }

    pub(super) fn cleanup(&mut self) -> Result<bool, ObserverWorkerV5Error> {
        event(
            "WORKER_V5_ROOTDIR_CLEAN_ENTER",
            "removing rootfs mountpoint",
        );
        let entries =
            fs::read_dir(&self.path).map_err(|_| reject("worker-v5-rootfs-clean-read"))?;
        if entries.count() != 0 {
            return Err(reject("worker-v5-rootfs-clean-not-empty"));
        }
        fs::remove_dir(&self.path).map_err(|_| reject("worker-v5-rootfs-clean-remove"))?;
        self.cleaned = true;
        event("WORKER_V5_ROOTDIR_CLEAN_EXIT", "rootfs mountpoint removed");
        Ok(!self.path.exists())
    }
}

impl Drop for RootfsMountpointV5 {
    fn drop(&mut self) {
        event("WORKER_V5_ROOTDIR_DROP_ENTER", "best-effort rootfs cleanup");
        if !self.cleaned {
            let _ = fs::remove_dir(&self.path);
        }
        event(
            "WORKER_V5_ROOTDIR_DROP_EXIT",
            "best-effort rootfs cleanup finished",
        );
    }
}

pub(super) fn apply_closed_rootfs_v5(
    mountpoint: &Path,
    bytes: u64,
) -> Result<bool, ObserverWorkerV5Error> {
    event(
        "WORKER_V5_ROOTFS_ENTER",
        "mounting and pivoting closed tmpfs root",
    );
    let path = mountpoint
        .to_str()
        .ok_or_else(|| reject("worker-v5-rootfs-path"))?;
    let target = std::ffi::CString::new(path).map_err(|_| reject("worker-v5-rootfs-path"))?;
    let options = std::ffi::CString::new(format!("size={bytes},mode=0700"))
        .map_err(|_| reject("worker-v5-rootfs-options"))?;
    if unsafe {
        ffi::mount(
            c"tmpfs".as_ptr(),
            target.as_ptr(),
            c"tmpfs".as_ptr(),
            ffi::MS_NOSUID | ffi::MS_NODEV | ffi::MS_NOEXEC,
            options.as_ptr().cast(),
        )
    } != 0
    {
        return Err(reject("worker-v5-rootfs-mount"));
    }
    let old_root = mountpoint.join(".old_root");
    fs::create_dir(&old_root).map_err(|_| reject("worker-v5-old-root-create"))?;
    if unsafe { ffi::chdir(target.as_ptr()) } != 0 {
        return Err(reject("worker-v5-rootfs-chdir"));
    }
    if unsafe { ffi::syscall(ffi::SYS_PIVOT_ROOT, c".".as_ptr(), c".old_root".as_ptr()) } != 0 {
        return Err(reject("worker-v5-pivot-root"));
    }
    if unsafe { ffi::chdir(c"/".as_ptr()) } != 0
        || unsafe { ffi::umount2(c"/.old_root".as_ptr(), ffi::MNT_DETACH) } != 0
        || unsafe { ffi::rmdir(c"/.old_root".as_ptr()) } != 0
    {
        return Err(reject("worker-v5-old-root-detach"));
    }
    if !closed_rootfs_self_readback()? {
        return Err(reject("worker-v5-rootfs-self-readback"));
    }
    event("WORKER_V5_ROOTFS_EXIT", "closed tmpfs root pivot verified");
    Ok(true)
}

fn closed_rootfs_self_readback() -> Result<bool, ObserverWorkerV5Error> {
    event("WORKER_V5_ROOTFS_SELF_ENTER", "reading child rootfs state");
    let mut stats = ffi::StatFs::default();
    if unsafe { ffi::statfs(c"/".as_ptr(), &mut stats) } != 0 {
        return Err(reject("worker-v5-rootfs-statfs"));
    }
    let result = stats.kind == TMPFS_MAGIC
        && !Path::new("/.old_root").exists()
        && !Path::new("/etc").exists()
        && fs::read_dir("/")
            .map_err(|_| reject("worker-v5-rootfs-list"))?
            .next()
            .is_none();
    event("WORKER_V5_ROOTFS_SELF_EXIT", "child rootfs state read");
    Ok(result)
}

pub(super) fn parent_closed_rootfs_readback(pid: u32) -> Result<bool, ObserverWorkerV5Error> {
    event(
        "WORKER_V5_ROOTFS_PARENT_ENTER",
        "reading child rootfs from parent",
    );
    let root = PathBuf::from(format!("/proc/{pid}/root"));
    let host = fs::metadata("/").map_err(|_| reject("worker-v5-host-root-stat"))?;
    let child = fs::metadata(&root).map_err(|_| reject("worker-v5-child-root-stat"))?;
    let mountinfo = fs::read_to_string(format!("/proc/{pid}/mountinfo"))
        .map_err(|_| reject("worker-v5-mountinfo-read"))?;
    let root_line = mountinfo
        .lines()
        .find(|line| line.split_whitespace().nth(4) == Some("/"))
        .ok_or_else(|| reject("worker-v5-mountinfo-root"))?;
    let private = !root_line.contains(" shared:") && !root_line.contains(" master:");
    let tmpfs = root_line
        .split(" - ")
        .nth(1)
        .is_some_and(|tail| tail.split_whitespace().next() == Some("tmpfs"));
    let result = (host.dev(), host.ino()) != (child.dev(), child.ino())
        && private
        && tmpfs
        && !root.join(".old_root").exists()
        && !root.join("etc").exists()
        && fs::read_dir(root)
            .map_err(|_| reject("worker-v5-child-root-list"))?
            .next()
            .is_none();
    event(
        "WORKER_V5_ROOTFS_PARENT_EXIT",
        "child rootfs read from parent",
    );
    Ok(result)
}

pub(super) fn verify_current_cgroup_v5(
    path: &Path,
    limits: ObserverWorkerLimitsV5,
) -> Result<bool, ObserverWorkerV5Error> {
    event(
        "WORKER_V5_CGROUP_CHILD_ENTER",
        "reading child cgroup membership",
    );
    let text = fs::read_to_string(path.join("cgroup.procs"))
        .map_err(|_| reject("worker-v5-cgroup-membership-read"))?;
    let pid = std::process::id().to_string();
    let result = text.lines().any(|line| line.trim() == pid);
    if !result {
        return Err(reject("worker-v5-cgroup-membership-mismatch"));
    }
    verify_cgroup_controls(path, limits)?;
    event(
        "WORKER_V5_CGROUP_CHILD_EXIT",
        "child cgroup membership read",
    );
    Ok(true)
}

pub(super) struct CgroupLeafV5 {
    pub(super) path: PathBuf,
    limits: ObserverWorkerLimitsV5,
    cleaned: bool,
}

impl CgroupLeafV5 {
    pub(super) fn create(
        root: &Path,
        limits: ObserverWorkerLimitsV5,
    ) -> Result<Self, ObserverWorkerV5Error> {
        event(
            "WORKER_V5_CGROUP_CREATE_ENTER",
            "creating delegated cgroup leaf",
        );
        let root = inspect_delegated_cgroup_root(root, Path::new(CGROUP_MOUNT))?;
        static NEXT: AtomicU64 = AtomicU64::new(0);
        let path = root.join(format!(
            "veyra-observer-v5-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&path).map_err(|_| reject("worker-v5-cgroup-create"))?;
        let mut leaf = Self {
            path,
            limits,
            cleaned: false,
        };
        if let Err(error) = leaf.write_and_verify() {
            let _ = fs::remove_dir(&leaf.path);
            return Err(error);
        }
        event(
            "WORKER_V5_CGROUP_CREATE_EXIT",
            "delegated cgroup leaf created",
        );
        Ok(leaf)
    }

    fn write_and_verify(&mut self) -> Result<(), ObserverWorkerV5Error> {
        event("WORKER_V5_CGROUP_WRITE_ENTER", "writing cgroup controls");
        fs::write(
            self.path.join("cpu.max"),
            format!(
                "{} {}\n",
                self.limits.cpu_quota_us, self.limits.cpu_period_us
            ),
        )
        .map_err(|_| reject("worker-v5-cgroup-cpu-write"))?;
        fs::write(
            self.path.join("memory.max"),
            format!("{}\n", self.limits.memory_bytes),
        )
        .map_err(|_| reject("worker-v5-cgroup-memory-write"))?;
        fs::write(
            self.path.join("pids.max"),
            format!("{}\n", self.limits.pids),
        )
        .map_err(|_| reject("worker-v5-cgroup-pids-write"))?;
        self.verify()?;
        event("WORKER_V5_CGROUP_WRITE_EXIT", "cgroup controls written");
        Ok(())
    }

    pub(super) fn verify(&self) -> Result<(), ObserverWorkerV5Error> {
        event("WORKER_V5_CGROUP_VERIFY_ENTER", "reading cgroup controls");
        verify_cgroup_controls(&self.path, self.limits)?;
        event("WORKER_V5_CGROUP_VERIFY_EXIT", "cgroup controls verified");
        Ok(())
    }

    pub(super) fn attach(&self, pid: u32) -> Result<bool, ObserverWorkerV5Error> {
        event(
            "WORKER_V5_CGROUP_ATTACH_ENTER",
            "attaching process to cgroup",
        );
        fs::write(self.path.join("cgroup.procs"), format!("{pid}\n"))
            .map_err(|_| reject("worker-v5-cgroup-membership-write"))?;
        let result = self.contains(pid);
        if !result {
            return Err(reject("worker-v5-cgroup-membership-mismatch"));
        }
        event("WORKER_V5_CGROUP_ATTACH_EXIT", "process attached to cgroup");
        Ok(true)
    }

    pub(super) fn contains(&self, pid: u32) -> bool {
        event(
            "WORKER_V5_CGROUP_CONTAINS_ENTER",
            "reading cgroup membership",
        );
        let expected = pid.to_string();
        let result = fs::read_to_string(self.path.join("cgroup.procs"))
            .map(|text| text.lines().any(|line| line.trim() == expected))
            .unwrap_or(false);
        event("WORKER_V5_CGROUP_CONTAINS_EXIT", "cgroup membership read");
        result
    }

    pub(super) fn cleanup(&mut self) -> Result<bool, ObserverWorkerV5Error> {
        event("WORKER_V5_CGROUP_CLEAN_ENTER", "removing empty cgroup leaf");
        let deadline = Instant::now() + Duration::from_secs(1);
        loop {
            let procs = fs::read_to_string(self.path.join("cgroup.procs"))
                .map_err(|_| reject("worker-v5-cgroup-clean-read"))?;
            let events = fs::read_to_string(self.path.join("cgroup.events"))
                .map_err(|_| reject("worker-v5-cgroup-events-read"))?;
            if procs.trim().is_empty() && events.lines().any(|line| line == "populated 0") {
                break;
            }
            if Instant::now() >= deadline {
                return Err(reject("worker-v5-cgroup-not-empty"));
            }
            thread::sleep(Duration::from_millis(5));
        }
        fs::remove_dir(&self.path).map_err(|_| reject("worker-v5-cgroup-remove"))?;
        self.cleaned = true;
        event("WORKER_V5_CGROUP_CLEAN_EXIT", "empty cgroup leaf removed");
        Ok(!self.path.exists())
    }
}

fn inspect_delegated_cgroup_root(
    root: &Path,
    mount: &Path,
) -> Result<PathBuf, ObserverWorkerV5Error> {
    event(
        "WORKER_V5_CGROUP_DELEGATION_ENTER",
        "inspecting delegated cgroup root",
    );
    let root = fs::canonicalize(root).map_err(|_| reject("worker-v5-cgroup-root"))?;
    let metadata = fs::metadata(&root).map_err(|_| reject("worker-v5-cgroup-root"))?;
    if !root.starts_with(mount) {
        return Err(reject("worker-v5-cgroup-delegation-invalid"));
    }
    if !metadata.is_dir() {
        return Err(reject("worker-v5-cgroup-root-not-directory"));
    }
    if root == mount || metadata.uid() != unsafe { ffi::getuid() } {
        return Err(reject("worker-v5-cgroup-not-delegated"));
    }
    let available = fs::read_to_string(root.join("cgroup.controllers"))
        .map_err(|_| reject("worker-v5-cgroup-controllers"))?;
    let enabled = fs::read_to_string(root.join("cgroup.subtree_control"))
        .map_err(|_| reject("worker-v5-cgroup-subtree"))?;
    if !["cpu", "memory", "pids"].iter().all(|name| {
        available.split_whitespace().any(|value| value == *name)
            && enabled.split_whitespace().any(|value| value == *name)
    }) {
        return Err(reject("worker-v5-cgroup-controller-unavailable"));
    }
    event(
        "WORKER_V5_CGROUP_DELEGATION_EXIT",
        "delegated cgroup root inspected",
    );
    Ok(root)
}

fn verify_cgroup_controls(
    path: &Path,
    limits: ObserverWorkerLimitsV5,
) -> Result<(), ObserverWorkerV5Error> {
    event(
        "WORKER_V5_CGROUP_EXACT_ENTER",
        "reading exact cgroup controls",
    );
    let cpu = fs::read_to_string(path.join("cpu.max"))
        .map_err(|_| reject("worker-v5-cgroup-cpu-read"))?;
    let memory = fs::read_to_string(path.join("memory.max"))
        .map_err(|_| reject("worker-v5-cgroup-memory-read"))?;
    let pids = fs::read_to_string(path.join("pids.max"))
        .map_err(|_| reject("worker-v5-cgroup-pids-read"))?;
    if cpu.trim() != format!("{} {}", limits.cpu_quota_us, limits.cpu_period_us)
        || memory.trim() != limits.memory_bytes.to_string()
        || pids.trim() != limits.pids.to_string()
    {
        return Err(reject("worker-v5-cgroup-control-mismatch"));
    }
    event("WORKER_V5_CGROUP_EXACT_EXIT", "exact cgroup controls read");
    Ok(())
}

impl Drop for CgroupLeafV5 {
    fn drop(&mut self) {
        event("WORKER_V5_CGROUP_DROP_ENTER", "best-effort cgroup cleanup");
        if !self.cleaned {
            let _ = fs::remove_dir(&self.path);
        }
        event(
            "WORKER_V5_CGROUP_DROP_EXIT",
            "best-effort cgroup cleanup finished",
        );
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CgroupHarnessStatusV5 {
    Passed,
    Unavailable,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CgroupHarnessReportV5 {
    status: CgroupHarnessStatusV5,
    reason: &'static str,
    cpu_limit_readback: bool,
    memory_limit_readback: bool,
    pids_limit_readback: bool,
    normal_cleanup: bool,
    sigkill_cleanup: bool,
    crash_cleanup: bool,
}

impl CgroupHarnessReportV5 {
    pub fn status(&self) -> CgroupHarnessStatusV5 {
        event("WORKER_V5_HARNESS_STATUS", "reading harness status");
        self.status
    }
    pub fn reason(&self) -> &'static str {
        event("WORKER_V5_HARNESS_REASON", "reading harness reason");
        self.reason
    }
    pub fn controls_readback(&self) -> bool {
        event("WORKER_V5_HARNESS_CONTROLS", "reading harness controls");
        self.cpu_limit_readback && self.memory_limit_readback && self.pids_limit_readback
    }
    pub fn cpu_limit_readback(&self) -> bool {
        event("WORKER_V5_HARNESS_CPU", "reading harness cpu limit");
        self.cpu_limit_readback
    }
    pub fn memory_limit_readback(&self) -> bool {
        event("WORKER_V5_HARNESS_MEMORY", "reading harness memory limit");
        self.memory_limit_readback
    }
    pub fn pids_limit_readback(&self) -> bool {
        event("WORKER_V5_HARNESS_PIDS", "reading harness pids limit");
        self.pids_limit_readback
    }
    pub fn normal_cleanup(&self) -> bool {
        event("WORKER_V5_HARNESS_NORMAL", "reading normal cleanup");
        self.normal_cleanup
    }
    pub fn sigkill_cleanup(&self) -> bool {
        event("WORKER_V5_HARNESS_SIGKILL", "reading SIGKILL cleanup");
        self.sigkill_cleanup
    }
    pub fn crash_cleanup(&self) -> bool {
        event("WORKER_V5_HARNESS_CRASH", "reading crash cleanup");
        self.crash_cleanup
    }
}

fn unavailable_reason(reason: &'static str) -> bool {
    event(
        "WORKER_V5_HARNESS_CLASSIFY_ENTER",
        "classifying cgroup unavailability",
    );
    let result = matches!(
        reason,
        "worker-v5-cgroup-not-delegated"
            | "worker-v5-cgroup-controllers"
            | "worker-v5-cgroup-subtree"
            | "worker-v5-cgroup-controller-unavailable"
            | "worker-v5-cgroup-create"
            | "worker-v5-cgroup-cpu-write"
            | "worker-v5-cgroup-memory-write"
            | "worker-v5-cgroup-pids-write"
            | "worker-v5-cgroup-cpu-read"
            | "worker-v5-cgroup-memory-read"
            | "worker-v5-cgroup-pids-read"
    );
    event(
        "WORKER_V5_HARNESS_CLASSIFY_EXIT",
        "cgroup unavailability classified",
    );
    result
}

fn unavailable_harness_report(reason: &'static str) -> CgroupHarnessReportV5 {
    event(
        "WORKER_V5_HARNESS_UNAVAILABLE_ENTER",
        "constructing unavailable cgroup harness report",
    );
    let report = CgroupHarnessReportV5 {
        status: CgroupHarnessStatusV5::Unavailable,
        reason,
        cpu_limit_readback: false,
        memory_limit_readback: false,
        pids_limit_readback: false,
        normal_cleanup: false,
        sigkill_cleanup: false,
        crash_cleanup: false,
    };
    event(
        "WORKER_V5_HARNESS_UNAVAILABLE_EXIT",
        "unavailable cgroup harness report constructed",
    );
    report
}

fn harness_process(
    root: &Path,
    limits: ObserverWorkerLimitsV5,
    signal: Option<i32>,
) -> Result<bool, ObserverWorkerV5Error> {
    event(
        "WORKER_V5_HARNESS_PROCESS_ENTER",
        "running cgroup harness process",
    );
    let mut leaf = CgroupLeafV5::create(root, limits)?;
    let mut child = match Command::new("/bin/cat")
        .stdin(Stdio::piped())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
    {
        Ok(value) => value,
        Err(_) => {
            let _ = leaf.cleanup();
            return Err(reject("worker-v5-harness-spawn"));
        }
    };
    if let Err(error) = leaf.attach(child.id()) {
        let _ = unsafe { ffi::kill(child.id() as i32, ffi::SIGKILL) };
        let _ = child.wait();
        let _ = leaf.cleanup();
        return Err(error);
    }
    match signal {
        Some(value) => {
            if unsafe { ffi::kill(child.id() as i32, value) } != 0 {
                let _ = unsafe { ffi::kill(child.id() as i32, ffi::SIGKILL) };
                let _ = child.wait();
                let _ = leaf.cleanup();
                return Err(reject("worker-v5-harness-signal"));
            }
        }
        None => {
            drop(child.stdin.take());
        }
    }
    if child.wait().is_err() {
        let _ = unsafe { ffi::kill(child.id() as i32, ffi::SIGKILL) };
        let _ = child.wait();
        let _ = leaf.cleanup();
        return Err(reject("worker-v5-harness-wait"));
    }
    let cleaned = leaf.cleanup()?;
    event(
        "WORKER_V5_HARNESS_PROCESS_EXIT",
        "cgroup harness process completed",
    );
    Ok(cleaned)
}

pub fn run_cgroup_v5_e2e_harness(
    root: &Path,
    limits: ObserverWorkerLimitsV5,
) -> Result<CgroupHarnessReportV5, ObserverWorkerV5Error> {
    event(
        "WORKER_V5_HARNESS_ENTER",
        "running delegated cgroup e2e harness",
    );
    validate_limits(limits)?;
    match run_cgroup_v5_e2e_harness_checked(root, limits) {
        Ok(report) => {
            event(
                "WORKER_V5_HARNESS_EXIT",
                "delegated cgroup e2e harness completed",
            );
            Ok(report)
        }
        Err(error) if unavailable_reason(error.0) => {
            let report = unavailable_harness_report(error.0);
            event(
                "WORKER_V5_HARNESS_EXIT",
                "delegated cgroup e2e harness unavailable",
            );
            Ok(report)
        }
        Err(error) => Err(error),
    }
}

fn run_cgroup_v5_e2e_harness_checked(
    root: &Path,
    limits: ObserverWorkerLimitsV5,
) -> Result<CgroupHarnessReportV5, ObserverWorkerV5Error> {
    event(
        "WORKER_V5_HARNESS_CHECKED_ENTER",
        "executing delegated cgroup harness checks",
    );
    let mut probe = CgroupLeafV5::create(root, limits)?;
    probe.verify()?;
    let controls_readback = probe.cleanup()?;
    let normal_cleanup = harness_process(root, limits, None)?;
    let sigkill_cleanup = harness_process(root, limits, Some(ffi::SIGKILL))?;
    let crash_cleanup = harness_process(root, limits, Some(ffi::SIGSEGV))?;
    let report = CgroupHarnessReportV5 {
        status: CgroupHarnessStatusV5::Passed,
        reason: "passed",
        cpu_limit_readback: controls_readback,
        memory_limit_readback: controls_readback,
        pids_limit_readback: controls_readback,
        normal_cleanup,
        sigkill_cleanup,
        crash_cleanup,
    };
    event(
        "WORKER_V5_HARNESS_CHECKED_EXIT",
        "delegated cgroup harness checks completed",
    );
    Ok(report)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn controller_and_subtree_read_failures_are_environmental_unavailability() {
        let mount =
            std::env::temp_dir().join(format!("veyra-v5-cgroup-inspection-{}", std::process::id()));
        let root = mount.join("delegated");
        fs::create_dir_all(&root).unwrap();

        let controllers = inspect_delegated_cgroup_root(&root, &mount).unwrap_err();
        assert_eq!(controllers.0, "worker-v5-cgroup-controllers");
        assert!(unavailable_reason(controllers.0));
        assert_eq!(
            unavailable_harness_report(controllers.0).status(),
            CgroupHarnessStatusV5::Unavailable
        );

        fs::write(root.join("cgroup.controllers"), "cpu memory pids\n").unwrap();
        let subtree = inspect_delegated_cgroup_root(&root, &mount).unwrap_err();
        assert_eq!(subtree.0, "worker-v5-cgroup-subtree");
        assert!(unavailable_reason(subtree.0));
        assert_eq!(
            unavailable_harness_report(subtree.0).status(),
            CgroupHarnessStatusV5::Unavailable
        );

        fs::remove_dir_all(&mount).unwrap();
    }

    #[test]
    fn malformed_roots_are_not_environmental_unavailability() {
        assert!(!unavailable_reason("worker-v5-cgroup-root"));
        assert!(!unavailable_reason("worker-v5-cgroup-root-not-directory"));
        assert!(!unavailable_reason("worker-v5-cgroup-delegation-invalid"));
        assert!(!unavailable_reason("worker-v5-invalid-limits"));
    }
}

mod ffi {
    use std::os::raw::{c_char, c_int, c_long, c_ulong, c_void};

    pub const MS_NOSUID: c_ulong = 2;
    pub const MS_NODEV: c_ulong = 4;
    pub const MS_NOEXEC: c_ulong = 8;
    pub const MNT_DETACH: c_int = 2;
    pub const SYS_PIVOT_ROOT: c_long = 155;
    pub const SIGKILL: c_int = 9;
    pub const SIGSEGV: c_int = 11;

    #[repr(C)]
    #[derive(Default)]
    pub struct StatFs {
        pub kind: c_long,
        pub block_size: c_long,
        pub blocks: u64,
        pub blocks_free: u64,
        pub blocks_available: u64,
        pub files: u64,
        pub files_free: u64,
        pub fsid: [i32; 2],
        pub name_length: c_long,
        pub fragment_size: c_long,
        pub flags: c_long,
        pub spare: [c_long; 4],
    }

    unsafe extern "C" {
        pub fn mount(
            source: *const c_char,
            target: *const c_char,
            filesystemtype: *const c_char,
            mountflags: c_ulong,
            data: *const c_void,
        ) -> c_int;
        pub fn chdir(path: *const c_char) -> c_int;
        pub fn syscall(number: c_long, ...) -> c_long;
        pub fn umount2(target: *const c_char, flags: c_int) -> c_int;
        pub fn rmdir(path: *const c_char) -> c_int;
        pub fn statfs(path: *const c_char, buffer: *mut StatFs) -> c_int;
        pub fn getuid() -> u32;
        pub fn kill(pid: c_int, signal: c_int) -> c_int;
    }
}
