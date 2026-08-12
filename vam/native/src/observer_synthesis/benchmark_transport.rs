//! Explicit source-witness transport evidence across fixed representations.

use super::ast::SynthesisCoreError;
use super::benchmark_suite::{
    NativeBenchmarkExperimentRun, MIXTURE_BENCHMARK_ID, PERMUTED_TRANSPORT_BENCHMARK_ID,
    SHIFT_TRANSPORT_BENCHMARK_ID,
};
use super::cegis::{ExpectedRelation, SynthesisStatus};
use super::diagnostics;
use super::grammar::{enumerate_observer_grammar, GrammarConfig};
use super::hash::domain_sha256_hex;
use super::semantics::{echo, EchoOutcome};

const TRANSPORT_SCHEMA: &str = "veyra.native-observer-benchmark.transport.v1";
const TRANSPORT_DOMAIN: &str = "veyra.native-observer-benchmark.transport.v1.binding";
pub const NATIVE_REPRESENTATION_TRANSPORT_BOUNDARY: &str =
    "exact source-witness evaluation followed by separate bounded re-synthesis on one fixed target encoding; failure or repair is finite grammar-relative evidence, not representation invariance, impossibility, or a transport theorem";

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NativeRepresentationTransportReceiptV1 {
    pub schema: &'static str,
    pub source_benchmark_id: &'static str,
    pub source_benchmark_digest: String,
    pub source_representation_id: &'static str,
    pub target_benchmark_id: &'static str,
    pub target_benchmark_digest: String,
    pub target_representation_id: &'static str,
    pub abstract_task_digest: String,
    pub source_winner_digest: String,
    pub source_winner_cost: usize,
    pub transfer_case_results: Vec<bool>,
    pub transfer_relation_hits: usize,
    pub obligations: usize,
    pub transfer_preserved: bool,
    pub target_resynthesis_status: SynthesisStatus,
    pub target_winner_digest: Option<String>,
    pub target_winner_cost: Option<usize>,
    pub target_cost_delta: Option<usize>,
    pub boundary: &'static str,
    pub transport_digest: String,
}

fn bool_array(values: &[bool]) -> String {
    diagnostics::event(
        "TRANSPORT_BOOL_ARRAY_ENTER",
        "encoding transfer truth table",
    );
    let result = values
        .iter()
        .map(bool::to_string)
        .collect::<Vec<_>>()
        .join(",");
    diagnostics::event("TRANSPORT_BOOL_ARRAY_EXIT", "transfer truth table encoded");
    result
}

fn option_string(value: Option<&str>) -> String {
    diagnostics::event("TRANSPORT_OPTION_STRING_ENTER", "encoding optional digest");
    let result = value
        .map(|value| format!("\"{value}\""))
        .unwrap_or_else(|| "null".to_owned());
    diagnostics::event("TRANSPORT_OPTION_STRING_EXIT", "optional digest encoded");
    result
}

fn option_usize(value: Option<usize>) -> String {
    diagnostics::event(
        "TRANSPORT_OPTION_INTEGER_ENTER",
        "encoding optional integer",
    );
    let result = value.map_or_else(|| "null".to_owned(), |value| value.to_string());
    diagnostics::event("TRANSPORT_OPTION_INTEGER_EXIT", "optional integer encoded");
    result
}

fn transport_body(row: &NativeRepresentationTransportReceiptV1) -> String {
    diagnostics::event("TRANSPORT_JSON_ENTER", "encoding transport evidence");
    let result = format!(
        concat!(
            "{{\"abstract_task_digest\":\"{}\",\"boundary\":\"{}\",",
            "\"obligations\":{},\"schema\":\"{}\",",
            "\"source_benchmark_digest\":\"{}\",\"source_benchmark_id\":\"{}\",",
            "\"source_representation_id\":\"{}\",\"source_winner_cost\":{},",
            "\"source_winner_digest\":\"{}\",\"target_benchmark_digest\":\"{}\",",
            "\"target_benchmark_id\":\"{}\",\"target_cost_delta\":{},",
            "\"target_representation_id\":\"{}\",\"target_resynthesis_status\":\"{}\",",
            "\"target_winner_cost\":{},\"target_winner_digest\":{},",
            "\"transfer_case_results\":[{}],\"transfer_preserved\":{},",
            "\"transfer_relation_hits\":{}}}"
        ),
        row.abstract_task_digest,
        row.boundary,
        row.obligations,
        row.schema,
        row.source_benchmark_digest,
        row.source_benchmark_id,
        row.source_representation_id,
        row.source_winner_cost,
        row.source_winner_digest,
        row.target_benchmark_digest,
        row.target_benchmark_id,
        option_usize(row.target_cost_delta),
        row.target_representation_id,
        row.target_resynthesis_status.as_str(),
        option_usize(row.target_winner_cost),
        option_string(row.target_winner_digest.as_deref()),
        bool_array(&row.transfer_case_results),
        row.transfer_preserved,
        row.transfer_relation_hits,
    );
    diagnostics::event("TRANSPORT_JSON_EXIT", "transport evidence encoded");
    result
}

