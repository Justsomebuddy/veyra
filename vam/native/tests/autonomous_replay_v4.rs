//! Exact autonomous replay-v4 and hostile mutation tests.

use ed25519_dalek::SigningKey;
use std::io::Write;
use std::process::{Command, Stdio};

use vam_native::observer_synthesis::{
    differential_joint_search, enumerate_representation_family, FiniteDomainV1,
    JointSynthesisLimits, NamedObserverBaselineV1, NativePartitionTaskId, ObserverGapPolicyV1,
    ObserverGapRequestV1, ObserverGrammarProfileId, ObserverSynthesisPipelineRequestV3,
    TransportOpV1, TransportTermV1,
};
use vam_native::observer_worker::{
    build_autonomous_replay_package_v4, decode_autonomous_replay_package_v4_bytes,
    encode_autonomous_replay_package_v4, verify_autonomous_replay_package_v4, ManifestEntryV4,
    ManifestKindV4, WorkerPolicyManifestV4,
};

fn request() -> ObserverSynthesisPipelineRequestV3 {
    let limits = JointSynthesisLimits::default();
    let winner = differential_joint_search(
        NativePartitionTaskId::XorParity,
        ObserverGrammarProfileId::ParityV2,
        limits,
    )
    .unwrap()
    .oracle
    .winner
    .unwrap();
    let transform =
        &enumerate_representation_family().unwrap().transforms[winner.transform_ordinal];
    ObserverSynthesisPipelineRequestV3 {
        gap_request: ObserverGapRequestV1 {
            task_id: NativePartitionTaskId::XorParity,
            grammar_profile_id: ObserverGrammarProfileId::ParityV2,
            joint_limits: limits,
            baselines: vec![NamedObserverBaselineV1 {
                name: "input".to_owned(),
                observer_ordinal: 0,
            }],
            policy: ObserverGapPolicyV1::default(),
            information_loss_penalty: 0,
        },
        transports: vec![TransportTermV1 {
            source: FiniteDomainV1::new("legacy-four-abstract-states-v1", 4).unwrap(),
            target: FiniteDomainV1::new("bounded-recurrence-encoding-0-8-v1", 9).unwrap(),
            op: TransportOpV1::CanonicalEncode(
                transform
                    .permutation()
                    .into_iter()
                    .map(|value| u16::from(value) + u16::from(transform.shift()))
                    .collect(),
            ),
        }],
    }
}

fn manifests() -> Vec<ManifestEntryV4> {
    vec![
        ManifestEntryV4 {
            kind: ManifestKindV4::Toolchain,
            name: "rustc-1.83.0".to_owned(),
            digest: [0x22; 32],
        },
        ManifestEntryV4 {
            kind: ManifestKindV4::Source,
            name: "vam/native/src/observer_synthesis/pipeline_v3.rs".to_owned(),
            digest: [0x11; 32],
        },
    ]
}

#[test]
fn exact_package_roundtrips_and_rebuilds_without_producer_state() {
    let key = SigningKey::from_bytes(&[0x41; 32]);
    let package = build_autonomous_replay_package_v4(
        &request(),
        "portable-v4",
        manifests(),
        WorkerPolicyManifestV4::not_executed(),
        &key,
    )
    .unwrap();
    let encoded = encode_autonomous_replay_package_v4(&package).unwrap();
    let decoded = decode_autonomous_replay_package_v4_bytes(&encoded).unwrap();
    assert_eq!(decoded, package);
    verify_autonomous_replay_package_v4(&decoded, key.verifying_key().to_bytes()).unwrap();
    assert_ne!(package.grammar_registry_root, [0; 32]);
    assert_ne!(package.transport_set_root, [0; 32]);
}

