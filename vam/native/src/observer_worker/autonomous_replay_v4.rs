//! Autonomous, externally trusted replay package for observer pipeline v3.
//!
//! VOR4 wraps one exact Ed25519-authenticated VOR2 pipeline bundle together
//! with bounded source, toolchain, and worker-policy manifests.  Both layers
//! are independently signed.  Verification authenticates opaque bytes before
//! decoding them, then performs the mandatory fresh pipeline rebuild.

use std::fmt;
use std::io::{Cursor, Read};

use ed25519_dalek::{Signature, Signer, SigningKey, VerifyingKey};

use crate::observer_synthesis::{
    run_observer_synthesis_pipeline_v3, ObserverSynthesisPipelineRequestV3, PipelineStatusV3,
};

use super::digest::{constant_time_eq, domain_sha256};
use super::event;
use super::pipeline_replay_v3::{
    build_ed25519_observer_pipeline_bundle_v3, canonical_observer_pipeline_result_v3_bytes,
    decode_observer_pipeline_request_v3, encode_observer_pipeline_request_v3,
};
use super::replay_v2::{
    decode_replay_bundle_v2_bytes, ed25519_key_id, encode_replay_bundle_v2,
    verify_replay_bundle_v2, Ed25519ReplayTrustV2, ReplayPayloadKindV2, ReplayTrustPolicyV2,
};
use super::supervisor_v4::{
    worker_v4_request_digest, worker_v4_result_digest, IsolationProfileV4,
    ObserverWorkerControlsV4, ObserverWorkerReceiptV4,
};

pub const AUTONOMOUS_REPLAY_V4_MAGIC: [u8; 4] = *b"VOR4";
pub const AUTONOMOUS_REPLAY_V4_VERSION: u16 = 4;
pub const MAX_AUTONOMOUS_REPLAY_V4_BYTES: usize = 64 * 1024;
pub const MAX_AUTONOMOUS_MANIFEST_ROWS_V4: usize = 64;
pub const AUTONOMOUS_REPLAY_V4_SCHEMA: &str = "veyra.observer-replay.autonomous.v4";
pub const AUTONOMOUS_REPLAY_V4_BOUNDARY: &str = "a valid VOR4 package authenticates bounded manifest and VOR2 bytes under an externally supplied Ed25519 key and exactly rebuilds the finite observer pipeline; manifest labels remain signed declarations, not source retrieval, executable attestation, trusted time, signer identity, sandbox proof, or theorem evidence";

const PACKAGE_DOMAIN: &[u8] = b"veyra.observer-replay.autonomous.v4.package";
const SIGNATURE_DOMAIN: &[u8] = b"veyra.observer-replay.autonomous.v4.signature";
const TRANSPORT_ROOT_DOMAIN: &[u8] = b"veyra.observer-replay.autonomous.v4.transports";

#[derive(Clone, Copy, Debug, Eq, PartialEq, Ord, PartialOrd)]
#[repr(u8)]
pub enum ManifestKindV4 {
    Source = 1,
    Toolchain = 2,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ManifestEntryV4 {
    pub kind: ManifestKindV4,
    pub name: String,
    pub digest: [u8; 32],
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(u8)]
pub enum WorkerProfileEvidenceV4 {
    NotExecuted = 0,
    Baseline = 1,
    Isolated = 2,
    Strict = 3,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct WorkerPolicyManifestV4 {
    profile: WorkerProfileEvidenceV4,
    receipt_digest: [u8; 32],
    custody_ready: bool,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct WorkerPolicyAndReceiptV4<'a> {
    policy: WorkerPolicyManifestV4,
    receipt: &'a ObserverWorkerReceiptV4,
}

impl<'a> WorkerPolicyAndReceiptV4<'a> {
    pub fn policy(self) -> WorkerPolicyManifestV4 {
        event(
            "REPLAY_V4_BOUND_POLICY_ENTER",
            "reading bound worker policy",
        );
        let policy = self.policy;
        event("REPLAY_V4_BOUND_POLICY_EXIT", "bound worker policy read");
        policy
    }

