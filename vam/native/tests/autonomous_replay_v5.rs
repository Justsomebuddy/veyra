//! State-free signed replay-v5 threshold and hostile mutation tests.

use ed25519_dalek::SigningKey;
use std::io::Write;
use std::process::{Command, Stdio};
use vam_native::observer_synthesis::{
    synthesize_discovery_v5, DiscoveryBenchmarkIdV5, DiscoverySearchRequestV5,
};
use vam_native::observer_worker::{
    build_autonomous_replay_package_v5, decode_autonomous_replay_package_v5,
    encode_autonomous_replay_package_v5, verify_autonomous_replay_package_v5, ManifestEntryV4,
    ManifestKindV4, ReplayTrustKeyV5, ReplayTrustPolicyV5, WorkerPolicyManifestV5,
};

fn manifests() -> Vec<ManifestEntryV4> {
    vec![
        ManifestEntryV4 {
            kind: ManifestKindV4::Source,
            name: "vam/native/src/observer_synthesis/synthesis_v5.rs".to_owned(),
            digest: [0x31; 32],
        },
        ManifestEntryV4 {
            kind: ManifestKindV4::Toolchain,
            name: "rustc-1.83.0".to_owned(),
            digest: [0x32; 32],
        },
    ]
}

fn keys() -> (Vec<SigningKey>, ReplayTrustPolicyV5) {
    let signing = vec![
        SigningKey::from_bytes(&[0x51; 32]),
        SigningKey::from_bytes(&[0x52; 32]),
    ];
    let trust = signing
        .iter()
        .map(|key| ReplayTrustKeyV5::new(key.verifying_key().to_bytes(), 4, 8).unwrap())
        .collect();
    (signing, ReplayTrustPolicyV5::new(6, 2, trust).unwrap())
}

fn key_spec(key: &SigningKey) -> String {
    format!(
        "{}:4:8",
        key.verifying_key()
            .to_bytes()
            .iter()
            .map(|byte| format!("{byte:02x}"))
            .collect::<String>()
    )
}

#[test]
fn threshold_package_roundtrips_and_replays_without_producer_state() {
    let request = DiscoverySearchRequestV5::systematic(DiscoveryBenchmarkIdV5::HiddenAffine);
    let result = synthesize_discovery_v5(&request).unwrap();
    let (signing, policy) = keys();
    let package = build_autonomous_replay_package_v5(
        &request,
        &result,
        manifests(),
        WorkerPolicyManifestV5::not_executed(),
        &signing,
    )
    .unwrap();
    let encoded = encode_autonomous_replay_package_v5(&package).unwrap();
    let decoded = decode_autonomous_replay_package_v5(&encoded).unwrap();
    assert_eq!(decoded, package);
    assert_eq!(
        verify_autonomous_replay_package_v5(&decoded, &policy).unwrap(),
        result
    );
    assert_ne!(decoded.request_root(), [0; 32]);
    assert_ne!(decoded.result_root(), [0; 32]);
    assert_ne!(decoded.pruning_root(), [0; 32]);
}

#[test]
fn payload_signature_and_trailing_mutations_fail_closed() {
    let request = DiscoverySearchRequestV5::systematic(DiscoveryBenchmarkIdV5::ReflectionSymmetry);
    let result = synthesize_discovery_v5(&request).unwrap();
    let (signing, policy) = keys();
    let package = build_autonomous_replay_package_v5(
        &request,
        &result,
        manifests(),
        WorkerPolicyManifestV5::not_executed(),
        &signing,
    )
    .unwrap();
    let encoded = encode_autonomous_replay_package_v5(&package).unwrap();

    let mut payload = encoded.clone();
    payload[12] ^= 1;
    assert!(decode_autonomous_replay_package_v5(&payload)
        .and_then(|value| verify_autonomous_replay_package_v5(&value, &policy))
        .is_err());

    let mut signature = encoded.clone();
    let last = signature.len() - 1;
    signature[last] ^= 1;
    let decoded = decode_autonomous_replay_package_v5(&signature).unwrap();
    assert!(verify_autonomous_replay_package_v5(&decoded, &policy).is_err());

    let mut trailing = encoded;
    trailing.push(0);
    assert!(decode_autonomous_replay_package_v5(&trailing).is_err());
}

