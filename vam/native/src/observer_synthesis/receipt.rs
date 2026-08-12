//! Canonical replayable receipt for the finite native surprise calibration.

use super::ast::SynthesisCoreError;
use super::benchmark::{
    synthesize_zero_positive_surprise, NativeSurpriseRun, NativeSurpriseScore,
    NATIVE_SURPRISE_BOUNDARY, ZERO_POSITIVE_BENCHMARK_ID,
};
use super::budget::{BudgetLimits, BudgetSnapshot, MAX_OUTPUT_BYTES};
use super::cegis::SynthesisStatus;
use super::diagnostics;
use super::hash::domain_sha256_hex;

pub const NATIVE_SURPRISE_RECEIPT_SCHEMA: &str = "veyra.native-observer-surprise.receipt.v1";
const RECEIPT_DOMAIN: &str = "veyra.native-observer-surprise.receipt.v1.binding";

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NativeObserverSurpriseReceiptV1 {
    pub schema: &'static str,
    pub benchmark_id: &'static str,
    pub benchmark_digest: String,
    pub catalog_digest: String,
    pub training_digest: String,
    pub limits_digest: String,
    pub trace_digest: String,
    pub detail: &'static str,
    pub surface_observer_digest: String,
    pub hidden_observer_digest: String,
    pub traversed_candidates: usize,
    pub active_case_ids: Vec<u32>,
    pub ledger: BudgetSnapshot,
    pub wall_clock_enforced: bool,
    pub process_as_enforced: bool,
    pub winner_ordinal: usize,
    pub winner_cost: usize,
    pub winner_depth: usize,
    pub winner_canonical: Vec<u8>,
    pub winner_digest: String,
    pub score: NativeSurpriseScore,
    pub boundary: &'static str,
    pub receipt_digest: String,
}

fn hex_bytes(bytes: &[u8]) -> String {
    diagnostics::event("SURPRISE_HEX_ENTER", "encoding bounded winner bytes");
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut out = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        out.push(HEX[(byte >> 4) as usize] as char);
        out.push(HEX[(byte & 15) as usize] as char);
    }
    diagnostics::event("SURPRISE_HEX_EXIT", "bounded winner bytes encoded");
    out
}

fn receipt_json(receipt: &NativeObserverSurpriseReceiptV1, include_digest: bool) -> Vec<u8> {
    diagnostics::event("SURPRISE_JSON_ENTER", "encoding validated receipt fields");
    let ids = receipt
        .active_case_ids
        .iter()
        .map(u32::to_string)
        .collect::<Vec<_>>()
        .join(",");
    let cutoff = receipt
        .ledger
        .cutoff
        .map(|value| format!("\"{}\"", value.as_str()))
        .unwrap_or_else(|| "null".to_string());
    let digest_field = if include_digest {
        format!(",\"receipt_digest\":\"{}\"", receipt.receipt_digest)
    } else {
        String::new()
    };
    let result = format!(
        concat!(
            "{{\"active_case_ids\":[{}],",
            "\"benchmark_digest\":\"{}\",",
            "\"benchmark_id\":\"{}\",",
            "\"boundary\":\"{}\",",
            "\"catalog_digest\":\"{}\",",
            "\"detail\":\"{}\",",
            "\"hidden_observer_digest\":\"{}\",",
            "\"ledger\":{{\"candidate_limit\":{},\"candidates\":{},",
            "\"canonical_bytes\":{},\"canonical_bytes_limit\":{},",
            "\"cutoff\":{},\"evaluation_limit\":{},\"evaluations\":{},",
            "\"output_bytes\":{},\"output_bytes_limit\":{}}},",
            "\"limits_digest\":\"{}\",",
            "\"process_as_enforced\":false{},",
            "\"schema\":\"{}\",",
            "\"score\":{{\"class_saving\":{},\"fit_gap_hits\":{},",
            "\"hidden_classes\":{},\"hidden_hits\":{},\"hidden_saving\":{},",
            "\"obligations\":{},\"surface_classes\":{},\"surface_hits\":{},",
            "\"surface_saving\":{}}},",
            "\"status\":\"FOUND\",",
            "\"surface_observer_digest\":\"{}\",",
            "\"trace_digest\":\"{}\",",
            "\"training_digest\":\"{}\",",
            "\"traversed_candidates\":{},",
            "\"wall_clock_enforced\":false,",
            "\"winner\":{{\"canonical_hex\":\"{}\",\"cost\":{},\"depth\":{},",
            "\"digest\":\"{}\",\"ordinal\":{}}}}}"
        ),
        ids,
        receipt.benchmark_digest,
        receipt.benchmark_id,
        receipt.boundary,
        receipt.catalog_digest,
        receipt.detail,
        receipt.hidden_observer_digest,
        receipt.ledger.limits.candidate_limit,
        receipt.ledger.candidates,
        receipt.ledger.canonical_bytes,
        receipt.ledger.limits.canonical_bytes_limit,
        cutoff,
        receipt.ledger.limits.evaluation_limit,
        receipt.ledger.evaluations,
        receipt.ledger.output_bytes,
        receipt.ledger.limits.output_bytes_limit,
        receipt.limits_digest,
        digest_field,
        receipt.schema,
        receipt.score.class_saving,
        receipt.score.fit_gap_hits,
        receipt.score.hidden_classes,
        receipt.score.hidden_hits,
        receipt.score.hidden_saving,
        receipt.score.obligations,
        receipt.score.surface_classes,
        receipt.score.surface_hits,
        receipt.score.surface_saving,
        receipt.surface_observer_digest,
        receipt.trace_digest,
        receipt.training_digest,
        receipt.traversed_candidates,
        hex_bytes(&receipt.winner_canonical),
        receipt.winner_cost,
        receipt.winner_depth,
        receipt.winner_digest,
        receipt.winner_ordinal,
    )
    .into_bytes();
    diagnostics::event("SURPRISE_JSON_EXIT", "validated receipt fields encoded");
    result
}

