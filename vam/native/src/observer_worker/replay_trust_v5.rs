//! Bounded external Ed25519 trust policy for autonomous replay v5.
//!
//! Epochs are caller-selected rotation coordinates, not trusted wall time.
//! Key possession authenticates bytes only; it does not prove signer identity,
//! executable attestation, source truth, chronology, or theorem status.

use std::fmt;

use ed25519_dalek::{Signature, Signer, SigningKey, VerifyingKey};

use super::event;
use super::replay_v2::ed25519_key_id;

pub const MAX_REPLAY_TRUST_KEYS_V5: usize = 16;
pub const MAX_REPLAY_SIGNATURES_V5: usize = 16;
pub const MAX_REPLAY_SIGNATURE_MESSAGE_V5: usize = 128 * 1024;
pub const REPLAY_TRUST_V5_BOUNDARY: &str = "verification epoch is an externally selected key-rotation coordinate rather than trusted time; threshold-valid Ed25519 signatures authenticate exact bytes under externally supplied public keys but do not establish signer identity, executable attestation, source truth, chronology, or theorem evidence";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ReplayTrustV5Error(pub &'static str);

impl fmt::Display for ReplayTrustV5Error {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        event("REPLAY_TRUST_V5_ERROR_ENTER", "rendering trust error");
        let result = formatter.write_str(self.0);
        event("REPLAY_TRUST_V5_ERROR_EXIT", "trust error rendered");
        result
    }
}

impl std::error::Error for ReplayTrustV5Error {}

