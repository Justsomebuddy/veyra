//! Portable exact-receipt package with external-key HMAC-SHA256 authentication.

use super::digest::{constant_time_eq, domain_sha256, hmac_sha256};
use super::event;
use super::protocol::{
    decode_request_frame, decode_worker_receipt, encode_worker_receipt_frame, request_digest,
    NativeWorkerStatus, MAX_WORKER_FRAME_BYTES,
};
use super::supervisor::supervise_current_executable;
use super::synthesis_v2::build_observer_synthesis_v2_receipt;
use std::path::Path;

const MAGIC: &[u8; 4] = b"VORP";
const VERSION: u16 = 1;
const AUTH_PROFILE: u8 = 1;
const PAYLOAD_DOMAIN: &[u8] = b"veyra.native-observer-replay.package.v1";
const AUTH_DOMAIN: &[u8] = b"veyra.native-observer-replay.hmac-sha256.v1";
pub const MAX_PORTABLE_REPLAY_BYTES: usize = MAX_WORKER_FRAME_BYTES + 4096;
pub const PORTABLE_REPLAY_BOUNDARY: &str =
    "portable exact native worker-receipt bytes plus external-key HMAC-SHA256 integrity; the key is supplied only to build/verify and is never serialized, persisted, logged, or included in the package; shared-key authentication is not public verification, signer identity, nonrepudiation, trusted time, source truth, or theorem evidence";

fn reject(reason: &'static str) -> &'static str {
    event("REPLAY_REJECT", reason);
    reason
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PortableReplayPackageV1 {
    pub signer_id: String,
    pub worker_request: Vec<u8>,
    pub worker_receipt: Vec<u8>,
    pub worker_receipt_digest: [u8; 32],
    pub payload_digest: [u8; 32],
    pub authentication_tag: [u8; 32],
}

pub fn build_portable_replay_package(
    worker_request: &[u8],
    worker_receipt: &[u8],
    signer_id: &str,
    key: &[u8],
) -> Result<PortableReplayPackageV1, &'static str> {
    event(
        "REPLAY_BUILD_ENTER",
        "building authenticated portable replay package",
    );
    validate_signer(signer_id)?;
    validate_key(key)?;
    let request = decode_request_frame(worker_request)?;
    let receipt = decode_worker_receipt(worker_receipt)?;
    if receipt.status != NativeWorkerStatus::Ready
        || !constant_time_eq(&receipt.request_digest, &request_digest(&request))
    {
        return Err(reject("replay-worker-not-ready"));
    }
    validate_fresh_v2_artifact(&receipt.artifact)?;
    let worker_receipt_digest = domain_sha256(
        b"veyra.native-observer-replay.worker-receipt.v1",
        worker_receipt,
    );
    let mut package = PortableReplayPackageV1 {
        signer_id: signer_id.to_owned(),
        worker_request: worker_request.to_vec(),
        worker_receipt: worker_receipt.to_vec(),
        worker_receipt_digest,
        payload_digest: [0; 32],
        authentication_tag: [0; 32],
    };
    package.payload_digest = domain_sha256(PAYLOAD_DOMAIN, &payload_data(&package));
    package.authentication_tag = authentication_tag(&package.payload_digest, key);
    if package_data(&package).len() + 4 > MAX_PORTABLE_REPLAY_BYTES {
        return Err(reject("replay-package-size"));
    }
    event(
        "REPLAY_BUILD_EXIT",
        "authenticated portable replay package built",
    );
    Ok(package)
}

pub fn validate_portable_replay_package(package: &PortableReplayPackageV1, key: &[u8]) -> bool {
    event(
        "REPLAY_VALIDATE_ENTER",
        "validating authenticated portable replay package",
    );
    let result = (|| {
        validate_signer(&package.signer_id)?;
        validate_key(key)?;
        let request = decode_request_frame(&package.worker_request)?;
        let receipt = decode_worker_receipt(&package.worker_receipt)?;
        if receipt.status != NativeWorkerStatus::Ready
            || !constant_time_eq(&receipt.request_digest, &request_digest(&request))
        {
            return Err(reject("replay-worker-not-ready"));
        }
        let worker_digest = domain_sha256(
            b"veyra.native-observer-replay.worker-receipt.v1",
            &package.worker_receipt,
        );
        let payload_digest = domain_sha256(PAYLOAD_DOMAIN, &payload_data(package));
        let tag = authentication_tag(&payload_digest, key);
        if !constant_time_eq(&package.worker_receipt_digest, &worker_digest)
            || !constant_time_eq(&package.payload_digest, &payload_digest)
            || !constant_time_eq(&package.authentication_tag, &tag)
        {
            return Err(reject("replay-authentication"));
        }
        // Authentication precedes the comparatively expensive closed-search
        // rebuild, so an unauthenticated package cannot amplify CPU work.
        validate_fresh_v2_artifact(&receipt.artifact)?;
        Ok(())
    })()
    .is_ok();
    event(
        "REPLAY_VALIDATE_EXIT",
        "authenticated portable replay package validated",
    );
    result
}

pub fn replay_portable_package(
    executable: &Path,
    package: &PortableReplayPackageV1,
    key: &[u8],
) -> Result<super::protocol::NativeWorkerReceiptV1, &'static str> {
    event(
        "REPLAY_EXECUTE_ENTER",
        "re-executing portable package request",
    );
    if !validate_portable_replay_package(package, key) {
        return Err(reject("replay-authentication"));
    }
    let request = decode_request_frame(&package.worker_request)?;
    let result = supervise_current_executable(executable, &request)
        .map_err(|_| reject("replay-worker-execution"))?;
    let replayed = encode_worker_receipt_frame(&result)?;
    if !constant_time_eq(&replayed, &package.worker_receipt) {
        return Err(reject("replay-worker-mismatch"));
    }
    event(
        "REPLAY_EXECUTE_EXIT",
        "portable package request replayed exactly",
    );
    Ok(result)
}

