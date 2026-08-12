//! Linux namespace, seccomp and delegated cgroup-v2 primitives for worker v4.

#![cfg(target_os = "linux")]

use std::fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

use std::os::unix::fs::MetadataExt;

use super::event;
use super::supervisor_v4::{
    reject, ObserverWorkerLimitsV4, ObserverWorkerV4Error, SECCOMP_ALLOWLIST_X86_64,
};

#[cfg(target_os = "linux")]
pub(super) fn namespace_links(pid: u32) -> Result<Vec<String>, ObserverWorkerV4Error> {
    event("WORKER_V4_NS_READ_ENTER", "reading namespace identities");
    let mut links = Vec::with_capacity(5);
    for name in ["user", "mnt", "net", "ipc", "uts"] {
        let link = fs::read_link(format!("/proc/{pid}/ns/{name}"))
            .map_err(|_| reject("worker-v4-namespace-readback"))?;
        links.push(link.to_string_lossy().into_owned());
    }
    event("WORKER_V4_NS_READ_EXIT", "namespace identities read");
    Ok(links)
}

#[cfg(target_os = "linux")]
pub(super) fn apply_and_verify_namespaces() -> Result<bool, ObserverWorkerV4Error> {
    event("WORKER_V4_NS_ENTER", "creating isolated namespaces");
    let before = namespace_links(std::process::id())?;
    let uid = unsafe { ffi::getuid() };
    let gid = unsafe { ffi::getgid() };
    if unsafe { ffi::unshare(ffi::CLONE_NEWUSER) } != 0 {
        return Err(reject("worker-v4-user-namespace-unavailable"));
    }
    fs::write("/proc/self/setgroups", "deny\n").map_err(|_| reject("worker-v4-setgroups-write"))?;
    if fs::read_to_string("/proc/self/setgroups")
        .map_err(|_| reject("worker-v4-setgroups-read"))?
        .trim()
        != "deny"
    {
        return Err(reject("worker-v4-setgroups-readback"));
    }
    fs::write("/proc/self/uid_map", format!("0 {uid} 1\n"))
        .map_err(|_| reject("worker-v4-uid-map"))?;
    fs::write("/proc/self/gid_map", format!("0 {gid} 1\n"))
        .map_err(|_| reject("worker-v4-gid-map"))?;
    verify_id_map("/proc/self/uid_map", uid, "worker-v4-uid-map-readback")?;
    verify_id_map("/proc/self/gid_map", gid, "worker-v4-gid-map-readback")?;
    let flags = ffi::CLONE_NEWNS | ffi::CLONE_NEWNET | ffi::CLONE_NEWIPC | ffi::CLONE_NEWUTS;
    if unsafe { ffi::unshare(flags) } != 0 {
        return Err(reject("worker-v4-namespace-unavailable"));
    }
    if unsafe {
        ffi::mount(
            std::ptr::null(),
            b"/\0".as_ptr().cast(),
            std::ptr::null(),
            ffi::MS_REC | ffi::MS_PRIVATE,
            std::ptr::null(),
        )
    } != 0
    {
        return Err(reject("worker-v4-mount-private"));
    }
    let after = namespace_links(std::process::id())?;
    let verified = before.iter().zip(&after).all(|(a, b)| a != b);
    if !verified {
        return Err(reject("worker-v4-namespace-readback"));
    }
    event("WORKER_V4_NS_EXIT", "isolated namespaces verified");
    Ok(true)
}

fn verify_id_map(
    path: &str,
    host_id: u32,
    reason: &'static str,
) -> Result<(), ObserverWorkerV4Error> {
    event("WORKER_V4_IDMAP_ENTER", "reading namespace identity map");
    let text = fs::read_to_string(path).map_err(|_| reject(reason))?;
    let rows = text
        .lines()
        .map(|line| {
            line.split_whitespace()
                .map(str::parse::<u64>)
                .collect::<Result<Vec<_>, _>>()
        })
        .collect::<Result<Vec<_>, _>>()
        .map_err(|_| reject(reason))?;
    if rows != vec![vec![0, u64::from(host_id), 1]] {
        return Err(reject(reason));
    }
    event("WORKER_V4_IDMAP_EXIT", "namespace identity map verified");
    Ok(())
}

