//! Bounded, authenticated observer-worker replay bundles (wire version 2).
//!
//! Version 1 (`replay`) remains byte-for-byte unchanged.  V2 adds an outer
//! length prefix for bounded streaming, explicit algorithms and key IDs, and
//! a deliberately separate trust-policy layer.  Authentication is checked
//! before request/receipt semantics are decoded.

use std::fmt;
use std::io::{Cursor, Read};

use ed25519_dalek::{Signature, Signer, SigningKey, VerifyingKey};

use super::digest::{constant_time_eq, domain_sha256, hmac_sha256};
use super::event;
use super::pipeline_replay_v3::validate_pipeline_replay_semantics_v3;
use super::protocol::{
    decode_request_frame, decode_worker_receipt, request_digest, NativeWorkerStatus,
    MAX_WORKER_FRAME_BYTES,
};
use super::synthesis_v2::build_observer_synthesis_v2_receipt;

pub const REPLAY_V2_MAGIC: [u8; 4] = *b"VOR2";
pub const REPLAY_V2_VERSION: u16 = 2;
pub const MAX_REPLAY_BUNDLE_V2_BYTES: usize = 32 * 1024;
pub const MAX_REPLAY_V2_LABEL_BYTES: usize = 128;
pub const MAX_REPLAY_V2_REQUEST_BYTES: usize = 4 * 1024;
pub const MAX_REPLAY_V2_RECEIPT_BYTES: usize = 24 * 1024;
pub const REPLAY_V2_BOUNDARY: &str =
    "bounded canonical VOR2 bytes authenticated by an externally trusted HMAC key or Ed25519 public key; semantic validation deterministically rebuilds the pinned artifact in-process, but is not worker re-execution, sandbox custody, trusted time, signer authorization beyond the supplied trust policy, or theorem evidence";

const PAYLOAD_DOMAIN: &[u8] = b"veyra.native-observer-replay.bundle.v2.payload";
const HMAC_AUTH_DOMAIN: &[u8] = b"veyra.native-observer-replay.bundle.v2.auth.hmac-sha256";
const ED25519_AUTH_DOMAIN: &[u8] = b"veyra.native-observer-replay.bundle.v2.auth.ed25519";
const ED25519_KEY_ID_DOMAIN: &[u8] = b"veyra.native-observer-replay.bundle.v2.key-id.ed25519";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(u8)]
pub enum ReplayAuthAlgorithmV2 {
    HmacSha256 = 1,
    Ed25519 = 2,
}

impl ReplayAuthAlgorithmV2 {
    fn from_wire(value: u8) -> Result<Self, ReplayV2Error> {
        event("replay-v2", "algorithm-decode-enter");
        match value {
            1 => Ok(Self::HmacSha256),
            2 => Ok(Self::Ed25519),
            _ => reject("unsupported replay-v2 authentication algorithm"),
        }
    }