pub(super) fn representation_transport_row_json(
    row: &NativeRepresentationTransportReceiptV1,
) -> String {
    diagnostics::event("TRANSPORT_ROW_JSON_ENTER", "encoding bound transport row");
    let body = transport_body(row);
    let result = format!(
        "{{\"body\":{body},\"transport_digest\":\"{}\"}}",
        row.transport_digest
    );
    diagnostics::event("TRANSPORT_ROW_JSON_EXIT", "bound transport row encoded");
    result
}

fn relation_result(
    source: &super::grammar::ObserverCandidate,
    target_case: &super::cegis::ObserverCase,
) -> Result<bool, SynthesisCoreError> {
    diagnostics::event(
        "TRANSPORT_RELATION_ENTER",
        "evaluating source witness on target case",
    );
    let actual =
        match echo(&source.observer, target_case.left, target_case.right).inspect_err(|_| {
            diagnostics::event(
                "TRANSPORT_RELATION_REJECT",
                "source witness evaluation rejected",
            )
        })? {
            EchoOutcome::Echo(_) => ExpectedRelation::Echo,
            EchoOutcome::Mismatch { .. } => ExpectedRelation::Separate,
            EchoOutcome::DomainBlocked { .. } => ExpectedRelation::DomainBlocked,
        };
    let result = actual == target_case.expected;
    diagnostics::event(
        "TRANSPORT_RELATION_EXIT",
        "source witness target case evaluated",
    );
    Ok(result)
}

