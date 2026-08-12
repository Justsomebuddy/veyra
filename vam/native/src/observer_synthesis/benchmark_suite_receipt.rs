//! Canonical binding and exact replay for the native benchmark family.

use super::ast::SynthesisCoreError;
use super::benchmark_suite::{
    run_native_benchmark_suite, NativeBenchmarkExperimentRun, NativeBenchmarkRowReceiptV1,
    NativeBenchmarkSuiteReceiptV1, NativeBenchmarkSuiteRun, NativeBenchmarkWinnerReceiptV1,
    NATIVE_BENCHMARK_SUITE_BOUNDARY, NATIVE_BENCHMARK_SUITE_SCHEMA,
};
use super::benchmark_transport::{
    build_representation_transport_rows, representation_transport_row_json,
};
use super::budget::{BudgetLimits, MAX_OUTPUT_BYTES};
use super::cegis::{SynthesisReport, SynthesisStatus};
use super::diagnostics;
use super::hash::domain_sha256_hex;

const SUITE_DOMAIN: &str = "veyra.native-observer-benchmark-suite.receipt.v1.binding";

fn winner_receipt(report: &SynthesisReport) -> Option<NativeBenchmarkWinnerReceiptV1> {
    diagnostics::event(
        "BENCHMARK_WINNER_RECEIPT_ENTER",
        "copying bounded winner fields",
    );
    let result = report
        .winner
        .as_ref()
        .map(|winner| NativeBenchmarkWinnerReceiptV1 {
            ordinal: winner.ordinal,
            cost: winner.cost,
            depth: winner.depth,
            canonical: winner.canonical.clone(),
            digest: winner.digest.clone(),
        });
    diagnostics::event(
        "BENCHMARK_WINNER_RECEIPT_EXIT",
        "bounded winner fields copied",
    );
    result
}

fn receipt_row(
    experiment: &NativeBenchmarkExperimentRun,
) -> Result<NativeBenchmarkRowReceiptV1, SynthesisCoreError> {
    diagnostics::event("BENCHMARK_ROW_RECEIPT_ENTER", "binding one benchmark row");
    if !matches!(
        experiment.report.status,
        SynthesisStatus::Found | SynthesisStatus::Exhausted
    ) {
        diagnostics::event(
            "BENCHMARK_ROW_RECEIPT_REJECT",
            "benchmark row is inconclusive",
        );
        return Err(SynthesisCoreError(
            "benchmark-suite-requires-conclusive-rows",
        ));
    }
    let ledger = experiment
        .report
        .ledger
        .ok_or(SynthesisCoreError("benchmark-suite-missing-ledger"))
        .inspect_err(|_| diagnostics::event("BENCHMARK_ROW_RECEIPT_REJECT", "ledger missing"))?;
    let result = NativeBenchmarkRowReceiptV1 {
        benchmark_id: experiment.benchmark.benchmark_id,
        benchmark_digest: experiment.benchmark.benchmark_digest.clone(),
        abstract_task_digest: experiment.benchmark.abstract_task_digest.clone(),
        cegis_boundary: experiment.report.boundary,
        representation_id: experiment.benchmark.representation_id,
        transport_source_id: experiment.benchmark.transport_source_id,
        status: experiment.report.status,
        detail: experiment.report.detail,
        catalog_digest: experiment.report.catalog_digest.clone(),
        training_digest: experiment.report.training_digest.clone(),
        limits_digest: experiment.report.limits_digest.clone(),
        trace_digest: experiment.report.trace_digest.clone(),
        traversed_candidates: experiment.report.traversed_candidates,
        active_case_ids: experiment.report.active_case_ids.clone(),
        ledger,
        wall_clock_enforced: false,
        process_as_enforced: false,
        marginal_balance: experiment.benchmark.marginal_balance.clone(),
        score: experiment.score,
        winner: winner_receipt(&experiment.report),
    };
    diagnostics::event("BENCHMARK_ROW_RECEIPT_EXIT", "one benchmark row bound");
    Ok(result)
}

fn option_usize(value: Option<usize>) -> String {
    diagnostics::event(
        "BENCHMARK_OPTION_ENTER",
        "encoding bounded optional integer",
    );
    let result = value.map_or_else(|| "null".to_owned(), |value| value.to_string());
    diagnostics::event("BENCHMARK_OPTION_EXIT", "bounded optional integer encoded");
    result
}

