//! Deterministic public calibration suite for observer-synthesis v4.

use super::ast::SynthesisCoreError;
use super::diagnostics;
use super::grammar_profile::ObserverGrammarProfileId;
use super::hash::domain_sha256_hex;
use super::joint_synthesis::NativePartitionTaskId;
use super::representation_survey_v4::{
    survey_representation_family_v4, RepresentationFamilyKindV4, RepresentationTaskClassV4,
};
use super::synthesis_v4::{
    differential_representation_observer_v4, ObserverSynthesisCutoffV4, ObserverSynthesisRequestV4,
    ObserverSynthesisStatusV4,
};

pub const OBSERVER_SYNTHESIS_BENCHMARK_V4_SCHEMA: &str =
    "veyra.observer-synthesis-benchmark-suite.v4";
pub const OBSERVER_SYNTHESIS_BENCHMARK_V4_DIGEST: &str =
    "55fb30d48d761ea66733db802598d9b4a161ca3feaf811de89108664f30dfe71";
const ROW_DOMAIN: &str = "veyra.observer-synthesis-benchmark-suite.row.v4.binding";
const SUITE_DOMAIN: &str = "veyra.observer-synthesis-benchmark-suite.v4.binding";
pub const OBSERVER_SYNTHESIS_BENCHMARK_V4_BOUNDARY: &str = "six deterministic finite calibration cases: a positive hidden witness, a complete negative control, a representation trap, a family containing information-destroying quotients, a physical counter cutoff, and an empty cost-admitted exhaustion; PASS means exact implementation/oracle and declared expectation agreement only";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ObserverSynthesisBenchmarkIdV4 {
    PositiveHidden,
    NegativeControl,
    RepresentationTrap,
    LossyInformationDestroyed,
    CounterCutoff,
    CostAdmittedExhaustion,
}

