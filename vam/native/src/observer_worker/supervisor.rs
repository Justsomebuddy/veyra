//! Parent wall-clock custody and fixed child entry for observer-synthesis v2.

use super::digest::domain_sha256;
use super::event;
use super::linux::{apply_child_limits, enter_owned_process_group, signal_process_group};
use super::protocol::{
    bind_worker_receipt, decode_request_frame, decode_worker_receipt, encode_request_frame,
    encode_worker_receipt_frame, request_digest, validate_request, IsolationProfile,
    NativeWorkerReceiptV1, NativeWorkerRequestV1, NativeWorkerStatus,
    MAX_WORKER_REQUEST_FRAME_BYTES,
};
use super::synthesis_v2::{
    build_observer_synthesis_v2_receipt, validate_observer_synthesis_v2_canonical,
};
use std::fmt;
use std::io::{self, Read, Write};
use std::path::Path;
use std::process::{Child, Command, ExitStatus, Stdio};
use std::sync::mpsc::{self, TryRecvError};
use std::thread;
use std::time::{Duration, Instant};

const POLL_INTERVAL: Duration = Duration::from_millis(5);
const TERM_GRACE: Duration = Duration::from_millis(200);

#[derive(Debug)]
pub struct NativeWorkerError {
    pub reason: &'static str,
}

impl fmt::Display for NativeWorkerError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(self.reason)
    }
}

impl std::error::Error for NativeWorkerError {}

fn reject(reason: &'static str) -> NativeWorkerError {
    event("WORKER_REJECT", reason);
    NativeWorkerError { reason }
}

pub fn supervise_current_executable(
    executable: &Path,
    request: &NativeWorkerRequestV1,
) -> Result<NativeWorkerReceiptV1, NativeWorkerError> {
    event("SUPERVISOR_ENTER", "starting fixed native observer worker");
    validate_request(request).map_err(reject)?;
    if request.isolation_profile == IsolationProfile::Strict {
        return Err(reject("strict-isolation-unsupported"));
    }
    if !cfg!(target_os = "linux") {
        return Err(reject("linux-rlimit-unavailable"));
    }
    let request_frame = encode_request_frame(request).map_err(reject)?;
    let mut child = Command::new(executable)
        .arg("--child")
        .env_clear()
        .env("LANG", "C.UTF-8")
        .env("LC_ALL", "C.UTF-8")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|_| reject("worker-spawn"))?;
    let child_pid = child.id();
    if write_request(&mut child, &request_frame).is_err() {
        terminate_and_reap(&mut child);
        return Err(reject("worker-request-write"));
    }
    let deadline = Instant::now() + Duration::from_millis(request.wall_timeout_ms as u64);
    let (status, output) =
        collect_child_output(&mut child, request.max_response_bytes, deadline).map_err(reject)?;
    if !status.success() {
        terminate_and_reap(&mut child);
        return Err(reject("worker-child-exit"));
    }
    // ESRCH means the now-reaped leader has no surviving process group; every
    // other signalling failure must block custody instead of being attested.
    signal_process_group(child_pid, true).map_err(|_| reject("worker-process-group-reap"))?;
    let mut receipt = decode_worker_receipt(&output).map_err(reject)?;
    if receipt.status != NativeWorkerStatus::CustodyPending
        || receipt.request_digest != request_digest(request)
        || receipt.wall_clock_enforced
        || receipt.process_group_custody
        || !receipt.cpu_rlimit_enforced
        || !receipt.process_as_enforced
        || !receipt.core_dump_disabled
    {
        return Err(reject("worker-custody-binding"));
    }
    // Parent validation is a bounded hash/size pin, not a second unbounded
    // synthesis run outside the child's resource limits.
    if !validate_observer_synthesis_v2_canonical(&receipt.artifact) {
        return Err(reject("worker-artifact-mismatch"));
    }
    // Only the supervising parent can attest that the wall deadline remained
    // active and that the owned process group was reaped. A directly invoked
    // child therefore never emits a terminal READY receipt on its own.
    receipt.status = NativeWorkerStatus::Ready;
    receipt.wall_clock_enforced = true;
    receipt.process_group_custody = true;
    receipt = bind_worker_receipt(receipt);
    event("SUPERVISOR_EXIT", "fixed native observer worker completed");
    Ok(receipt)
}

fn collect_child_output(
    child: &mut Child,
    output_limit: u64,
    deadline: Instant,
) -> Result<(ExitStatus, Vec<u8>), &'static str> {
    event(
        "SUPERVISOR_DRAIN_ENTER",
        "draining bounded child output concurrently",
    );
    // Waiting for exit before reading can deadlock as soon as a valid artifact
    // fills the kernel pipe buffer, so the reader starts before the wait loop.
    let stdout = match child.stdout.take() {
        Some(stdout) => stdout,
        None => {
            terminate_and_reap(child);
            return Err("worker-output-pipe");
        }
    };
    let (output_sender, output_receiver) = mpsc::sync_channel(1);
    let output_reader = thread::spawn(move || {
        let mut output = Vec::new();
        let result = stdout
            .take(output_limit + 1)
            .read_to_end(&mut output)
            .map(|_| output);
        let _ = output_sender.send(result);
    });
    let mut status = None;
    let mut output = None;
    loop {
        if status.is_none() {
            match child.try_wait() {
                Ok(completed) => status = completed,
                Err(_) => {
                    terminate_and_reap(child);
                    let _ = output_reader.join();
                    return Err("worker-wait");
                }
            }
        }
        if output.is_none() {
            match output_receiver.try_recv() {
                Ok(Ok(bytes)) => {
                    if bytes.len() as u64 > output_limit {
                        terminate_and_reap(child);
                        let _ = output_reader.join();
                        return Err("worker-output-limit");
                    }
                    output = Some(bytes);
                }
                Ok(Err(_)) | Err(TryRecvError::Disconnected) => {
                    terminate_and_reap(child);
                    let _ = output_reader.join();
                    return Err("worker-output-read");
                }
                Err(TryRecvError::Empty) => {}
            }
        }
        if status.is_some() && output.is_some() {
            break;
        }
        if Instant::now() >= deadline {
            terminate_and_reap(child);
            let _ = output_reader.join();
            return Err("worker-wall-timeout");
        }
        thread::sleep(POLL_INTERVAL);
    }
    if output_reader.join().is_err() {
        terminate_and_reap(child);
        return Err("worker-output-reader");
    }
    let status = status.expect("loop exits only with child status");
    let output = output.expect("loop exits only with bounded output");
    event(
        "SUPERVISOR_DRAIN_EXIT",
        "bounded child output drained and child reaped",
    );
    Ok((status, output))
}

