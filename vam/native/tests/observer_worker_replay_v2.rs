//! Focused compatibility and adversarial tests for the bounded replay-v2 lane.

use std::cell::Cell;
use std::io::{self, Read, Write};
use std::path::Path;
use std::process::{Command, Stdio};

use ed25519_dalek::{Signature, SigningKey, VerifyingKey};
use vam_native::observer_worker::{
    build_ed25519_replay_bundle_v2, build_hmac_replay_bundle_v2, decode_replay_bundle_v2,
    decode_replay_bundle_v2_bytes, ed25519_key_id, encode_replay_bundle_v2, encode_request_frame,
    encode_worker_receipt_frame, supervise_current_executable, verify_replay_bundle_v2,
    Ed25519ReplayTrustV2, HmacReplayTrustV2, NativeWorkerRequestV1, ReplayAuthAlgorithmV2,
    ReplayTrustPolicyV2, ReplayTrustResolverV2, MAX_REPLAY_BUNDLE_V2_BYTES,
};

const HMAC_KEY: &[u8] = b"0123456789abcdef0123456789abcdef";
const HMAC_KEY_ID: [u8; 32] = [0x51; 32];

fn worker_path() -> &'static Path {
    Path::new(env!("CARGO_BIN_EXE_vam-observer-worker"))
}

fn replay_cli_path() -> &'static Path {
    Path::new(env!("CARGO_BIN_EXE_vam-observer-replay"))
}

fn hex_string(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}

fn hex<const N: usize>(input: &str) -> [u8; N] {
    assert_eq!(input.len(), N * 2);
    let mut output = [0_u8; N];
    for (index, byte) in output.iter_mut().enumerate() {
        *byte = u8::from_str_radix(&input[index * 2..index * 2 + 2], 16).unwrap();
    }
    output
}

fn fixture() -> (Vec<u8>, Vec<u8>) {
    let request = NativeWorkerRequestV1::default();
    let receipt = supervise_current_executable(worker_path(), &request).unwrap();
    (
        encode_request_frame(&request).unwrap(),
        encode_worker_receipt_frame(&receipt).unwrap(),
    )
}

#[test]
fn rfc8032_vector_and_v1_request_golden_are_stable() {
    // RFC 8032 section 7.1, test vector 1 (empty message).
    let secret = hex::<32>("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60");
    let public = hex::<32>("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a");
    let expected = hex::<64>(
        "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155\
         5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"
            .split_whitespace()
            .collect::<String>()
            .as_str(),
    );
    let signing = SigningKey::from_bytes(&secret);
    assert_eq!(signing.verifying_key().to_bytes(), public);
    let signature: Signature = ed25519_dalek::Signer::sign(&signing, b"");
    assert_eq!(signature.to_bytes(), expected);
    assert!(VerifyingKey::from_bytes(&public)
        .unwrap()
        .verify_strict(b"", &signature)
        .is_ok());

    let v1 = encode_request_frame(&NativeWorkerRequestV1::default()).unwrap();
    assert_eq!(
        v1,
        hex::<36>("00000020564f575100010101000075300000000a00000000200000000000000000005000")
    );
}

#[test]
fn hmac_and_ed25519_roundtrip_under_explicit_trust() {
    if !cfg!(target_os = "linux") {
        return;
    }
    let (request, receipt) = fixture();
    let hmac = build_hmac_replay_bundle_v2(&request, &receipt, "local-hmac", HMAC_KEY_ID, HMAC_KEY)
        .unwrap();
    let hmac_bytes = encode_replay_bundle_v2(&hmac).unwrap();
    assert!(hmac_bytes.len() <= MAX_REPLAY_BUNDLE_V2_BYTES + 4);
    let decoded_hmac = decode_replay_bundle_v2_bytes(&hmac_bytes).unwrap();
    let hmac_trust = HmacReplayTrustV2::new(HMAC_KEY_ID, HMAC_KEY).unwrap();
    verify_replay_bundle_v2(
        &decoded_hmac,
        &ReplayTrustPolicyV2::hmac_only(),
        &hmac_trust,
    )
    .unwrap();
    assert!(
        verify_replay_bundle_v2(&decoded_hmac, &ReplayTrustPolicyV2::deny_all(), &hmac_trust,)
            .is_err()
    );

    let signing_key = SigningKey::from_bytes(&[0x23; 32]);
    let ed =
        build_ed25519_replay_bundle_v2(&request, &receipt, "local-ed25519", &signing_key).unwrap();
    assert_eq!(
        ed.key_id,
        ed25519_key_id(&signing_key.verifying_key().to_bytes())
    );
    let ed_bytes = encode_replay_bundle_v2(&ed).unwrap();
    let decoded_ed = decode_replay_bundle_v2_bytes(&ed_bytes).unwrap();
    let ed_trust = Ed25519ReplayTrustV2::new(signing_key.verifying_key().to_bytes()).unwrap();
    verify_replay_bundle_v2(&decoded_ed, &ReplayTrustPolicyV2::ed25519_only(), &ed_trust).unwrap();
}

