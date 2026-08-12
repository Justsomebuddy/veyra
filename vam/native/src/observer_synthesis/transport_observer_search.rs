//! Exact joint search over caller-declared typed transports and registered observers.

use super::ast::SynthesisCoreError;
use super::cegis::ExpectedRelation;
use super::diagnostics;
use super::grammar::{
    enumerate_observer_grammar_profile, grammar_config_for_profile, ObserverCandidate,
};
use super::grammar_profile::ObserverGrammarProfileId;
use super::hash::domain_sha256_hex;
use super::joint_synthesis::{
    JointBudgetCutoff, JointSynthesisLedger, JointSynthesisLimits, JointSynthesisStatus,
    NativePartitionTaskId, MAX_JOINT_CANDIDATES, MAX_JOINT_RELATION_EVALUATIONS,
    MAX_JOINT_TRANSFORMS,
};
use super::semantics::{echo, observe, EchoOutcome, Observation, Recurrence};
use super::transport_dsl::{
    compile_transport, CompiledTransportV1, TransportInformationClassV1, TransportTermV1,
};

pub const DIRECT_SEARCH_SCHEMA: &str = "veyra.typed-transport-observer-search.v3";
const DIRECT_SEARCH_DOMAIN: &str = "veyra.typed-transport-observer-search.v3.binding";
const DIRECT_DIFF_DOMAIN: &str = "veyra.typed-transport-observer-search.differential.v3.binding";
pub const DIRECT_SEARCH_BOUNDARY: &str = "exact finite cost-ordered search over only the declared compiled four-state transport candidates and one registered observer catalog; equivalence is between independent exhaustive and bucketed implementations for the exact budgets and inputs";

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DirectSearchWinnerV3 {
    pub joint_cost: usize,
    pub transport_ordinal: usize,
    pub transport_cost: usize,
    pub transport_digest: String,
    pub information_class: TransportInformationClassV1,
    pub collision_count: u32,
    pub observer_ordinal: usize,
    pub observer_cost: usize,
    pub observer_digest: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DirectSearchReportV3 {
    pub schema: &'static str,
    pub optimized: bool,
    pub status: JointSynthesisStatus,
    pub detail: &'static str,
    pub ledger: JointSynthesisLedger,
    pub winner: Option<DirectSearchWinnerV3>,
    pub profile_digest: String,
    pub catalog_digest: String,
    pub declared_transport_digest: String,
    pub result_digest: String,
    pub boundary: &'static str,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DirectSearchDifferentialV3 {
    pub oracle: DirectSearchReportV3,
    pub optimized: DirectSearchReportV3,
    pub equivalent: bool,
    pub differential_digest: String,
    pub boundary: &'static str,
}

fn validate_limits(limits: JointSynthesisLimits) -> Result<(), SynthesisCoreError> {
    diagnostics::event("DIRECT_LIMITS_ENTER", "validating direct search limits");
    if limits.transform_limit == 0
        || limits.transform_limit > MAX_JOINT_TRANSFORMS
        || limits.candidate_limit == 0
        || limits.candidate_limit > MAX_JOINT_CANDIDATES
        || limits.relation_evaluation_limit == 0
        || limits.relation_evaluation_limit > MAX_JOINT_RELATION_EVALUATIONS
    {
        diagnostics::event("DIRECT_LIMITS_REJECT", "direct search limits rejected");
        return Err(SynthesisCoreError("invalid-direct-search-limits"));
    }
    diagnostics::event("DIRECT_LIMITS_EXIT", "direct search limits validated");
    Ok(())
}

fn compile_declared(
    terms: &[TransportTermV1],
) -> Result<(Vec<CompiledTransportV1>, String), SynthesisCoreError> {
    diagnostics::event("DIRECT_COMPILE_ENTER", "compiling declared transport set");
    if terms.is_empty() || terms.len() > MAX_JOINT_TRANSFORMS {
        diagnostics::event("DIRECT_COMPILE_REJECT", "declared transport count rejected");
        return Err(SynthesisCoreError("invalid-direct-transport-count"));
    }
    let mut compiled = Vec::with_capacity(terms.len());
    for term in terms {
        let row = compile_transport(term).inspect_err(|_| {
            diagnostics::event("DIRECT_COMPILE_REJECT", "declared transport rejected")
        })?;
        if row.source().cardinality() != 4
            || row
                .image()
                .iter()
                .any(|value| *value > super::semantics::MAX_RECURRENCE_PULSES)
        {
            diagnostics::event(
                "DIRECT_COMPILE_REJECT",
                "transport is outside recurrence task",
            );
            return Err(SynthesisCoreError("direct-transport-recurrence-domain"));
        }
        compiled.push(row);
    }
    let body = compiled
        .iter()
        .enumerate()
        .map(|(ordinal, row)| format!("{ordinal}:{}", row.digest()))
        .collect::<Vec<_>>()
        .join("|");
    let digest = domain_sha256_hex(DIRECT_SEARCH_DOMAIN, body.as_bytes());
    diagnostics::event("DIRECT_COMPILE_EXIT", "declared transport set compiled");
    Ok((compiled, digest))
}

fn recurrences(transport: &CompiledTransportV1) -> Result<[Recurrence; 4], SynthesisCoreError> {
    diagnostics::event(
        "DIRECT_STATES_ENTER",
        "constructing transported recurrence states",
    );
    let rows = transport.image();
    let result = [
        Recurrence::new(rows[0])?,
        Recurrence::new(rows[1])?,
        Recurrence::new(rows[2])?,
        Recurrence::new(rows[3])?,
    ];
    diagnostics::event(
        "DIRECT_STATES_EXIT",
        "transported recurrence states constructed",
    );
    Ok(result)
}

fn satisfies_oracle(
    candidate: &ObserverCandidate,
    transport: &CompiledTransportV1,
    targets: [u8; 4],
) -> Result<bool, SynthesisCoreError> {
    diagnostics::event("DIRECT_ORACLE_PAIR_ENTER", "evaluating exhaustive pair");
    let states = recurrences(transport)?;
    for left in 0..4 {
        for right in left + 1..4 {
            let expected = if targets[left] == targets[right] {
                ExpectedRelation::Echo
            } else {
                ExpectedRelation::Separate
            };
            let actual = match echo(&candidate.observer, states[left], states[right])? {
                EchoOutcome::Echo(_) => ExpectedRelation::Echo,
                EchoOutcome::Mismatch { .. } => ExpectedRelation::Separate,
                EchoOutcome::DomainBlocked { .. } => ExpectedRelation::DomainBlocked,
            };
            if actual != expected {
                diagnostics::event("DIRECT_ORACLE_PAIR_EXIT", "exhaustive pair rejected task");
                return Ok(false);
            }
        }
    }
    diagnostics::event("DIRECT_ORACLE_PAIR_EXIT", "exhaustive pair satisfied task");
    Ok(true)
}

fn satisfies_memoized(
    candidate: &ObserverCandidate,
    transport: &CompiledTransportV1,
    targets: [u8; 4],
) -> Result<bool, SynthesisCoreError> {
    diagnostics::event("DIRECT_OPT_PAIR_ENTER", "evaluating memoized pair");
    let states = recurrences(transport)?;
    let responses = states
        .into_iter()
        .map(|state| observe(&candidate.observer, state))
        .collect::<Result<Vec<_>, _>>()?;
    for left in 0..4 {
        for right in left + 1..4 {
            let expected = if targets[left] == targets[right] {
                ExpectedRelation::Echo
            } else {
                ExpectedRelation::Separate
            };
            let actual = match (&responses[left], &responses[right]) {
                (Observation::Ready(left), Observation::Ready(right)) if left == right => {
                    ExpectedRelation::Echo
                }
                (Observation::Ready(_), Observation::Ready(_)) => ExpectedRelation::Separate,
                _ => ExpectedRelation::DomainBlocked,
            };
            if actual != expected {
                diagnostics::event("DIRECT_OPT_PAIR_EXIT", "memoized pair rejected task");
                return Ok(false);
            }
        }
    }
    diagnostics::event("DIRECT_OPT_PAIR_EXIT", "memoized pair satisfied task");
    Ok(true)
}

#[allow(clippy::too_many_arguments)]
fn terminal(
    optimized: bool,
    task: NativePartitionTaskId,
    profile_digest: String,
    catalog_digest: String,
    declared_transport_digest: String,
    status: JointSynthesisStatus,
    detail: &'static str,
    ledger: JointSynthesisLedger,
    winner: Option<DirectSearchWinnerV3>,
) -> DirectSearchReportV3 {
    diagnostics::event("DIRECT_TERMINAL_ENTER", "binding direct search terminal");
    let winner_root = winner.as_ref().map_or_else(
        || "null".to_owned(),
        |row| {
            format!(
                "{}:{}:{}:{}:{}:{}:{}:{}:{}",
                row.transport_ordinal,
                row.transport_cost,
                row.transport_digest,
                row.information_class.as_str(),
                row.collision_count,
                row.observer_ordinal,
                row.observer_cost,
                row.observer_digest,
                row.joint_cost
            )
        },
    );
    let body = format!(
        "{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}",
        optimized,
        task.as_str(),
        profile_digest,
        catalog_digest,
        declared_transport_digest,
        status.as_str(),
        detail,
        ledger.limits.transform_limit,
        ledger.limits.candidate_limit,
        ledger.limits.relation_evaluation_limit,
        ledger.transforms,
        ledger.candidates,
        ledger.pair_attempts,
        ledger.relation_evaluations,
        ledger.cutoff.map_or("none", JointBudgetCutoff::as_str),
        winner_root
    );
    let result = DirectSearchReportV3 {
        schema: DIRECT_SEARCH_SCHEMA,
        optimized,
        status,
        detail,
        ledger,
        winner,
        profile_digest,
        catalog_digest,
        declared_transport_digest,
        result_digest: domain_sha256_hex(DIRECT_SEARCH_DOMAIN, body.as_bytes()),
        boundary: DIRECT_SEARCH_BOUNDARY,
    };
    diagnostics::event("DIRECT_TERMINAL_EXIT", "direct search terminal bound");
    result
}

fn search(
    task: NativePartitionTaskId,
    profile: ObserverGrammarProfileId,
    terms: &[TransportTermV1],
    limits: JointSynthesisLimits,
    optimized: bool,
) -> Result<DirectSearchReportV3, SynthesisCoreError> {
    diagnostics::event("DIRECT_SEARCH_ENTER", "starting direct joint search");
    validate_limits(limits)?;
    let (compiled, transport_digest) = compile_declared(terms)?;
    let grammar = enumerate_observer_grammar_profile(profile, grammar_config_for_profile(profile))?;
    let mut ledger = JointSynthesisLedger {
        limits,
        transforms: 0,
        candidates: 0,
        pair_attempts: 0,
        relation_evaluations: 0,
        cutoff: None,
    };
    if compiled.len() > limits.transform_limit {
        ledger.cutoff = Some(JointBudgetCutoff::Transforms);
        return Ok(terminal(
            optimized,
            task,
            grammar.profile.profile_digest,
            grammar.enumeration.catalog_digest,
            transport_digest,
            JointSynthesisStatus::Incomplete,
            "transform-limit",
            ledger,
            None,
        ));
    }
    ledger.transforms = compiled.len();
    if grammar.enumeration.candidates.len() > limits.candidate_limit {
        ledger.cutoff = Some(JointBudgetCutoff::Candidates);
        return Ok(terminal(
            optimized,
            task,
            grammar.profile.profile_digest,
            grammar.enumeration.catalog_digest,
            transport_digest,
            JointSynthesisStatus::Incomplete,
            "candidate-limit",
            ledger,
            None,
        ));
    }
    ledger.candidates = grammar.enumeration.candidates.len();
    let max_t = compiled
        .iter()
        .map(|row| row.cost() as usize)
        .max()
        .unwrap_or(0);
    let max_o = grammar
        .enumeration
        .candidates
        .iter()
        .map(|row| row.cost)
        .max()
        .unwrap_or(0);
    let mut ordered_pairs = Vec::new();
    if optimized {
        for cost in 0..=max_t + max_o {
            for transport_cost in 0..=cost {
                let observer_cost = cost - transport_cost;
                for (transport_ordinal, _) in compiled
                    .iter()
                    .enumerate()
                    .filter(|(_, row)| row.cost() as usize == transport_cost)
                {
                    for (observer_ordinal, _) in grammar
                        .enumeration
                        .candidates
                        .iter()
                        .enumerate()
                        .filter(|(_, row)| row.cost == observer_cost)
                    {
                        ordered_pairs.push((cost, transport_ordinal, observer_ordinal));
                    }
                }
            }
        }
    } else {
        for (transport_ordinal, transport) in compiled.iter().enumerate() {
            for (observer_ordinal, candidate) in grammar.enumeration.candidates.iter().enumerate() {
                ordered_pairs.push((
                    transport.cost() as usize + candidate.cost,
                    transport_ordinal,
                    observer_ordinal,
                ));
            }
        }
        ordered_pairs.sort_by_key(|(cost, transport_ordinal, observer_ordinal)| {
            (
                *cost,
                compiled[*transport_ordinal].cost(),
                grammar.enumeration.candidates[*observer_ordinal].cost,
                *transport_ordinal,
                *observer_ordinal,
            )
        });
    }
    for (cost, transport_ordinal, observer_ordinal) in ordered_pairs {
        let transport = &compiled[transport_ordinal];
        let candidate = &grammar.enumeration.candidates[observer_ordinal];
        let transport_cost = transport.cost() as usize;
        let observer_cost = candidate.cost;
        let charged = ledger
            .relation_evaluations
            .checked_add(6)
            .ok_or(SynthesisCoreError("direct-relation-overflow"))?;
        if charged > limits.relation_evaluation_limit {
            ledger.cutoff = Some(JointBudgetCutoff::RelationEvaluations);
            return Ok(terminal(
                optimized,
                task,
                grammar.profile.profile_digest,
                grammar.enumeration.catalog_digest,
                transport_digest,
                JointSynthesisStatus::Incomplete,
                "relation-evaluation-limit",
                ledger,
                None,
            ));
        }
        ledger.relation_evaluations = charged;
        ledger.pair_attempts += 1;
        let satisfied = if optimized {
            satisfies_memoized(candidate, transport, task.target_classes())?
        } else {
            satisfies_oracle(candidate, transport, task.target_classes())?
        };
        if satisfied {
            let winner = DirectSearchWinnerV3 {
                joint_cost: cost,
                transport_ordinal,
                transport_cost,
                transport_digest: transport.digest().to_owned(),
                information_class: transport.information_class(),
                collision_count: transport.collision_count(),
                observer_ordinal,
                observer_cost,
                observer_digest: candidate.digest.clone(),
            };
            diagnostics::event("DIRECT_SEARCH_EXIT", "direct winner found");
            return Ok(terminal(
                optimized,
                task,
                grammar.profile.profile_digest,
                grammar.enumeration.catalog_digest,
                transport_digest,
                JointSynthesisStatus::Found,
                "first-cost-ordered-winner",
                ledger,
                Some(winner),
            ));
        }
    }
    diagnostics::event("DIRECT_SEARCH_EXIT", "direct product exhausted");
    Ok(terminal(
        optimized,
        task,
        grammar.profile.profile_digest,
        grammar.enumeration.catalog_digest,
        transport_digest,
        JointSynthesisStatus::Exhausted,
        "exact-declared-product-exhausted",
        ledger,
        None,
    ))
}

pub fn differential_transport_observer_search(
    task: NativePartitionTaskId,
    profile: ObserverGrammarProfileId,
    terms: &[TransportTermV1],
    limits: JointSynthesisLimits,
) -> Result<DirectSearchDifferentialV3, SynthesisCoreError> {
    diagnostics::event("DIRECT_DIFF_ENTER", "starting direct search differential");
    let oracle = search(task, profile, terms, limits, false)?;
    let optimized = search(task, profile, terms, limits, true)?;
    let equivalent = oracle.status == optimized.status
        && oracle.detail == optimized.detail
        && oracle.ledger == optimized.ledger
        && oracle.winner == optimized.winner
        && oracle.profile_digest == optimized.profile_digest
        && oracle.catalog_digest == optimized.catalog_digest
        && oracle.declared_transport_digest == optimized.declared_transport_digest;
    let body = format!(
        "{}:{}:{}",
        oracle.result_digest, optimized.result_digest, equivalent
    );
    let result = DirectSearchDifferentialV3 {
        oracle,
        optimized,
        equivalent,
        differential_digest: domain_sha256_hex(DIRECT_DIFF_DOMAIN, body.as_bytes()),
        boundary: DIRECT_SEARCH_BOUNDARY,
    };
    diagnostics::event(
        if equivalent {
            "DIRECT_DIFF_EXIT"
        } else {
            "DIRECT_DIFF_DIVERGED"
        },
        "direct search differential completed",
    );
    Ok(result)
}