    pub fn receipt(self) -> &'a ObserverWorkerReceiptV4 {
        event(
            "REPLAY_V4_BOUND_RECEIPT_ENTER",
            "reading bound worker receipt",
        );
        let receipt = self.receipt;
        event("REPLAY_V4_BOUND_RECEIPT_EXIT", "bound worker receipt read");
        receipt
    }
}

impl WorkerPolicyManifestV4 {
    pub fn profile(self) -> WorkerProfileEvidenceV4 {
        event("REPLAY_V4_WORKER_PROFILE_ENTER", "reading worker profile");
        let profile = self.profile;
        event("REPLAY_V4_WORKER_PROFILE_EXIT", "worker profile read");
        profile
    }

    pub fn receipt_digest(self) -> [u8; 32] {
        event(
            "REPLAY_V4_WORKER_DIGEST_ENTER",
            "reading worker receipt digest",
        );
        let digest = self.receipt_digest;
        event("REPLAY_V4_WORKER_DIGEST_EXIT", "worker receipt digest read");
        digest
    }

    pub fn custody_ready(self) -> bool {
        event(
            "REPLAY_V4_WORKER_CUSTODY_ENTER",
            "reading worker custody state",
        );
        let ready = self.custody_ready;
        event("REPLAY_V4_WORKER_CUSTODY_EXIT", "worker custody state read");
        ready
    }

    pub fn not_executed() -> Self {
        event(
            "REPLAY_V4_WORKER_NONE_ENTER",
            "constructing no-worker manifest",
        );
        let result = Self {
            profile: WorkerProfileEvidenceV4::NotExecuted,
            receipt_digest: [0; 32],
            custody_ready: false,
        };
        event(
            "REPLAY_V4_WORKER_NONE_EXIT",
            "no-worker manifest constructed",
        );
        result
    }

    /// Derive a signed-manifest policy only from a completed worker receipt.
    /// Wire encoding remains internal to this module; callers cannot construct
    /// an executed claim except through a profile-complete physical receipt.
    pub fn from_worker_receipt(
        receipt: &ObserverWorkerReceiptV4,
    ) -> Result<Self, AutonomousReplayV4Error> {
        event(
            "REPLAY_V4_WORKER_RECEIPT_ENTER",
            "deriving worker policy from receipt",
        );
        let profile = match receipt.profile() {
            IsolationProfileV4::Baseline => WorkerProfileEvidenceV4::Baseline,
            IsolationProfileV4::Isolated => WorkerProfileEvidenceV4::Isolated,
            IsolationProfileV4::Strict => WorkerProfileEvidenceV4::Strict,
        };
        let custody_ready = controls_complete(receipt.profile(), receipt.controls());
        if !custody_ready || receipt.receipt_digest() == [0; 32] {
            event(
                "REPLAY_V4_WORKER_RECEIPT_REJECT",
                "worker receipt lacks profile custody",
            );
            return Err(AutonomousReplayV4Error("replay-v4-worker-receipt"));
        }
        let policy = Self {
            profile,
            receipt_digest: receipt.receipt_digest(),
            custody_ready,
        };
        validate_worker_policy(policy)?;
        event(
            "REPLAY_V4_WORKER_RECEIPT_EXIT",
            "worker policy derived from receipt",
        );
        Ok(policy)
    }

    pub fn bind_worker_receipt(
        receipt: &ObserverWorkerReceiptV4,
    ) -> Result<WorkerPolicyAndReceiptV4<'_>, AutonomousReplayV4Error> {
        event(
            "REPLAY_V4_WORKER_BIND_ENTER",
            "binding policy to worker receipt",
        );
        let policy = Self::from_worker_receipt(receipt)?;
        event(
            "REPLAY_V4_WORKER_BIND_EXIT",
            "policy bound to worker receipt",
        );
        Ok(WorkerPolicyAndReceiptV4 { policy, receipt })
    }
}

#[cfg(test)]
mod worker_policy_tests {
    use super::*;

    #[test]
    fn false_or_forged_executed_policy_is_rejected() {
        assert!(validate_worker_policy(WorkerPolicyManifestV4 {
            profile: WorkerProfileEvidenceV4::Baseline,
            receipt_digest: [1; 32],
            custody_ready: false,
        })
        .is_err());
        assert!(validate_worker_policy(WorkerPolicyManifestV4 {
            profile: WorkerProfileEvidenceV4::Strict,
            receipt_digest: [0; 32],
            custody_ready: true,
        })
        .is_err());
    }
}