#[cfg(target_os = "linux")]
pub(super) fn enter_and_verify_cgroup(path: &Path) -> Result<bool, ObserverWorkerV4Error> {
    event("WORKER_V4_CGROUP_ENTER", "entering delegated cgroup leaf");
    fs::write(
        path.join("cgroup.procs"),
        format!("{}\n", std::process::id()),
    )
    .map_err(|_| reject("worker-v4-cgroup-membership-write"))?;
    let contents = fs::read_to_string(path.join("cgroup.procs"))
        .map_err(|_| reject("worker-v4-cgroup-membership-read"))?;
    if !contents
        .lines()
        .any(|line| line.trim().parse::<u32>().ok() == Some(std::process::id()))
    {
        return Err(reject("worker-v4-cgroup-membership-mismatch"));
    }
    event(
        "WORKER_V4_CGROUP_EXIT",
        "delegated cgroup membership verified",
    );
    Ok(true)
}

#[cfg(all(target_os = "linux", target_arch = "x86_64"))]
pub(super) fn apply_and_verify_seccomp() -> Result<bool, ObserverWorkerV4Error> {
    event(
        "WORKER_V4_SECCOMP_ENTER",
        "installing pinned seccomp allowlist",
    );
    let mut filters = Vec::with_capacity(100);
    filters.push(ffi::stmt(ffi::BPF_LD_W_ABS, 4));
    filters.push(ffi::jump(ffi::BPF_JMP_JEQ_K, ffi::AUDIT_ARCH_X86_64, 1, 0));
    filters.push(ffi::stmt(ffi::BPF_RET_K, ffi::SECCOMP_RET_KILL_PROCESS));
    filters.push(ffi::stmt(ffi::BPF_LD_W_ABS, 0));
    for syscall in SECCOMP_ALLOWLIST_X86_64 {
        filters.push(ffi::jump(ffi::BPF_JMP_JEQ_K, *syscall, 0, 1));
        filters.push(ffi::stmt(ffi::BPF_RET_K, ffi::SECCOMP_RET_ALLOW));
    }
    filters.push(ffi::stmt(ffi::BPF_RET_K, ffi::SECCOMP_RET_KILL_PROCESS));
    let program = ffi::SockFprog {
        len: filters.len() as u16,
        filter: filters.as_ptr(),
    };
    if unsafe {
        ffi::prctl(
            ffi::PR_SET_SECCOMP,
            ffi::SECCOMP_MODE_FILTER as _,
            &program as *const _ as usize as _,
            0,
            0,
        )
    } != 0
    {
        return Err(reject("worker-v4-seccomp-install"));
    }
    if unsafe { ffi::prctl(ffi::PR_GET_SECCOMP, 0, 0, 0, 0) } != ffi::SECCOMP_MODE_FILTER as i32 {
        return Err(reject("worker-v4-seccomp-readback"));
    }
    event(
        "WORKER_V4_SECCOMP_EXIT",
        "pinned seccomp allowlist verified",
    );
    Ok(true)
}

#[cfg(target_os = "linux")]
pub(super) struct CgroupLeaf {
    pub(super) path: PathBuf,
    limits: ObserverWorkerLimitsV4,
    cleaned: bool,
}