fn reject(reason: &'static str) -> ReplayTrustV5Error {
    event("REPLAY_TRUST_V5_REJECT", reason);
    ReplayTrustV5Error(reason)
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ReplayTrustKeyV5 {
    key_id: [u8; 32],
    public_key: [u8; 32],
    valid_from_epoch: u64,
    valid_through_epoch: u64,
}

impl ReplayTrustKeyV5 {
    pub fn new(
        public_key: [u8; 32],
        valid_from_epoch: u64,
        valid_through_epoch: u64,
    ) -> Result<Self, ReplayTrustV5Error> {
        event("REPLAY_TRUST_V5_KEY_ENTER", "constructing rotation key");
        let verifying_key =
            VerifyingKey::from_bytes(&public_key).map_err(|_| reject("replay-trust-v5-key"))?;
        if valid_from_epoch > valid_through_epoch || verifying_key.is_weak() {
            return Err(reject("replay-trust-v5-key"));
        }
        let key = Self {
            key_id: ed25519_key_id(&public_key),
            public_key,
            valid_from_epoch,
            valid_through_epoch,
        };
        event("REPLAY_TRUST_V5_KEY_EXIT", "rotation key constructed");
        Ok(key)
    }

    pub fn key_id(self) -> [u8; 32] {
        event("REPLAY_TRUST_V5_KEY_ID_ENTER", "reading bounded key id");
        let value = self.key_id;
        event("REPLAY_TRUST_V5_KEY_ID_EXIT", "bounded key id read");
        value
    }

    pub fn public_key(self) -> [u8; 32] {
        event("REPLAY_TRUST_V5_PUBLIC_ENTER", "reading public key");
        let value = self.public_key;
        event("REPLAY_TRUST_V5_PUBLIC_EXIT", "public key read");
        value
    }

    pub fn valid_from_epoch(self) -> u64 {
        event("REPLAY_TRUST_V5_FROM_ENTER", "reading rotation start");
        let value = self.valid_from_epoch;
        event("REPLAY_TRUST_V5_FROM_EXIT", "rotation start read");
        value
    }

    pub fn valid_through_epoch(self) -> u64 {
        event("REPLAY_TRUST_V5_THROUGH_ENTER", "reading rotation end");
        let value = self.valid_through_epoch;
        event("REPLAY_TRUST_V5_THROUGH_EXIT", "rotation end read");
        value
    }

    fn active(self, epoch: u64) -> bool {
        event("REPLAY_TRUST_V5_ACTIVE_ENTER", "checking rotation window");
        let active = self.valid_from_epoch <= epoch && epoch <= self.valid_through_epoch;
        event("REPLAY_TRUST_V5_ACTIVE_EXIT", "rotation window checked");
        active
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ReplayTrustPolicyV5 {
    verification_epoch: u64,
    threshold: u8,
    keys: Vec<ReplayTrustKeyV5>,
}

impl ReplayTrustPolicyV5 {
    pub fn new(
        verification_epoch: u64,
        threshold: u8,
        mut keys: Vec<ReplayTrustKeyV5>,
    ) -> Result<Self, ReplayTrustV5Error> {
        event("REPLAY_TRUST_V5_POLICY_ENTER", "constructing trust policy");
        keys.sort_by_key(|key| key.key_id);
        if keys.is_empty()
            || keys.len() > MAX_REPLAY_TRUST_KEYS_V5
            || threshold == 0
            || usize::from(threshold) > keys.len()
            || keys.windows(2).any(|pair| pair[0].key_id == pair[1].key_id)
            || keys
                .iter()
                .filter(|key| key.active(verification_epoch))
                .count()
                < usize::from(threshold)
        {
            return Err(reject("replay-trust-v5-policy"));
        }
        let policy = Self {
            verification_epoch,
            threshold,
            keys,
        };
        event("REPLAY_TRUST_V5_POLICY_EXIT", "trust policy constructed");
        Ok(policy)
    }

    pub fn verification_epoch(&self) -> u64 {
        event("REPLAY_TRUST_V5_EPOCH_ENTER", "reading verification epoch");
        let value = self.verification_epoch;
        event("REPLAY_TRUST_V5_EPOCH_EXIT", "verification epoch read");
        value
    }

    pub fn threshold(&self) -> u8 {
        event(
            "REPLAY_TRUST_V5_THRESHOLD_ENTER",
            "reading signature threshold",
        );
        let value = self.threshold;
        event("REPLAY_TRUST_V5_THRESHOLD_EXIT", "signature threshold read");
        value
    }

    pub fn keys(&self) -> &[ReplayTrustKeyV5] {
        event("REPLAY_TRUST_V5_KEYS_ENTER", "borrowing trust keys");
        let value = self.keys.as_slice();
        event("REPLAY_TRUST_V5_KEYS_EXIT", "trust keys borrowed");
        value
    }
}

pub fn canonical_replay_trust_policy_v5_bytes(policy: &ReplayTrustPolicyV5) -> Vec<u8> {
    event(
        "REPLAY_TRUST_V5_CODEC_ENTER",
        "encoding canonical trust policy",
    );
    let mut bytes = Vec::with_capacity(16 + policy.keys.len() * 80);
    bytes.extend_from_slice(&policy.verification_epoch.to_be_bytes());
    bytes.push(policy.threshold);
    bytes.push(policy.keys.len() as u8);
    for key in &policy.keys {
        bytes.extend_from_slice(&key.key_id);
        bytes.extend_from_slice(&key.public_key);
        bytes.extend_from_slice(&key.valid_from_epoch.to_be_bytes());
        bytes.extend_from_slice(&key.valid_through_epoch.to_be_bytes());
    }
    event(
        "REPLAY_TRUST_V5_CODEC_EXIT",
        "canonical trust policy encoded",
    );
    bytes
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub struct ReplaySignatureV5 {
    key_id: [u8; 32],
    signature: [u8; 64],
}

impl ReplaySignatureV5 {
    pub fn key_id(self) -> [u8; 32] {
        event("REPLAY_TRUST_V5_SIG_ID_ENTER", "reading signature key id");
        let value = self.key_id;
        event("REPLAY_TRUST_V5_SIG_ID_EXIT", "signature key id read");
        value
    }

    pub fn signature(self) -> [u8; 64] {
        event("REPLAY_TRUST_V5_SIG_ENTER", "reading signature bytes");
        let value = self.signature;
        event("REPLAY_TRUST_V5_SIG_EXIT", "signature bytes read");
        value
    }

    pub fn from_parts(key_id: [u8; 32], signature: [u8; 64]) -> Self {
        event(
            "REPLAY_TRUST_V5_SIG_PARTS_ENTER",
            "constructing decoded signature",
        );
        let value = Self { key_id, signature };
        event(
            "REPLAY_TRUST_V5_SIG_PARTS_EXIT",
            "decoded signature constructed",
        );
        value
    }
}

pub fn sign_replay_message_v5(
    signing_key: &SigningKey,
    message: &[u8],
) -> Result<ReplaySignatureV5, ReplayTrustV5Error> {
    event(
        "REPLAY_TRUST_V5_SIGN_ENTER",
        "signing bounded replay message",
    );
    if message.is_empty() || message.len() > MAX_REPLAY_SIGNATURE_MESSAGE_V5 {
        return Err(reject("replay-trust-v5-message-size"));
    }
    let public_key = signing_key.verifying_key().to_bytes();
    let value = ReplaySignatureV5 {
        key_id: ed25519_key_id(&public_key),
        signature: signing_key.sign(message).to_bytes(),
    };
    event("REPLAY_TRUST_V5_SIGN_EXIT", "bounded replay message signed");
    Ok(value)
}

pub fn verify_replay_threshold_v5(
    policy: &ReplayTrustPolicyV5,
    signatures: &[ReplaySignatureV5],
    message: &[u8],
) -> Result<(), ReplayTrustV5Error> {
    event(
        "REPLAY_TRUST_V5_VERIFY_ENTER",
        "verifying signature threshold",
    );
    if message.is_empty()
        || message.len() > MAX_REPLAY_SIGNATURE_MESSAGE_V5
        || signatures.is_empty()
        || signatures.len() > MAX_REPLAY_SIGNATURES_V5
        || signatures
            .windows(2)
            .any(|pair| pair[0].key_id >= pair[1].key_id)
    {
        return Err(reject("replay-trust-v5-signature-set"));
    }
    let mut accepted = 0usize;
    for signature in signatures {
        let key = policy
            .keys
            .binary_search_by_key(&signature.key_id, |key| key.key_id)
            .ok()
            .map(|index| policy.keys[index])
            .ok_or_else(|| reject("replay-trust-v5-untrusted-key"))?;
        if !key.active(policy.verification_epoch) {
            return Err(reject("replay-trust-v5-key-window"));
        }
        let verifying_key =
            VerifyingKey::from_bytes(&key.public_key).map_err(|_| reject("replay-trust-v5-key"))?;
        verifying_key
            .verify_strict(message, &Signature::from_bytes(&signature.signature))
            .map_err(|_| reject("replay-trust-v5-signature"))?;
        accepted += 1;
    }
    if accepted < usize::from(policy.threshold) {
        return Err(reject("replay-trust-v5-threshold"));
    }
    event(
        "REPLAY_TRUST_V5_VERIFY_EXIT",
        "signature threshold verified",
    );
    Ok(())
}
