//! Replayable finite benchmark family for observer synthesis and its limits.

use std::collections::HashSet;

use super::ast::{ObserverExpr, PrimitiveId, SynthesisCoreError};
use super::benchmark_marginals::{derive_binary_marginals, NativeBitMarginalBalanceV1};
use super::benchmark_transport::NativeRepresentationTransportReceiptV1;
use super::budget::{BudgetLimits, BudgetSnapshot};
use super::canonical::observer_digest;
use super::cegis::{
    fit_observer_cegis, ExpectedRelation, ObserverCase, SynthesisReport, SynthesisStatus,
};
use super::diagnostics;
use super::grammar::{enumerate_observer_grammar, GrammarConfig};
use super::hash::domain_sha256_hex;
use super::semantics::{echo, observe, EchoOutcome, Observation, Recurrence, ResponseValue};

const SPEC_SCHEMA: &str = "veyra.native-observer-benchmark.spec.v1";
const SPEC_DOMAIN: &str = "veyra.native-observer-benchmark.spec.v1.binding";
const ABSTRACT_TASK_DOMAIN: &str = "veyra.native-observer-benchmark.abstract-task.v1.binding";
pub const NATIVE_BENCHMARK_SUITE_SCHEMA: &str = "veyra.native-observer-benchmark-suite.receipt.v1";
pub const MIXTURE_BENCHMARK_ID: &str = "mixture-zero-vs-positive-v1";
pub const XOR_PARITY_BENCHMARK_ID: &str = "xor-parity-balanced-marginals-v1";
pub const SHIFT_TRANSPORT_BENCHMARK_ID: &str = "mixture-shift-transport-v1";
pub const PERMUTED_TRANSPORT_BENCHMARK_ID: &str = "mixture-permuted-transport-v1";

