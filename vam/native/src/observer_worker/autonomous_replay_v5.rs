//! Threshold-authenticated autonomous replay package for discovery v5.
//!
//! The verifier authenticates bounded opaque payload bytes first, then decodes
//! canonical request/result bytes and independently reruns the branch-and-bound
//! proof checker. Trust policy is external and state-free.

use std::fmt;

use ed25519_dalek::SigningKey;

use crate::observer_synthesis::{
    canonical_discovery_request_v5_bytes, canonical_discovery_result_v5_bytes,
    decode_discovery_request_v5_bytes, decode_discovery_result_v5_bytes, discovery_request_v5_root,
    discovery_result_v5_root, verify_branch_bound_proof_v5, DiscoverySearchRequestV5,
    DiscoverySearchResultV5,
};

use super::autonomous_replay_v4::{ManifestEntryV4, ManifestKindV4};
use super::digest::domain_sha256;
use super::event;
use super::replay_trust_v5::{
    sign_replay_message_v5, verify_replay_threshold_v5, ReplaySignatureV5, ReplayTrustPolicyV5,
    MAX_REPLAY_SIGNATURES_V5,
};
use super::supervisor_v5::ObserverWorkerReceiptV5;

pub const AUTONOMOUS_REPLAY_V5_MAGIC: [u8; 4] = *b"VOR5";
pub const AUTONOMOUS_REPLAY_V5_VERSION: u16 = 5;
pub const MAX_AUTONOMOUS_REPLAY_V5_BYTES: usize = 128 * 1024;
pub const MAX_AUTONOMOUS_MANIFEST_ROWS_V5: usize = 64;
pub const AUTONOMOUS_REPLAY_V5_BOUNDARY: &str = "a valid VOR5 package has threshold-valid signatures under an externally supplied bounded rotation policy, exact canonical discovery request/result bytes, a result-contained pruning ledger bound again by its proof root, bounded signed source/toolchain digest declarations, and optional strict-v5 worker-policy evidence; verification reruns the finite branch-and-bound checker without producer state, but does not establish signer identity, trusted time, executable attestation, source truth, chronology, physical isolation of discovery execution, semantic completeness beyond the catalog, or theorem status";

const PAYLOAD_DOMAIN: &[u8] = b"veyra.discovery-replay.autonomous.v5.payload";
const SIGNATURE_DOMAIN: &[u8] = b"veyra.discovery-replay.autonomous.v5.signature";
const MAX_REQUEST_BYTES: usize = 4 * 1024;
const MAX_RESULT_BYTES: usize = 32 * 1024;
const MAX_LABEL_BYTES: usize = 160;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct AutonomousReplayV5Error(pub &'static str);

impl fmt::Display for AutonomousReplayV5Error {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        event("REPLAY_V5_ERROR_ENTER", "rendering replay-v5 error");
        let result = formatter.write_str(self.0);
        event("REPLAY_V5_ERROR_EXIT", "replay-v5 error rendered");
        result
    }
}

impl std::error::Error for AutonomousReplayV5Error {}