pub fn encode_portable_replay_package(
    package: &PortableReplayPackageV1,
    key: &[u8],
) -> Result<Vec<u8>, &'static str> {
    event("REPLAY_ENCODE_ENTER", "encoding portable replay package");
    if !validate_portable_replay_package(package, key) {
        return Err(reject("replay-authentication"));
    }
    let payload = package_data(package);
    if payload.len() + 4 > MAX_PORTABLE_REPLAY_BYTES {
        return Err(reject("replay-package-size"));
    }
    let mut result = Vec::with_capacity(payload.len() + 4);
    result.extend_from_slice(&(payload.len() as u32).to_be_bytes());
    result.extend_from_slice(&payload);
    event("REPLAY_ENCODE_EXIT", "portable replay package encoded");
    Ok(result)
}

pub fn decode_portable_replay_package(
    bytes: &[u8],
) -> Result<PortableReplayPackageV1, &'static str> {
    event("REPLAY_DECODE_ENTER", "decoding portable replay package");
    if bytes.len() < 4 || bytes.len() > MAX_PORTABLE_REPLAY_BYTES {
        return Err(reject("replay-package-size"));
    }
    let size = u32::from_be_bytes(bytes[..4].try_into().expect("fixed slice")) as usize;
    if size == 0 || bytes.len() != size + 4 {
        return Err(reject("replay-package-frame"));
    }
    let mut reader = Reader::new(&bytes[4..]);
    if reader.take(4)? != MAGIC || reader.u16()? != VERSION || reader.u8()? != AUTH_PROFILE {
        return Err(reject("replay-package-schema"));
    }
    let signer_len = reader.u16()? as usize;
    if signer_len == 0 || signer_len > 512 {
        return Err(reject("replay-signer-size"));
    }
    let signer_id = std::str::from_utf8(reader.take(signer_len)?)
        .map_err(|_| reject("replay-signer"))?
        .to_owned();
    let request_len = reader.u32()? as usize;
    if request_len == 0 || request_len > 4096 {
        return Err(reject("replay-worker-request-size"));
    }
    let worker_request = reader.take(request_len)?.to_vec();
    let receipt_len = reader.u32()? as usize;
    if receipt_len == 0 || receipt_len > MAX_WORKER_FRAME_BYTES {
        return Err(reject("replay-worker-receipt-size"));
    }
    let worker_receipt = reader.take(receipt_len)?.to_vec();
    let package = PortableReplayPackageV1 {
        signer_id,
        worker_request,
        worker_receipt,
        worker_receipt_digest: reader.array32()?,
        payload_digest: reader.array32()?,
        authentication_tag: reader.array32()?,
    };
    reader.finish()?;
    validate_signer(&package.signer_id)?;
    decode_request_frame(&package.worker_request)?;
    decode_worker_receipt(&package.worker_receipt)?;
    if package_data(&package) != bytes[4..] {
        return Err(reject("replay-package-noncanonical"));
    }
    event("REPLAY_DECODE_EXIT", "portable replay package decoded");
    Ok(package)
}