fn row_json(row: &NativeBenchmarkRowReceiptV1) -> String {
    diagnostics::event("BENCHMARK_ROW_JSON_ENTER", "encoding one receipt row");
    let active = row
        .active_case_ids
        .iter()
        .map(u32::to_string)
        .collect::<Vec<_>>()
        .join(",");
    let source = row
        .transport_source_id
        .map(|value| format!("\"{value}\""))
        .unwrap_or_else(|| "null".to_owned());
    let cutoff = row
        .ledger
        .cutoff
        .map(|value| format!("\"{}\"", value.as_str()))
        .unwrap_or_else(|| "null".to_owned());
    let winner = row.winner.as_ref().map_or_else(
        || "null".to_owned(),
        |winner| {
            format!(
                "{{\"canonical_hex\":\"{}\",\"cost\":{},\"depth\":{},\"digest\":\"{}\",\"ordinal\":{}}}",
                super::receipt::hex_bytes_for_benchmark(&winner.canonical),
                winner.cost,
                winner.depth,
                winner.digest,
                winner.ordinal,
            )
        },
    );
    let marginal = row
        .marginal_balance
        .as_ref()
        .map(super::benchmark_marginals::marginal_json)
        .unwrap_or_else(|| "null".to_owned());
    let result = format!(
        concat!(
            "{{\"abstract_task_digest\":\"{}\",\"active_case_ids\":[{active}],",
            "\"benchmark_digest\":\"{}\",\"benchmark_id\":\"{}\",",
            "\"catalog_digest\":\"{}\",\"cegis_boundary\":\"{}\",\"detail\":\"{}\",",
            "\"ledger\":{{\"candidate_limit\":{},\"candidates\":{},",
            "\"canonical_bytes\":{},\"canonical_bytes_limit\":{},\"cutoff\":{cutoff},",
            "\"evaluation_limit\":{},\"evaluations\":{},\"output_bytes\":{},",
            "\"output_bytes_limit\":{}}},\"limits_digest\":\"{}\",\"marginal_balance\":{marginal},",
            "\"process_as_enforced\":{},\"representation_id\":\"{}\",",
            "\"score\":{{\"class_saving\":{},",
            "\"obligations\":{},\"surface_classes\":{},\"surface_hits\":{},",
            "\"surface_saving\":{},\"winner_classes\":{},\"winner_hits\":{},",
            "\"winner_saving\":{}}},\"status\":\"{}\",",
            "\"trace_digest\":\"{}\",\"training_digest\":\"{}\",",
            "\"transport_source_id\":{source},\"traversed_candidates\":{},",
            "\"wall_clock_enforced\":{},\"winner\":{winner}}}"
        ),
        row.abstract_task_digest,
        row.benchmark_digest,
        row.benchmark_id,
        row.catalog_digest,
        row.cegis_boundary,
        row.detail,
        row.ledger.limits.candidate_limit,
        row.ledger.candidates,
        row.ledger.canonical_bytes,
        row.ledger.limits.canonical_bytes_limit,
        row.ledger.limits.evaluation_limit,
        row.ledger.evaluations,
        row.ledger.output_bytes,
        row.ledger.limits.output_bytes_limit,
        row.limits_digest,
        row.process_as_enforced,
        row.representation_id,
        option_usize(row.score.class_saving),
        row.score.obligations,
        row.score.surface_classes,
        row.score.surface_hits,
        row.score.surface_saving,
        option_usize(row.score.winner_classes),
        option_usize(row.score.winner_hits),
        option_usize(row.score.winner_saving),
        row.status.as_str(),
        row.trace_digest,
        row.training_digest,
        row.traversed_candidates,
        row.wall_clock_enforced,
        active = active,
        cutoff = cutoff,
        source = source,
        winner = winner,
        marginal = marginal,
    );
    diagnostics::event("BENCHMARK_ROW_JSON_EXIT", "one receipt row encoded");
    result
}

