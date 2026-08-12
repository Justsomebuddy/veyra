//! One finite hidden-structure calibration over the native R11 recurrence domain.

use super::ast::{ObserverExpr, PrimitiveId, SynthesisCoreError};
use super::budget::BudgetLimits;
use super::canonical::observer_digest;
use super::cegis::{
    default_train_cases, fit_observer_cegis, ExpectedRelation, ObserverCase, SynthesisReport,
    SynthesisStatus,
};
use super::diagnostics;
use super::grammar::{enumerate_observer_grammar, GrammarConfig};
use super::hash::domain_sha256_hex;
use super::semantics::{echo, observe, EchoOutcome, Observation, Recurrence, ResponseValue};

const BENCHMARK_SCHEMA: &str = "veyra.native-observer-surprise.benchmark.v1";
const WITNESS_SCHEMA: &str = "veyra.native-observer-surprise.witness.v1";
const BENCHMARK_DOMAIN: &str = "veyra.native-observer-surprise.benchmark.v1.binding";

pub const ZERO_POSITIVE_BENCHMARK_ID: &str = "zero-positive-quotient-v1";
pub const NATIVE_SURPRISE_BOUNDARY: &str =
    "one finite unary-recurrence zero-vs-positive quotient calibration; no holdout, hidden-variable discovery, BM-F009, general synthesis, minimality, theorem, performance, or promotion claim";

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct NativeSurpriseScore {
    pub obligations: usize,
    pub surface_hits: usize,
    pub hidden_hits: usize,
    pub fit_gap_hits: usize,
    pub surface_classes: usize,
    pub hidden_classes: usize,
    pub surface_saving: usize,
    pub hidden_saving: usize,
    pub class_saving: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NativeSurpriseBenchmark {
    pub schema: &'static str,
    pub benchmark_id: &'static str,
    pub cases: Vec<ObserverCase>,
    pub surface_observer: ObserverExpr,
    pub expected_hidden_observer: ObserverExpr,
    pub benchmark_digest: String,
    pub boundary: &'static str,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NativeSurpriseWitness {
    pub schema: &'static str,
    pub benchmark_digest: String,
    pub surface_observer_digest: String,
    pub hidden_observer_digest: String,
    pub hidden_ordinal: usize,
    pub hidden_cost: usize,
    pub hidden_depth: usize,
    pub score: NativeSurpriseScore,
    pub boundary: &'static str,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NativeSurpriseRun {
    pub benchmark: NativeSurpriseBenchmark,
    pub report: SynthesisReport,
    pub witness: Option<NativeSurpriseWitness>,
}

fn benchmark_bytes(cases: &[ObserverCase], surface_digest: &str, hidden_digest: &str) -> Vec<u8> {
    diagnostics::event("SURPRISE_BYTES_ENTER", "encoding fixed benchmark identity");
    let result = format!(
        "{{\"benchmark_id\":\"{ZERO_POSITIVE_BENCHMARK_ID}\",\"case_digests\":[\"{}\",\"{}\"],\"expected_hidden_digest\":\"{hidden_digest}\",\"response_inputs\":[0,1,2],\"schema\":\"{BENCHMARK_SCHEMA}\",\"surface_digest\":\"{surface_digest}\",\"target_partition\":[[0],[1,2]]}}",
        cases[0].case_digest, cases[1].case_digest,
    )
    .into_bytes();
    diagnostics::event("SURPRISE_BYTES_EXIT", "fixed benchmark identity encoded");
    result
}

pub fn zero_positive_surprise_benchmark() -> Result<NativeSurpriseBenchmark, SynthesisCoreError> {
    diagnostics::event(
        "SURPRISE_BENCHMARK_ENTER",
        "constructing fixed zero-positive benchmark",
    );
    let cases = default_train_cases();
    if cases.len() != 2 || cases[0].case_id != 101 || cases[1].case_id != 102 {
        diagnostics::event(
            "SURPRISE_BENCHMARK_REJECT",
            "fixed TRAIN case identity drifted",
        );
        return Err(SynthesisCoreError("surprise-benchmark-case-drift"));
    }
    let surface_observer = ObserverExpr::Input;
    let expected_hidden_observer = ObserverExpr::apply(PrimitiveId::Crest, ObserverExpr::Input);
    let surface_digest = observer_digest(&surface_observer).map_err(|error| {
        diagnostics::event("SURPRISE_BENCHMARK_REJECT", "surface identity rejected");
        error
    })?;
    let hidden_digest = observer_digest(&expected_hidden_observer).map_err(|error| {
        diagnostics::event("SURPRISE_BENCHMARK_REJECT", "hidden identity rejected");
        error
    })?;
    let canonical = benchmark_bytes(&cases, &surface_digest, &hidden_digest);
    let result = NativeSurpriseBenchmark {
        schema: BENCHMARK_SCHEMA,
        benchmark_id: ZERO_POSITIVE_BENCHMARK_ID,
        cases,
        surface_observer,
        expected_hidden_observer,
        benchmark_digest: domain_sha256_hex(BENCHMARK_DOMAIN, &canonical),
        boundary: NATIVE_SURPRISE_BOUNDARY,
    };
    diagnostics::event(
        "SURPRISE_BENCHMARK_EXIT",
        "fixed zero-positive benchmark bound",
    );
    Ok(result)
}

fn relation_hit(observer: &ObserverExpr, case: &ObserverCase) -> Result<bool, SynthesisCoreError> {
    diagnostics::event("SURPRISE_RELATION_ENTER", "evaluating one fixed obligation");
    let actual = match echo(observer, case.left, case.right).map_err(|error| {
        diagnostics::event("SURPRISE_RELATION_REJECT", "fixed obligation rejected");
        error
    })? {
        EchoOutcome::Echo(_) => ExpectedRelation::Echo,
        EchoOutcome::Mismatch { .. } => ExpectedRelation::Separate,
        EchoOutcome::DomainBlocked { .. } => ExpectedRelation::DomainBlocked,
    };
    let result = actual == case.expected;
    diagnostics::event("SURPRISE_RELATION_EXIT", "fixed obligation evaluated");
    Ok(result)
}

fn response_class_count(observer: &ObserverExpr) -> Result<usize, SynthesisCoreError> {
    diagnostics::event("SURPRISE_CLASSES_ENTER", "counting fixed response classes");
    let positive_one = Recurrence::new(1).map_err(|error| {
        diagnostics::event("SURPRISE_CLASSES_REJECT", "fixed recurrence rejected");
        error
    })?;
    let positive_two = Recurrence::new(2).map_err(|error| {
        diagnostics::event("SURPRISE_CLASSES_REJECT", "fixed recurrence rejected");
        error
    })?;
    let inputs = [Recurrence::silence(), positive_one, positive_two];
    let mut classes: Vec<ResponseValue> = Vec::new();
    for recurrence in inputs {
        let Observation::Ready(value) = observe(observer, recurrence).map_err(|error| {
            diagnostics::event("SURPRISE_CLASSES_REJECT", "observer evaluation rejected");
            error
        })?
        else {
            diagnostics::event("SURPRISE_CLASSES_REJECT", "observer domain blocked");
            return Err(SynthesisCoreError("surprise-benchmark-domain-blocked"));
        };
        if !classes.contains(&value) {
            classes.push(value);
        }
    }
    let result = classes.len();
    diagnostics::event("SURPRISE_CLASSES_EXIT", "fixed response classes counted");
    Ok(result)
}

fn score_benchmark(
    benchmark: &NativeSurpriseBenchmark,
    hidden: &ObserverExpr,
) -> Result<NativeSurpriseScore, SynthesisCoreError> {
    diagnostics::event(
        "SURPRISE_SCORE_ENTER",
        "evaluating fixed surface and hidden observers",
    );
    let obligations = benchmark.cases.len();
    let surface_hits = benchmark
        .cases
        .iter()
        .map(|case| relation_hit(&benchmark.surface_observer, case))
        .collect::<Result<Vec<_>, _>>()?
        .into_iter()
        .filter(|hit| *hit)
        .count();
    let hidden_hits = benchmark
        .cases
        .iter()
        .map(|case| relation_hit(hidden, case))
        .collect::<Result<Vec<_>, _>>()?
        .into_iter()
        .filter(|hit| *hit)
        .count();
    let surface_classes = response_class_count(&benchmark.surface_observer)?;
    let hidden_classes = response_class_count(hidden)?;
    let surface_saving = 3usize.saturating_sub(surface_classes);
    let hidden_saving = 3usize.saturating_sub(hidden_classes);
    let Some(fit_gap_hits) = hidden_hits.checked_sub(surface_hits) else {
        diagnostics::event(
            "SURPRISE_SCORE_REJECT",
            "hidden fit does not improve surface",
        );
        return Err(SynthesisCoreError("invalid-surprise-fit-gap"));
    };
    let Some(class_saving) = hidden_saving.checked_sub(surface_saving) else {
        diagnostics::event(
            "SURPRISE_SCORE_REJECT",
            "hidden observer does not improve compression",
        );
        return Err(SynthesisCoreError("invalid-surprise-class-gap"));
    };
    let result = NativeSurpriseScore {
        obligations,
        surface_hits,
        hidden_hits,
        fit_gap_hits,
        surface_classes,
        hidden_classes,
        surface_saving,
        hidden_saving,
        class_saving,
    };
    if result
        != (NativeSurpriseScore {
            obligations: 2,
            surface_hits: 1,
            hidden_hits: 2,
            fit_gap_hits: 1,
            surface_classes: 3,
            hidden_classes: 2,
            surface_saving: 0,
            hidden_saving: 1,
            class_saving: 1,
        })
    {
        diagnostics::event("SURPRISE_SCORE_REJECT", "fixed benchmark score drifted");
        return Err(SynthesisCoreError("surprise-benchmark-score-drift"));
    }
    diagnostics::event("SURPRISE_SCORE_EXIT", "fixed observer gap reproduced");
    Ok(result)
}

pub fn synthesize_zero_positive_surprise(
    limits: BudgetLimits,
) -> Result<NativeSurpriseRun, SynthesisCoreError> {
    diagnostics::event(
        "SURPRISE_SYNTHESIS_ENTER",
        "starting bounded zero-positive synthesis",
    );
    let benchmark = zero_positive_surprise_benchmark()?;
    let catalog = enumerate_observer_grammar(GrammarConfig::default())?;
    let report = fit_observer_cegis(&catalog, &benchmark.cases, limits);
    let witness = if report.status == SynthesisStatus::Found {
        let winner = report
            .winner
            .as_ref()
            .ok_or(SynthesisCoreError("missing-surprise-winner"))?;
        let candidate = catalog
            .candidates
            .get(winner.ordinal)
            .ok_or(SynthesisCoreError("invalid-surprise-winner-ordinal"))?;
        let expected_digest = observer_digest(&benchmark.expected_hidden_observer)?;
        if candidate.observer != benchmark.expected_hidden_observer
            || winner.ordinal != 1
            || winner.cost != 1
            || winner.depth != 1
            || winner.digest != expected_digest
            || winner.digest != candidate.digest
            || winner.canonical != candidate.canonical
        {
            diagnostics::event(
                "SURPRISE_SYNTHESIS_REJECT",
                "fixed hidden observer identity drifted",
            );
            return Err(SynthesisCoreError("surprise-winner-drift"));
        }
        Some(NativeSurpriseWitness {
            schema: WITNESS_SCHEMA,
            benchmark_digest: benchmark.benchmark_digest.clone(),
            surface_observer_digest: observer_digest(&benchmark.surface_observer)?,
            hidden_observer_digest: winner.digest.clone(),
            hidden_ordinal: winner.ordinal,
            hidden_cost: winner.cost,
            hidden_depth: winner.depth,
            score: score_benchmark(&benchmark, &candidate.observer)?,
            boundary: NATIVE_SURPRISE_BOUNDARY,
        })
    } else {
        None
    };
    diagnostics::event(
        if witness.is_some() {
            "SURPRISE_SYNTHESIS_EXIT"
        } else {
            "SURPRISE_SYNTHESIS_INCOMPLETE"
        },
        "bounded zero-positive synthesis terminated",
    );
    Ok(NativeSurpriseRun {
        benchmark,
        report,
        witness,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zero_positive_gap_and_hidden_witness_are_exact() {
        let run = synthesize_zero_positive_surprise(BudgetLimits::default()).unwrap();
        let witness = run.witness.unwrap();
        assert_eq!(run.report.status, SynthesisStatus::Found);
        assert_eq!(witness.hidden_ordinal, 1);
        assert_eq!(witness.score.surface_hits, 1);
        assert_eq!(witness.score.hidden_hits, 2);
        assert_eq!(witness.score.surface_classes, 3);
        assert_eq!(witness.score.hidden_classes, 2);
        assert_eq!(witness.score.class_saving, 1);
    }

    #[test]
    fn counter_cutoff_never_mints_a_witness() {
        let limits = BudgetLimits {
            evaluation_limit: 1,
            ..BudgetLimits::default()
        };
        let run = synthesize_zero_positive_surprise(limits).unwrap();
        assert_eq!(run.report.status, SynthesisStatus::Incomplete);
        assert!(run.witness.is_none());
    }
}