fn receipt_from_valid_run(
    run: &NativeSurpriseRun,
) -> Result<NativeObserverSurpriseReceiptV1, SynthesisCoreError> {
    diagnostics::event(
        "SURPRISE_FROM_RUN_ENTER",
        "binding one validated native run",
    );
    let witness = run
        .witness
        .as_ref()
        .ok_or(SynthesisCoreError("surprise-receipt-requires-witness"))
        .map_err(|error| {
            diagnostics::event("SURPRISE_FROM_RUN_REJECT", "native witness missing");
            error
        })?;
    if run.report.status != SynthesisStatus::Found {
        diagnostics::event("SURPRISE_FROM_RUN_REJECT", "native run is not found");
        return Err(SynthesisCoreError("surprise-receipt-requires-found"));
    }
    let winner = run
        .report
        .winner
        .as_ref()
        .ok_or(SynthesisCoreError("surprise-receipt-missing-winner"))
        .map_err(|error| {
            diagnostics::event("SURPRISE_FROM_RUN_REJECT", "native winner missing");
            error
        })?;
    let ledger = run
        .report
        .ledger
        .ok_or(SynthesisCoreError("surprise-receipt-missing-ledger"))
        .map_err(|error| {
            diagnostics::event("SURPRISE_FROM_RUN_REJECT", "native ledger missing");
            error
        })?;
    let mut receipt = NativeObserverSurpriseReceiptV1 {
        schema: NATIVE_SURPRISE_RECEIPT_SCHEMA,
        benchmark_id: ZERO_POSITIVE_BENCHMARK_ID,
        benchmark_digest: run.benchmark.benchmark_digest.clone(),
        catalog_digest: run.report.catalog_digest.clone(),
        training_digest: run.report.training_digest.clone(),
        limits_digest: run.report.limits_digest.clone(),
        trace_digest: run.report.trace_digest.clone(),
        detail: run.report.detail,
        surface_observer_digest: witness.surface_observer_digest.clone(),
        hidden_observer_digest: witness.hidden_observer_digest.clone(),
        traversed_candidates: run.report.traversed_candidates,
        active_case_ids: run.report.active_case_ids.clone(),
        ledger,
        wall_clock_enforced: false,
        process_as_enforced: false,
        winner_ordinal: winner.ordinal,
        winner_cost: winner.cost,
        winner_depth: winner.depth,
        winner_canonical: winner.canonical.clone(),
        winner_digest: winner.digest.clone(),
        score: witness.score,
        boundary: NATIVE_SURPRISE_BOUNDARY,
        receipt_digest: String::new(),
    };
    let body = receipt_json(&receipt, false);
    if body.len() > MAX_OUTPUT_BYTES {
        diagnostics::event("SURPRISE_FROM_RUN_REJECT", "receipt byte cap exceeded");
        return Err(SynthesisCoreError("surprise-receipt-byte-limit"));
    }
    receipt.receipt_digest = domain_sha256_hex(RECEIPT_DOMAIN, &body);
    diagnostics::event("SURPRISE_FROM_RUN_EXIT", "validated native run bound");
    Ok(receipt)
}