    fn authentication_len(self) -> usize {
        event("replay-v2", "algorithm-length");
        match self {
            Self::HmacSha256 => 32,
            Self::Ed25519 => 64,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(u8)]
pub enum ReplayPayloadKindV2 {
    WorkerV1 = 1,
    ObserverPipelineV3 = 2,
}

impl ReplayPayloadKindV2 {
    fn from_wire(value: u8) -> Result<Self, ReplayV2Error> {
        event("replay-v2", "payload-kind-decode-enter");
        let result = match value {
            1 => Ok(Self::WorkerV1),
            2 => Ok(Self::ObserverPipelineV3),
            _ => reject("unsupported replay-v2 payload kind"),
        };
        event("replay-v2", "payload-kind-decode-exit");
        result
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ReplayBundleV2 {
    pub algorithm: ReplayAuthAlgorithmV2,
    pub payload_kind: ReplayPayloadKindV2,
    pub key_id: [u8; 32],
    pub signer_label: String,
    pub worker_request: Vec<u8>,
    pub worker_receipt: Vec<u8>,
    pub payload_digest: [u8; 32],
    pub authentication: Vec<u8>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ReplayTrustPolicyV2 {
    pub allow_hmac_sha256: bool,
    pub allow_ed25519: bool,
    pub require_ready_receipt: bool,
    /// Require a deterministic in-process artifact rebuild. This is not an
    /// isolated worker re-execution or independent execution custody.
    pub require_fresh_artifact: bool,
}

impl ReplayTrustPolicyV2 {
    /// Deny all algorithms until the caller opts into an explicit trust mode.
    pub fn deny_all() -> Self {
        event("replay-v2", "policy-deny-all");
        Self {
            allow_hmac_sha256: false,
            allow_ed25519: false,
            require_ready_receipt: true,
            require_fresh_artifact: true,
        }
    }

    pub fn hmac_only() -> Self {
        event("replay-v2", "policy-hmac-only");
        Self {
            allow_hmac_sha256: true,
            allow_ed25519: false,
            require_ready_receipt: true,
            require_fresh_artifact: true,
        }
    }

    pub fn ed25519_only() -> Self {
        event("replay-v2", "policy-ed25519-only");
        Self {
            allow_hmac_sha256: false,
            allow_ed25519: true,
            require_ready_receipt: true,
            require_fresh_artifact: true,
        }
    }
}

impl Default for ReplayTrustPolicyV2 {
    fn default() -> Self {
        event("replay-v2", "policy-default");
        Self::deny_all()
    }
}

/// Trust resolution is external to the bundle: no embedded key can authorize
/// itself.  Implementations may use a KMS, a keyring, or the focused helpers
/// below.
pub trait ReplayTrustResolverV2 {
    fn verify(
        &self,
        algorithm: ReplayAuthAlgorithmV2,
        key_id: &[u8; 32],
        authenticated_message: &[u8],
        authentication: &[u8],
    ) -> bool;
}

pub struct HmacReplayTrustV2<'a> {
    key_id: [u8; 32],
    key: &'a [u8],
}

impl<'a> HmacReplayTrustV2<'a> {
    pub fn new(key_id: [u8; 32], key: &'a [u8]) -> Result<Self, ReplayV2Error> {
        event("replay-v2", "hmac-trust-new-enter");
        validate_hmac_key(key)?;
        event("replay-v2", "hmac-trust-new-exit");
        Ok(Self { key_id, key })
    }
}

impl ReplayTrustResolverV2 for HmacReplayTrustV2<'_> {
    fn verify(
        &self,
        algorithm: ReplayAuthAlgorithmV2,
        key_id: &[u8; 32],
        authenticated_message: &[u8],
        authentication: &[u8],
    ) -> bool {
        event("replay-v2", "hmac-trust-verify-enter");
        let valid = algorithm == ReplayAuthAlgorithmV2::HmacSha256
            && constant_time_eq(&self.key_id, key_id)
            && constant_time_eq(
                &hmac_sha256(self.key, authenticated_message),
                authentication,
            );
        event("replay-v2", "hmac-trust-verify-exit");
        valid
    }
}

#[derive(Clone)]
pub struct Ed25519ReplayTrustV2 {
    key_id: [u8; 32],
    verifying_key: VerifyingKey,
}

impl Ed25519ReplayTrustV2 {
    pub fn new(public_key: [u8; 32]) -> Result<Self, ReplayV2Error> {
        event("replay-v2", "ed25519-trust-new-enter");
        let verifying_key = VerifyingKey::from_bytes(&public_key)
            .map_err(|_| ReplayV2Error("invalid Ed25519 public key"))?;
        let key_id = ed25519_key_id(&public_key);
        event("replay-v2", "ed25519-trust-new-exit");
        Ok(Self {
            key_id,
            verifying_key,
        })
    }

    pub fn key_id(&self) -> [u8; 32] {
        event("replay-v2", "ed25519-trust-key-id");
        self.key_id
    }
}

impl ReplayTrustResolverV2 for Ed25519ReplayTrustV2 {
    fn verify(
        &self,
        algorithm: ReplayAuthAlgorithmV2,
        key_id: &[u8; 32],
        authenticated_message: &[u8],
        authentication: &[u8],
    ) -> bool {
        event("replay-v2", "ed25519-trust-verify-enter");
        if algorithm != ReplayAuthAlgorithmV2::Ed25519
            || !constant_time_eq(&self.key_id, key_id)
            || authentication.len() != 64
        {
            event("replay-v2", "ed25519-trust-verify-reject");
            return false;
        }
        let mut bytes = [0_u8; 64];
        bytes.copy_from_slice(authentication);
        let signature = Signature::from_bytes(&bytes);
        let valid = self
            .verifying_key
            .verify_strict(authenticated_message, &signature)
            .is_ok();
        event("replay-v2", "ed25519-trust-verify-exit");
        valid
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ReplayV2Error(pub &'static str);

impl fmt::Display for ReplayV2Error {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        event("replay-v2", "error-display");
        formatter.write_str(self.0)
    }
}

impl std::error::Error for ReplayV2Error {}

pub fn ed25519_key_id(public_key: &[u8; 32]) -> [u8; 32] {
    event("replay-v2", "ed25519-key-id-enter");
    let digest = domain_sha256(ED25519_KEY_ID_DOMAIN, public_key);
    event("replay-v2", "ed25519-key-id-exit");
    digest
}

pub fn build_hmac_replay_bundle_v2(
    worker_request: &[u8],
    worker_receipt: &[u8],
    signer_label: &str,
    key_id: [u8; 32],
    key: &[u8],
) -> Result<ReplayBundleV2, ReplayV2Error> {
    event("replay-v2", "build-hmac-enter");
    validate_hmac_key(key)?;
    let mut bundle = unsigned_bundle(
        ReplayAuthAlgorithmV2::HmacSha256,
        ReplayPayloadKindV2::WorkerV1,
        key_id,
        signer_label,
        worker_request,
        worker_receipt,
    )?;
    let message = authenticated_message(&bundle)?;
    bundle.authentication = hmac_sha256(key, &message).to_vec();
    event("replay-v2", "build-hmac-exit");
    Ok(bundle)
}

pub fn build_ed25519_replay_bundle_v2(
    worker_request: &[u8],
    worker_receipt: &[u8],
    signer_label: &str,
    signing_key: &SigningKey,
) -> Result<ReplayBundleV2, ReplayV2Error> {
    event("replay-v2", "build-ed25519-enter");
    let public_key = signing_key.verifying_key().to_bytes();
    let mut bundle = unsigned_bundle(
        ReplayAuthAlgorithmV2::Ed25519,
        ReplayPayloadKindV2::WorkerV1,
        ed25519_key_id(&public_key),
        signer_label,
        worker_request,
        worker_receipt,
    )?;
    let message = authenticated_message(&bundle)?;
    bundle.authentication = signing_key.sign(&message).to_bytes().to_vec();
    event("replay-v2", "build-ed25519-exit");
    Ok(bundle)
}

pub(crate) fn build_hmac_payload_bundle_v2(
    payload_kind: ReplayPayloadKindV2,
    request: &[u8],
    receipt: &[u8],
    signer_label: &str,
    key_id: [u8; 32],
    key: &[u8],
) -> Result<ReplayBundleV2, ReplayV2Error> {
    event("replay-v2", "build-hmac-payload-enter");
    validate_hmac_key(key)?;
    let mut bundle = unsigned_bundle(
        ReplayAuthAlgorithmV2::HmacSha256,
        payload_kind,
        key_id,
        signer_label,
        request,
        receipt,
    )?;
    let message = authenticated_message(&bundle)?;
    bundle.authentication = hmac_sha256(key, &message).to_vec();
    event("replay-v2", "build-hmac-payload-exit");
    Ok(bundle)
}

pub(crate) fn build_ed25519_payload_bundle_v2(
    payload_kind: ReplayPayloadKindV2,
    request: &[u8],
    receipt: &[u8],
    signer_label: &str,
    signing_key: &SigningKey,
) -> Result<ReplayBundleV2, ReplayV2Error> {
    event("replay-v2", "build-ed25519-payload-enter");
    let public_key = signing_key.verifying_key().to_bytes();
    let mut bundle = unsigned_bundle(
        ReplayAuthAlgorithmV2::Ed25519,
        payload_kind,
        ed25519_key_id(&public_key),
        signer_label,
        request,
        receipt,
    )?;
    let message = authenticated_message(&bundle)?;
    bundle.authentication = signing_key.sign(&message).to_bytes().to_vec();
    event("replay-v2", "build-ed25519-payload-exit");
    Ok(bundle)
}

pub fn encode_replay_bundle_v2(bundle: &ReplayBundleV2) -> Result<Vec<u8>, ReplayV2Error> {
    event("replay-v2", "encode-enter");
    validate_structure(bundle)?;
    let mut body = unsigned_payload(bundle)?;
    body.extend_from_slice(&bundle.payload_digest);
    push_u16(&mut body, bundle.authentication.len())?;
    body.extend_from_slice(&bundle.authentication);
    if body.len() > MAX_REPLAY_BUNDLE_V2_BYTES {
        return reject("replay-v2 bundle exceeds the bounded maximum");
    }
    let mut encoded = Vec::with_capacity(4 + body.len());
    push_u32(&mut encoded, body.len())?;
    encoded.extend_from_slice(&body);
    event("replay-v2", "encode-exit");
    Ok(encoded)
}

/// Read exactly one bounded frame.  The caller owns any trailing stream data.
pub fn decode_replay_bundle_v2<R: Read>(reader: &mut R) -> Result<ReplayBundleV2, ReplayV2Error> {
    event("replay-v2", "decode-stream-enter");
    let mut length_bytes = [0_u8; 4];
    reader
        .read_exact(&mut length_bytes)
        .map_err(|_| ReplayV2Error("truncated replay-v2 length prefix"))?;
    let length = u32::from_be_bytes(length_bytes) as usize;
    if length == 0 || length > MAX_REPLAY_BUNDLE_V2_BYTES {
        return reject("invalid replay-v2 bounded frame length");
    }
    let mut body = vec![0_u8; length];
    reader
        .read_exact(&mut body)
        .map_err(|_| ReplayV2Error("truncated replay-v2 body"))?;
    let bundle = decode_body(&body)?;
    event("replay-v2", "decode-stream-exit");
    Ok(bundle)
}

pub fn decode_replay_bundle_v2_exact<R: Read>(
    reader: &mut R,
) -> Result<ReplayBundleV2, ReplayV2Error> {
    event("replay-v2", "decode-exact-enter");
    let bundle = decode_replay_bundle_v2(reader)?;
    let mut trailing = [0_u8; 1];
    match reader.read(&mut trailing) {
        Ok(0) => {
            event("replay-v2", "decode-exact-exit");
            Ok(bundle)
        }
        Ok(_) => reject("trailing bytes after replay-v2 frame"),
        Err(_) => reject("failed checking replay-v2 trailing bytes"),
    }
}

pub fn decode_replay_bundle_v2_bytes(bytes: &[u8]) -> Result<ReplayBundleV2, ReplayV2Error> {
    event("replay-v2", "decode-bytes-enter");
    let mut cursor = Cursor::new(bytes);
    let result = decode_replay_bundle_v2_exact(&mut cursor);
    event("replay-v2", "decode-bytes-exit");
    result
}

pub fn verify_replay_bundle_v2(
    bundle: &ReplayBundleV2,
    policy: &ReplayTrustPolicyV2,
    resolver: &dyn ReplayTrustResolverV2,
) -> Result<(), ReplayV2Error> {
    event("replay-v2", "verify-enter");
    validate_structure(bundle)?;
    if !algorithm_allowed(bundle.algorithm, policy) {
        return reject("replay-v2 algorithm denied by trust policy");
    }

    // Authenticate opaque bytes before decoding their request/receipt meaning.
    let unsigned = unsigned_payload(bundle)?;
    let expected_payload_digest = domain_sha256(PAYLOAD_DOMAIN, &unsigned);
    if !constant_time_eq(&expected_payload_digest, &bundle.payload_digest) {
        return reject("replay-v2 payload digest mismatch");
    }
    let message = authenticated_message(bundle)?;
    if !resolver.verify(
        bundle.algorithm,
        &bundle.key_id,
        &message,
        &bundle.authentication,
    ) {
        return reject("replay-v2 authentication failed");
    }
    event("replay-v2", "verify-authenticated");

    match bundle.payload_kind {
        ReplayPayloadKindV2::WorkerV1 => validate_semantics(bundle, policy)?,
        ReplayPayloadKindV2::ObserverPipelineV3 => {
            validate_pipeline_replay_semantics_v3(bundle, policy)?
        }
    }
    event("replay-v2", "verify-exit");
    Ok(())
}

fn unsigned_bundle(
    algorithm: ReplayAuthAlgorithmV2,
    payload_kind: ReplayPayloadKindV2,
    key_id: [u8; 32],
    signer_label: &str,
    worker_request: &[u8],
    worker_receipt: &[u8],
) -> Result<ReplayBundleV2, ReplayV2Error> {
    event("replay-v2", "unsigned-bundle-enter");
    let mut bundle = ReplayBundleV2 {
        algorithm,
        payload_kind,
        key_id,
        signer_label: signer_label.to_owned(),
        worker_request: worker_request.to_vec(),
        worker_receipt: worker_receipt.to_vec(),
        payload_digest: [0_u8; 32],
        authentication: Vec::new(),
    };
    validate_structure_without_auth(&bundle)?;
    let unsigned = unsigned_payload(&bundle)?;
    bundle.payload_digest = domain_sha256(PAYLOAD_DOMAIN, &unsigned);
    event("replay-v2", "unsigned-bundle-exit");
    Ok(bundle)
}

fn validate_semantics(
    bundle: &ReplayBundleV2,
    policy: &ReplayTrustPolicyV2,
) -> Result<(), ReplayV2Error> {
    event("replay-v2", "semantics-enter");
    let request = decode_request_frame(&bundle.worker_request)
        .map_err(|_| ReplayV2Error("authenticated replay-v2 request is invalid"))?;
    let receipt = decode_worker_receipt(&bundle.worker_receipt)
        .map_err(|_| ReplayV2Error("authenticated replay-v2 receipt is invalid"))?;
    if !constant_time_eq(&request_digest(&request), &receipt.request_digest) {
        return reject("authenticated replay-v2 request/receipt binding mismatch");
    }
    if policy.require_ready_receipt && receipt.status != NativeWorkerStatus::Ready {
        return reject("authenticated replay-v2 receipt is not ready");
    }
    if policy.require_fresh_artifact {
        let expected = build_observer_synthesis_v2_receipt()
            .map_err(|_| ReplayV2Error("failed rebuilding authenticated replay-v2 artifact"))?;
        if !constant_time_eq(&expected.canonical, &receipt.artifact) {
            return reject("authenticated replay-v2 artifact differs from fresh execution");
        }
    }
    event("replay-v2", "semantics-exit");
    Ok(())
}

fn validate_structure(bundle: &ReplayBundleV2) -> Result<(), ReplayV2Error> {
    event("replay-v2", "structure-enter");
    validate_structure_without_auth(bundle)?;
    if bundle.authentication.len() != bundle.algorithm.authentication_len() {
        return reject("replay-v2 authentication has a non-canonical length");
    }
    event("replay-v2", "structure-exit");
    Ok(())
}

fn validate_structure_without_auth(bundle: &ReplayBundleV2) -> Result<(), ReplayV2Error> {
    event("replay-v2", "structure-no-auth-enter");
    let label = bundle.signer_label.as_bytes();
    if label.is_empty()
        || label.len() > MAX_REPLAY_V2_LABEL_BYTES
        || !label
            .iter()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b':' | b'-'))
    {
        return reject("invalid replay-v2 signer label");
    }
    if bundle.worker_request.is_empty() || bundle.worker_request.len() > MAX_REPLAY_V2_REQUEST_BYTES
    {
        return reject("invalid replay-v2 request length");
    }
    let receipt_maximum = match bundle.payload_kind {
        ReplayPayloadKindV2::WorkerV1 => MAX_WORKER_FRAME_BYTES,
        ReplayPayloadKindV2::ObserverPipelineV3 => MAX_REPLAY_V2_RECEIPT_BYTES,
    };
    if bundle.worker_receipt.is_empty() || bundle.worker_receipt.len() > receipt_maximum {
        return reject("invalid replay-v2 receipt length");
    }
    event("replay-v2", "structure-no-auth-exit");
    Ok(())
}

fn unsigned_payload(bundle: &ReplayBundleV2) -> Result<Vec<u8>, ReplayV2Error> {
    event("replay-v2", "unsigned-payload-enter");
    validate_structure_without_auth(bundle)?;
    let mut payload = Vec::with_capacity(
        80 + bundle.signer_label.len() + bundle.worker_request.len() + bundle.worker_receipt.len(),
    );
    payload.extend_from_slice(&REPLAY_V2_MAGIC);
    payload.extend_from_slice(&REPLAY_V2_VERSION.to_be_bytes());
    payload.push(bundle.algorithm as u8);
    payload.push(0); // reserved flags: canonical V2 requires zero.
    payload.push(bundle.payload_kind as u8);
    payload.extend_from_slice(&bundle.key_id);
    push_u16(&mut payload, bundle.signer_label.len())?;
    payload.extend_from_slice(bundle.signer_label.as_bytes());
    push_u32(&mut payload, bundle.worker_request.len())?;
    payload.extend_from_slice(&bundle.worker_request);
    push_u32(&mut payload, bundle.worker_receipt.len())?;
    payload.extend_from_slice(&bundle.worker_receipt);
    event("replay-v2", "unsigned-payload-exit");
    Ok(payload)
}

fn authenticated_message(bundle: &ReplayBundleV2) -> Result<Vec<u8>, ReplayV2Error> {
    event("replay-v2", "auth-message-enter");
    let domain = match bundle.algorithm {
        ReplayAuthAlgorithmV2::HmacSha256 => HMAC_AUTH_DOMAIN,
        ReplayAuthAlgorithmV2::Ed25519 => ED25519_AUTH_DOMAIN,
    };
    let mut message = Vec::with_capacity(domain.len() + 1 + 32);
    message.extend_from_slice(domain);
    message.push(0);
    message.extend_from_slice(&bundle.payload_digest);
    event("replay-v2", "auth-message-exit");
    Ok(message)
}

fn decode_body(body: &[u8]) -> Result<ReplayBundleV2, ReplayV2Error> {
    event("replay-v2", "decode-body-enter");
    let mut parser = Parser::new(body);
    if parser.take(4)? != REPLAY_V2_MAGIC {
        return reject("invalid replay-v2 magic");
    }
    if parser.u16()? != REPLAY_V2_VERSION {
        return reject("unsupported replay-v2 version");
    }
    let algorithm = ReplayAuthAlgorithmV2::from_wire(parser.u8()?)?;
    if parser.u8()? != 0 {
        return reject("non-zero replay-v2 reserved flags");
    }
    let payload_kind = ReplayPayloadKindV2::from_wire(parser.u8()?)?;
    let key_id = parser.array_32()?;
    let label_len = parser.u16()? as usize;
    if label_len == 0 || label_len > MAX_REPLAY_V2_LABEL_BYTES {
        return reject("invalid replay-v2 signer-label length");
    }
    let signer_label = std::str::from_utf8(parser.take(label_len)?)
        .map_err(|_| ReplayV2Error("replay-v2 signer label is not UTF-8"))?
        .to_owned();
    let request_len = parser.u32()? as usize;
    if request_len == 0 || request_len > MAX_REPLAY_V2_REQUEST_BYTES {
        return reject("invalid replay-v2 request length");
    }
    let worker_request = parser.take(request_len)?.to_vec();
    let receipt_len = parser.u32()? as usize;
    let receipt_maximum = match payload_kind {
        ReplayPayloadKindV2::WorkerV1 => MAX_WORKER_FRAME_BYTES,
        ReplayPayloadKindV2::ObserverPipelineV3 => MAX_REPLAY_V2_RECEIPT_BYTES,
    };
    if receipt_len == 0 || receipt_len > receipt_maximum {
        return reject("invalid replay-v2 receipt length");
    }
    let worker_receipt = parser.take(receipt_len)?.to_vec();
    let payload_digest = parser.array_32()?;
    let authentication_len = parser.u16()? as usize;
    if authentication_len != algorithm.authentication_len() {
        return reject("replay-v2 authentication has a non-canonical length");
    }
    let authentication = parser.take(authentication_len)?.to_vec();
    if !parser.is_empty() {
        return reject("trailing bytes inside replay-v2 bounded frame");
    }
    let bundle = ReplayBundleV2 {
        algorithm,
        payload_kind,
        key_id,
        signer_label,
        worker_request,
        worker_receipt,
        payload_digest,
        authentication,
    };
    validate_structure(&bundle)?;
    event("replay-v2", "decode-body-exit");
    Ok(bundle)
}

fn validate_hmac_key(key: &[u8]) -> Result<(), ReplayV2Error> {
    event("replay-v2", "hmac-key-validate-enter");
    if !(32..=4096).contains(&key.len()) {
        return reject("replay-v2 HMAC key must contain 32..=4096 bytes");
    }
    event("replay-v2", "hmac-key-validate-exit");
    Ok(())
}

fn algorithm_allowed(algorithm: ReplayAuthAlgorithmV2, policy: &ReplayTrustPolicyV2) -> bool {
    event("replay-v2", "policy-check");
    match algorithm {
        ReplayAuthAlgorithmV2::HmacSha256 => policy.allow_hmac_sha256,
        ReplayAuthAlgorithmV2::Ed25519 => policy.allow_ed25519,
    }
}

fn push_u16(output: &mut Vec<u8>, value: usize) -> Result<(), ReplayV2Error> {
    event("replay-v2", "push-u16");
    let value = u16::try_from(value).map_err(|_| ReplayV2Error("replay-v2 u16 overflow"))?;
    output.extend_from_slice(&value.to_be_bytes());
    Ok(())
}

fn push_u32(output: &mut Vec<u8>, value: usize) -> Result<(), ReplayV2Error> {
    event("replay-v2", "push-u32");
    let value = u32::try_from(value).map_err(|_| ReplayV2Error("replay-v2 u32 overflow"))?;
    output.extend_from_slice(&value.to_be_bytes());
    Ok(())
}

fn reject<T>(reason: &'static str) -> Result<T, ReplayV2Error> {
    event("replay-v2", "reject");
    Err(ReplayV2Error(reason))
}

struct Parser<'a> {
    bytes: &'a [u8],
    offset: usize,
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::cell::Cell;

    struct AcceptingResolver(Cell<usize>);

    impl ReplayTrustResolverV2 for AcceptingResolver {
        fn verify(
            &self,
            _algorithm: ReplayAuthAlgorithmV2,
            _key_id: &[u8; 32],
            _authenticated_message: &[u8],
            _authentication: &[u8],
        ) -> bool {
            event("replay-v2-test", "resolver-called");
            self.0.set(self.0.get() + 1);
            true
        }
    }

    #[test]
    fn validly_authenticated_pipeline_kind_reaches_semantic_rejection() {
        let key = [0x42; 32];
        let mut bundle = unsigned_bundle(
            ReplayAuthAlgorithmV2::HmacSha256,
            ReplayPayloadKindV2::ObserverPipelineV3,
            [0x18; 32],
            "semantic-order",
            b"authenticated-but-not-a-pipeline-request",
            b"authenticated-but-not-a-pipeline-result",
        )
        .unwrap();
        bundle.authentication =
            hmac_sha256(&key, &authenticated_message(&bundle).unwrap()).to_vec();
        let resolver = AcceptingResolver(Cell::new(0));
        assert!(
            verify_replay_bundle_v2(&bundle, &ReplayTrustPolicyV2::hmac_only(), &resolver,)
                .is_err()
        );
        assert_eq!(resolver.0.get(), 1);
    }
}

impl<'a> Parser<'a> {
    fn new(bytes: &'a [u8]) -> Self {
        event("replay-v2", "parser-new");
        Self { bytes, offset: 0 }
    }

    fn take(&mut self, count: usize) -> Result<&'a [u8], ReplayV2Error> {
        event("replay-v2", "parser-take");
        let end = self
            .offset
            .checked_add(count)
            .ok_or(ReplayV2Error("replay-v2 parser offset overflow"))?;
        let slice = self
            .bytes
            .get(self.offset..end)
            .ok_or(ReplayV2Error("truncated replay-v2 field"))?;
        self.offset = end;
        Ok(slice)
    }

    fn u8(&mut self) -> Result<u8, ReplayV2Error> {
        event("replay-v2", "parser-u8");
        Ok(self.take(1)?[0])
    }

    fn u16(&mut self) -> Result<u16, ReplayV2Error> {
        event("replay-v2", "parser-u16");
        let mut bytes = [0_u8; 2];
        bytes.copy_from_slice(self.take(2)?);
        Ok(u16::from_be_bytes(bytes))
    }

    fn u32(&mut self) -> Result<u32, ReplayV2Error> {
        event("replay-v2", "parser-u32");
        let mut bytes = [0_u8; 4];
        bytes.copy_from_slice(self.take(4)?);
        Ok(u32::from_be_bytes(bytes))
    }

    fn array_32(&mut self) -> Result<[u8; 32], ReplayV2Error> {
        event("replay-v2", "parser-array32");
        let mut bytes = [0_u8; 32];
        bytes.copy_from_slice(self.take(32)?);
        Ok(bytes)
    }

    fn is_empty(&self) -> bool {
        event("replay-v2", "parser-empty");
        self.offset == self.bytes.len()
    }
}
