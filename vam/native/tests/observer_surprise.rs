//! Public-crate checks for the finite native surprise receipt.

use vam_native::observer_synthesis::{
    build_zero_positive_surprise_receipt, canonical_native_surprise_receipt_bytes,
    native_surprise_receipt_from_run, replay_native_surprise_receipt,
    synthesize_zero_positive_surprise, BudgetLimits, SynthesisStatus, DEFAULT_CANDIDATES,
    DEFAULT_CANONICAL_BYTES, DEFAULT_CATALOG_DIGEST,
};

const PYTHON_RUST_VECTOR: &str =
    include_str!("../../../tests/fixtures/observer_synthesis_python_rust_v1.json");

#[test]
fn public_api_builds_and_replays_one_exact_receipt() {
    let first = build_zero_positive_surprise_receipt().unwrap();
    let second = build_zero_positive_surprise_receipt().unwrap();
    assert_eq!(first, second);
    assert_eq!(
        first.receipt_digest,
        "b7bbfdfdfbf33fc1bae1cd58ec7da126d88b90558552bddccd59f1ba48cb9547"
    );
    assert_eq!(first.score.surface_saving, 0);
    assert_eq!(first.score.hidden_saving, 1);
    assert_eq!(first.score.class_saving, 1);
    assert_eq!(first.winner_ordinal, 1);
    assert_eq!(replay_native_surprise_receipt(&first).unwrap(), first);
    assert_eq!(
        canonical_native_surprise_receipt_bytes(&first).unwrap(),
        canonical_native_surprise_receipt_bytes(&second).unwrap()
    );
}

#[test]
fn public_api_keeps_cutoff_disjoint_from_receipt() {
    let limits = BudgetLimits {
        evaluation_limit: 1,
        ..BudgetLimits::default()
    };
    let run = synthesize_zero_positive_surprise(limits).unwrap();
    assert_eq!(run.report.status, SynthesisStatus::Incomplete);
    assert!(run.witness.is_none());
    assert!(native_surprise_receipt_from_run(&run).is_err());
}

#[test]
fn public_api_matches_the_shared_python_rust_identity_vector() {
    let receipt = build_zero_positive_surprise_receipt().unwrap();
    let canonical = String::from_utf8(receipt.winner_canonical)
        .unwrap()
        .replace('"', "\\\"");
    let expected = format!(
        concat!(
            "{{\"candidate_count\":{},\"canonical_bytes\":{},",
            "\"catalog_digest\":\"{}\",",
            "\"schema\":\"veyra.observer-synthesis.python-rust-vector.v1\",",
            "\"winner\":{{\"canonical\":\"{}\",\"cost\":{},\"depth\":{},",
            "\"digest\":\"{}\",\"ordinal\":{}}}}}\n"
        ),
        DEFAULT_CANDIDATES,
        DEFAULT_CANONICAL_BYTES,
        DEFAULT_CATALOG_DIGEST,
        canonical,
        receipt.winner_cost,
        receipt.winner_depth,
        receipt.winner_digest,
        receipt.winner_ordinal,
    );
    assert_eq!(PYTHON_RUST_VECTOR, expected);
}