#[test]
fn signature_manifest_and_inner_mutations_fail_closed() {
    let key = SigningKey::from_bytes(&[0x42; 32]);
    let package = build_autonomous_replay_package_v4(
        &request(),
        "mutation-v4",
        manifests(),
        WorkerPolicyManifestV4::not_executed(),
        &key,
    )
    .unwrap();
    let public = key.verifying_key().to_bytes();

    let mut signature = package.clone();
    signature.signature[0] ^= 1;
    assert!(verify_autonomous_replay_package_v4(&signature, public).is_err());

    let mut manifest = package.clone();
    manifest.manifests[0].digest[0] ^= 1;
    assert!(verify_autonomous_replay_package_v4(&manifest, public).is_err());

    let mut inner = package.clone();
    let last = inner.inner_vor2.len() - 1;
    inner.inner_vor2[last] ^= 1;
    assert!(verify_autonomous_replay_package_v4(&inner, public).is_err());

    let wrong = SigningKey::from_bytes(&[0x43; 32]);
    assert!(
        verify_autonomous_replay_package_v4(&package, wrong.verifying_key().to_bytes()).is_err()
    );
}

#[test]
fn decoding_rejects_trailing_and_noncanonical_manifest_rows() {
    let key = SigningKey::from_bytes(&[0x44; 32]);
    let package = build_autonomous_replay_package_v4(
        &request(),
        "decode-v4",
        manifests(),
        WorkerPolicyManifestV4::not_executed(),
        &key,
    )
    .unwrap();
    let mut encoded = encode_autonomous_replay_package_v4(&package).unwrap();
    encoded.push(0);
    assert!(decode_autonomous_replay_package_v4_bytes(&encoded).is_err());

    let duplicate = vec![
        ManifestEntryV4 {
            kind: ManifestKindV4::Source,
            name: "same".to_owned(),
            digest: [1; 32],
        },
        ManifestEntryV4 {
            kind: ManifestKindV4::Source,
            name: "same".to_owned(),
            digest: [1; 32],
        },
    ];
    assert!(build_autonomous_replay_package_v4(
        &request(),
        "duplicate-v4",
        duplicate,
        WorkerPolicyManifestV4::not_executed(),
        &key,
    )
    .is_err());

    for hostile_name in [
        "/absolute/source.rs",
        "../outside.rs",
        "src/../outside.rs",
        "C:/host/source.rs",
    ] {
        let hostile = vec![
            ManifestEntryV4 {
                kind: ManifestKindV4::Source,
                name: hostile_name.to_owned(),
                digest: [2; 32],
            },
            ManifestEntryV4 {
                kind: ManifestKindV4::Toolchain,
                name: "rustc-1.83.0".to_owned(),
                digest: [3; 32],
            },
        ];
        assert!(build_autonomous_replay_package_v4(
            &request(),
            "hostile-path-v4",
            hostile,
            WorkerPolicyManifestV4::not_executed(),
            &key,
        )
        .is_err());
    }
}

#[test]
fn independent_cli_verifies_stdin_and_rejects_wrong_key() {
    let key = SigningKey::from_bytes(&[0x45; 32]);
    let package = build_autonomous_replay_package_v4(
        &request(),
        "cli-v4",
        manifests(),
        WorkerPolicyManifestV4::not_executed(),
        &key,
    )
    .unwrap();
    let encoded = encode_autonomous_replay_package_v4(&package).unwrap();
    let public = key
        .verifying_key()
        .to_bytes()
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect::<String>();

    let mut child = Command::new(env!("CARGO_BIN_EXE_vam-observer-replay-v4"))
        .arg("verify-ed25519")
        .arg(&public)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .unwrap();
    child.stdin.take().unwrap().write_all(&encoded).unwrap();
    let output = child.wait_with_output().unwrap();
    assert!(output.status.success());
    assert_eq!(String::from_utf8_lossy(&output.stdout).trim(), "verified");

    let wrong = "00".repeat(32);
    let mut child = Command::new(env!("CARGO_BIN_EXE_vam-observer-replay-v4"))
        .arg("verify-ed25519")
        .arg(wrong)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
        .unwrap();
    child.stdin.take().unwrap().write_all(&encoded).unwrap();
    assert!(!child.wait().unwrap().success());
}
