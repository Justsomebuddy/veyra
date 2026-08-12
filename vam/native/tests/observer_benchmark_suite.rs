//! Public-crate checks for the finite benchmark-family receipt.

use vam_native::observer_synthesis::{
    build_native_benchmark_suite_receipt, canonical_native_benchmark_suite_receipt_bytes,
    replay_native_benchmark_suite_receipt, run_native_benchmark_suite, BudgetLimits,
    SynthesisStatus, MIXTURE_BENCHMARK_ID, PERMUTED_TRANSPORT_BENCHMARK_ID,
    SHIFT_TRANSPORT_BENCHMARK_ID, XOR_PARITY_BENCHMARK_ID,
};

#[test]
fn public_suite_replays_exact_positive_negative_and_transport_evidence() {
    let first = build_native_benchmark_suite_receipt().unwrap();
    let second = build_native_benchmark_suite_receipt().unwrap();
    assert_eq!(first, second);
    assert_eq!(
        first.receipt_digest,
        "5ff3518bf37060ac410c1a80765235da2d4758e6f2d2497ac5c38cfafbf96a17"
    );
    assert_eq!(first.rows.len(), 4);
    assert!(first
        .rows
        .iter()
        .all(|row| !row.wall_clock_enforced && !row.process_as_enforced));
    assert_eq!(
        first
            .rows
            .iter()
            .map(|row| (row.benchmark_id, row.status))
            .collect::<Vec<_>>(),
        vec![
            (MIXTURE_BENCHMARK_ID, SynthesisStatus::Found),
            (XOR_PARITY_BENCHMARK_ID, SynthesisStatus::Exhausted),
            (SHIFT_TRANSPORT_BENCHMARK_ID, SynthesisStatus::Found),
            (PERMUTED_TRANSPORT_BENCHMARK_ID, SynthesisStatus::Exhausted),
        ]
    );
    assert_eq!(first.rows[0].score.surface_hits, 3);
    assert_eq!(first.rows[0].score.winner_hits, Some(6));
    assert_eq!(first.rows[0].score.class_saving, Some(2));
    assert_eq!(first.rows[0].winner.as_ref().unwrap().cost, 1);
    let shifted_winner = first.rows[2].winner.as_ref().unwrap();
    assert_eq!(
        (
            shifted_winner.ordinal,
            shifted_winner.cost,
            shifted_winner.depth
        ),
        (4, 2, 2)
    );
    assert_eq!(
        shifted_winner.digest,
        "12ff5359b1e666a2a397570bb26387a9a36033ee23603b0c8741a52065677bbc"
    );
    assert_eq!(first.shift_cost_delta, 1);

    let parity = first.rows[1].marginal_balance.as_ref().unwrap();
    assert!(parity.balanced);
    assert_eq!(parity.bit_order, ["feature_a", "feature_b"]);
    assert_eq!(parity.counts, [[[1, 1], [1, 1]], [[1, 1], [1, 1]]]);

    assert_eq!(first.transport_rows.len(), 2);
    assert!(first
        .transport_rows
        .iter()
        .all(|row| !row.transfer_preserved));
    assert_eq!(
        first.transport_rows[0].transfer_case_results,
        [false, false, false, true, true, true]
    );
    assert_eq!(
        first.transport_rows[1].transfer_case_results,
        [true, false, false, false, false, true]
    );
    assert_eq!(first.transport_rows[0].target_cost_delta, Some(1));
    assert_eq!(
        first.transport_rows[1].target_resynthesis_status,
        SynthesisStatus::Exhausted
    );
    assert!(first.transport_rows[1].target_winner_digest.is_none());
    assert_eq!(
        replay_native_benchmark_suite_receipt(&first).unwrap(),
        first
    );
    assert_eq!(
        canonical_native_benchmark_suite_receipt_bytes(&first).unwrap(),
        canonical_native_benchmark_suite_receipt_bytes(&second).unwrap()
    );
    let canonical =
        String::from_utf8(canonical_native_benchmark_suite_receipt_bytes(&first).unwrap()).unwrap();
    let permutation = canonical
        .find("\"permutation_discoverability_preserved\"")
        .unwrap();
    let receipt_digest = canonical.find("\"receipt_digest\"").unwrap();
    let representation = canonical.find("\"representation_sensitive\"").unwrap();
    assert!(permutation < receipt_digest && receipt_digest < representation);
}

#[test]
fn public_suite_rejects_semantic_and_transport_tampering() {
    let receipt = build_native_benchmark_suite_receipt().unwrap();

    let mut reordered = receipt.clone();
    reordered.rows.swap(0, 1);
    assert_eq!(
        replay_native_benchmark_suite_receipt(&reordered)
            .unwrap_err()
            .0,
        "benchmark-suite-replay-mismatch"
    );

    let mut rebound_transport = receipt.clone();
    rebound_transport.transport_rows[0].transfer_preserved = true;
    assert_eq!(
        replay_native_benchmark_suite_receipt(&rebound_transport)
            .unwrap_err()
            .0,
        "benchmark-suite-replay-mismatch"
    );

    let mut dropped_child = receipt.clone();
    dropped_child.rows.pop();
    assert_eq!(
        replay_native_benchmark_suite_receipt(&dropped_child)
            .unwrap_err()
            .0,
        "benchmark-suite-cardinality-drift"
    );

    let mut rebound_terminal = receipt.clone();
    rebound_terminal.rows[1].status = SynthesisStatus::Found;
    rebound_terminal.rows[1].detail = "winner-found";
    assert_eq!(
        replay_native_benchmark_suite_receipt(&rebound_terminal)
            .unwrap_err()
            .0,
        "benchmark-suite-replay-mismatch"
    );

    let mut rebound_trace = receipt.clone();
    let replacement = if rebound_trace.rows[1].trace_digest.starts_with('0') {
        "1"
    } else {
        "0"
    };
    rebound_trace.rows[1]
        .trace_digest
        .replace_range(0..1, replacement);
    assert_eq!(
        replay_native_benchmark_suite_receipt(&rebound_trace)
            .unwrap_err()
            .0,
        "benchmark-suite-replay-mismatch"
    );

    let mut reordered_transport = receipt.clone();
    reordered_transport.transport_rows.swap(0, 1);
    assert_eq!(
        replay_native_benchmark_suite_receipt(&reordered_transport)
            .unwrap_err()
            .0,
        "benchmark-suite-replay-mismatch"
    );

    let mut injected_winner = receipt;
    injected_winner.rows[1].winner = injected_winner.rows[0].winner.clone();
    assert_eq!(
        canonical_native_benchmark_suite_receipt_bytes(&injected_winner)
            .unwrap_err()
            .0,
        "invalid-benchmark-suite-receipt-binding"
    );
}

#[test]
fn public_suite_keeps_counter_cutoff_incomplete_and_nonreceiptable() {
    let limits = BudgetLimits {
        evaluation_limit: 1,
        ..BudgetLimits::default()
    };
    let run = run_native_benchmark_suite(limits).unwrap();
    assert!(run
        .experiments
        .iter()
        .all(|row| row.report.status == SynthesisStatus::Incomplete));
    assert!(run
        .experiments
        .iter()
        .all(|row| row.report.winner.is_none()));
}