fn replay_exact_receipt(
    receipt: &NativeObserverSurpriseReceiptV1,
) -> Result<NativeObserverSurpriseReceiptV1, SynthesisCoreError> {
    diagnostics::event(
        "SURPRISE_EXACT_REPLAY_ENTER",
        "reconstructing receipt before serialization",
    );
    let run = synthesize_zero_positive_surprise(receipt.ledger.limits).map_err(|error| {
        diagnostics::event("SURPRISE_EXACT_REPLAY_REJECT", "bounded synthesis rejected");
        error
    })?;
    let expected = receipt_from_valid_run(&run).map_err(|error| {
        diagnostics::event(
            "SURPRISE_EXACT_REPLAY_REJECT",
            "receipt reconstruction rejected",
        );
        error
    })?;
    if &expected != receipt {
        diagnostics::event(
            "SURPRISE_EXACT_REPLAY_REJECT",
            "receipt differs from bounded reconstruction",
        );
        return Err(SynthesisCoreError("surprise-receipt-replay-mismatch"));
    }
    diagnostics::event(
        "SURPRISE_EXACT_REPLAY_EXIT",
        "receipt equals bounded reconstruction",
    );
    Ok(expected)
}

pub fn native_surprise_receipt_from_run(
    run: &NativeSurpriseRun,
) -> Result<NativeObserverSurpriseReceiptV1, SynthesisCoreError> {
    diagnostics::event(
        "SURPRISE_RECEIPT_ENTER",
        "validating native surprise run before receipt",
    );
    let limits = run
        .report
        .ledger
        .ok_or(SynthesisCoreError("surprise-receipt-missing-ledger"))
        .map_err(|error| {
            diagnostics::event("SURPRISE_RECEIPT_REJECT", "native ledger missing");
            error
        })?
        .limits;
    let rebuilt = synthesize_zero_positive_surprise(limits).map_err(|error| {
        diagnostics::event("SURPRISE_RECEIPT_REJECT", "native replay rejected");
        error
    })?;
    if &rebuilt != run {
        diagnostics::event(
            "SURPRISE_RECEIPT_REJECT",
            "native surprise run replay mismatch",
        );
        return Err(SynthesisCoreError("surprise-run-replay-mismatch"));
    }
    let result = receipt_from_valid_run(run);
    diagnostics::event(
        if result.is_ok() {
            "SURPRISE_RECEIPT_EXIT"
        } else {
            "SURPRISE_RECEIPT_REJECT"
        },
        "native surprise receipt construction terminated",
    );
    result
}

pub fn build_zero_positive_surprise_receipt(
) -> Result<NativeObserverSurpriseReceiptV1, SynthesisCoreError> {
    diagnostics::event(
        "SURPRISE_RECEIPT_DEFAULT_ENTER",
        "building default native surprise receipt",
    );
    let run = synthesize_zero_positive_surprise(BudgetLimits::default()).map_err(|error| {
        diagnostics::event(
            "SURPRISE_RECEIPT_DEFAULT_REJECT",
            "default bounded synthesis rejected",
        );
        error
    })?;
    let result = native_surprise_receipt_from_run(&run);
    diagnostics::event(
        if result.is_ok() {
            "SURPRISE_RECEIPT_DEFAULT_EXIT"
        } else {
            "SURPRISE_RECEIPT_DEFAULT_REJECT"
        },
        "default native surprise receipt construction terminated",
    );
    result
}