fn suite_json(receipt: &NativeBenchmarkSuiteReceiptV1, include_digest: bool) -> Vec<u8> {
    diagnostics::event("BENCHMARK_SUITE_JSON_ENTER", "encoding suite receipt");
    let rows = receipt
        .rows
        .iter()
        .map(row_json)
        .collect::<Vec<_>>()
        .join(",");
    let digest = if include_digest {
        format!("\"receipt_digest\":\"{}\",", receipt.receipt_digest)
    } else {
        String::new()
    };
    let transport_rows = receipt
        .transport_rows
        .iter()
        .map(representation_transport_row_json)
        .collect::<Vec<_>>()
        .join(",");
    let result = format!(
        concat!(
            "{{\"abstract_mixture_partition_preserved\":{},\"boundary\":\"{}\",",
            "\"permutation_discoverability_preserved\":{},{digest}\"representation_sensitive\":{},",
            "\"rows\":[{rows}],\"schema\":\"{}\",\"shift_cost_delta\":{},",
            "\"shift_discoverability_preserved\":{},\"transport_rows\":[{transport_rows}]}}"
        ),
        receipt.abstract_mixture_partition_preserved,
        receipt.boundary,
        receipt.permutation_discoverability_preserved,
        receipt.representation_sensitive,
        receipt.schema,
        receipt.shift_cost_delta,
        receipt.shift_discoverability_preserved,
        rows = rows,
        transport_rows = transport_rows,
        digest = digest,
    )
    .into_bytes();
    diagnostics::event("BENCHMARK_SUITE_JSON_EXIT", "suite receipt encoded");
    result
}

fn receipt_from_run(
    run: &NativeBenchmarkSuiteRun,
) -> Result<NativeBenchmarkSuiteReceiptV1, SynthesisCoreError> {
    diagnostics::event(
        "BENCHMARK_SUITE_RECEIPT_ENTER",
        "binding benchmark suite run",
    );
    if run.experiments.len() != 4 {
        diagnostics::event(
            "BENCHMARK_SUITE_RECEIPT_REJECT",
            "suite cardinality drifted",
        );
        return Err(SynthesisCoreError("benchmark-suite-cardinality-drift"));
    }
    let rows = run
        .experiments
        .iter()
        .map(receipt_row)
        .collect::<Result<Vec<_>, _>>()
        .inspect_err(|_| {
            diagnostics::event("BENCHMARK_SUITE_RECEIPT_REJECT", "row binding rejected")
        })?;
    let transport_rows =
        build_representation_transport_rows(&run.experiments).inspect_err(|_| {
            diagnostics::event(
                "BENCHMARK_SUITE_RECEIPT_REJECT",
                "transport binding rejected",
            )
        })?;
    let mixture_status = rows[0].status;
    let shifted_status = rows[2].status;
    let permuted_status = rows[3].status;
    let mixture_cost = rows[0]
        .winner
        .as_ref()
        .ok_or(SynthesisCoreError("benchmark-suite-mixture-winner-missing"))
        .inspect_err(|_| {
            diagnostics::event("BENCHMARK_SUITE_RECEIPT_REJECT", "mixture winner missing")
        })?
        .cost;
    let shift_cost = rows[2]
        .winner
        .as_ref()
        .ok_or(SynthesisCoreError("benchmark-suite-shift-winner-missing"))
        .inspect_err(|_| {
            diagnostics::event("BENCHMARK_SUITE_RECEIPT_REJECT", "shift winner missing")
        })?
        .cost;
    let shift_cost_delta = shift_cost.checked_sub(mixture_cost).ok_or_else(|| {
        diagnostics::event(
            "BENCHMARK_SUITE_RECEIPT_REJECT",
            "shift cost delta rejected",
        );
        SynthesisCoreError("benchmark-suite-shift-cost-drift")
    })?;
    let mut receipt = NativeBenchmarkSuiteReceiptV1 {
        schema: NATIVE_BENCHMARK_SUITE_SCHEMA,
        rows,
        transport_rows,
        abstract_mixture_partition_preserved: run.experiments[0].benchmark.abstract_task_digest
            == run.experiments[2].benchmark.abstract_task_digest
            && run.experiments[0].benchmark.abstract_task_digest
                == run.experiments[3].benchmark.abstract_task_digest,
        shift_discoverability_preserved: mixture_status == shifted_status,
        shift_cost_delta,
        permutation_discoverability_preserved: mixture_status == permuted_status,
        representation_sensitive: mixture_status != permuted_status || mixture_cost != shift_cost,
        boundary: NATIVE_BENCHMARK_SUITE_BOUNDARY,
        receipt_digest: String::new(),
    };
    let body = suite_json(&receipt, false);
    if body.len() > MAX_OUTPUT_BYTES {
        diagnostics::event(
            "BENCHMARK_SUITE_RECEIPT_REJECT",
            "suite receipt exceeds byte cap",
        );
        return Err(SynthesisCoreError("benchmark-suite-receipt-byte-limit"));
    }
    receipt.receipt_digest = domain_sha256_hex(SUITE_DOMAIN, &body);
    diagnostics::event("BENCHMARK_SUITE_RECEIPT_EXIT", "benchmark suite run bound");
    Ok(receipt)
}