fn write_request(child: &mut Child, request: &[u8]) -> io::Result<()> {
    event("SUPERVISOR_WRITE_ENTER", "writing bounded request to child");
    let stdin = child
        .stdin
        .as_mut()
        .ok_or_else(|| io::Error::new(io::ErrorKind::BrokenPipe, "missing-child-stdin"))?;
    stdin.write_all(request)?;
    child.stdin.take();
    event("SUPERVISOR_WRITE_EXIT", "bounded request written to child");
    Ok(())
}

fn terminate_and_reap(child: &mut Child) {
    event(
        "SUPERVISOR_TERMINATE_ENTER",
        "terminating owned child process group",
    );
    if signal_process_group(child.id(), false).is_err() {
        event(
            "SUPERVISOR_TERMINATE_WARN",
            "initial process-group termination signal failed",
        );
    }
    let grace = Instant::now() + TERM_GRACE;
    while Instant::now() < grace {
        if matches!(child.try_wait(), Ok(Some(_))) {
            // The leader can exit before descendants. Close the entire owned
            // group before reporting that timeout/error custody is complete.
            if signal_process_group(child.id(), true).is_err() {
                event(
                    "SUPERVISOR_TERMINATE_WARN",
                    "descendant process-group kill signal failed after leader reap",
                );
            }
            event(
                "SUPERVISOR_TERMINATE_EXIT",
                "child reaped after termination",
            );
            return;
        }
        thread::sleep(POLL_INTERVAL);
    }
    if signal_process_group(child.id(), true).is_err() {
        event(
            "SUPERVISOR_TERMINATE_WARN",
            "forced process-group kill signal failed",
        );
    }
    if child.kill().is_err() {
        event("SUPERVISOR_TERMINATE_WARN", "leader kill failed");
    }
    if child.wait().is_err() {
        event("SUPERVISOR_TERMINATE_WARN", "leader reap failed");
    }
    event(
        "SUPERVISOR_TERMINATE_EXIT",
        "child reaped after forced kill",
    );
}

pub fn run_child_entry() -> Result<(), NativeWorkerError> {
    event("CHILD_ENTER", "starting fixed worker child entry");
    if !enter_owned_process_group().map_err(|_| reject("worker-process-group"))? {
        return Err(reject("worker-process-group-unavailable"));
    }
    let mut raw = Vec::new();
    io::stdin()
        .take((MAX_WORKER_REQUEST_FRAME_BYTES + 1) as u64)
        .read_to_end(&mut raw)
        .map_err(|_| reject("worker-request-read"))?;
    if raw.len() > MAX_WORKER_REQUEST_FRAME_BYTES {
        return Err(reject("worker-request-limit"));
    }
    let request = decode_request_frame(&raw).map_err(reject)?;
    if request.isolation_profile != IsolationProfile::LinuxRlimitV1 {
        return Err(reject("strict-isolation-unsupported"));
    }
    if !apply_child_limits(request.cpu_seconds, request.process_as_bytes)
        .map_err(|_| reject("worker-rlimit-bootstrap"))?
    {
        return Err(reject("worker-rlimit-verification"));
    }
    let artifact = build_observer_synthesis_v2_receipt()
        .map_err(|_| reject("worker-execution"))?
        .canonical;
    if artifact.len() as u64 + 256 > request.max_response_bytes {
        return Err(reject("worker-response-limit"));
    }
    let artifact_digest = domain_sha256(b"veyra.native-observer-worker.artifact.v1", &artifact);
    let receipt = bind_worker_receipt(NativeWorkerReceiptV1 {
        status: NativeWorkerStatus::CustodyPending,
        request_digest: request_digest(&request),
        artifact_digest,
        artifact,
        wall_clock_enforced: false,
        cpu_rlimit_enforced: true,
        process_as_enforced: true,
        core_dump_disabled: true,
        process_group_custody: false,
        obstruction: String::new(),
        receipt_digest: [0; 32],
    });
    let encoded = encode_worker_receipt_frame(&receipt).map_err(reject)?;
    io::stdout()
        .write_all(&encoded)
        .map_err(|_| reject("worker-response-write"))?;
    event("CHILD_EXIT", "fixed worker child entry completed");
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    #[cfg(target_os = "linux")]
    fn concurrent_drain_handles_more_than_a_pipe_buffer() {
        let mut child = Command::new("/usr/bin/head")
            .args(["-c", "262144", "/dev/zero"])
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn()
            .unwrap();
        let (status, output) =
            collect_child_output(&mut child, 262_144, Instant::now() + Duration::from_secs(2))
                .unwrap();
        assert!(status.success());
        assert_eq!(output.len(), 262_144);
    }
}