pub fn canonical_native_surprise_receipt_bytes(
    receipt: &NativeObserverSurpriseReceiptV1,
) -> Result<Vec<u8>, SynthesisCoreError> {
    diagnostics::event(
        "SURPRISE_RECEIPT_CANONICAL_ENTER",
        "validating native surprise receipt binding",
    );
    let expected = replay_exact_receipt(receipt).map_err(|_| {
        diagnostics::event(
            "SURPRISE_RECEIPT_CANONICAL_REJECT",
            "native surprise receipt replay is invalid",
        );
        SynthesisCoreError("invalid-surprise-receipt-binding")
    })?;
    let canonical = receipt_json(&expected, true);
    if canonical.len() > MAX_OUTPUT_BYTES {
        diagnostics::event(
            "SURPRISE_RECEIPT_CANONICAL_REJECT",
            "native surprise receipt bytes exceed limit",
        );
        return Err(SynthesisCoreError("surprise-receipt-byte-limit"));
    }
    diagnostics::event(
        "SURPRISE_RECEIPT_CANONICAL_EXIT",
        "native surprise receipt binding accepted",
    );
    Ok(canonical)
}

pub fn replay_native_surprise_receipt(
    receipt: &NativeObserverSurpriseReceiptV1,
) -> Result<NativeObserverSurpriseReceiptV1, SynthesisCoreError> {
    diagnostics::event(
        "SURPRISE_RECEIPT_REPLAY_ENTER",
        "replaying native surprise receipt from fixed inputs",
    );
    let expected = replay_exact_receipt(receipt).map_err(|error| {
        diagnostics::event(
            "SURPRISE_RECEIPT_REPLAY_REJECT",
            "exact receipt replay rejected",
        );
        error
    })?;
    diagnostics::event(
        "SURPRISE_RECEIPT_REPLAY_EXIT",
        "native surprise receipt replayed exactly",
    );
    Ok(expected)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn canonical_receipt_is_deterministic_and_replayable() {
        let first = build_zero_positive_surprise_receipt().unwrap();
        let second = build_zero_positive_surprise_receipt().unwrap();
        assert_eq!(first, second);
        assert_eq!(
            first.benchmark_digest,
            "2002a7f81d09a1ffd1e7ddcb063baa96b50b99b38443c1b51d285b8d2d395bdc"
        );
        assert_eq!(
            first.receipt_digest,
            "b7bbfdfdfbf33fc1bae1cd58ec7da126d88b90558552bddccd59f1ba48cb9547"
        );
        assert!(!first.wall_clock_enforced);
        assert!(!first.process_as_enforced);
        assert_eq!(
            canonical_native_surprise_receipt_bytes(&first).unwrap(),
            canonical_native_surprise_receipt_bytes(&second).unwrap()
        );
        assert_eq!(replay_native_surprise_receipt(&first).unwrap(), first);
    }

    #[test]
    fn receipt_replay_rejects_tampering() {
        let receipt = build_zero_positive_surprise_receipt().unwrap();

        let mut rebound = receipt.clone();
        rebound.score.hidden_hits = 1;
        let body = receipt_json(&rebound, false);
        rebound.receipt_digest = domain_sha256_hex(RECEIPT_DOMAIN, &body);
        assert_eq!(
            replay_native_surprise_receipt(&rebound).unwrap_err().0,
            "surprise-receipt-replay-mismatch"
        );

        let mut broken_binding = receipt;
        let replacement = if broken_binding.receipt_digest.ends_with('0') {
            "1"
        } else {
            "0"
        };
        broken_binding
            .receipt_digest
            .replace_range(63..64, replacement);
        assert_eq!(
            canonical_native_surprise_receipt_bytes(&broken_binding)
                .unwrap_err()
                .0,
            "invalid-surprise-receipt-binding"
        );
    }

    #[test]
    fn incomplete_run_cannot_mint_a_receipt() {
        let limits = BudgetLimits {
            evaluation_limit: 1,
            ..BudgetLimits::default()
        };
        let run = synthesize_zero_positive_surprise(limits).unwrap();
        assert_eq!(run.report.status, SynthesisStatus::Incomplete);
        assert_eq!(
            native_surprise_receipt_from_run(&run).unwrap_err().0,
            "surprise-receipt-requires-witness"
        );
    }

    #[test]
    fn replay_preserves_the_receipts_exact_counter_limits() {
        let limits = BudgetLimits {
            evaluation_limit: 6,
            ..BudgetLimits::default()
        };
        let run = synthesize_zero_positive_surprise(limits).unwrap();
        let receipt = native_surprise_receipt_from_run(&run).unwrap();
        assert_eq!(receipt.ledger.limits, limits);
        assert_eq!(replay_native_surprise_receipt(&receipt).unwrap(), receipt);
    }
}
