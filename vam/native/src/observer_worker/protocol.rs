//! Strict bounded binary protocol for the fixed observer-synthesis v2 worker.

use super::digest::{constant_time_eq, domain_sha256};
use super::event;
use super::synthesis_v2::MAX_V2_RECEIPT_BYTES;

const REQUEST_MAGIC: &[u8; 4] = b"VOWQ";
const RECEIPT_MAGIC: &[u8; 4] = b"VOWR";
const VERSION: u16 = 1;
const REQUEST_PAYLOAD_BYTES: usize = 32;
pub(crate) const MAX_WORKER_REQUEST_FRAME_BYTES: usize = REQUEST_PAYLOAD_BYTES + 4;
pub const MAX_WORKER_ARTIFACT_BYTES: usize = MAX_V2_RECEIPT_BYTES;
pub const MAX_WORKER_FRAME_BYTES: usize = MAX_WORKER_ARTIFACT_BYTES + 4096;
const REQUEST_DOMAIN: &[u8] = b"veyra.native-observer-worker.request.v1";
const RECEIPT_DOMAIN: &[u8] = b"veyra.native-observer-worker.receipt.v1";

fn reject(reason: &'static str) -> &'static str {
    event("PROTOCOL_REJECT", reason);
    reason
}

pub const NATIVE_WORKER_BOUNDARY: &str =
    "one fixed Rust observer-synthesis v2 evidence child under parent wall timeout, owned process-group kill/reap, and verified Linux RLIMIT_CPU/RLIMIT_AS/RLIMIT_CORE ceilings; not seccomp, a namespace/container/VM, network/filesystem isolation, trusted time, remote custody, or theorem evidence";

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum IsolationProfile {
    LinuxRlimitV1,
    Strict,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NativeWorkerStatus {
    Ready,
    Blocked,
    /// Internal child result awaiting parent wall-clock and process-group custody.
    CustodyPending,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NativeWorkerRequestV1 {
    pub isolation_profile: IsolationProfile,
    pub wall_timeout_ms: u32,
    pub cpu_seconds: u32,
    pub process_as_bytes: u64,
    pub max_response_bytes: u64,
}

impl Default for NativeWorkerRequestV1 {
    fn default() -> Self {
        Self {
            isolation_profile: IsolationProfile::LinuxRlimitV1,
            // The exact search is normally sub-second on the reference host,
            // but shared CI runners can be heavily contended. These remain
            // hard ceilings rather than benchmark expectations.
            wall_timeout_ms: 30_000,
            cpu_seconds: 10,
            process_as_bytes: 512 * 1024 * 1024,
            max_response_bytes: MAX_WORKER_FRAME_BYTES as u64,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NativeWorkerReceiptV1 {
    pub status: NativeWorkerStatus,
    pub request_digest: [u8; 32],
    pub artifact_digest: [u8; 32],
    pub artifact: Vec<u8>,
    pub wall_clock_enforced: bool,
    pub cpu_rlimit_enforced: bool,
    pub process_as_enforced: bool,
    pub core_dump_disabled: bool,
    pub process_group_custody: bool,
    pub obstruction: String,
    pub receipt_digest: [u8; 32],
}

pub fn encode_request_frame(request: &NativeWorkerRequestV1) -> Result<Vec<u8>, &'static str> {
    event("REQUEST_ENCODE_ENTER", "encoding fixed worker request");
    validate_request(request)?;
    let payload = request_payload(request);
    let result = frame(&payload)?;
    event("REQUEST_ENCODE_EXIT", "fixed worker request encoded");
    Ok(result)
}

pub(crate) fn decode_request_frame(frame: &[u8]) -> Result<NativeWorkerRequestV1, &'static str> {
    event("REQUEST_DECODE_ENTER", "decoding fixed worker request");
    let payload = unframe(frame, REQUEST_PAYLOAD_BYTES)?;
    let mut reader = Reader::new(payload);
    if reader.take(4)? != REQUEST_MAGIC || reader.u16()? != VERSION {
        return Err(reject("worker-request-schema"));
    }
    let isolation_profile = match reader.u8()? {
        1 => IsolationProfile::LinuxRlimitV1,
        2 => IsolationProfile::Strict,
        _ => return Err(reject("worker-request-isolation")),
    };
    if reader.u8()? != 1 {
        return Err(reject("worker-request-profile"));
    }
    let request = NativeWorkerRequestV1 {
        isolation_profile,
        wall_timeout_ms: reader.u32()?,
        cpu_seconds: reader.u32()?,
        process_as_bytes: reader.u64()?,
        max_response_bytes: reader.u64()?,
    };
    reader.finish()?;
    validate_request(&request)?;
    if request_payload(&request) != payload {
        return Err(reject("worker-request-noncanonical"));
    }
    event("REQUEST_DECODE_EXIT", "fixed worker request decoded");
    Ok(request)
}

pub fn encode_worker_receipt_frame(
    receipt: &NativeWorkerReceiptV1,
) -> Result<Vec<u8>, &'static str> {
    event("RECEIPT_ENCODE_ENTER", "encoding isolated worker receipt");
    validate_worker_receipt(receipt)?;
    if receipt.receipt_digest == [0; 32] {
        return Err(reject("worker-receipt-unbound"));
    }
    let result = frame(&receipt_data(receipt, true))?;
    event("RECEIPT_ENCODE_EXIT", "isolated worker receipt encoded");
    Ok(result)
}

pub fn decode_worker_receipt(frame: &[u8]) -> Result<NativeWorkerReceiptV1, &'static str> {
    event("RECEIPT_DECODE_ENTER", "decoding isolated worker receipt");
    let payload = unframe(frame, MAX_WORKER_FRAME_BYTES)?;
    let mut reader = Reader::new(payload);
    if reader.take(4)? != RECEIPT_MAGIC || reader.u16()? != VERSION {
        return Err(reject("worker-receipt-schema"));
    }
    let status = match reader.u8()? {
        1 => NativeWorkerStatus::Ready,
        2 => NativeWorkerStatus::Blocked,
        3 => NativeWorkerStatus::CustodyPending,
        _ => return Err(reject("worker-receipt-status")),
    };
    let flags = reader.u8()?;
    if flags & !0x1f != 0 {
        return Err(reject("worker-receipt-flags"));
    }
    let request_digest = reader.array32()?;
    let artifact_digest = reader.array32()?;
    let artifact_len = reader.u32()? as usize;
    if artifact_len > MAX_WORKER_ARTIFACT_BYTES {
        return Err(reject("worker-receipt-artifact-size"));
    }
    let artifact = reader.take(artifact_len)?.to_vec();
    let obstruction_len = reader.u16()? as usize;
    if obstruction_len > 256 {
        return Err(reject("worker-receipt-obstruction-size"));
    }
    let obstruction = std::str::from_utf8(reader.take(obstruction_len)?)
        .map_err(|_| reject("worker-receipt-obstruction"))?
        .to_owned();
    let receipt_digest = reader.array32()?;
    reader.finish()?;
    let receipt = NativeWorkerReceiptV1 {
        status,
        request_digest,
        artifact_digest,
        artifact,
        wall_clock_enforced: flags & 1 != 0,
        cpu_rlimit_enforced: flags & 2 != 0,
        process_as_enforced: flags & 4 != 0,
        core_dump_disabled: flags & 8 != 0,
        process_group_custody: flags & 16 != 0,
        obstruction,
        receipt_digest,
    };
    validate_worker_receipt(&receipt)?;
    if receipt.receipt_digest == [0; 32] {
        return Err(reject("worker-receipt-unbound"));
    }
    if receipt_data(&receipt, true) != payload {
        return Err(reject("worker-receipt-noncanonical"));
    }
    event("RECEIPT_DECODE_EXIT", "isolated worker receipt decoded");
    Ok(receipt)
}

pub(crate) fn bind_worker_receipt(mut receipt: NativeWorkerReceiptV1) -> NativeWorkerReceiptV1 {
    event("RECEIPT_BIND_ENTER", "binding isolated worker receipt");
    receipt.receipt_digest = domain_sha256(RECEIPT_DOMAIN, &receipt_data(&receipt, false));
    event("RECEIPT_BIND_EXIT", "isolated worker receipt bound");
    receipt
}

pub(crate) fn request_digest(request: &NativeWorkerRequestV1) -> [u8; 32] {
    event("REQUEST_DIGEST_ENTER", "binding fixed worker request");
    let result = domain_sha256(REQUEST_DOMAIN, &request_payload(request));
    event("REQUEST_DIGEST_EXIT", "fixed worker request bound");
    result
}

pub(crate) fn validate_request(request: &NativeWorkerRequestV1) -> Result<(), &'static str> {
    event("REQUEST_VALIDATE_ENTER", "validating fixed worker request");
    if !(1..=30_000).contains(&request.wall_timeout_ms)
        || !(1..=10).contains(&request.cpu_seconds)
        || !(128 * 1024 * 1024..=2 * 1024 * 1024 * 1024).contains(&request.process_as_bytes)
        || request.max_response_bytes < 1024
        || request.max_response_bytes > MAX_WORKER_FRAME_BYTES as u64
    {
        return Err(reject("worker-request-limits"));
    }
    event("REQUEST_VALIDATE_EXIT", "fixed worker request validated");
    Ok(())
}

pub(crate) fn validate_worker_receipt(receipt: &NativeWorkerReceiptV1) -> Result<(), &'static str> {
    event(
        "RECEIPT_VALIDATE_ENTER",
        "validating isolated worker receipt",
    );
    if receipt.artifact.len() > MAX_WORKER_ARTIFACT_BYTES
        || receipt.obstruction.len() > 256
        || receipt.obstruction.as_bytes().contains(&0)
    {
        return Err(reject("worker-receipt-shape"));
    }
    let valid_terminal_shape = match receipt.status {
        NativeWorkerStatus::Ready => {
            receipt.obstruction.is_empty()
                && !receipt.artifact.is_empty()
                && receipt.wall_clock_enforced
                && receipt.cpu_rlimit_enforced
                && receipt.process_as_enforced
                && receipt.core_dump_disabled
                && receipt.process_group_custody
        }
        NativeWorkerStatus::CustodyPending => {
            receipt.obstruction.is_empty()
                && !receipt.artifact.is_empty()
                && !receipt.wall_clock_enforced
                && receipt.cpu_rlimit_enforced
                && receipt.process_as_enforced
                && receipt.core_dump_disabled
                && !receipt.process_group_custody
        }
        NativeWorkerStatus::Blocked => {
            !receipt.obstruction.is_empty()
                && receipt.artifact.is_empty()
                && !receipt.wall_clock_enforced
                && !receipt.cpu_rlimit_enforced
                && !receipt.process_as_enforced
                && !receipt.core_dump_disabled
                && !receipt.process_group_custody
        }
    };
    if !valid_terminal_shape {
        return Err(reject("worker-receipt-terminal-shape"));
    }
    let expected_artifact = if receipt.artifact.is_empty() {
        [0; 32]
    } else {
        domain_sha256(
            b"veyra.native-observer-worker.artifact.v1",
            &receipt.artifact,
        )
    };
    if !constant_time_eq(&receipt.artifact_digest, &expected_artifact) {
        return Err(reject("worker-receipt-artifact-digest"));
    }
    let expected = domain_sha256(RECEIPT_DOMAIN, &receipt_data(receipt, false));
    if receipt.receipt_digest != [0; 32] && !constant_time_eq(&receipt.receipt_digest, &expected) {
        return Err(reject("worker-receipt-digest"));
    }
    event("RECEIPT_VALIDATE_EXIT", "isolated worker receipt validated");
    Ok(())
}