fn controls_complete(profile: IsolationProfileV4, controls: ObserverWorkerControlsV4) -> bool {
    event(
        "REPLAY_V4_WORKER_CONTROLS_ENTER",
        "checking profile-required worker controls",
    );
    let common = controls.no_new_privileges
        && controls.resource_limits
        && controls.child_owned_process_group
        && controls.inherited_fd_boundary
        && controls.parent_control_readback
        && controls.wall_clock_limit
        && controls.output_limit
        && controls.process_group_custody
        && !controls.filesystem_closed;
    let complete = common
        && match profile {
            IsolationProfileV4::Baseline => {
                !controls.namespaces
                    && !controls.seccomp_allowlist
                    && !controls.cgroup_limits
                    && !controls.cgroup_membership
                    && !controls.cgroup_cleanup
            }
            IsolationProfileV4::Isolated => {
                controls.namespaces
                    && controls.seccomp_allowlist
                    && !controls.cgroup_limits
                    && !controls.cgroup_membership
                    && !controls.cgroup_cleanup
            }
            IsolationProfileV4::Strict => {
                controls.namespaces
                    && controls.seccomp_allowlist
                    && controls.cgroup_limits
                    && controls.cgroup_membership
                    && controls.cgroup_cleanup
            }
        };
    event(
        "REPLAY_V4_WORKER_CONTROLS_EXIT",
        "profile-required worker controls checked",
    );
    complete
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AutonomousReplayPackageV4 {
    pub schema: String,
    pub key_id: [u8; 32],
    pub signer_label: String,
    pub grammar_registry_root: [u8; 32],
    pub transport_set_root: [u8; 32],
    pub worker_policy: WorkerPolicyManifestV4,
    pub manifests: Vec<ManifestEntryV4>,
    pub inner_vor2: Vec<u8>,
    pub package_digest: [u8; 32],
    pub signature: [u8; 64],
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct AutonomousReplayV4Error(pub &'static str);

impl fmt::Display for AutonomousReplayV4Error {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        event("REPLAY_V4_ERROR_DISPLAY", "rendering replay-v4 error");
        formatter.write_str(self.0)
    }
}

impl std::error::Error for AutonomousReplayV4Error {}

fn reject(reason: &'static str) -> Result<(), AutonomousReplayV4Error> {
    event("REPLAY_V4_REJECT", reason);
    Err(AutonomousReplayV4Error(reason))
}

fn safe_label(value: &str, maximum: usize) -> bool {
    event("REPLAY_V4_LABEL_ENTER", "validating bounded manifest label");
    let result = !value.is_empty()
        && value.len() <= maximum
        && value.bytes().all(|byte| {
            byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-' | b'/' | b':' | b'+')
        });
    event("REPLAY_V4_LABEL_EXIT", "bounded manifest label validated");
    result
}

fn validate_manifest(rows: &[ManifestEntryV4]) -> Result<(), AutonomousReplayV4Error> {
    event("REPLAY_V4_MANIFEST_ENTER", "validating canonical manifest");
    if rows.is_empty() || rows.len() > MAX_AUTONOMOUS_MANIFEST_ROWS_V4 {
        return reject("replay-v4-manifest-count");
    }
    for (index, row) in rows.iter().enumerate() {
        let source_name_is_relative = row.kind != ManifestKindV4::Source
            || (!row.name.starts_with('/')
                && !row.name.contains(':')
                && row
                    .name
                    .split('/')
                    .all(|component| !matches!(component, "" | "." | "..")));
        if !safe_label(&row.name, 160) || !source_name_is_relative || row.digest == [0; 32] {
            return reject("replay-v4-manifest-row");
        }
        if index > 0 && rows[index - 1] >= *row {
            return reject("replay-v4-manifest-order");
        }
    }
    if !rows.iter().any(|row| row.kind == ManifestKindV4::Source)
        || !rows.iter().any(|row| row.kind == ManifestKindV4::Toolchain)
    {
        return reject("replay-v4-manifest-kinds");
    }
    event("REPLAY_V4_MANIFEST_EXIT", "canonical manifest validated");
    Ok(())
}

impl Ord for ManifestEntryV4 {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        (self.kind, &self.name, self.digest).cmp(&(other.kind, &other.name, other.digest))
    }
}

impl PartialOrd for ManifestEntryV4 {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

fn validate_worker_policy(policy: WorkerPolicyManifestV4) -> Result<(), AutonomousReplayV4Error> {
    event(
        "REPLAY_V4_POLICY_ENTER",
        "validating worker-policy manifest",
    );
    let valid = match policy.profile {
        WorkerProfileEvidenceV4::NotExecuted => {
            !policy.custody_ready && policy.receipt_digest == [0; 32]
        }
        WorkerProfileEvidenceV4::Baseline
        | WorkerProfileEvidenceV4::Isolated
        | WorkerProfileEvidenceV4::Strict => {
            policy.custody_ready && policy.receipt_digest != [0; 32]
        }
    };
    if !valid {
        return reject("replay-v4-worker-policy");
    }
    event("REPLAY_V4_POLICY_EXIT", "worker-policy manifest validated");
    Ok(())
}

fn decode_hex_root(value: &str) -> Result<[u8; 32], AutonomousReplayV4Error> {
    event("REPLAY_V4_HEX_ENTER", "decoding evidence root");
    if value.len() != 64 || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(AutonomousReplayV4Error("replay-v4-evidence-root"));
    }
    let mut result = [0; 32];
    for (index, slot) in result.iter_mut().enumerate() {
        *slot = u8::from_str_radix(&value[index * 2..index * 2 + 2], 16)
            .map_err(|_| AutonomousReplayV4Error("replay-v4-evidence-root"))?;
    }
    event("REPLAY_V4_HEX_EXIT", "evidence root decoded");
    Ok(result)
}

fn pipeline_roots(request_bytes: &[u8]) -> Result<([u8; 32], [u8; 32]), AutonomousReplayV4Error> {
    event("REPLAY_V4_ROOTS_ENTER", "rebuilding pipeline roots");
    let request = decode_observer_pipeline_request_v3(request_bytes)
        .map_err(|_| AutonomousReplayV4Error("replay-v4-request"))?;
    let result = run_observer_synthesis_pipeline_v3(&request)
        .map_err(|_| AutonomousReplayV4Error("replay-v4-rebuild"))?;
    if result.status != PipelineStatusV3::Ready {
        return Err(AutonomousReplayV4Error("replay-v4-result-not-ready"));
    }
    let evidence = result
        .evidence
        .ok_or(AutonomousReplayV4Error("replay-v4-evidence-missing"))?;
    let registry = decode_hex_root(&evidence.grammar_registry_digest)?;
    let mut body = Vec::new();
    for row in evidence.transports {
        body.extend_from_slice(&(row.ordinal as u32).to_be_bytes());
        body.extend_from_slice(row.transport_digest.as_bytes());
        body.push(match row.information_class {
            crate::observer_synthesis::TransportInformationClassV1::Bijection => 1,
            crate::observer_synthesis::TransportInformationClassV1::Injection => 2,
            crate::observer_synthesis::TransportInformationClassV1::Loss => 3,
        });
        body.extend_from_slice(&row.collision_count.to_be_bytes());
        body.extend_from_slice(&row.cost.to_be_bytes());
    }
    let transports = domain_sha256(TRANSPORT_ROOT_DOMAIN, &body);
    event("REPLAY_V4_ROOTS_EXIT", "pipeline roots rebuilt");
    Ok((registry, transports))
}

fn push_u16(output: &mut Vec<u8>, value: usize) -> Result<(), AutonomousReplayV4Error> {
    event("REPLAY_V4_ENCODE_U16", "encoding bounded u16");
    output.extend_from_slice(
        &u16::try_from(value)
            .map_err(|_| AutonomousReplayV4Error("replay-v4-u16"))?
            .to_be_bytes(),
    );
    Ok(())
}

fn push_u32(output: &mut Vec<u8>, value: usize) -> Result<(), AutonomousReplayV4Error> {
    event("REPLAY_V4_ENCODE_U32", "encoding bounded u32");
    output.extend_from_slice(
        &u32::try_from(value)
            .map_err(|_| AutonomousReplayV4Error("replay-v4-u32"))?
            .to_be_bytes(),
    );
    Ok(())
}

fn unsigned_bytes(package: &AutonomousReplayPackageV4) -> Result<Vec<u8>, AutonomousReplayV4Error> {
    event("REPLAY_V4_UNSIGNED_ENTER", "encoding unsigned package");
    validate_manifest(&package.manifests)?;
    validate_worker_policy(package.worker_policy)?;
    if package.schema != AUTONOMOUS_REPLAY_V4_SCHEMA
        || !safe_label(&package.signer_label, 128)
        || package.inner_vor2.is_empty()
        || package.inner_vor2.len() > 32 * 1024 + 4
    {
        return Err(AutonomousReplayV4Error("replay-v4-structure"));
    }
    let mut output = Vec::new();
    output.extend_from_slice(&AUTONOMOUS_REPLAY_V4_MAGIC);
    output.extend_from_slice(&AUTONOMOUS_REPLAY_V4_VERSION.to_be_bytes());
    push_u16(&mut output, package.schema.len())?;
    output.extend_from_slice(package.schema.as_bytes());
    output.extend_from_slice(&package.key_id);
    push_u16(&mut output, package.signer_label.len())?;
    output.extend_from_slice(package.signer_label.as_bytes());
    output.extend_from_slice(&package.grammar_registry_root);
    output.extend_from_slice(&package.transport_set_root);
    output.push(package.worker_policy.profile as u8);
    output.push(u8::from(package.worker_policy.custody_ready));
    output.extend_from_slice(&package.worker_policy.receipt_digest);
    push_u16(&mut output, package.manifests.len())?;
    for row in &package.manifests {
        output.push(row.kind as u8);
        push_u16(&mut output, row.name.len())?;
        output.extend_from_slice(row.name.as_bytes());
        output.extend_from_slice(&row.digest);
    }
    push_u32(&mut output, package.inner_vor2.len())?;
    output.extend_from_slice(&package.inner_vor2);
    event("REPLAY_V4_UNSIGNED_EXIT", "unsigned package encoded");
    Ok(output)
}

fn signature_message(unsigned: &[u8], digest: &[u8; 32]) -> Vec<u8> {
    event(
        "REPLAY_V4_SIGNATURE_MESSAGE_ENTER",
        "binding signature message",
    );
    let mut result = Vec::with_capacity(SIGNATURE_DOMAIN.len() + unsigned.len() + 32);
    result.extend_from_slice(SIGNATURE_DOMAIN);
    result.extend_from_slice(unsigned);
    result.extend_from_slice(digest);
    event(
        "REPLAY_V4_SIGNATURE_MESSAGE_EXIT",
        "signature message bound",
    );
    result
}

pub fn build_autonomous_replay_package_v4(
    request: &ObserverSynthesisPipelineRequestV3,
    signer_label: &str,
    mut manifests: Vec<ManifestEntryV4>,
    worker_policy: WorkerPolicyManifestV4,
    signing_key: &SigningKey,
) -> Result<AutonomousReplayPackageV4, AutonomousReplayV4Error> {
    event(
        "REPLAY_V4_BUILD_ENTER",
        "building autonomous replay package",
    );
    manifests.sort();
    validate_manifest(&manifests)?;
    validate_worker_policy(worker_policy)?;
    let inner = build_ed25519_observer_pipeline_bundle_v3(request, signer_label, signing_key)
        .map_err(|_| AutonomousReplayV4Error("replay-v4-inner-build"))?;
    let inner_vor2 = encode_replay_bundle_v2(&inner)
        .map_err(|_| AutonomousReplayV4Error("replay-v4-inner-encode"))?;
    let (grammar_registry_root, transport_set_root) = pipeline_roots(&inner.worker_request)?;
    let mut package = AutonomousReplayPackageV4 {
        schema: AUTONOMOUS_REPLAY_V4_SCHEMA.to_owned(),
        key_id: ed25519_key_id(&signing_key.verifying_key().to_bytes()),
        signer_label: signer_label.to_owned(),
        grammar_registry_root,
        transport_set_root,
        worker_policy,
        manifests,
        inner_vor2,
        package_digest: [0; 32],
        signature: [0; 64],
    };
    let unsigned = unsigned_bytes(&package)?;
    package.package_digest = domain_sha256(PACKAGE_DOMAIN, &unsigned);
    package.signature = signing_key
        .sign(&signature_message(&unsigned, &package.package_digest))
        .to_bytes();
    if unsigned.len() + 96 > MAX_AUTONOMOUS_REPLAY_V4_BYTES {
        return Err(AutonomousReplayV4Error("replay-v4-size"));
    }
    event("REPLAY_V4_BUILD_EXIT", "autonomous replay package built");
    Ok(package)
}

pub fn build_autonomous_replay_package_from_worker_v4(
    request: &ObserverSynthesisPipelineRequestV3,
    signer_label: &str,
    manifests: Vec<ManifestEntryV4>,
    worker: WorkerPolicyAndReceiptV4<'_>,
    signing_key: &SigningKey,
) -> Result<AutonomousReplayPackageV4, AutonomousReplayV4Error> {
    event(
        "REPLAY_V4_BUILD_WORKER_ENTER",
        "building replay package from bound worker receipt",
    );
    let policy = WorkerPolicyManifestV4::from_worker_receipt(worker.receipt())?;
    if policy != worker.policy() {
        return Err(AutonomousReplayV4Error("replay-v4-worker-binding"));
    }
    let canonical_request = encode_observer_pipeline_request_v3(request)
        .map_err(|_| AutonomousReplayV4Error("replay-v4-worker-request-encode"))?;
    if worker_v4_request_digest(&canonical_request) != worker.receipt().request_digest() {
        return Err(AutonomousReplayV4Error("replay-v4-worker-request-binding"));
    }
    let fresh = run_observer_synthesis_pipeline_v3(request)
        .map_err(|_| AutonomousReplayV4Error("replay-v4-worker-fresh-execution"))?;
    let fresh_bytes = canonical_observer_pipeline_result_v3_bytes(&fresh)
        .map_err(|_| AutonomousReplayV4Error("replay-v4-worker-fresh-encode"))?;
    if &fresh != worker.receipt().result()
        || fresh_bytes != worker.receipt().canonical_result()
        || worker_v4_result_digest(&fresh_bytes) != worker.receipt().result_digest()
    {
        return Err(AutonomousReplayV4Error("replay-v4-worker-result-binding"));
    }
    let package =
        build_autonomous_replay_package_v4(request, signer_label, manifests, policy, signing_key)?;
    event(
        "REPLAY_V4_BUILD_WORKER_EXIT",
        "replay package built from bound worker receipt",
    );
    Ok(package)
}

pub fn encode_autonomous_replay_package_v4(
    package: &AutonomousReplayPackageV4,
) -> Result<Vec<u8>, AutonomousReplayV4Error> {
    event(
        "REPLAY_V4_ENCODE_ENTER",
        "encoding autonomous replay package",
    );
    let mut body = unsigned_bytes(package)?;
    body.extend_from_slice(&package.package_digest);
    body.extend_from_slice(&package.signature);
    if body.len() > MAX_AUTONOMOUS_REPLAY_V4_BYTES {
        return Err(AutonomousReplayV4Error("replay-v4-size"));
    }
    let mut output = Vec::with_capacity(body.len() + 4);
    push_u32(&mut output, body.len())?;
    output.extend_from_slice(&body);
    event("REPLAY_V4_ENCODE_EXIT", "autonomous replay package encoded");
    Ok(output)
}

struct Decoder<'a> {
    bytes: &'a [u8],
    offset: usize,
}