fn reject(reason: &'static str) -> AutonomousReplayV5Error {
    event("REPLAY_V5_REJECT", reason);
    AutonomousReplayV5Error(reason)
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum WorkerProfileEvidenceV5 {
    NotExecuted,
    StrictV5,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct WorkerPolicyManifestV5 {
    profile: WorkerProfileEvidenceV5,
    receipt_digest: [u8; 32],
    policy_digest: [u8; 32],
    request_root: [u8; 32],
    result_root: [u8; 32],
    custody_ready: bool,
}

impl WorkerPolicyManifestV5 {
    pub fn not_executed() -> Self {
        event(
            "REPLAY_V5_WORKER_NONE_ENTER",
            "constructing no-worker policy",
        );
        let policy = Self {
            profile: WorkerProfileEvidenceV5::NotExecuted,
            receipt_digest: [0; 32],
            policy_digest: [0; 32],
            request_root: [0; 32],
            result_root: [0; 32],
            custody_ready: false,
        };
        event("REPLAY_V5_WORKER_NONE_EXIT", "no-worker policy constructed");
        policy
    }

    fn from_worker_receipt(
        receipt: &ObserverWorkerReceiptV5,
    ) -> Result<Self, AutonomousReplayV5Error> {
        event("REPLAY_V5_WORKER_ENTER", "deriving strict-v5 worker policy");
        let controls = receipt.controls();
        let ready = controls.no_new_privileges
            && controls.resource_limits
            && controls.child_owned_process_group
            && controls.inherited_fd_boundary
            && controls.namespaces
            && controls.seccomp_allowlist
            && controls.private_mount_propagation
            && controls.tmpfs_root
            && controls.old_root_detached
            && controls.filesystem_closed
            && controls.cgroup_limits
            && controls.cgroup_membership
            && controls.parent_control_readback
            && controls.wall_clock_limit
            && controls.output_limit
            && controls.process_group_custody
            && controls.cgroup_cleanup
            && controls.rootfs_cleanup;
        if !ready
            || receipt.receipt_digest() == [0; 32]
            || receipt.isolation_policy_digest() == [0; 32]
        {
            return Err(reject("replay-v5-worker-receipt"));
        }
        let policy = Self {
            profile: WorkerProfileEvidenceV5::StrictV5,
            receipt_digest: receipt.receipt_digest(),
            policy_digest: receipt.isolation_policy_digest(),
            request_root: receipt.request_root(),
            result_root: receipt.result_root(),
            custody_ready: true,
        };
        event("REPLAY_V5_WORKER_EXIT", "strict-v5 worker policy derived");
        Ok(policy)
    }

    pub fn profile(self) -> WorkerProfileEvidenceV5 {
        event("REPLAY_V5_WORKER_PROFILE_ENTER", "reading worker profile");
        let value = self.profile;
        event("REPLAY_V5_WORKER_PROFILE_EXIT", "worker profile read");
        value
    }

    pub fn receipt_digest(self) -> [u8; 32] {
        event("REPLAY_V5_WORKER_ROOT_ENTER", "reading worker receipt root");
        let value = self.receipt_digest;
        event("REPLAY_V5_WORKER_ROOT_EXIT", "worker receipt root read");
        value
    }

    pub fn custody_ready(self) -> bool {
        event("REPLAY_V5_WORKER_READY_ENTER", "reading worker custody");
        let value = self.custody_ready;
        event("REPLAY_V5_WORKER_READY_EXIT", "worker custody read");
        value
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AutonomousReplayPackageV5 {
    request: Vec<u8>,
    result: Vec<u8>,
    request_root: [u8; 32],
    result_root: [u8; 32],
    pruning_root: [u8; 32],
    worker_policy: WorkerPolicyManifestV5,
    manifests: Vec<ManifestEntryV4>,
    payload_digest: [u8; 32],
    signatures: Vec<ReplaySignatureV5>,
}

impl AutonomousReplayPackageV5 {
    pub fn request_bytes(&self) -> &[u8] {
        event("REPLAY_V5_REQUEST_ENTER", "borrowing request bytes");
        let value = self.request.as_slice();
        event("REPLAY_V5_REQUEST_EXIT", "request bytes borrowed");
        value
    }

    pub fn result_bytes(&self) -> &[u8] {
        event("REPLAY_V5_RESULT_ENTER", "borrowing result bytes");
        let value = self.result.as_slice();
        event("REPLAY_V5_RESULT_EXIT", "result bytes borrowed");
        value
    }

    pub fn request_root(&self) -> [u8; 32] {
        event("REPLAY_V5_REQUEST_ROOT_ENTER", "reading request root");
        let value = self.request_root;
        event("REPLAY_V5_REQUEST_ROOT_EXIT", "request root read");
        value
    }

    pub fn result_root(&self) -> [u8; 32] {
        event("REPLAY_V5_RESULT_ROOT_ENTER", "reading result root");
        let value = self.result_root;
        event("REPLAY_V5_RESULT_ROOT_EXIT", "result root read");
        value
    }

    pub fn pruning_root(&self) -> [u8; 32] {
        event("REPLAY_V5_PRUNE_ROOT_ENTER", "reading pruning root");
        let value = self.pruning_root;
        event("REPLAY_V5_PRUNE_ROOT_EXIT", "pruning root read");
        value
    }

    pub fn worker_policy(&self) -> WorkerPolicyManifestV5 {
        event("REPLAY_V5_POLICY_ENTER", "reading worker policy");
        let value = self.worker_policy;
        event("REPLAY_V5_POLICY_EXIT", "worker policy read");
        value
    }

    pub fn manifests(&self) -> &[ManifestEntryV4] {
        event("REPLAY_V5_MANIFESTS_ENTER", "borrowing manifests");
        let value = self.manifests.as_slice();
        event("REPLAY_V5_MANIFESTS_EXIT", "manifests borrowed");
        value
    }

    pub fn payload_digest(&self) -> [u8; 32] {
        event("REPLAY_V5_DIGEST_ENTER", "reading payload digest");
        let value = self.payload_digest;
        event("REPLAY_V5_DIGEST_EXIT", "payload digest read");
        value
    }

    pub fn signatures(&self) -> &[ReplaySignatureV5] {
        event("REPLAY_V5_SIGNATURES_ENTER", "borrowing signatures");
        let value = self.signatures.as_slice();
        event("REPLAY_V5_SIGNATURES_EXIT", "signatures borrowed");
        value
    }
}

fn decode_hex_root(text: &str) -> Result<[u8; 32], AutonomousReplayV5Error> {
    event("REPLAY_V5_HEX_ENTER", "decoding bounded root");
    if text.len() != 64 || !text.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(reject("replay-v5-root-shape"));
    }
    let mut root = [0u8; 32];
    for (index, slot) in root.iter_mut().enumerate() {
        *slot = u8::from_str_radix(&text[index * 2..index * 2 + 2], 16)
            .map_err(|_| reject("replay-v5-root-shape"))?;
    }
    event("REPLAY_V5_HEX_EXIT", "bounded root decoded");
    Ok(root)
}

fn valid_manifest(rows: &[ManifestEntryV4]) -> bool {
    event("REPLAY_V5_MANIFEST_ENTER", "validating signed manifests");
    let valid = !rows.is_empty()
        && rows.len() <= MAX_AUTONOMOUS_MANIFEST_ROWS_V5
        && rows.windows(2).all(|pair| pair[0] < pair[1])
        && rows.iter().all(|row| {
            !row.name.is_empty()
                && row.name.len() <= MAX_LABEL_BYTES
                && row.digest != [0; 32]
                && row.name.bytes().all(|byte| {
                    byte.is_ascii_alphanumeric()
                        || matches!(byte, b'.' | b'_' | b'-' | b'/' | b':' | b'+')
                })
                && (row.kind != ManifestKindV4::Source
                    || (!row.name.starts_with('/')
                        && row
                            .name
                            .split('/')
                            .all(|part| !matches!(part, "" | "." | ".."))))
        })
        && rows.iter().any(|row| row.kind == ManifestKindV4::Source)
        && rows.iter().any(|row| row.kind == ManifestKindV4::Toolchain);
    event("REPLAY_V5_MANIFEST_EXIT", "signed manifests validated");
    valid
}

fn valid_worker(
    policy: WorkerPolicyManifestV5,
    request_root: [u8; 32],
    result_root: [u8; 32],
) -> bool {
    event(
        "REPLAY_V5_WORKER_VALIDATE_ENTER",
        "validating worker policy",
    );
    let valid = match policy.profile {
        WorkerProfileEvidenceV5::NotExecuted => {
            !policy.custody_ready
                && policy.receipt_digest == [0; 32]
                && policy.policy_digest == [0; 32]
                && policy.request_root == [0; 32]
                && policy.result_root == [0; 32]
        }
        WorkerProfileEvidenceV5::StrictV5 => {
            policy.custody_ready
                && policy.receipt_digest != [0; 32]
                && policy.policy_digest != [0; 32]
                && policy.request_root == request_root
                && policy.result_root == result_root
        }
    };
    event("REPLAY_V5_WORKER_VALIDATE_EXIT", "worker policy validated");
    valid
}

fn push_u16(bytes: &mut Vec<u8>, value: usize) -> Result<(), AutonomousReplayV5Error> {
    event("REPLAY_V5_U16_ENTER", "encoding bounded u16 length");
    let value = u16::try_from(value).map_err(|_| reject("replay-v5-length"))?;
    bytes.extend_from_slice(&value.to_be_bytes());
    event("REPLAY_V5_U16_EXIT", "bounded u16 length encoded");
    Ok(())
}

fn push_u32(bytes: &mut Vec<u8>, value: usize) -> Result<(), AutonomousReplayV5Error> {
    event("REPLAY_V5_U32_ENTER", "encoding bounded u32 length");
    let value = u32::try_from(value).map_err(|_| reject("replay-v5-length"))?;
    bytes.extend_from_slice(&value.to_be_bytes());
    event("REPLAY_V5_U32_EXIT", "bounded u32 length encoded");
    Ok(())
}

fn unsigned_bytes(package: &AutonomousReplayPackageV5) -> Result<Vec<u8>, AutonomousReplayV5Error> {
    event("REPLAY_V5_UNSIGNED_ENTER", "encoding unsigned v5 payload");
    if package.request.len() > MAX_REQUEST_BYTES
        || package.result.len() > MAX_RESULT_BYTES
        || !valid_manifest(&package.manifests)
        || !valid_worker(
            package.worker_policy,
            package.request_root,
            package.result_root,
        )
    {
        return Err(reject("replay-v5-payload"));
    }
    let mut bytes = Vec::new();
    bytes.extend_from_slice(&AUTONOMOUS_REPLAY_V5_MAGIC);
    bytes.extend_from_slice(&AUTONOMOUS_REPLAY_V5_VERSION.to_be_bytes());
    bytes.extend_from_slice(&package.request_root);
    bytes.extend_from_slice(&package.result_root);
    bytes.extend_from_slice(&package.pruning_root);
    bytes.push(match package.worker_policy.profile {
        WorkerProfileEvidenceV5::NotExecuted => 0,
        WorkerProfileEvidenceV5::StrictV5 => 1,
    });
    bytes.push(u8::from(package.worker_policy.custody_ready));
    bytes.extend_from_slice(&package.worker_policy.receipt_digest);
    bytes.extend_from_slice(&package.worker_policy.policy_digest);
    bytes.extend_from_slice(&package.worker_policy.request_root);
    bytes.extend_from_slice(&package.worker_policy.result_root);
    push_u32(&mut bytes, package.request.len())?;
    bytes.extend_from_slice(&package.request);
    push_u32(&mut bytes, package.result.len())?;
    bytes.extend_from_slice(&package.result);
    bytes.push(package.manifests.len() as u8);
    for row in &package.manifests {
        bytes.push(match row.kind {
            ManifestKindV4::Source => 1,
            ManifestKindV4::Toolchain => 2,
        });
        push_u16(&mut bytes, row.name.len())?;
        bytes.extend_from_slice(row.name.as_bytes());
        bytes.extend_from_slice(&row.digest);
    }
    event("REPLAY_V5_UNSIGNED_EXIT", "unsigned v5 payload encoded");
    Ok(bytes)
}

fn signature_message(unsigned: &[u8], digest: &[u8; 32]) -> Vec<u8> {
    event("REPLAY_V5_SIGN_MESSAGE_ENTER", "binding signature message");
    let mut message = Vec::with_capacity(SIGNATURE_DOMAIN.len() + unsigned.len() + 32);
    message.extend_from_slice(SIGNATURE_DOMAIN);
    message.extend_from_slice(unsigned);
    message.extend_from_slice(digest);
    event("REPLAY_V5_SIGN_MESSAGE_EXIT", "signature message bound");
    message
}

pub fn build_autonomous_replay_package_v5(
    request: &DiscoverySearchRequestV5,
    result: &DiscoverySearchResultV5,
    manifests: Vec<ManifestEntryV4>,
    worker_policy: WorkerPolicyManifestV5,
    signing_keys: &[SigningKey],
) -> Result<AutonomousReplayPackageV5, AutonomousReplayV5Error> {
    event("REPLAY_V5_BUILD_ENTER", "building autonomous replay v5");
    if worker_policy.profile != WorkerProfileEvidenceV5::NotExecuted {
        return Err(reject("replay-v5-worker-builder-required"));
    }
    build_autonomous_replay_package_internal_v5(
        request,
        result,
        manifests,
        worker_policy,
        signing_keys,
    )
}

pub fn build_autonomous_replay_package_from_worker_v5(
    receipt: &ObserverWorkerReceiptV5,
    manifests: Vec<ManifestEntryV4>,
    signing_keys: &[SigningKey],
) -> Result<AutonomousReplayPackageV5, AutonomousReplayV5Error> {
    event(
        "REPLAY_V5_WORKER_BUILD_ENTER",
        "building replay from strict discovery receipt",
    );
    let request_bytes = canonical_discovery_request_v5_bytes(receipt.request())
        .map_err(|_| reject("replay-v5-worker-request-encode"))?;
    let result_bytes = canonical_discovery_result_v5_bytes(receipt.result())
        .map_err(|_| reject("replay-v5-worker-result-encode"))?;
    let request_root = decode_hex_root(
        &discovery_request_v5_root(receipt.request())
            .map_err(|_| reject("replay-v5-worker-request-root"))?,
    )?;
    let result_root = decode_hex_root(
        &discovery_result_v5_root(receipt.result())
            .map_err(|_| reject("replay-v5-worker-result-root"))?,
    )?;
    if receipt.canonical_request() != request_bytes
        || receipt.canonical_result() != result_bytes
        || receipt.request_root() != request_root
        || receipt.result_root() != result_root
    {
        return Err(reject("replay-v5-worker-semantic-binding"));
    }
    let worker_policy = WorkerPolicyManifestV5::from_worker_receipt(receipt)?;
    let package = build_autonomous_replay_package_internal_v5(
        receipt.request(),
        receipt.result(),
        manifests,
        worker_policy,
        signing_keys,
    )?;
    event(
        "REPLAY_V5_WORKER_BUILD_EXIT",
        "replay built from strict discovery receipt",
    );
    Ok(package)
}

fn build_autonomous_replay_package_internal_v5(
    request: &DiscoverySearchRequestV5,
    result: &DiscoverySearchResultV5,
    mut manifests: Vec<ManifestEntryV4>,
    worker_policy: WorkerPolicyManifestV5,
    signing_keys: &[SigningKey],
) -> Result<AutonomousReplayPackageV5, AutonomousReplayV5Error> {
    event(
        "REPLAY_V5_BUILD_INTERNAL_ENTER",
        "building bound replay payload",
    );
    if signing_keys.is_empty() || signing_keys.len() > MAX_REPLAY_SIGNATURES_V5 {
        return Err(reject("replay-v5-no-signers"));
    }
    manifests.sort();
    let request_bytes = canonical_discovery_request_v5_bytes(request)
        .map_err(|_| reject("replay-v5-request-encode"))?;
    let result_bytes = canonical_discovery_result_v5_bytes(result)
        .map_err(|_| reject("replay-v5-result-encode"))?;
    if !verify_branch_bound_proof_v5(request, result)
        .map_err(|_| reject("replay-v5-proof-check"))?
    {
        return Err(reject("replay-v5-proof-invalid"));
    }
    let mut package = AutonomousReplayPackageV5 {
        request: request_bytes,
        result: result_bytes,
        request_root: decode_hex_root(
            &discovery_request_v5_root(request).map_err(|_| reject("replay-v5-request-root"))?,
        )?,
        result_root: decode_hex_root(
            &discovery_result_v5_root(result).map_err(|_| reject("replay-v5-result-root"))?,
        )?,
        pruning_root: decode_hex_root(&result.ledger.prune_proof_digest)?,
        worker_policy,
        manifests,
        payload_digest: [0; 32],
        signatures: Vec::new(),
    };
    let unsigned = unsigned_bytes(&package)?;
    package.payload_digest = domain_sha256(PAYLOAD_DOMAIN, &unsigned);
    let message = signature_message(&unsigned, &package.payload_digest);
    package.signatures = signing_keys
        .iter()
        .map(|key| sign_replay_message_v5(key, &message).map_err(|_| reject("replay-v5-sign")))
        .collect::<Result<Vec<_>, _>>()?;
    package.signatures.sort();
    if package.signatures.windows(2).any(|pair| pair[0] >= pair[1]) {
        return Err(reject("replay-v5-duplicate-signer"));
    }
    event(
        "REPLAY_V5_BUILD_INTERNAL_EXIT",
        "bound replay payload built",
    );
    Ok(package)
}

pub fn verify_autonomous_replay_package_v5(
    package: &AutonomousReplayPackageV5,
    policy: &ReplayTrustPolicyV5,
) -> Result<DiscoverySearchResultV5, AutonomousReplayV5Error> {
    event("REPLAY_V5_VERIFY_ENTER", "verifying autonomous replay v5");
    let unsigned = unsigned_bytes(package)?;
    let expected_digest = domain_sha256(PAYLOAD_DOMAIN, &unsigned);
    if expected_digest != package.payload_digest {
        return Err(reject("replay-v5-payload-digest"));
    }
    let message = signature_message(&unsigned, &expected_digest);
    verify_replay_threshold_v5(policy, &package.signatures, &message)
        .map_err(|_| reject("replay-v5-threshold-auth"))?;
    let request = decode_discovery_request_v5_bytes(&package.request)
        .map_err(|_| reject("replay-v5-request-decode"))?;
    let result = decode_discovery_result_v5_bytes(&package.result)
        .map_err(|_| reject("replay-v5-result-decode"))?;
    if canonical_discovery_request_v5_bytes(&request)
        .map_err(|_| reject("replay-v5-request-encode"))?
        != package.request
        || canonical_discovery_result_v5_bytes(&result)
            .map_err(|_| reject("replay-v5-result-encode"))?
            != package.result
        || decode_hex_root(
            &discovery_request_v5_root(&request).map_err(|_| reject("replay-v5-request-root"))?,
        )? != package.request_root
        || decode_hex_root(
            &discovery_result_v5_root(&result).map_err(|_| reject("replay-v5-result-root"))?,
        )? != package.result_root
        || decode_hex_root(&result.ledger.prune_proof_digest)? != package.pruning_root
        || !verify_branch_bound_proof_v5(&request, &result)
            .map_err(|_| reject("replay-v5-proof-check"))?
    {
        return Err(reject("replay-v5-semantic-binding"));
    }
    event("REPLAY_V5_VERIFY_EXIT", "autonomous replay v5 verified");
    Ok(result)
}

pub fn encode_autonomous_replay_package_v5(
    package: &AutonomousReplayPackageV5,
) -> Result<Vec<u8>, AutonomousReplayV5Error> {
    event("REPLAY_V5_ENCODE_ENTER", "encoding autonomous replay v5");
    if package.signatures.is_empty()
        || package.signatures.len() > MAX_REPLAY_SIGNATURES_V5
        || package.signatures.windows(2).any(|pair| pair[0] >= pair[1])
    {
        return Err(reject("replay-v5-signature-set"));
    }
    let unsigned = unsigned_bytes(package)?;
    let mut bytes = Vec::new();
    push_u32(&mut bytes, unsigned.len())?;
    bytes.extend_from_slice(&unsigned);
    bytes.extend_from_slice(&package.payload_digest);
    bytes.push(package.signatures.len() as u8);
    for signature in &package.signatures {
        bytes.extend_from_slice(&signature.key_id());
        bytes.extend_from_slice(&signature.signature());
    }
    if bytes.len() > MAX_AUTONOMOUS_REPLAY_V5_BYTES {
        return Err(reject("replay-v5-size"));
    }
    event("REPLAY_V5_ENCODE_EXIT", "autonomous replay v5 encoded");
    Ok(bytes)
}

struct Decoder<'a> {
    bytes: &'a [u8],
    cursor: usize,
}

impl<'a> Decoder<'a> {
    fn take(&mut self, count: usize) -> Result<&'a [u8], AutonomousReplayV5Error> {
        event("REPLAY_V5_TAKE_ENTER", "taking bounded encoded field");
        let end = self
            .cursor
            .checked_add(count)
            .ok_or_else(|| reject("replay-v5-overflow"))?;
        let value = self
            .bytes
            .get(self.cursor..end)
            .ok_or_else(|| reject("replay-v5-truncated"))?;
        self.cursor = end;
        event("REPLAY_V5_TAKE_EXIT", "bounded encoded field taken");
        Ok(value)
    }

    fn u8(&mut self) -> Result<u8, AutonomousReplayV5Error> {
        event("REPLAY_V5_DECODE_U8_ENTER", "decoding bounded u8");
        let value = self.take(1)?[0];
        event("REPLAY_V5_DECODE_U8_EXIT", "bounded u8 decoded");
        Ok(value)
    }

    fn u16(&mut self) -> Result<usize, AutonomousReplayV5Error> {
        event("REPLAY_V5_DECODE_U16_ENTER", "decoding bounded u16");
        let value = u16::from_be_bytes(
            self.take(2)?
                .try_into()
                .map_err(|_| reject("replay-v5-truncated"))?,
        ) as usize;
        event("REPLAY_V5_DECODE_U16_EXIT", "bounded u16 decoded");
        Ok(value)
    }

    fn u32(&mut self) -> Result<usize, AutonomousReplayV5Error> {
        event("REPLAY_V5_DECODE_U32_ENTER", "decoding bounded u32");
        let value = u32::from_be_bytes(
            self.take(4)?
                .try_into()
                .map_err(|_| reject("replay-v5-truncated"))?,
        ) as usize;
        event("REPLAY_V5_DECODE_U32_EXIT", "bounded u32 decoded");
        Ok(value)
    }

    fn root(&mut self) -> Result<[u8; 32], AutonomousReplayV5Error> {
        event("REPLAY_V5_DECODE_ROOT_ENTER", "decoding bounded root");
        let value = self
            .take(32)?
            .try_into()
            .map_err(|_| reject("replay-v5-truncated"))?;
        event("REPLAY_V5_DECODE_ROOT_EXIT", "bounded root decoded");
        Ok(value)
    }
}

pub fn decode_autonomous_replay_package_v5(
    bytes: &[u8],
) -> Result<AutonomousReplayPackageV5, AutonomousReplayV5Error> {
    event("REPLAY_V5_DECODE_ENTER", "decoding autonomous replay v5");
    if bytes.len() > MAX_AUTONOMOUS_REPLAY_V5_BYTES {
        return Err(reject("replay-v5-size"));
    }
    let mut outer = Decoder { bytes, cursor: 0 };
    let unsigned_len = outer.u32()?;
    let unsigned = outer.take(unsigned_len)?;
    let payload_digest = outer.root()?;
    let signature_count = outer.u8()? as usize;
    if signature_count == 0 || signature_count > MAX_REPLAY_SIGNATURES_V5 {
        return Err(reject("replay-v5-signature-set"));
    }
    let mut signatures = Vec::with_capacity(signature_count);
    for _ in 0..signature_count {
        signatures.push(ReplaySignatureV5::from_parts(
            outer.root()?,
            outer
                .take(64)?
                .try_into()
                .map_err(|_| reject("replay-v5-truncated"))?,
        ));
    }
    if outer.cursor != bytes.len() {
        return Err(reject("replay-v5-trailing"));
    }
    let mut decoder = Decoder {
        bytes: unsigned,
        cursor: 0,
    };
    if decoder.take(4)? != AUTONOMOUS_REPLAY_V5_MAGIC
        || u16::from_be_bytes(
            decoder
                .take(2)?
                .try_into()
                .map_err(|_| reject("replay-v5-truncated"))?,
        ) != AUTONOMOUS_REPLAY_V5_VERSION
    {
        return Err(reject("replay-v5-header"));
    }
    let request_root = decoder.root()?;
    let result_root = decoder.root()?;
    let pruning_root = decoder.root()?;
    let profile = match decoder.u8()? {
        0 => WorkerProfileEvidenceV5::NotExecuted,
        1 => WorkerProfileEvidenceV5::StrictV5,
        _ => return Err(reject("replay-v5-worker-profile")),
    };
    let custody_ready = match decoder.u8()? {
        0 => false,
        1 => true,
        _ => return Err(reject("replay-v5-worker-custody")),
    };
    let worker_policy = WorkerPolicyManifestV5 {
        profile,
        custody_ready,
        receipt_digest: decoder.root()?,
        policy_digest: decoder.root()?,
        request_root: decoder.root()?,
        result_root: decoder.root()?,
    };
    let request_len = decoder.u32()?;
    if request_len > MAX_REQUEST_BYTES {
        return Err(reject("replay-v5-request-size"));
    }
    let request = decoder.take(request_len)?.to_vec();
    let result_len = decoder.u32()?;
    if result_len > MAX_RESULT_BYTES {
        return Err(reject("replay-v5-result-size"));
    }
    let result = decoder.take(result_len)?.to_vec();
    let manifest_count = decoder.u8()? as usize;
    if manifest_count == 0 || manifest_count > MAX_AUTONOMOUS_MANIFEST_ROWS_V5 {
        return Err(reject("replay-v5-manifest-count"));
    }
    let mut manifests = Vec::with_capacity(manifest_count);
    for _ in 0..manifest_count {
        let kind = match decoder.u8()? {
            1 => ManifestKindV4::Source,
            2 => ManifestKindV4::Toolchain,
            _ => return Err(reject("replay-v5-manifest-kind")),
        };
        let length = decoder.u16()?;
        let name = String::from_utf8(decoder.take(length)?.to_vec())
            .map_err(|_| reject("replay-v5-manifest-name"))?;
        manifests.push(ManifestEntryV4 {
            kind,
            name,
            digest: decoder.root()?,
        });
    }
    if decoder.cursor != unsigned.len() {
        return Err(reject("replay-v5-unsigned-trailing"));
    }
    let package = AutonomousReplayPackageV5 {
        request,
        result,
        request_root,
        result_root,
        pruning_root,
        worker_policy,
        manifests,
        payload_digest,
        signatures,
    };
    if unsigned_bytes(&package)? != unsigned {
        return Err(reject("replay-v5-noncanonical"));
    }
    event("REPLAY_V5_DECODE_EXIT", "autonomous replay v5 decoded");
    Ok(package)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::observer_synthesis::{synthesize_discovery_v5, DiscoveryBenchmarkIdV5};

    fn manifests() -> Vec<ManifestEntryV4> {
        vec![
            ManifestEntryV4 {
                kind: ManifestKindV4::Source,
                name: "vam/native/src/observer_synthesis/synthesis_v5.rs".to_owned(),
                digest: [0x81; 32],
            },
            ManifestEntryV4 {
                kind: ManifestKindV4::Toolchain,
                name: "rustc-1.83.0".to_owned(),
                digest: [0x82; 32],
            },
        ]
    }

    #[test]
    fn strict_receipt_roots_cannot_be_rebound_to_another_request() {
        let request_a = DiscoverySearchRequestV5::systematic(DiscoveryBenchmarkIdV5::HiddenAffine);
        let request_b =
            DiscoverySearchRequestV5::systematic(DiscoveryBenchmarkIdV5::ReflectionSymmetry);
        let result_b = synthesize_discovery_v5(&request_b).unwrap();
        let worker_policy = WorkerPolicyManifestV5 {
            profile: WorkerProfileEvidenceV5::StrictV5,
            receipt_digest: [0x83; 32],
            policy_digest: [0x84; 32],
            request_root: decode_hex_root(&discovery_request_v5_root(&request_a).unwrap()).unwrap(),
            result_root: [0x85; 32],
            custody_ready: true,
        };
        let signing = SigningKey::from_bytes(&[0x86; 32]);
        assert!(build_autonomous_replay_package_internal_v5(
            &request_b,
            &result_b,
            manifests(),
            worker_policy,
            &[signing.clone()],
        )
        .is_err());
        assert!(build_autonomous_replay_package_v5(
            &request_b,
            &result_b,
            manifests(),
            worker_policy,
            &[signing],
        )
        .is_err());
    }
}