#[test]
fn mutations_wrong_keys_and_algorithm_substitution_fail_closed() {
    if !cfg!(target_os = "linux") {
        return;
    }
    let (request, receipt) = fixture();
    let bundle =
        build_hmac_replay_bundle_v2(&request, &receipt, "mutation-test", HMAC_KEY_ID, HMAC_KEY)
            .unwrap();
    let trust = HmacReplayTrustV2::new(HMAC_KEY_ID, HMAC_KEY).unwrap();
    let wrong = HmacReplayTrustV2::new(HMAC_KEY_ID, &[0x99; 32]).unwrap();
    assert!(verify_replay_bundle_v2(&bundle, &ReplayTrustPolicyV2::hmac_only(), &wrong).is_err());

    let mut authentication_mutation = bundle.clone();
    authentication_mutation.authentication[0] ^= 1;
    assert!(verify_replay_bundle_v2(
        &authentication_mutation,
        &ReplayTrustPolicyV2::hmac_only(),
        &trust,
    )
    .is_err());

    let mut encoded = encode_replay_bundle_v2(&bundle).unwrap();
    // prefix(4) + magic(4) + version(2) => algorithm byte.
    encoded[10] = ReplayAuthAlgorithmV2::Ed25519 as u8;
    assert!(decode_replay_bundle_v2_bytes(&encoded).is_err());
}

struct Fragmented<'a> {
    bytes: &'a [u8],
    offset: usize,
    width: usize,
}

impl Read for Fragmented<'_> {
    fn read(&mut self, output: &mut [u8]) -> io::Result<usize> {
        if self.offset == self.bytes.len() {
            return Ok(0);
        }
        let count = output
            .len()
            .min(self.width)
            .min(self.bytes.len() - self.offset);
        output[..count].copy_from_slice(&self.bytes[self.offset..self.offset + count]);
        self.offset += count;
        Ok(count)
    }
}

#[test]
fn streaming_is_fragment_safe_and_all_bounds_are_exact() {
    if !cfg!(target_os = "linux") {
        return;
    }
    let (request, receipt) = fixture();
    let bundle =
        build_hmac_replay_bundle_v2(&request, &receipt, "stream-test", HMAC_KEY_ID, HMAC_KEY)
            .unwrap();
    let encoded = encode_replay_bundle_v2(&bundle).unwrap();
    let mut fragmented = Fragmented {
        bytes: &encoded,
        offset: 0,
        width: 3,
    };
    assert_eq!(decode_replay_bundle_v2(&mut fragmented).unwrap(), bundle);

    assert!(decode_replay_bundle_v2_bytes(&encoded[..encoded.len() - 1]).is_err());
    let mut trailing = encoded.clone();
    trailing.push(0);
    assert!(decode_replay_bundle_v2_bytes(&trailing).is_err());
    let oversized = ((MAX_REPLAY_BUNDLE_V2_BYTES + 1) as u32).to_be_bytes();
    assert!(decode_replay_bundle_v2_bytes(&oversized).is_err());
}

struct CountingResolver {
    calls: Cell<usize>,
}

impl ReplayTrustResolverV2 for CountingResolver {
    fn verify(
        &self,
        _algorithm: ReplayAuthAlgorithmV2,
        _key_id: &[u8; 32],
        _authenticated_message: &[u8],
        _authentication: &[u8],
    ) -> bool {
        self.calls.set(self.calls.get() + 1);
        true
    }
}

#[test]
fn payload_digest_is_rejected_before_the_trust_resolver_runs() {
    if !cfg!(target_os = "linux") {
        return;
    }
    let (request, receipt) = fixture();
    let mut bundle =
        build_hmac_replay_bundle_v2(&request, &receipt, "ordering-test", HMAC_KEY_ID, HMAC_KEY)
            .unwrap();
    bundle.payload_digest[0] ^= 1;
    let resolver = CountingResolver {
        calls: Cell::new(0),
    };
    assert!(
        verify_replay_bundle_v2(&bundle, &ReplayTrustPolicyV2::hmac_only(), &resolver,).is_err()
    );
    assert_eq!(resolver.calls.get(), 0);
}

#[test]
fn ed25519_cli_verifies_stdin_and_returns_static_failure_for_mutation() {
    if !cfg!(target_os = "linux") {
        return;
    }
    let (request, receipt) = fixture();
    let signing_key = SigningKey::from_bytes(&[0x42; 32]);
    let bundle =
        build_ed25519_replay_bundle_v2(&request, &receipt, "cli-ed25519", &signing_key).unwrap();
    let encoded = encode_replay_bundle_v2(&bundle).unwrap();
    let public_key = hex_string(&signing_key.verifying_key().to_bytes());

    let mut valid = Command::new(replay_cli_path())
        .args(["verify-ed25519", &public_key])
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    valid.stdin.as_mut().unwrap().write_all(&encoded).unwrap();
    valid.stdin.take();
    let valid = valid.wait_with_output().unwrap();
    assert!(valid.status.success());
    assert_eq!(valid.stdout, b"verified\n");

    let mut mutation = encoded;
    let last = mutation.len() - 1;
    mutation[last] ^= 1;
    let mut invalid = Command::new(replay_cli_path())
        .args(["verify-ed25519", &public_key])
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    invalid
        .stdin
        .as_mut()
        .unwrap()
        .write_all(&mutation)
        .unwrap();
    invalid.stdin.take();
    let invalid = invalid.wait_with_output().unwrap();
    assert!(!invalid.status.success());
    assert_eq!(
        invalid.stderr,
        b"vam-observer-replay blocked: bundle-verification-blocked\n"
    );
}