impl<'a> Decoder<'a> {
    fn take(&mut self, count: usize) -> Result<&'a [u8], AutonomousReplayV4Error> {
        event("REPLAY_V4_DECODE_TAKE", "decoding bounded field");
        let end = self
            .offset
            .checked_add(count)
            .ok_or(AutonomousReplayV4Error("replay-v4-offset"))?;
        let value = self
            .bytes
            .get(self.offset..end)
            .ok_or(AutonomousReplayV4Error("replay-v4-truncated"))?;
        self.offset = end;
        Ok(value)
    }

    fn u8(&mut self) -> Result<u8, AutonomousReplayV4Error> {
        Ok(self.take(1)?[0])
    }

    fn u16(&mut self) -> Result<usize, AutonomousReplayV4Error> {
        let mut bytes = [0; 2];
        bytes.copy_from_slice(self.take(2)?);
        Ok(u16::from_be_bytes(bytes) as usize)
    }

    fn u32(&mut self) -> Result<usize, AutonomousReplayV4Error> {
        let mut bytes = [0; 4];
        bytes.copy_from_slice(self.take(4)?);
        Ok(u32::from_be_bytes(bytes) as usize)
    }

    fn array32(&mut self) -> Result<[u8; 32], AutonomousReplayV4Error> {
        let mut value = [0; 32];
        value.copy_from_slice(self.take(32)?);
        Ok(value)
    }

    fn text(&mut self, maximum: usize) -> Result<String, AutonomousReplayV4Error> {
        let length = self.u16()?;
        if length > maximum {
            return Err(AutonomousReplayV4Error("replay-v4-text-size"));
        }
        Ok(std::str::from_utf8(self.take(length)?)
            .map_err(|_| AutonomousReplayV4Error("replay-v4-text-utf8"))?
            .to_owned())
    }
}

