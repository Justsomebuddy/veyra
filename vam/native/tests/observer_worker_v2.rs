//! Focused tests for truthful worker-v2 control-state reporting.

use std::path::Path;
use std::process::Command;
use std::sync::Mutex;

#[cfg(target_os = "linux")]
use std::os::fd::AsRawFd;
#[cfg(target_os = "linux")]
use std::os::unix::process::CommandExt;

use vam_native::observer_worker::{
    inspect_worker_v2_capabilities, WorkerControlStateV2, WorkerV2Admission, WorkerV2LaunchOptions,
    WorkerV2Policy,
};

fn probe_path() -> &'static Path {
    Path::new(env!("CARGO_BIN_EXE_vam-observer-worker-v2"))
}

fn clean_probe_command() -> Command {
    let mut command = Command::new(probe_path());
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

// These tests intentionally manipulate an inheritable process-wide descriptor.
// Serialize child launches inside this test binary so a parallel sibling cannot
// accidentally change another probe's inherited-FD result.
static CHILD_LAUNCH_LOCK: Mutex<()> = Mutex::new(());

#[test]
fn baseline_child_enforces_local_controls_but_never_mints_parent_custody() {
    if !cfg!(target_os = "linux") {
        return;
    }
    let _guard = CHILD_LAUNCH_LOCK.lock().unwrap();
    let output = clean_probe_command()
        .arg("--baseline-child-probe")
        .env_clear()
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report = String::from_utf8(output.stdout).unwrap();
    assert!(report.contains("policy=baseline\n"));
    assert!(report.contains("admission=custody-pending\n"));
    assert!(report.contains("no_new_privileges=enforced\n"));
    assert!(report.contains("resource_limits=enforced\n"));
    assert!(report.contains("process_group=enforced\n"));
    assert!(report.contains("inherited_fd_boundary=enforced\n"));
    assert!(report.contains("wall_clock_limit=available\n"));
    assert!(report.contains("output_limit=available\n"));
    assert!(!report.contains("admission=ready\n"));
}

#[test]
fn strict_policy_blocks_instead_of_faking_unimplemented_controls() {
    let report =
        inspect_worker_v2_capabilities(WorkerV2Policy::Strict, &WorkerV2LaunchOptions::default());
    assert_eq!(report.admission, WorkerV2Admission::Blocked);
    if cfg!(target_os = "linux") {
        assert_ne!(report.cgroup_v2.state, WorkerControlStateV2::Enforced);
        assert_eq!(report.seccomp.state, WorkerControlStateV2::Unavailable);
        assert_eq!(report.namespaces.state, WorkerControlStateV2::Unavailable);
    } else {
        assert_eq!(
            report.no_new_privileges.state,
            WorkerControlStateV2::UnsupportedPlatform
        );
    }
    assert!(report.obstruction.contains("strict policy requires"));
}

#[test]
fn delegated_cgroup_path_is_launch_only_and_does_not_self_authorize() {
    if !cfg!(target_os = "linux") {
        return;
    }
    let options = WorkerV2LaunchOptions {
        delegated_cgroup: Some("/sys/fs/cgroup".into()),
    };
    let report = inspect_worker_v2_capabilities(WorkerV2Policy::Strict, &options);
    assert_eq!(report.admission, WorkerV2Admission::Blocked);
    assert_ne!(report.cgroup_v2.state, WorkerControlStateV2::Enforced);
}

#[test]
fn strict_probe_cli_reports_the_same_static_block() {
    let output = clean_probe_command()
        .arg("--strict-preflight")
        .env_clear()
        .output()
        .unwrap();
    assert!(output.status.success());
    let report = String::from_utf8(output.stdout).unwrap();
    assert!(report.contains("policy=strict\n"));
    assert!(report.contains("admission=blocked\n"));
    if cfg!(target_os = "linux") {
        assert!(report.contains("seccomp=unavailable\n"));
        assert!(report.contains("namespaces=unavailable\n"));
    } else {
        assert!(report.contains("seccomp=unsupported-platform\n"));
        assert!(report.contains("namespaces=unsupported-platform\n"));
    }
}

#[test]
fn baseline_child_detects_an_inherited_descriptor_above_the_old_scan_window() {
    if !cfg!(target_os = "linux") {
        return;
    }
    #[cfg(target_os = "linux")]
    {
        let _guard = CHILD_LAUNCH_LOCK.lock().unwrap();
        let source = std::fs::File::open("/dev/null").unwrap();
        // SAFETY: F_DUPFD duplicates a valid descriptor; the returned owned
        // descriptor is closed after the child finishes.
        let inherited = unsafe { fcntl(source.as_raw_fd(), F_DUPFD, 4096) };
        assert!(inherited >= 4096);
        let output = Command::new(probe_path())
            .arg("--baseline-child-probe")
            .env_clear()
            .output()
            .unwrap();
        // SAFETY: `inherited` is the successful F_DUPFD result owned here.
        assert_eq!(unsafe { close(inherited) }, 0);
        assert!(output.status.success());
        let report = String::from_utf8(output.stdout).unwrap();
        assert!(report.contains("admission=blocked\n"));
        assert!(report.contains("inherited_fd_boundary=failed\n"));
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