impl ObserverSynthesisBenchmarkIdV4 {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::PositiveHidden => "positive-hidden-v4",
            Self::NegativeControl => "negative-control-v4",
            Self::RepresentationTrap => "representation-trap-v4",
            Self::LossyInformationDestroyed => "lossy-information-destroyed-v4",
            Self::CounterCutoff => "counter-cutoff-v4",
            Self::CostAdmittedExhaustion => "cost-admitted-exhaustion-v4",
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ObserverSynthesisBenchmarkSpecV4 {
    pub id: ObserverSynthesisBenchmarkIdV4,
    pub request: ObserverSynthesisRequestV4,
    pub expected_status: ObserverSynthesisStatusV4,
    pub expected_winner_class: Option<RepresentationTaskClassV4>,
    pub expected_cutoff: Option<ObserverSynthesisCutoffV4>,
    pub require_hidden_rows: bool,
    pub require_destroyed_rows: bool,
    pub require_nonempty_exhaustion: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ObserverSynthesisBenchmarkRowV4 {
    pub id: ObserverSynthesisBenchmarkIdV4,
    pub passed: bool,
    pub status: ObserverSynthesisStatusV4,
    pub winner_class: Option<RepresentationTaskClassV4>,
    pub stable_count: usize,
    pub hidden_count: usize,
    pub destroyed_count: usize,
    pub admissible_pairs: usize,
    pub pair_attempts: usize,
    pub differential_digest: String,
    pub row_digest: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ObserverSynthesisBenchmarkSuiteV4 {
    pub schema: &'static str,
    pub rows: Vec<ObserverSynthesisBenchmarkRowV4>,
    pub passed: usize,
    pub failed: usize,
    pub suite_digest: String,
    pub boundary: &'static str,
}

fn request(
    family: RepresentationFamilyKindV4,
    profile: ObserverGrammarProfileId,
) -> ObserverSynthesisRequestV4 {
    diagnostics::event("BENCH_V4_REQUEST_ENTER", "constructing benchmark request");
    let mut request =
        ObserverSynthesisRequestV4::systematic(NativePartitionTaskId::XorParity, profile);
    request.families = vec![family];
    diagnostics::event("BENCH_V4_REQUEST_EXIT", "benchmark request constructed");
    request
}

pub fn observer_synthesis_benchmarks_v4() -> Vec<ObserverSynthesisBenchmarkSpecV4> {
    diagnostics::event(
        "BENCH_V4_SPECS_ENTER",
        "building v4 benchmark specifications",
    );
    let positive = request(
        RepresentationFamilyKindV4::Permutation,
        ObserverGrammarProfileId::ParityV2,
    );
    let negative = request(
        RepresentationFamilyKindV4::Permutation,
        ObserverGrammarProfileId::LegacyV1,
    );
    let trap = request(
        RepresentationFamilyKindV4::CanonicalEncoding,
        ObserverGrammarProfileId::LegacyV1,
    );
    let lossy = request(
        RepresentationFamilyKindV4::GroupingQuotient,
        ObserverGrammarProfileId::ParityV2,
    );
    let mut cutoff = positive.clone();
    cutoff.limits.relation_evaluation_limit = 1;
    let mut exhaustion = positive.clone();
    exhaustion.maximum_total_cost = 1;
    let result = vec![
        ObserverSynthesisBenchmarkSpecV4 {
            id: ObserverSynthesisBenchmarkIdV4::PositiveHidden,
            request: positive,
            expected_status: ObserverSynthesisStatusV4::Found,
            expected_winner_class: Some(RepresentationTaskClassV4::RepresentationHidden),
            expected_cutoff: None,
            require_hidden_rows: true,
            require_destroyed_rows: false,
            require_nonempty_exhaustion: false,
        },
        ObserverSynthesisBenchmarkSpecV4 {
            id: ObserverSynthesisBenchmarkIdV4::NegativeControl,
            request: negative,
            expected_status: ObserverSynthesisStatusV4::Exhausted,
            expected_winner_class: None,
            expected_cutoff: None,
            require_hidden_rows: true,
            require_destroyed_rows: false,
            require_nonempty_exhaustion: true,
        },
        ObserverSynthesisBenchmarkSpecV4 {
            id: ObserverSynthesisBenchmarkIdV4::RepresentationTrap,
            request: trap,
            expected_status: ObserverSynthesisStatusV4::Exhausted,
            expected_winner_class: None,
            expected_cutoff: None,
            require_hidden_rows: true,
            require_destroyed_rows: false,
            require_nonempty_exhaustion: true,
        },
        ObserverSynthesisBenchmarkSpecV4 {
            id: ObserverSynthesisBenchmarkIdV4::LossyInformationDestroyed,
            request: lossy,
            expected_status: ObserverSynthesisStatusV4::Found,
            expected_winner_class: Some(RepresentationTaskClassV4::RepresentationStable),
            expected_cutoff: None,
            require_hidden_rows: true,
            require_destroyed_rows: true,
            require_nonempty_exhaustion: false,
        },
        ObserverSynthesisBenchmarkSpecV4 {
            id: ObserverSynthesisBenchmarkIdV4::CounterCutoff,
            request: cutoff,
            expected_status: ObserverSynthesisStatusV4::Cutoff,
            expected_winner_class: None,
            expected_cutoff: Some(ObserverSynthesisCutoffV4::RelationEvaluations),
            require_hidden_rows: true,
            require_destroyed_rows: false,
            require_nonempty_exhaustion: false,
        },
        ObserverSynthesisBenchmarkSpecV4 {
            id: ObserverSynthesisBenchmarkIdV4::CostAdmittedExhaustion,
            request: exhaustion,
            expected_status: ObserverSynthesisStatusV4::Exhausted,
            expected_winner_class: None,
            expected_cutoff: None,
            require_hidden_rows: true,
            require_destroyed_rows: false,
            require_nonempty_exhaustion: false,
        },
    ];
    diagnostics::event("BENCH_V4_SPECS_EXIT", "v4 benchmark specifications built");
    result
}

fn run_row(
    spec: &ObserverSynthesisBenchmarkSpecV4,
) -> Result<ObserverSynthesisBenchmarkRowV4, SynthesisCoreError> {
    diagnostics::event("BENCH_V4_ROW_ENTER", "running v4 benchmark row");
    let survey = survey_representation_family_v4(spec.request.task_id, &spec.request.families)?;
    let differential = differential_representation_observer_v4(&spec.request)?;
    let report = &differential.oracle;
    let winner_class = report
        .winner
        .as_ref()
        .map(|winner| winner.representation_class);
    let passed = differential.equivalent
        && report.status == spec.expected_status
        && winner_class == spec.expected_winner_class
        && report.ledger.cutoff == spec.expected_cutoff
        && (!spec.require_hidden_rows || survey.hidden_count > 0)
        && (!spec.require_destroyed_rows || survey.destroyed_count > 0)
        && (!spec.require_nonempty_exhaustion
            || (report.status == ObserverSynthesisStatusV4::Exhausted
                && report.ledger.admissible_pairs > 0
                && report.ledger.pair_attempts == report.ledger.admissible_pairs));
    let body = format!(
        "{}:{passed}:{}:{}:{}:{}:{}:{}:{}:{}",
        spec.id.as_str(),
        report.status.as_str(),
        winner_class.map_or("none", RepresentationTaskClassV4::as_str),
        survey.stable_count,
        survey.hidden_count,
        survey.destroyed_count,
        report.ledger.admissible_pairs,
        report.ledger.pair_attempts,
        differential.differential_digest,
    );
    let result = ObserverSynthesisBenchmarkRowV4 {
        id: spec.id,
        passed,
        status: report.status,
        winner_class,
        stable_count: survey.stable_count,
        hidden_count: survey.hidden_count,
        destroyed_count: survey.destroyed_count,
        admissible_pairs: report.ledger.admissible_pairs,
        pair_attempts: report.ledger.pair_attempts,
        differential_digest: differential.differential_digest,
        row_digest: domain_sha256_hex(ROW_DOMAIN, body.as_bytes()),
    };
    diagnostics::event("BENCH_V4_ROW_EXIT", "v4 benchmark row completed");
    Ok(result)
}

pub fn run_observer_synthesis_benchmark_suite_v4(
) -> Result<ObserverSynthesisBenchmarkSuiteV4, SynthesisCoreError> {
    diagnostics::event("BENCH_V4_SUITE_ENTER", "running v4 benchmark suite");
    let rows = observer_synthesis_benchmarks_v4()
        .iter()
        .map(run_row)
        .collect::<Result<Vec<_>, _>>()?;
    let passed = rows.iter().filter(|row| row.passed).count();
    let failed = rows.len() - passed;
    let body = format!(
        "{passed}:{failed}:{}",
        rows.iter()
            .map(|row| row.row_digest.as_str())
            .collect::<Vec<_>>()
            .join(":")
    );
    let result = ObserverSynthesisBenchmarkSuiteV4 {
        schema: OBSERVER_SYNTHESIS_BENCHMARK_V4_SCHEMA,
        rows,
        passed,
        failed,
        suite_digest: domain_sha256_hex(SUITE_DOMAIN, body.as_bytes()),
        boundary: OBSERVER_SYNTHESIS_BENCHMARK_V4_BOUNDARY,
    };
    if result.suite_digest != OBSERVER_SYNTHESIS_BENCHMARK_V4_DIGEST {
        diagnostics::event("BENCH_V4_SUITE_REJECT", "v4 benchmark suite digest drifted");
        return Err(SynthesisCoreError("observer-synthesis-v4-benchmark-drift"));
    }
    diagnostics::event("BENCH_V4_SUITE_EXIT", "v4 benchmark suite completed");
    Ok(result)
}