fn transport_row(
    source: &NativeBenchmarkExperimentRun,
    target: &NativeBenchmarkExperimentRun,
) -> Result<NativeRepresentationTransportReceiptV1, SynthesisCoreError> {
    diagnostics::event(
        "TRANSPORT_ROW_ENTER",
        "building one representation transport row",
    );
    if source.benchmark.benchmark_id != MIXTURE_BENCHMARK_ID
        || !matches!(
            target.benchmark.benchmark_id,
            SHIFT_TRANSPORT_BENCHMARK_ID | PERMUTED_TRANSPORT_BENCHMARK_ID
        )
        || target.benchmark.transport_source_id != Some(MIXTURE_BENCHMARK_ID)
        || source.benchmark.abstract_task_digest != target.benchmark.abstract_task_digest
        || source.report.status != SynthesisStatus::Found
        || !matches!(
            target.report.status,
            SynthesisStatus::Found | SynthesisStatus::Exhausted
        )
    {
        diagnostics::event("TRANSPORT_ROW_REJECT", "transport endpoints are invalid");
        return Err(SynthesisCoreError(
            "invalid-representation-transport-endpoints",
        ));
    }
    let catalog = enumerate_observer_grammar(GrammarConfig::default()).inspect_err(|_| {
        diagnostics::event("TRANSPORT_ROW_REJECT", "catalog enumeration rejected")
    })?;
    let source_winner = source
        .report
        .winner
        .as_ref()
        .ok_or(SynthesisCoreError("transport-source-winner-missing"))
        .inspect_err(|_| diagnostics::event("TRANSPORT_ROW_REJECT", "source winner missing"))?;
    let source_candidate = catalog
        .candidates
        .get(source_winner.ordinal)
        .ok_or(SynthesisCoreError("transport-source-winner-ordinal"))
        .inspect_err(|_| {
            diagnostics::event("TRANSPORT_ROW_REJECT", "source winner ordinal rejected")
        })?;
    if source_candidate.digest != source_winner.digest
        || source_candidate.canonical != source_winner.canonical
    {
        diagnostics::event("TRANSPORT_ROW_REJECT", "source winner identity drifted");
        return Err(SynthesisCoreError("transport-source-winner-drift"));
    }
    let transfer_case_results = target
        .benchmark
        .cases
        .iter()
        .map(|case| relation_result(source_candidate, case))
        .collect::<Result<Vec<_>, _>>()
        .inspect_err(|_| {
            diagnostics::event("TRANSPORT_ROW_REJECT", "target truth table rejected")
        })?;
    let transfer_relation_hits = transfer_case_results
        .iter()
        .filter(|result| **result)
        .count();
    let target_winner = target.report.winner.as_ref();
    let target_winner_cost = target_winner.map(|winner| winner.cost);
    let target_cost_delta = target_winner_cost
        .map(|cost| {
            cost.checked_sub(source_winner.cost)
                .ok_or(SynthesisCoreError("transport-target-cost-drift"))
        })
        .transpose()
        .inspect_err(|_| diagnostics::event("TRANSPORT_ROW_REJECT", "target cost rejected"))?;
    let mut row = NativeRepresentationTransportReceiptV1 {
        schema: TRANSPORT_SCHEMA,
        source_benchmark_id: source.benchmark.benchmark_id,
        source_benchmark_digest: source.benchmark.benchmark_digest.clone(),
        source_representation_id: source.benchmark.representation_id,
        target_benchmark_id: target.benchmark.benchmark_id,
        target_benchmark_digest: target.benchmark.benchmark_digest.clone(),
        target_representation_id: target.benchmark.representation_id,
        abstract_task_digest: source.benchmark.abstract_task_digest.clone(),
        source_winner_digest: source_winner.digest.clone(),
        source_winner_cost: source_winner.cost,
        transfer_preserved: transfer_relation_hits == transfer_case_results.len(),
        obligations: transfer_case_results.len(),
        transfer_relation_hits,
        transfer_case_results,
        target_resynthesis_status: target.report.status,
        target_winner_digest: target_winner.map(|winner| winner.digest.clone()),
        target_winner_cost,
        target_cost_delta,
        boundary: NATIVE_REPRESENTATION_TRANSPORT_BOUNDARY,
        transport_digest: String::new(),
    };
    row.transport_digest = domain_sha256_hex(TRANSPORT_DOMAIN, transport_body(&row).as_bytes());
    diagnostics::event("TRANSPORT_ROW_EXIT", "representation transport row built");
    Ok(row)
}

pub(super) fn build_representation_transport_rows(
    experiments: &[NativeBenchmarkExperimentRun],
) -> Result<Vec<NativeRepresentationTransportReceiptV1>, SynthesisCoreError> {
    diagnostics::event(
        "TRANSPORT_ROWS_ENTER",
        "building fixed representation transport rows",
    );
    if experiments.len() != 4 {
        diagnostics::event(
            "TRANSPORT_ROWS_REJECT",
            "benchmark suite cardinality drifted",
        );
        return Err(SynthesisCoreError("transport-suite-cardinality-drift"));
    }
    let result = vec![
        transport_row(&experiments[0], &experiments[2]).inspect_err(|_| {
            diagnostics::event("TRANSPORT_ROWS_REJECT", "shift transport rejected")
        })?,
        transport_row(&experiments[0], &experiments[3]).inspect_err(|_| {
            diagnostics::event("TRANSPORT_ROWS_REJECT", "permutation transport rejected")
        })?,
    ];
    if result.iter().any(|row| row.transfer_preserved)
        || result[0].target_resynthesis_status != SynthesisStatus::Found
        || result[0].target_cost_delta != Some(1)
        || result[1].target_resynthesis_status != SynthesisStatus::Exhausted
        || result[1].target_winner_digest.is_some()
    {
        diagnostics::event(
            "TRANSPORT_ROWS_REJECT",
            "fixed transport calibration drifted",
        );
        return Err(SynthesisCoreError(
            "representation-transport-calibration-drift",
        ));
    }
    diagnostics::event(
        "TRANSPORT_ROWS_EXIT",
        "fixed representation transport rows built",
    );
    Ok(result)
}
