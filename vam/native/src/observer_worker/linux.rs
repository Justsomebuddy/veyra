//! Minimal Linux process primitives without adding a libc crate dependency.

use super::event;
use std::io;

#[cfg(target_os = "linux")]
mod ffi {
    use std::os::raw::{c_int, c_ulong};

    pub const RLIMIT_CPU: c_int = 0;
    pub const RLIMIT_CORE: c_int = 4;
    pub const RLIMIT_AS: c_int = 9;
    pub const SIGTERM: c_int = 15;
    pub const SIGKILL: c_int = 9;

    #[repr(C)]
    #[derive(Clone, Copy)]
    pub struct RLimit {
        pub current: c_ulong,
        pub maximum: c_ulong,
    }

    unsafe extern "C" {
        pub fn setrlimit(resource: c_int, limits: *const RLimit) -> c_int;
        pub fn getrlimit(resource: c_int, limits: *mut RLimit) -> c_int;
        pub fn setpgid(pid: c_int, pgid: c_int) -> c_int;
        pub fn kill(pid: c_int, signal: c_int) -> c_int;
    }
}

#[cfg(target_os = "linux")]
fn set_and_verify(resource: i32, value: u64) -> io::Result<bool> {
    event("RLIMIT_SET_ENTER", "setting one exact Linux resource limit");
    let requested = ffi::RLimit {
        current: value as _,
        maximum: value as _,
    };
    let mut actual = ffi::RLimit {
        current: 0,
        maximum: 0,
    };
    // SAFETY: pointers reference live RLimit objects and the resource constant is fixed.
    if unsafe { ffi::setrlimit(resource, &requested) } != 0
        || unsafe { ffi::getrlimit(resource, &mut actual) } != 0
    {
        return Err(io::Error::last_os_error());
    }
    let result = actual.current as u64 == value && actual.maximum as u64 == value;
    event("RLIMIT_SET_EXIT", "one exact Linux resource limit verified");
    Ok(result)
}

pub(crate) fn apply_child_limits(cpu_seconds: u32, address_space: u64) -> io::Result<bool> {
    event(
        "RLIMIT_BOOTSTRAP_ENTER",
        "applying worker CPU/address-space/core limits",
    );
    #[cfg(target_os = "linux")]
    {
        let result = set_and_verify(ffi::RLIMIT_CPU, cpu_seconds as u64)?
            && set_and_verify(ffi::RLIMIT_AS, address_space)?
            && set_and_verify(ffi::RLIMIT_CORE, 0)?;
        event(
            "RLIMIT_BOOTSTRAP_EXIT",
            "worker limits applied and verified",
        );
        Ok(result)
    }
    #[cfg(not(target_os = "linux"))]
    {
        let _ = (cpu_seconds, address_space);
        event(
            "RLIMIT_BOOTSTRAP_REJECT",
            "Linux resource limits unavailable",
        );
        Ok(false)
    }
}

pub(crate) fn enter_owned_process_group() -> io::Result<bool> {
    event("PROCESS_GROUP_ENTER", "creating owned worker process group");
    #[cfg(target_os = "linux")]
    {
        // SAFETY: pid 0 means the calling process and pgid 0 selects its pid.
        let result = unsafe { ffi::setpgid(0, 0) } == 0;
        if !result {
            return Err(io::Error::last_os_error());
        }
        event("PROCESS_GROUP_EXIT", "owned worker process group created");
        Ok(true)
    }
    #[cfg(not(target_os = "linux"))]
    {
        event("PROCESS_GROUP_REJECT", "process-group custody unavailable");
        Ok(false)
    }
}

pub(crate) fn signal_process_group(pid: u32, kill: bool) -> io::Result<()> {
    event(
        "PROCESS_GROUP_SIGNAL_ENTER",
        "signalling owned worker process group",
    );
    #[cfg(target_os = "linux")]
    {
        let signal = if kill { ffi::SIGKILL } else { ffi::SIGTERM };
        // SAFETY: negative pid addresses the group whose leader pid is owned by the caller.
        if unsafe { ffi::kill(-(pid as i32), signal) } != 0 {
            let error = io::Error::last_os_error();
            if error.raw_os_error() != Some(3) {
                return Err(error);
            }
        }
        event(
            "PROCESS_GROUP_SIGNAL_EXIT",
            "owned worker process group signalled",
        );
        Ok(())
    }
    #[cfg(not(target_os = "linux"))]
    {
        let _ = (pid, kill);
        Err(io::Error::new(
            io::ErrorKind::Unsupported,
            "process-group-unavailable",
        ))
    }
}
