//! Focused canonical/authenticated replay tests for observer pipeline v3.

use std::cell::Cell;

use ed25519_dalek::SigningKey;
use vam_native::observer_synthesis::{
    differential_joint_search, enumerate_representation_family, FiniteDomainV1,
    JointSynthesisLimits, NamedObserverBaselineV1, NativePartitionTaskId, ObserverGapPolicyV1,
    ObserverGapRequestV1, ObserverGrammarProfileId, ObserverSynthesisPipelineRequestV3,
    TransportOpV1, TransportTermV1,
};
use vam_native::observer_worker::{
    build_ed25519_observer_pipeline_bundle_v3, build_hmac_observer_pipeline_bundle_v3,
    decode_observer_pipeline_request_v3, decode_replay_bundle_v2_bytes,
    encode_observer_pipeline_request_v3, encode_replay_bundle_v2, verify_replay_bundle_v2,
    Ed25519ReplayTrustV2, HmacReplayTrustV2, ReplayAuthAlgorithmV2, ReplayPayloadKindV2,
    ReplayTrustPolicyV2, ReplayTrustResolverV2,
};

const HMAC_KEY: &[u8] = b"observer-pipeline-v3-hmac-key-0001";
const HMAC_KEY_ID: [u8; 32] = [0x91; 32];

fn request() -> ObserverSynthesisPipelineRequestV3 {
    let winner = differential_joint_search(
        NativePartitionTaskId::XorParity,
        ObserverGrammarProfileId::ParityV2,
        JointSynthesisLimits::default(),
    )
    .unwrap()
    .oracle
    .winner
    .unwrap();
    let transform =
        enumerate_representation_family().unwrap().transforms[winner.transform_ordinal].clone();
    let source = FiniteDomainV1::new("legacy-four-abstract-states-v1", 4).unwrap();
    let middle = FiniteDomainV1::new("replay-middle", 4).unwrap();
    let target = FiniteDomainV1::new("bounded-recurrence-encoding-0-8-v1", 9).unwrap();
    let transforms = vec![
        TransportTermV1 {
            source: source.clone(),
            target: middle.clone(),
            op: TransportOpV1::Relabel(
                transform.permutation().into_iter().map(u16::from).collect(),
            ),
        },
        TransportTermV1 {
            source: middle.clone(),
            target: target.clone(),
            op: TransportOpV1::ShiftEmbed(u16::from(transform.shift())),
        },
    ];
    let composed = TransportTermV1 {
        source,
        target,
        op: TransportOpV1::Compose(transforms),
    };
    ObserverSynthesisPipelineRequestV3 {
        gap_request: ObserverGapRequestV1 {
            task_id: NativePartitionTaskId::XorParity,
            grammar_profile_id: ObserverGrammarProfileId::ParityV2,
            joint_limits: JointSynthesisLimits::default(),
            baselines: vec![NamedObserverBaselineV1 {
                name: "input".to_owned(),
                observer_ordinal: 0,
            }],
            policy: ObserverGapPolicyV1::default(),
            information_loss_penalty: 0,
        },
        transports: vec![composed],
    }
}

#[test]
fn recursive_request_codec_is_exact_and_trailing_bytes_fail() {
    let request = request();
    let encoded = encode_observer_pipeline_request_v3(&request).unwrap();
    assert_eq!(
        decode_observer_pipeline_request_v3(&encoded).unwrap(),
        request
    );
    let mut trailing = encoded;
    trailing.push(0);
    assert!(decode_observer_pipeline_request_v3(&trailing).is_err());
}

#[test]
fn hmac_and_ed25519_pipeline_bundles_rebuild_exactly() {
    let request = request();
    let hmac =
        build_hmac_observer_pipeline_bundle_v3(&request, "pipeline-hmac", HMAC_KEY_ID, HMAC_KEY)
            .unwrap();
    assert_eq!(hmac.payload_kind, ReplayPayloadKindV2::ObserverPipelineV3);
    let hmac = decode_replay_bundle_v2_bytes(&encode_replay_bundle_v2(&hmac).unwrap()).unwrap();
    verify_replay_bundle_v2(
        &hmac,
        &ReplayTrustPolicyV2::hmac_only(),
        &HmacReplayTrustV2::new(HMAC_KEY_ID, HMAC_KEY).unwrap(),
    )
    .unwrap();

    let signing = SigningKey::from_bytes(&[0x77; 32]);
    let ed = build_ed25519_observer_pipeline_bundle_v3(&request, "pipeline-ed", &signing).unwrap();
    verify_replay_bundle_v2(
        &ed,
        &ReplayTrustPolicyV2::ed25519_only(),
        &Ed25519ReplayTrustV2::new(signing.verifying_key().to_bytes()).unwrap(),
    )
    .unwrap();
}

#[test]
fn kind_substitution_and_control_character_labels_fail_closed() {
    let request = request();
    assert!(
        build_hmac_observer_pipeline_bundle_v3(&request, "bad\nlabel", HMAC_KEY_ID, HMAC_KEY,)
            .is_err()
    );
    let mut bundle =
        build_hmac_observer_pipeline_bundle_v3(&request, "kind-test", HMAC_KEY_ID, HMAC_KEY)
            .unwrap();
    bundle.payload_kind = ReplayPayloadKindV2::WorkerV1;
    assert!(verify_replay_bundle_v2(
        &bundle,
        &ReplayTrustPolicyV2::hmac_only(),
        &HmacReplayTrustV2::new(HMAC_KEY_ID, HMAC_KEY).unwrap(),
    )
    .is_err());
}

struct AcceptingResolver {
    calls: Cell<usize>,
}

impl ReplayTrustResolverV2 for AcceptingResolver {
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
fn unauthenticated_invalid_request_is_rejected_before_resolver() {
    let request = request();
    let mut bundle =
        build_hmac_observer_pipeline_bundle_v3(&request, "ordering-test", HMAC_KEY_ID, HMAC_KEY)
            .unwrap();
    // Make the request non-canonical without renewing the authenticated
    // envelope. Payload authentication must fail before semantic parsing.
    bundle.worker_request = b"VPR3\0\x01invalid".to_vec();
    let resolver = AcceptingResolver {
        calls: Cell::new(0),
    };
    assert!(
        verify_replay_bundle_v2(&bundle, &ReplayTrustPolicyV2::hmac_only(), &resolver,).is_err()
    );
    // Payload digest rejects before resolver because mutation was not signed.
    assert_eq!(resolver.calls.get(), 0);
}