pub const NATIVE_BENCHMARK_SUITE_BOUNDARY: &str =
    "four fixed finite encodings over the exact 1,565-row Tail/Crest/Pair grammar; FOUND and EXHAUSTED are grammar-relative replay outcomes, not hidden-variable recovery, representation invariance, impossibility, BM-F009, theorem, novelty, performance, or promotion claims";

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct NativeEncodedState {
    pub abstract_id: u8,
    pub feature_a: u8,
    pub feature_b: u8,
    pub target_class: u8,
    pub recurrence: Recurrence,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum NativeBenchmarkExpectation {
    Found(ObserverExpr),
    Exhausted,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NativeObserverBenchmark {
    pub schema: &'static str,
    pub benchmark_id: &'static str,
    pub representation_id: &'static str,
    pub transport_source_id: Option<&'static str>,
    pub states: Vec<NativeEncodedState>,
    pub cases: Vec<ObserverCase>,
    pub surface_observer: ObserverExpr,
    pub abstract_task_digest: String,
    pub marginal_balance: Option<NativeBitMarginalBalanceV1>,
    pub benchmark_digest: String,
    pub boundary: &'static str,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct NativeBenchmarkScore {
    pub obligations: usize,
    pub surface_hits: usize,
    pub surface_classes: usize,
    pub surface_saving: usize,
    pub winner_hits: Option<usize>,
    pub winner_classes: Option<usize>,
    pub winner_saving: Option<usize>,
    pub class_saving: Option<usize>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NativeBenchmarkExperimentRun {
    pub benchmark: NativeObserverBenchmark,
    pub report: SynthesisReport,
    pub score: NativeBenchmarkScore,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NativeBenchmarkSuiteRun {
    pub experiments: Vec<NativeBenchmarkExperimentRun>,
    pub limits: BudgetLimits,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NativeBenchmarkWinnerReceiptV1 {
    pub ordinal: usize,
    pub cost: usize,
    pub depth: usize,
    pub canonical: Vec<u8>,
    pub digest: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NativeBenchmarkRowReceiptV1 {
    pub benchmark_id: &'static str,
    pub benchmark_digest: String,
    pub abstract_task_digest: String,
    pub cegis_boundary: &'static str,
    pub representation_id: &'static str,
    pub transport_source_id: Option<&'static str>,
    pub status: SynthesisStatus,
    pub detail: &'static str,
    pub catalog_digest: String,
    pub training_digest: String,
    pub limits_digest: String,
    pub trace_digest: String,
    pub traversed_candidates: usize,
    pub active_case_ids: Vec<u32>,
    pub ledger: BudgetSnapshot,
    pub wall_clock_enforced: bool,
    pub process_as_enforced: bool,
    pub marginal_balance: Option<NativeBitMarginalBalanceV1>,
    pub score: NativeBenchmarkScore,
    pub winner: Option<NativeBenchmarkWinnerReceiptV1>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NativeBenchmarkSuiteReceiptV1 {
    pub schema: &'static str,
    pub rows: Vec<NativeBenchmarkRowReceiptV1>,
    pub transport_rows: Vec<NativeRepresentationTransportReceiptV1>,
    pub abstract_mixture_partition_preserved: bool,
    pub shift_discoverability_preserved: bool,
    pub shift_cost_delta: usize,
    pub permutation_discoverability_preserved: bool,
    pub representation_sensitive: bool,
    pub boundary: &'static str,
    pub receipt_digest: String,
}

fn recurrence(pulses: u16) -> Result<Recurrence, SynthesisCoreError> {
    diagnostics::event("BENCHMARK_RECURRENCE_ENTER", "binding one encoded state");
    let result = Recurrence::new(pulses);
    diagnostics::event(
        if result.is_ok() {
            "BENCHMARK_RECURRENCE_EXIT"
        } else {
            "BENCHMARK_RECURRENCE_REJECT"
        },
        "encoded state binding terminated",
    );
    result
}

fn encoded_states(
    physical: [u16; 4],
    targets: [u8; 4],
) -> Result<Vec<NativeEncodedState>, SynthesisCoreError> {
    diagnostics::event("BENCHMARK_STATES_ENTER", "constructing four encoded states");
    if targets.iter().any(|target| *target > 1)
        || physical.iter().collect::<HashSet<_>>().len() != physical.len()
    {
        diagnostics::event(
            "BENCHMARK_STATES_REJECT",
            "state encoding is not binary/injective",
        );
        return Err(SynthesisCoreError("invalid-benchmark-state-encoding"));
    }
    let mut states = Vec::with_capacity(4);
    for abstract_id in 0..4u8 {
        states.push(NativeEncodedState {
            abstract_id,
            feature_a: (abstract_id >> 1) & 1,
            feature_b: abstract_id & 1,
            target_class: targets[abstract_id as usize],
            recurrence: recurrence(physical[abstract_id as usize]).inspect_err(|_| {
                diagnostics::event("BENCHMARK_STATES_REJECT", "encoded recurrence rejected")
            })?,
        });
    }
    diagnostics::event("BENCHMARK_STATES_EXIT", "four encoded states constructed");
    Ok(states)
}

fn pairwise_cases(states: &[NativeEncodedState]) -> Result<Vec<ObserverCase>, SynthesisCoreError> {
    diagnostics::event(
        "BENCHMARK_CASES_ENTER",
        "constructing exact quotient obligations",
    );
    if states.len() != 4 {
        diagnostics::event("BENCHMARK_CASES_REJECT", "state cardinality drifted");
        return Err(SynthesisCoreError("invalid-benchmark-state-count"));
    }
    let mut cases = Vec::with_capacity(6);
    for left in 0..states.len() {
        for right in (left + 1)..states.len() {
            let ordinal = cases.len() as u32;
            cases.push(
                ObserverCase::train(
                    101 + ordinal,
                    1001 + ordinal,
                    states[left].recurrence,
                    states[right].recurrence,
                    if states[left].target_class == states[right].target_class {
                        ExpectedRelation::Echo
                    } else {
                        ExpectedRelation::Separate
                    },
                )
                .inspect_err(|_| {
                    diagnostics::event("BENCHMARK_CASES_REJECT", "quotient obligation rejected")
                })?,
            );
        }
    }
    diagnostics::event(
        "BENCHMARK_CASES_EXIT",
        "exact quotient obligations constructed",
    );
    Ok(cases)
}

fn abstract_task_digest(states: &[NativeEncodedState]) -> String {
    diagnostics::event("BENCHMARK_TASK_ENTER", "binding abstract partition task");
    let classes = states
        .iter()
        .map(|state| state.target_class.to_string())
        .collect::<Vec<_>>()
        .join(",");
    let canonical = format!(
        "{{\"abstract_ordinals\":[0,1,2,3],\"schema\":\"veyra.native-observer-benchmark.abstract-task.v1\",\"target_classes\":[{classes}]}}"
    );
    let result = domain_sha256_hex(ABSTRACT_TASK_DOMAIN, canonical.as_bytes());
    diagnostics::event("BENCHMARK_TASK_EXIT", "abstract partition task bound");
    result
}

fn benchmark_json(
    benchmark_id: &str,
    representation_id: &str,
    transport_source_id: Option<&str>,
    states: &[NativeEncodedState],
    cases: &[ObserverCase],
    abstract_task_digest: &str,
    marginal_balance: Option<&NativeBitMarginalBalanceV1>,
) -> String {
    diagnostics::event("BENCHMARK_JSON_ENTER", "encoding benchmark identity");
    let states = states
        .iter()
        .map(|state| {
            format!(
                "{{\"abstract_id\":{},\"feature_a\":{},\"feature_b\":{},\"pulses\":{},\"target_class\":{}}}",
                state.abstract_id,
                state.feature_a,
                state.feature_b,
                state.recurrence.pulses(),
                state.target_class,
            )
        })
        .collect::<Vec<_>>()
        .join(",");
    let cases = cases
        .iter()
        .map(|case| format!("\"{}\"", case.case_digest))
        .collect::<Vec<_>>()
        .join(",");
    let marginal_root = marginal_balance
        .map(|balance| format!("\"{}\"", balance.marginal_digest))
        .unwrap_or_else(|| "null".to_owned());
    let source = transport_source_id
        .map(|value| format!("\"{value}\""))
        .unwrap_or_else(|| "null".to_owned());
    let result = format!(
        "{{\"abstract_task_digest\":\"{abstract_task_digest}\",\"benchmark_id\":\"{benchmark_id}\",\"case_digests\":[{cases}],\"marginal_digest\":{marginal_root},\"representation_id\":\"{representation_id}\",\"schema\":\"{SPEC_SCHEMA}\",\"states\":[{states}],\"transport_source_id\":{source}}}"
    );
    diagnostics::event("BENCHMARK_JSON_EXIT", "benchmark identity encoded");
    result
}

fn build_benchmark(
    benchmark_id: &'static str,
    representation_id: &'static str,
    transport_source_id: Option<&'static str>,
    physical: [u16; 4],
    targets: [u8; 4],
    require_balanced_marginals: bool,
) -> Result<NativeObserverBenchmark, SynthesisCoreError> {
    diagnostics::event("BENCHMARK_BUILD_ENTER", "building one fixed benchmark");
    let states = encoded_states(physical, targets).inspect_err(|_| {
        diagnostics::event("BENCHMARK_BUILD_REJECT", "state construction rejected")
    })?;
    let cases = pairwise_cases(&states).inspect_err(|_| {
        diagnostics::event("BENCHMARK_BUILD_REJECT", "case construction rejected")
    })?;
    let derived_marginals = derive_binary_marginals(&states).inspect_err(|_| {
        diagnostics::event("BENCHMARK_BUILD_REJECT", "marginal derivation rejected")
    })?;
    if require_balanced_marginals && !derived_marginals.balanced {
        diagnostics::event("BENCHMARK_BUILD_REJECT", "marginal calibration drifted");
        return Err(SynthesisCoreError("benchmark-marginal-balance-drift"));
    }
    let marginal_balance = require_balanced_marginals.then_some(derived_marginals);
    let abstract_task_digest = abstract_task_digest(&states);
    let canonical = benchmark_json(
        benchmark_id,
        representation_id,
        transport_source_id,
        &states,
        &cases,
        &abstract_task_digest,
        marginal_balance.as_ref(),
    );
    let result = NativeObserverBenchmark {
        schema: SPEC_SCHEMA,
        benchmark_id,
        representation_id,
        transport_source_id,
        states,
        cases,
        surface_observer: ObserverExpr::Input,
        abstract_task_digest,
        marginal_balance,
        benchmark_digest: domain_sha256_hex(SPEC_DOMAIN, canonical.as_bytes()),
        boundary: NATIVE_BENCHMARK_SUITE_BOUNDARY,
    };
    diagnostics::event("BENCHMARK_BUILD_EXIT", "fixed benchmark built");
    Ok(result)
}

pub fn native_observer_benchmarks() -> Result<Vec<NativeObserverBenchmark>, SynthesisCoreError> {
    diagnostics::event(
        "BENCHMARK_SUITE_SPECS_ENTER",
        "building fixed benchmark family",
    );
    let result = (|| {
        Ok(vec![
            build_benchmark(
                MIXTURE_BENCHMARK_ID,
                "identity-unary-0-1-2-3-v1",
                None,
                [0, 1, 2, 3],
                [0, 1, 1, 1],
                false,
            )?,
            build_benchmark(
                XOR_PARITY_BENCHMARK_ID,
                "binary-lexicographic-to-unary-v1",
                None,
                [0, 1, 2, 3],
                [0, 1, 1, 0],
                true,
            )?,
            build_benchmark(
                SHIFT_TRANSPORT_BENCHMARK_ID,
                "unary-plus-one-v1",
                Some(MIXTURE_BENCHMARK_ID),
                [1, 2, 3, 4],
                [0, 1, 1, 1],
                false,
            )?,
            build_benchmark(
                PERMUTED_TRANSPORT_BENCHMARK_ID,
                "swap-zero-one-unary-v1",
                Some(MIXTURE_BENCHMARK_ID),
                [1, 0, 2, 3],
                [0, 1, 1, 1],
                false,
            )?,
        ])
    })()
    .inspect_err(|_| {
        diagnostics::event("BENCHMARK_SUITE_SPECS_REJECT", "benchmark family rejected")
    })?;
    diagnostics::event("BENCHMARK_SUITE_SPECS_EXIT", "fixed benchmark family built");
    Ok(result)
}

fn relation_hits(
    observer: &ObserverExpr,
    cases: &[ObserverCase],
) -> Result<usize, SynthesisCoreError> {
    diagnostics::event("BENCHMARK_HITS_ENTER", "scoring exact quotient obligations");
    let mut hits = 0;
    for case in cases {
        let actual = match echo(observer, case.left, case.right).inspect_err(|_| {
            diagnostics::event("BENCHMARK_HITS_REJECT", "observer relation rejected")
        })? {
            EchoOutcome::Echo(_) => ExpectedRelation::Echo,
            EchoOutcome::Mismatch { .. } => ExpectedRelation::Separate,
            EchoOutcome::DomainBlocked { .. } => ExpectedRelation::DomainBlocked,
        };
        hits += usize::from(actual == case.expected);
    }
    diagnostics::event("BENCHMARK_HITS_EXIT", "exact quotient obligations scored");
    Ok(hits)
}

fn response_classes(
    observer: &ObserverExpr,
    states: &[NativeEncodedState],
) -> Result<usize, SynthesisCoreError> {
    diagnostics::event(
        "BENCHMARK_CLASSES_ENTER",
        "counting encoded response classes",
    );
    let mut classes: Vec<ResponseValue> = Vec::new();
    for state in states {
        let Observation::Ready(value) = observe(observer, state.recurrence).inspect_err(|_| {
            diagnostics::event("BENCHMARK_CLASSES_REJECT", "observer evaluation rejected")
        })?
        else {
            diagnostics::event("BENCHMARK_CLASSES_REJECT", "benchmark observer blocked");
            return Err(SynthesisCoreError("benchmark-observer-domain-blocked"));
        };
        if !classes.contains(&value) {
            classes.push(value);
        }
    }
    diagnostics::event("BENCHMARK_CLASSES_EXIT", "encoded response classes counted");
    Ok(classes.len())
}

fn score_run(
    benchmark: &NativeObserverBenchmark,
    report: &SynthesisReport,
    catalog: &super::grammar::GrammarEnumeration,
) -> Result<NativeBenchmarkScore, SynthesisCoreError> {
    diagnostics::event("BENCHMARK_SCORE_ENTER", "scoring one benchmark run");
    let surface_hits =
        relation_hits(&benchmark.surface_observer, &benchmark.cases).inspect_err(|_| {
            diagnostics::event("BENCHMARK_SCORE_REJECT", "surface relation score rejected")
        })?;
    let surface_classes = response_classes(&benchmark.surface_observer, &benchmark.states)
        .inspect_err(|_| {
            diagnostics::event("BENCHMARK_SCORE_REJECT", "surface class score rejected")
        })?;
    let (winner_hits, winner_classes, winner_saving, class_saving) = match &report.winner {
        Some(winner) => {
            let candidate = catalog
                .candidates
                .get(winner.ordinal)
                .ok_or(SynthesisCoreError("invalid-benchmark-winner-ordinal"))
                .inspect_err(|_| {
                    diagnostics::event("BENCHMARK_SCORE_REJECT", "winner ordinal rejected")
                })?;
            if winner.digest != candidate.digest || winner.canonical != candidate.canonical {
                diagnostics::event("BENCHMARK_SCORE_REJECT", "winner identity drifted");
                return Err(SynthesisCoreError("benchmark-winner-identity-drift"));
            }
            let hits = relation_hits(&candidate.observer, &benchmark.cases).inspect_err(|_| {
                diagnostics::event("BENCHMARK_SCORE_REJECT", "winner relation score rejected")
            })?;
            let classes =
                response_classes(&candidate.observer, &benchmark.states).inspect_err(|_| {
                    diagnostics::event("BENCHMARK_SCORE_REJECT", "winner class score rejected")
                })?;
            let saving = benchmark.states.len().saturating_sub(classes);
            (
                Some(hits),
                Some(classes),
                Some(saving),
                Some(saving.saturating_sub(benchmark.states.len().saturating_sub(surface_classes))),
            )
        }
        None => (None, None, None, None),
    };
    let result = NativeBenchmarkScore {
        obligations: benchmark.cases.len(),
        surface_hits,
        surface_classes,
        surface_saving: benchmark.states.len().saturating_sub(surface_classes),
        winner_hits,
        winner_classes,
        winner_saving,
        class_saving,
    };
    diagnostics::event("BENCHMARK_SCORE_EXIT", "one benchmark run scored");
    Ok(result)
}

fn validate_terminal(
    benchmark: &NativeObserverBenchmark,
    report: &SynthesisReport,
    catalog: &super::grammar::GrammarEnumeration,
) -> Result<(), SynthesisCoreError> {
    diagnostics::event(
        "BENCHMARK_TERMINAL_ENTER",
        "checking declared benchmark outcome",
    );
    let expectation = match benchmark.benchmark_id {
        MIXTURE_BENCHMARK_ID => NativeBenchmarkExpectation::Found(ObserverExpr::apply(
            PrimitiveId::Crest,
            ObserverExpr::Input,
        )),
        SHIFT_TRANSPORT_BENCHMARK_ID => NativeBenchmarkExpectation::Found(ObserverExpr::apply(
            PrimitiveId::Crest,
            ObserverExpr::apply(PrimitiveId::Tail, ObserverExpr::Input),
        )),
        XOR_PARITY_BENCHMARK_ID | PERMUTED_TRANSPORT_BENCHMARK_ID => {
            NativeBenchmarkExpectation::Exhausted
        }
        _ => {
            diagnostics::event(
                "BENCHMARK_TERMINAL_REJECT",
                "benchmark expectation identity is unknown",
            );
            return Err(SynthesisCoreError("unknown-benchmark-expectation"));
        }
    };
    match (&expectation, report.status) {
        (_, SynthesisStatus::Incomplete) => {}
        (NativeBenchmarkExpectation::Found(expected), SynthesisStatus::Found) => {
            let winner = report
                .winner
                .as_ref()
                .ok_or(SynthesisCoreError("benchmark-missing-winner"))
                .inspect_err(|_| {
                    diagnostics::event("BENCHMARK_TERMINAL_REJECT", "winner missing")
                })?;
            let candidate = catalog
                .candidates
                .get(winner.ordinal)
                .ok_or(SynthesisCoreError("invalid-benchmark-winner-ordinal"))
                .inspect_err(|_| {
                    diagnostics::event("BENCHMARK_TERMINAL_REJECT", "winner ordinal rejected")
                })?;
            let expected_digest = observer_digest(expected).inspect_err(|_| {
                diagnostics::event("BENCHMARK_TERMINAL_REJECT", "expected observer rejected")
            })?;
            if &candidate.observer != expected
                || winner.digest != expected_digest
                || winner.digest != candidate.digest
            {
                diagnostics::event("BENCHMARK_TERMINAL_REJECT", "expected winner drifted");
                return Err(SynthesisCoreError("benchmark-expected-winner-drift"));
            }
        }
        (NativeBenchmarkExpectation::Exhausted, SynthesisStatus::Exhausted) => {
            if report.winner.is_some() || report.detail != "exact-catalog-exhausted" {
                diagnostics::event("BENCHMARK_TERMINAL_REJECT", "exhaustion boundary drifted");
                return Err(SynthesisCoreError("benchmark-exhaustion-drift"));
            }
        }
        _ => {
            diagnostics::event("BENCHMARK_TERMINAL_REJECT", "declared outcome mismatched");
            return Err(SynthesisCoreError("benchmark-terminal-outcome-drift"));
        }
    }
    diagnostics::event(
        "BENCHMARK_TERMINAL_EXIT",
        "declared benchmark outcome checked",
    );
    Ok(())
}

pub fn run_native_benchmark_suite(
    limits: BudgetLimits,
) -> Result<NativeBenchmarkSuiteRun, SynthesisCoreError> {
    diagnostics::event(
        "BENCHMARK_SUITE_RUN_ENTER",
        "starting fixed benchmark family",
    );
    let catalog = enumerate_observer_grammar(GrammarConfig::default()).inspect_err(|_| {
        diagnostics::event("BENCHMARK_SUITE_RUN_REJECT", "catalog enumeration rejected")
    })?;
    let mut experiments = Vec::new();
    for benchmark in native_observer_benchmarks().inspect_err(|_| {
        diagnostics::event(
            "BENCHMARK_SUITE_RUN_REJECT",
            "benchmark construction rejected",
        )
    })? {
        let report = fit_observer_cegis(&catalog, &benchmark.cases, limits);
        validate_terminal(&benchmark, &report, &catalog).inspect_err(|_| {
            diagnostics::event("BENCHMARK_SUITE_RUN_REJECT", "terminal validation rejected")
        })?;
        let score = score_run(&benchmark, &report, &catalog).inspect_err(|_| {
            diagnostics::event("BENCHMARK_SUITE_RUN_REJECT", "benchmark score rejected")
        })?;
        if report.status == SynthesisStatus::Found
            && (score.winner_hits != Some(score.obligations)
                || score.winner_classes != Some(2)
                || score.class_saving != Some(2))
        {
            diagnostics::event("BENCHMARK_SUITE_RUN_REJECT", "positive score drifted");
            return Err(SynthesisCoreError("benchmark-positive-score-drift"));
        }
        experiments.push(NativeBenchmarkExperimentRun {
            benchmark,
            report,
            score,
        });
    }
    diagnostics::event(
        "BENCHMARK_SUITE_RUN_EXIT",
        "fixed benchmark family terminated",
    );
    Ok(NativeBenchmarkSuiteRun {
        experiments,
        limits,
    })
}