#[cfg(target_os = "linux")]
impl CgroupLeaf {
    pub(super) fn create(
        root: &Path,
        limits: ObserverWorkerLimitsV4,
    ) -> Result<Self, ObserverWorkerV4Error> {
        event(
            "WORKER_V4_CGROUP_CREATE_ENTER",
            "validating delegated cgroup root",
        );
        let root = fs::canonicalize(root).map_err(|_| reject("worker-v4-cgroup-root"))?;
        let mount = Path::new("/sys/fs/cgroup");
        let metadata = fs::metadata(&root).map_err(|_| reject("worker-v4-cgroup-root"))?;
        if root == mount
            || !root.starts_with(mount)
            || !metadata.is_dir()
            || metadata.uid() != unsafe { ffi::getuid() }
        {
            return Err(reject("worker-v4-cgroup-delegation-invalid"));
        }
        let controllers = fs::read_to_string(root.join("cgroup.controllers"))
            .map_err(|_| reject("worker-v4-cgroup-controllers"))?;
        let enabled = fs::read_to_string(root.join("cgroup.subtree_control"))
            .map_err(|_| reject("worker-v4-cgroup-subtree"))?;
        if !controllers_ready(&controllers, &enabled) {
            return Err(reject("worker-v4-cgroup-controller-unavailable"));
        }
        static NEXT: AtomicU64 = AtomicU64::new(0);
        let path = root.join(format!(
            "veyra-observer-v4-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&path).map_err(|_| reject("worker-v4-cgroup-create"))?;
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
            "WORKER_V4_CGROUP_CREATE_EXIT",
            "delegated cgroup leaf configured",
        );
        Ok(leaf)
    }

    fn write_and_verify(&mut self) -> Result<(), ObserverWorkerV4Error> {
        event(
            "WORKER_V4_CGROUP_WRITE_ENTER",
            "writing exact cgroup controls",
        );
        fs::write(
            self.path.join("cpu.max"),
            format!(
                "{} {}\n",
                self.limits.cgroup_cpu_quota_us, self.limits.cgroup_cpu_period_us
            ),
        )
        .map_err(|_| reject("worker-v4-cgroup-cpu-write"))?;
        fs::write(
            self.path.join("memory.max"),
            format!("{}\n", self.limits.cgroup_memory_bytes),
        )
        .map_err(|_| reject("worker-v4-cgroup-memory-write"))?;
        fs::write(
            self.path.join("pids.max"),
            format!("{}\n", self.limits.cgroup_pids),
        )
        .map_err(|_| reject("worker-v4-cgroup-pids-write"))?;
        self.verify_controls()?;
        event(
            "WORKER_V4_CGROUP_WRITE_EXIT",
            "exact cgroup controls verified",
        );
        Ok(())
    }

    pub(super) fn verify_controls(&self) -> Result<(), ObserverWorkerV4Error> {
        event(
            "WORKER_V4_CGROUP_VERIFY_ENTER",
            "reading exact cgroup controls",
        );
        let cpu = fs::read_to_string(self.path.join("cpu.max"))
            .map_err(|_| reject("worker-v4-cgroup-cpu-read"))?;
        let memory = fs::read_to_string(self.path.join("memory.max"))
            .map_err(|_| reject("worker-v4-cgroup-memory-read"))?;
        let pids = fs::read_to_string(self.path.join("pids.max"))
            .map_err(|_| reject("worker-v4-cgroup-pids-read"))?;
        if !controls_match(&cpu, &memory, &pids, self.limits) {
            return Err(reject("worker-v4-cgroup-control-mismatch"));
        }
        event(
            "WORKER_V4_CGROUP_VERIFY_EXIT",
            "exact cgroup controls read back",
        );
        Ok(())
    }

    pub(super) fn contains(&self, pid: u32) -> bool {
        event(
            "WORKER_V4_CGROUP_MEMBER_ENTER",
            "checking cgroup membership",
        );
        let result = fs::read_to_string(self.path.join("cgroup.procs"))
            .map(|text| {
                text.lines()
                    .any(|line| line.trim().parse::<u32>().ok() == Some(pid))
            })
            .unwrap_or(false);
        event("WORKER_V4_CGROUP_MEMBER_EXIT", "cgroup membership checked");
        result
    }

    pub(super) fn cleanup(&mut self) -> Result<(), ObserverWorkerV4Error> {
        event(
            "WORKER_V4_CGROUP_CLEAN_ENTER",
            "verifying empty cgroup leaf",
        );
        let procs = fs::read_to_string(self.path.join("cgroup.procs"))
            .map_err(|_| reject("worker-v4-cgroup-cleanup-read"))?;
        let events = fs::read_to_string(self.path.join("cgroup.events"))
            .map_err(|_| reject("worker-v4-cgroup-events-read"))?;
        if !procs.trim().is_empty() || !events.lines().any(|line| line == "populated 0") {
            return Err(reject("worker-v4-cgroup-not-empty"));
        }
        fs::remove_dir(&self.path).map_err(|_| reject("worker-v4-cgroup-remove"))?;
        self.cleaned = true;
        event("WORKER_V4_CGROUP_CLEAN_EXIT", "empty cgroup leaf removed");
        Ok(())
    }
}

fn controllers_ready(available: &str, enabled: &str) -> bool {
    event(
        "WORKER_V4_CONTROLLERS_ENTER",
        "checking delegated controllers",
    );
    let ready = ["cpu", "memory", "pids"].iter().all(|required| {
        available.split_whitespace().any(|value| value == *required)
            && enabled.split_whitespace().any(|value| value == *required)
    });
    event(
        "WORKER_V4_CONTROLLERS_EXIT",
        "delegated controllers checked",
    );
    ready
}

fn controls_match(cpu: &str, memory: &str, pids: &str, limits: ObserverWorkerLimitsV4) -> bool {
    event("WORKER_V4_CONTROL_MATCH_ENTER", "matching cgroup readback");
    let matches = cpu.trim()
        == format!(
            "{} {}",
            limits.cgroup_cpu_quota_us, limits.cgroup_cpu_period_us
        )
        && memory.trim() == limits.cgroup_memory_bytes.to_string()
        && pids.trim() == limits.cgroup_pids.to_string();
    event("WORKER_V4_CONTROL_MATCH_EXIT", "cgroup readback matched");
    matches
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn controller_set_is_exactly_requirement_sensitive() {
        assert!(controllers_ready(
            "cpuset cpu io memory pids",
            "cpu memory pids"
        ));
        assert!(!controllers_ready("cpu memory", "cpu memory pids"));
        assert!(!controllers_ready("cpu memory pids", "cpu memory"));
    }

    #[test]
    fn cgroup_readback_mismatch_is_detected() {
        let limits = ObserverWorkerLimitsV4::default();
        assert!(controls_match(
            "100000 100000\n",
            "536870912\n",
            "1\n",
            limits
        ));
        assert!(!controls_match(
            "50000 100000\n",
            "536870912\n",
            "1\n",
            limits
        ));
        assert!(!controls_match("100000 100000\n", "max\n", "1\n", limits));
    }
}

#[cfg(target_os = "linux")]
impl Drop for CgroupLeaf {
    fn drop(&mut self) {
        event(
            "WORKER_V4_CGROUP_DROP_ENTER",
            "performing best-effort cgroup cleanup",
        );
        if !self.cleaned {
            let _ = fs::remove_dir(&self.path);
        }
        event(
            "WORKER_V4_CGROUP_DROP_EXIT",
            "best-effort cgroup cleanup finished",
        );
    }
}

#[cfg(target_os = "linux")]
mod ffi {
    use std::os::raw::{c_char, c_int, c_ulong, c_void};
    pub const CLONE_NEWNS: c_int = 0x0002_0000;
    pub const CLONE_NEWUTS: c_int = 0x0400_0000;
    pub const CLONE_NEWIPC: c_int = 0x0800_0000;
    pub const CLONE_NEWUSER: c_int = 0x1000_0000;
    pub const CLONE_NEWNET: c_int = 0x4000_0000;
    pub const MS_REC: c_ulong = 16_384;
    pub const MS_PRIVATE: c_ulong = 1 << 18;
    pub const PR_GET_SECCOMP: c_int = 21;
    pub const PR_SET_SECCOMP: c_int = 22;
    pub const SECCOMP_MODE_FILTER: usize = 2;
    pub const BPF_LD_W_ABS: u16 = 0x20;
    pub const BPF_JMP_JEQ_K: u16 = 0x15;
    pub const BPF_RET_K: u16 = 0x06;
    pub const AUDIT_ARCH_X86_64: u32 = 0xc000_003e;
    pub const SECCOMP_RET_KILL_PROCESS: u32 = 0x8000_0000;
    pub const SECCOMP_RET_ALLOW: u32 = 0x7fff_0000;
    #[repr(C)]
    pub struct SockFilter {
        code: u16,
        jt: u8,
        jf: u8,
        k: u32,
    }
    #[repr(C)]
    pub struct SockFprog {
        pub len: u16,
        pub filter: *const SockFilter,
    }
    pub const fn stmt(code: u16, k: u32) -> SockFilter {
        SockFilter {
            code,
            jt: 0,
            jf: 0,
            k,
        }
    }
    pub const fn jump(code: u16, k: u32, jt: u8, jf: u8) -> SockFilter {
        SockFilter { code, jt, jf, k }
    }
    unsafe extern "C" {
        pub fn unshare(flags: c_int) -> c_int;
        pub fn mount(
            source: *const c_char,
            target: *const c_char,
            filesystemtype: *const c_char,
            mountflags: c_ulong,
            data: *const c_void,
        ) -> c_int;
        pub fn prctl(
            option: c_int,
            arg2: c_ulong,
            arg3: c_ulong,
            arg4: c_ulong,
            arg5: c_ulong,
        ) -> c_int;
        pub fn getuid() -> u32;
        pub fn getgid() -> u32;
    }
}