fn decode_body(bytes: &[u8]) -> Result<AutonomousReplayPackageV4, AutonomousReplayV4Error> {
    event("REPLAY_V4_DECODE_BODY_ENTER", "decoding package body");
    let mut decoder = Decoder { bytes, offset: 0 };
    if decoder.take(4)? != AUTONOMOUS_REPLAY_V4_MAGIC
        || decoder.u16()? != AUTONOMOUS_REPLAY_V4_VERSION as usize
    {
        return Err(AutonomousReplayV4Error("replay-v4-header"));
    }
    let schema = decoder.text(128)?;
    let key_id = decoder.array32()?;
    let signer_label = decoder.text(128)?;
    let grammar_registry_root = decoder.array32()?;
    let transport_set_root = decoder.array32()?;
    let profile = match decoder.u8()? {
        0 => WorkerProfileEvidenceV4::NotExecuted,
        1 => WorkerProfileEvidenceV4::Baseline,
        2 => WorkerProfileEvidenceV4::Isolated,
        3 => WorkerProfileEvidenceV4::Strict,
        _ => return Err(AutonomousReplayV4Error("replay-v4-worker-profile")),
    };
    let custody_ready = match decoder.u8()? {
        0 => false,
        1 => true,
        _ => return Err(AutonomousReplayV4Error("replay-v4-boolean")),
    };
    let receipt_digest = decoder.array32()?;
    let row_count = decoder.u16()?;
    if row_count > MAX_AUTONOMOUS_MANIFEST_ROWS_V4 {
        return Err(AutonomousReplayV4Error("replay-v4-manifest-count"));
    }
    let mut manifests = Vec::with_capacity(row_count);
    for _ in 0..row_count {
        let kind = match decoder.u8()? {
            1 => ManifestKindV4::Source,
            2 => ManifestKindV4::Toolchain,
            _ => return Err(AutonomousReplayV4Error("replay-v4-manifest-kind")),
        };
        manifests.push(ManifestEntryV4 {
            kind,
            name: decoder.text(160)?,
            digest: decoder.array32()?,
        });
    }
    let inner_length = decoder.u32()?;
    if inner_length == 0 || inner_length > 32 * 1024 + 4 {
        return Err(AutonomousReplayV4Error("replay-v4-inner-size"));
    }
    let inner_vor2 = decoder.take(inner_length)?.to_vec();
    let package_digest = decoder.array32()?;
    let mut signature = [0; 64];
    signature.copy_from_slice(decoder.take(64)?);
    if decoder.offset != decoder.bytes.len() {
        return Err(AutonomousReplayV4Error("replay-v4-trailing"));
    }
    let package = AutonomousReplayPackageV4 {
        schema,
        key_id,
        signer_label,
        grammar_registry_root,
        transport_set_root,
        worker_policy: WorkerPolicyManifestV4 {
            profile,
            receipt_digest,
            custody_ready,
        },
        manifests,
        inner_vor2,
        package_digest,
        signature,
    };
    validate_manifest(&package.manifests)?;
    validate_worker_policy(package.worker_policy)?;
    event("REPLAY_V4_DECODE_BODY_EXIT", "package body decoded");
    Ok(package)
}