#[test]
fn decoder_supplied_strict_receipt_binding_cannot_bypass_signature() {
    let request = DiscoverySearchRequestV5::systematic(DiscoveryBenchmarkIdV5::HiddenAffine);
    let result = synthesize_discovery_v5(&request).unwrap();
    let (signing, policy) = keys();
    let package = build_autonomous_replay_package_v5(
        &request,
        &result,
        manifests(),
        WorkerPolicyManifestV5::not_executed(),
        &signing,
    )
    .unwrap();
    let mut encoded = encode_autonomous_replay_package_v5(&package).unwrap();

    // Outer length is four bytes. Inside the signed payload: magic/version and
    // three roots precede profile/custody, receipt/policy and receipt roots.
    let inner = 4usize;
    encoded[inner + 102] = 1;
    encoded[inner + 103] = 1;
    encoded[inner + 104..inner + 136].fill(0x41);
    encoded[inner + 136..inner + 168].fill(0x42);
    encoded.copy_within(inner + 6..inner + 38, inner + 168);
    encoded.copy_within(inner + 38..inner + 70, inner + 200);
    let forged = decode_autonomous_replay_package_v5(&encoded).unwrap();
    assert!(verify_autonomous_replay_package_v5(&forged, &policy).is_err());
}

#[test]
fn wrong_threshold_policy_and_duplicate_signer_fail_closed() {
    let request =
        DiscoverySearchRequestV5::systematic(DiscoveryBenchmarkIdV5::MisrepresentationRecovery);
    let result = synthesize_discovery_v5(&request).unwrap();
    let one = SigningKey::from_bytes(&[0x61; 32]);
    assert!(build_autonomous_replay_package_v5(
        &request,
        &result,
        manifests(),
        WorkerPolicyManifestV5::not_executed(),
        &[one.clone(), one],
    )
    .is_err());
    let excessive_signers = (0u8..17)
        .map(|index| SigningKey::from_bytes(&[index.saturating_add(1); 32]))
        .collect::<Vec<_>>();
    assert!(build_autonomous_replay_package_v5(
        &request,
        &result,
        manifests(),
        WorkerPolicyManifestV5::not_executed(),
        &excessive_signers,
    )
    .is_err());

    let (signing, _) = keys();
    let package = build_autonomous_replay_package_v5(
        &request,
        &result,
        manifests(),
        WorkerPolicyManifestV5::not_executed(),
        &signing,
    )
    .unwrap();
    let wrong = SigningKey::from_bytes(&[0x62; 32]);
    let wrong_policy = ReplayTrustPolicyV5::new(
        6,
        1,
        vec![ReplayTrustKeyV5::new(wrong.verifying_key().to_bytes(), 4, 8).unwrap()],
    )
    .unwrap();
    assert!(verify_autonomous_replay_package_v5(&package, &wrong_policy).is_err());
}

#[test]
fn state_free_cli_accepts_exact_policy_and_rejects_wrong_policy() {
    let request = DiscoverySearchRequestV5::systematic(DiscoveryBenchmarkIdV5::HiddenAffine);
    let result = synthesize_discovery_v5(&request).unwrap();
    let (signing, _) = keys();
    let package = build_autonomous_replay_package_v5(
        &request,
        &result,
        manifests(),
        WorkerPolicyManifestV5::not_executed(),
        &signing,
    )
    .unwrap();
    let encoded = encode_autonomous_replay_package_v5(&package).unwrap();
    let executable = env!("CARGO_BIN_EXE_vam-observer-replay-v5");
    let mut child = Command::new(executable)
        .args([
            "verify-threshold",
            "6",
            "2",
            &key_spec(&signing[0]),
            &key_spec(&signing[1]),
        ])
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .unwrap();
    child.stdin.take().unwrap().write_all(&encoded).unwrap();
    let output = child.wait_with_output().unwrap();
    assert!(output.status.success());
    assert_eq!(String::from_utf8_lossy(&output.stdout).trim(), "verified");

    let wrong = SigningKey::from_bytes(&[0x71; 32]);
    let mut child = Command::new(executable)
        .args(["verify-threshold", "6", "1", &key_spec(&wrong)])
        .stdin(Stdio::piped())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .unwrap();
    child.stdin.take().unwrap().write_all(&encoded).unwrap();
    assert!(!child.wait().unwrap().success());

    let identity_spec = format!("01{}:0:0", "00".repeat(31));
    let mut child = Command::new(executable)
        .args(["verify-threshold", "0", "1", &identity_spec])
        .stdin(Stdio::piped())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .unwrap();
    child.stdin.take().unwrap().write_all(&encoded).unwrap();
    assert!(!child.wait().unwrap().success());
}