fn validate_signer(signer: &str) -> Result<(), &'static str> {
    if signer.is_empty() || signer.len() > 512 || signer.as_bytes().contains(&0) {
        return Err(reject("replay-signer"));
    }
    Ok(())
}

fn validate_key(key: &[u8]) -> Result<(), &'static str> {
    if !(32..=4096).contains(&key.len()) {
        return Err(reject("replay-key-shape"));
    }
    Ok(())
}

fn validate_fresh_v2_artifact(artifact: &[u8]) -> Result<(), &'static str> {
    event(
        "REPLAY_FRESH_ARTIFACT_ENTER",
        "rebuilding the canonical atomic v2 artifact",
    );
    let expected = build_observer_synthesis_v2_receipt()
        .map_err(|_| reject("replay-fresh-v2-artifact"))?
        .canonical;
    if !constant_time_eq(artifact, &expected) {
        return Err(reject("replay-fresh-artifact-mismatch"));
    }
    event(
        "REPLAY_FRESH_ARTIFACT_EXIT",
        "canonical atomic v2 artifact matched",
    );
    Ok(())
}

fn authentication_tag(payload_digest: &[u8; 32], key: &[u8]) -> [u8; 32] {
    let mut message = Vec::with_capacity(AUTH_DOMAIN.len() + 33);
    message.extend_from_slice(AUTH_DOMAIN);
    message.push(0);
    message.extend_from_slice(payload_digest);
    hmac_sha256(key, &message)
}

fn payload_data(package: &PortableReplayPackageV1) -> Vec<u8> {
    let mut output = Vec::with_capacity(
        52 + package.signer_id.len() + package.worker_request.len() + package.worker_receipt.len(),
    );
    output.extend_from_slice(MAGIC);
    output.extend_from_slice(&VERSION.to_be_bytes());
    output.push(AUTH_PROFILE);
    output.extend_from_slice(&(package.signer_id.len() as u16).to_be_bytes());
    output.extend_from_slice(package.signer_id.as_bytes());
    output.extend_from_slice(&(package.worker_request.len() as u32).to_be_bytes());
    output.extend_from_slice(&package.worker_request);
    output.extend_from_slice(&(package.worker_receipt.len() as u32).to_be_bytes());
    output.extend_from_slice(&package.worker_receipt);
    output.extend_from_slice(&package.worker_receipt_digest);
    output
}

fn package_data(package: &PortableReplayPackageV1) -> Vec<u8> {
    let mut output = payload_data(package);
    output.extend_from_slice(&package.payload_digest);
    output.extend_from_slice(&package.authentication_tag);
    output
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
            .ok_or_else(|| reject("replay-wire-overflow"))?;
        let result = self
            .bytes
            .get(self.offset..end)
            .ok_or_else(|| reject("replay-wire-partial"))?;
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
    fn array32(&mut self) -> Result<[u8; 32], &'static str> {
        Ok(self.take(32)?.try_into().expect("fixed slice"))
    }
    fn finish(self) -> Result<(), &'static str> {
        if self.offset == self.bytes.len() {
            Ok(())
        } else {
            Err(reject("replay-wire-trailing"))
        }
    }
}