pub fn decode_autonomous_replay_package_v4<R: Read>(
    reader: &mut R,
) -> Result<AutonomousReplayPackageV4, AutonomousReplayV4Error> {
    event("REPLAY_V4_DECODE_ENTER", "reading exact autonomous package");
    let mut length = [0; 4];
    reader
        .read_exact(&mut length)
        .map_err(|_| AutonomousReplayV4Error("replay-v4-length"))?;
    let length = u32::from_be_bytes(length) as usize;
    if length == 0 || length > MAX_AUTONOMOUS_REPLAY_V4_BYTES {
        return Err(AutonomousReplayV4Error("replay-v4-size"));
    }
    let mut body = vec![0; length];
    reader
        .read_exact(&mut body)
        .map_err(|_| AutonomousReplayV4Error("replay-v4-truncated"))?;
    let mut trailing = [0; 1];
    if reader
        .read(&mut trailing)
        .map_err(|_| AutonomousReplayV4Error("replay-v4-read"))?
        != 0
    {
        return Err(AutonomousReplayV4Error("replay-v4-trailing"));
    }
    let result = decode_body(&body);
    event("REPLAY_V4_DECODE_EXIT", "exact autonomous package read");
    result
}

pub fn decode_autonomous_replay_package_v4_bytes(
    bytes: &[u8],
) -> Result<AutonomousReplayPackageV4, AutonomousReplayV4Error> {
    event(
        "REPLAY_V4_DECODE_BYTES_ENTER",
        "decoding autonomous package bytes",
    );
    let result = decode_autonomous_replay_package_v4(&mut Cursor::new(bytes));
    event(
        "REPLAY_V4_DECODE_BYTES_EXIT",
        "autonomous package bytes decoded",
    );
    result
}