pub fn build_native_benchmark_suite_receipt(
) -> Result<NativeBenchmarkSuiteReceiptV1, SynthesisCoreError> {
    diagnostics::event(
        "BENCHMARK_SUITE_DEFAULT_ENTER",
        "building default suite receipt",
    );
    let run = run_native_benchmark_suite(BudgetLimits::default()).inspect_err(|_| {
        diagnostics::event(
            "BENCHMARK_SUITE_DEFAULT_REJECT",
            "default suite run rejected",
        )
    })?;
    let result = receipt_from_run(&run);
    diagnostics::event(
        if result.is_ok() {
            "BENCHMARK_SUITE_DEFAULT_EXIT"
        } else {
            "BENCHMARK_SUITE_DEFAULT_REJECT"
        },
        "default suite receipt construction terminated",
    );
    result
}

pub fn replay_native_benchmark_suite_receipt(
    receipt: &NativeBenchmarkSuiteReceiptV1,
) -> Result<NativeBenchmarkSuiteReceiptV1, SynthesisCoreError> {
    diagnostics::event(
        "BENCHMARK_SUITE_REPLAY_ENTER",
        "replaying benchmark suite receipt",
    );
    if receipt.rows.len() != 4 || receipt.transport_rows.len() != 2 {
        diagnostics::event(
            "BENCHMARK_SUITE_REPLAY_REJECT",
            "receipt cardinality is not the fixed suite shape",
        );
        return Err(SynthesisCoreError("benchmark-suite-cardinality-drift"));
    }
    let limits = receipt.rows[0].ledger.limits;
    if receipt.rows.iter().any(|row| row.ledger.limits != limits) {
        diagnostics::event("BENCHMARK_SUITE_REPLAY_REJECT", "row limits disagree");
        return Err(SynthesisCoreError("benchmark-suite-limit-mismatch"));
    }
    let replayed = run_native_benchmark_suite(limits).inspect_err(|_| {
        diagnostics::event("BENCHMARK_SUITE_REPLAY_REJECT", "suite execution rejected")
    })?;
    let expected = receipt_from_run(&replayed).inspect_err(|_| {
        diagnostics::event(
            "BENCHMARK_SUITE_REPLAY_REJECT",
            "receipt reconstruction rejected",
        )
    })?;
    if &expected != receipt {
        diagnostics::event(
            "BENCHMARK_SUITE_REPLAY_REJECT",
            "suite receipt replay mismatched",
        );
        return Err(SynthesisCoreError("benchmark-suite-replay-mismatch"));
    }
    diagnostics::event(
        "BENCHMARK_SUITE_REPLAY_EXIT",
        "suite receipt replayed exactly",
    );
    Ok(expected)
}

pub fn canonical_native_benchmark_suite_receipt_bytes(
    receipt: &NativeBenchmarkSuiteReceiptV1,
) -> Result<Vec<u8>, SynthesisCoreError> {
    diagnostics::event(
        "BENCHMARK_SUITE_CANONICAL_ENTER",
        "validating suite receipt bytes",
    );
    let expected = replay_native_benchmark_suite_receipt(receipt).map_err(|_| {
        diagnostics::event(
            "BENCHMARK_SUITE_CANONICAL_REJECT",
            "suite receipt binding rejected",
        );
        SynthesisCoreError("invalid-benchmark-suite-receipt-binding")
    })?;
    let result = suite_json(&expected, true);
    if result.len() > MAX_OUTPUT_BYTES {
        diagnostics::event(
            "BENCHMARK_SUITE_CANONICAL_REJECT",
            "suite receipt exceeds byte cap",
        );
        return Err(SynthesisCoreError("benchmark-suite-receipt-byte-limit"));
    }
    diagnostics::event(
        "BENCHMARK_SUITE_CANONICAL_EXIT",
        "suite receipt bytes validated",
    );
    Ok(result)
}
