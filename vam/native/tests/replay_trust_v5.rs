//! Bounded threshold and key-rotation tests for replay trust v5.

use ed25519_dalek::{Signature, SigningKey, Verifier, VerifyingKey};
use vam_native::observer_worker::{
    sign_replay_message_v5, verify_replay_threshold_v5, ReplaySignatureV5, ReplayTrustKeyV5,
    ReplayTrustPolicyV5,
};

fn key(seed: u8, from: u64, through: u64) -> (SigningKey, ReplayTrustKeyV5) {
    let signing = SigningKey::from_bytes(&[seed; 32]);
    let trust = ReplayTrustKeyV5::new(signing.verifying_key().to_bytes(), from, through).unwrap();
    (signing, trust)
}

#[test]
fn threshold_accepts_unique_active_keys_independent_of_input_key_order() {
    let (first, first_trust) = key(1, 5, 10);
    let (second, second_trust) = key(2, 7, 12);
    let (_, third_trust) = key(3, 8, 20);
    let policy =
        ReplayTrustPolicyV5::new(8, 2, vec![third_trust, second_trust, first_trust]).unwrap();
    let message = b"bounded-v5-message";
    let mut signatures = vec![
        sign_replay_message_v5(&second, message).unwrap(),
        sign_replay_message_v5(&first, message).unwrap(),
    ];
    signatures.sort();
    verify_replay_threshold_v5(&policy, &signatures, message).unwrap();
}

#[test]
fn threshold_rotation_and_mutations_fail_closed() {
    let (first, first_trust) = key(4, 1, 4);
    let (second, second_trust) = key(5, 4, 8);
    assert!(ReplayTrustPolicyV5::new(2, 2, vec![first_trust, second_trust]).is_err());
    let policy = ReplayTrustPolicyV5::new(4, 2, vec![first_trust, second_trust]).unwrap();
    let message = b"rotation-overlap";
    let mut one = vec![sign_replay_message_v5(&first, message).unwrap()];
    assert!(verify_replay_threshold_v5(&policy, &one, message).is_err());
    one.push(sign_replay_message_v5(&second, message).unwrap());
    one.sort();
    assert!(verify_replay_threshold_v5(&policy, &one, b"mutated").is_err());
    let duplicate = vec![one[0], one[0]];
    assert!(verify_replay_threshold_v5(&policy, &duplicate, message).is_err());
}

#[test]
fn unknown_and_out_of_window_signatures_are_rejected() {
    let (trusted, trusted_key) = key(6, 10, 20);
    let (unknown, _) = key(7, 10, 20);
    let message = b"external-policy";
    let policy = ReplayTrustPolicyV5::new(10, 1, vec![trusted_key]).unwrap();
    let unknown_signature = vec![sign_replay_message_v5(&unknown, message).unwrap()];
    assert!(verify_replay_threshold_v5(&policy, &unknown_signature, message).is_err());
    let expired_policy = ReplayTrustPolicyV5::new(20, 1, vec![trusted_key]).unwrap();
    let trusted_signature = vec![sign_replay_message_v5(&trusted, message).unwrap()];
    verify_replay_threshold_v5(&expired_policy, &trusted_signature, message).unwrap();
    assert!(ReplayTrustPolicyV5::new(21, 1, vec![trusted_key]).is_err());
}

#[test]
fn key_ids_and_policy_inputs_are_canonical_and_bounded() {
    let (_, first) = key(8, 0, 10);
    assert_eq!(first.key_id(), first.key_id());
    assert_eq!(first.valid_from_epoch(), 0);
    assert_eq!(first.valid_through_epoch(), 10);
    let policy = ReplayTrustPolicyV5::new(5, 1, vec![first]).unwrap();
    assert_eq!(policy.verification_epoch(), 5);
    assert_eq!(policy.threshold(), 1);
    assert_eq!(policy.keys(), &[first]);
    assert!(ReplayTrustKeyV5::new(first.public_key(), 11, 10).is_err());
    assert!(ReplayTrustPolicyV5::new(5, 1, vec![first, first]).is_err());
}

#[test]
fn weak_identity_key_and_message_independent_forgery_are_rejected() {
    let mut identity = [0u8; 32];
    identity[0] = 1;

    // Under loose Ed25519 verification, A=identity, R=basepoint, S=1 is
    // independent of the message. Demonstrate that exact hostile vector, then
    // require V5 to reject A before it can enter a policy.
    let mut forged_bytes = [0u8; 64];
    forged_bytes[..32].fill(0x66);
    forged_bytes[0] = 0x58;
    forged_bytes[32] = 1;
    let weak_verifier = VerifyingKey::from_bytes(&identity).unwrap();
    let weak_signature = Signature::from_bytes(&forged_bytes);
    assert!(weak_verifier
        .verify(b"first-message", &weak_signature)
        .is_ok());
    assert!(weak_verifier
        .verify(b"different-message", &weak_signature)
        .is_ok());
    assert!(weak_verifier
        .verify_strict(b"first-message", &weak_signature)
        .is_err());
    assert!(ReplayTrustKeyV5::new(identity, 0, 0).is_err());
    assert!(ReplayTrustKeyV5::new([0; 32], 0, 0).is_err());

    let (_, sound_key) = key(9, 0, 0);
    let forged = ReplaySignatureV5::from_parts(sound_key.key_id(), forged_bytes);
    let sound_policy = ReplayTrustPolicyV5::new(0, 1, vec![sound_key]).unwrap();
    assert!(verify_replay_threshold_v5(&sound_policy, &[forged], b"arbitrary-message").is_err());
}