pub fn verify_autonomous_replay_package_v4(
    package: &AutonomousReplayPackageV4,
    public_key: [u8; 32],
) -> Result<(), AutonomousReplayV4Error> {
    event(
        "REPLAY_V4_VERIFY_ENTER",
        "verifying autonomous replay package",
    );
    let unsigned = unsigned_bytes(package)?;
    let expected_digest = domain_sha256(PACKAGE_DOMAIN, &unsigned);
    if !constant_time_eq(&expected_digest, &package.package_digest) {
        return reject("replay-v4-package-digest");
    }
    let verifying_key = VerifyingKey::from_bytes(&public_key)
        .map_err(|_| AutonomousReplayV4Error("replay-v4-public-key"))?;
    if !constant_time_eq(&ed25519_key_id(&public_key), &package.key_id)
        || verifying_key
            .verify_strict(
                &signature_message(&unsigned, &package.package_digest),
                &Signature::from_bytes(&package.signature),
            )
            .is_err()
    {
        return reject("replay-v4-signature");
    }
    let inner = decode_replay_bundle_v2_bytes(&package.inner_vor2)
        .map_err(|_| AutonomousReplayV4Error("replay-v4-inner-decode"))?;
    if inner.payload_kind != ReplayPayloadKindV2::ObserverPipelineV3
        || !constant_time_eq(&inner.key_id, &package.key_id)
    {
        return reject("replay-v4-inner-binding");
    }
    let trust = Ed25519ReplayTrustV2::new(public_key)
        .map_err(|_| AutonomousReplayV4Error("replay-v4-inner-key"))?;
    verify_replay_bundle_v2(&inner, &ReplayTrustPolicyV2::ed25519_only(), &trust)
        .map_err(|_| AutonomousReplayV4Error("replay-v4-inner-verification"))?;
    let roots = pipeline_roots(&inner.worker_request)?;
    if !constant_time_eq(&roots.0, &package.grammar_registry_root)
        || !constant_time_eq(&roots.1, &package.transport_set_root)
    {
        return reject("replay-v4-root-binding");
    }
    event(
        "REPLAY_V4_VERIFY_EXIT",
        "autonomous replay package verified",
    );
    Ok(())
}