fn request_payload(request: &NativeWorkerRequestV1) -> Vec<u8> {
    let mut output = Vec::with_capacity(REQUEST_PAYLOAD_BYTES);
    output.extend_from_slice(REQUEST_MAGIC);
    output.extend_from_slice(&VERSION.to_be_bytes());
    output.push(match request.isolation_profile {
        IsolationProfile::LinuxRlimitV1 => 1,
        IsolationProfile::Strict => 2,
    });
    output.push(1);
    output.extend_from_slice(&request.wall_timeout_ms.to_be_bytes());
    output.extend_from_slice(&request.cpu_seconds.to_be_bytes());
    output.extend_from_slice(&request.process_as_bytes.to_be_bytes());
    output.extend_from_slice(&request.max_response_bytes.to_be_bytes());
    output
}

fn receipt_data(receipt: &NativeWorkerReceiptV1, include_digest: bool) -> Vec<u8> {
    let mut output = Vec::with_capacity(110 + receipt.artifact.len() + receipt.obstruction.len());
    output.extend_from_slice(RECEIPT_MAGIC);
    output.extend_from_slice(&VERSION.to_be_bytes());
    output.push(match receipt.status {
        NativeWorkerStatus::Ready => 1,
        NativeWorkerStatus::Blocked => 2,
        NativeWorkerStatus::CustodyPending => 3,
    });
    output.push(
        receipt.wall_clock_enforced as u8
            | (receipt.cpu_rlimit_enforced as u8) << 1
            | (receipt.process_as_enforced as u8) << 2
            | (receipt.core_dump_disabled as u8) << 3
            | (receipt.process_group_custody as u8) << 4,
    );
    output.extend_from_slice(&receipt.request_digest);
    output.extend_from_slice(&receipt.artifact_digest);
    output.extend_from_slice(&(receipt.artifact.len() as u32).to_be_bytes());
    output.extend_from_slice(&receipt.artifact);
    output.extend_from_slice(&(receipt.obstruction.len() as u16).to_be_bytes());
    output.extend_from_slice(receipt.obstruction.as_bytes());
    if include_digest {
        output.extend_from_slice(&receipt.receipt_digest);
    }
    output
}

pub(crate) fn frame(payload: &[u8]) -> Result<Vec<u8>, &'static str> {
    if payload.len() > u32::MAX as usize {
        return Err(reject("worker-frame-size"));
    }
    let mut output = Vec::with_capacity(4 + payload.len());
    output.extend_from_slice(&(payload.len() as u32).to_be_bytes());
    output.extend_from_slice(payload);
    Ok(output)
}

pub(crate) fn unframe(frame: &[u8], maximum: usize) -> Result<&[u8], &'static str> {
    if frame.len() < 4 {
        return Err(reject("worker-frame-partial"));
    }
    let size = u32::from_be_bytes(frame[..4].try_into().expect("fixed slice")) as usize;
    if size == 0 || size > maximum || frame.len() != size + 4 {
        return Err(reject("worker-frame-size"));
    }
    Ok(&frame[4..])
}

struct Reader<'a> {
    bytes: &'a [u8],
    offset: usize,
}

impl<'a> Reader<'a> {
    fn new(bytes: &'a [u8]) -> Self {
        Self { bytes, offset: 0 }
    }
    fn take(&mut self, count: usize) -> Result<&'a [u8], &'static str> {
        let end = self
            .offset
            .checked_add(count)
            .ok_or_else(|| reject("worker-wire-overflow"))?;
        let result = self
            .bytes
            .get(self.offset..end)
            .ok_or_else(|| reject("worker-wire-partial"))?;
        self.offset = end;
        Ok(result)
    }
    fn u8(&mut self) -> Result<u8, &'static str> {
        Ok(self.take(1)?[0])
    }
    fn u16(&mut self) -> Result<u16, &'static str> {
        Ok(u16::from_be_bytes(
            self.take(2)?.try_into().expect("fixed slice"),
        ))
    }
    fn u32(&mut self) -> Result<u32, &'static str> {
        Ok(u32::from_be_bytes(
            self.take(4)?.try_into().expect("fixed slice"),
        ))
    }
    fn u64(&mut self) -> Result<u64, &'static str> {
        Ok(u64::from_be_bytes(
            self.take(8)?.try_into().expect("fixed slice"),
        ))
    }
    fn array32(&mut self) -> Result<[u8; 32], &'static str> {
        Ok(self.take(32)?.try_into().expect("fixed slice"))
    }
    fn finish(self) -> Result<(), &'static str> {
        if self.offset == self.bytes.len() {
            Ok(())
        } else {
            Err(reject("worker-wire-trailing"))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn request_roundtrip_and_trailing_bytes_fail_closed() {
        let request = NativeWorkerRequestV1::default();
        let frame = encode_request_frame(&request).unwrap();
        assert_eq!(decode_request_frame(&frame).unwrap(), request);
        let mut trailing = frame;
        trailing.push(0);
        assert!(decode_request_frame(&trailing).is_err());
    }
}
