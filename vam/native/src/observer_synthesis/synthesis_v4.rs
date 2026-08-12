//! Exact v4 representation → transport → observer → explanation synthesis.

use std::collections::BTreeMap;

use super::ast::SynthesisCoreError;
use super::cegis::ExpectedRelation;
use super::diagnostics;
use super::grammar::{
    enumerate_observer_grammar_profile, grammar_config_for_profile, ObserverCandidate,
};
use super::grammar_profile::ObserverGrammarProfileId;
use super::hash::domain_sha256_hex;
use super::joint_synthesis::NativePartitionTaskId;
use super::representation_survey_v4::{
    enumerate_representation_family_v4, survey_representation_family_v4, RepresentationCandidateV4,
    RepresentationFamilyKindV4, RepresentationTaskClassV4, ALL_REPRESENTATION_FAMILIES_V4,
};
use super::semantics::{echo, observe, EchoOutcome, Observation, Recurrence, ResponseValue};
use super::transport_dsl::{compile_transport, CompiledTransportV1};

pub const OBSERVER_SYNTHESIS_V4_SCHEMA: &str =
    "veyra.systematic-representation-observer-synthesis.v4";
const RESULT_DOMAIN: &str = "veyra.systematic-representation-observer-synthesis.v4.binding";
const DIFF_DOMAIN: &str = "veyra.systematic-representation-observer-differential.v4.binding";
pub const MAX_V4_REPRESENTATIONS: usize = 52;
pub const MAX_V4_OBSERVERS: usize = 2_048;
pub const MAX_V4_RELATION_EVALUATIONS: usize = 2_000_000;
pub const MAX_V4_TOTAL_COST: usize = 1_024;
pub const OBSERVER_SYNTHESIS_V4_BOUNDARY: &str = "FOUND is the first exact unified-cost winner inside the declared versioned representation families, registered observer catalog, total-cost cap, and counters; EXHAUSTED covers that complete cost-admitted finite product only; CUTOFF is never exhaustion; optimized/reference equality covers terminal semantics, ledger, winner and bound inputs, while the intentional engine tag and its result digest remain distinct";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ObserverSynthesisStatusV4 {
    Found,
    Exhausted,
    Cutoff,
}

impl ObserverSynthesisStatusV4 {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Found => "FOUND",
            Self::Exhausted => "EXHAUSTED",
            Self::Cutoff => "CUTOFF",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ObserverSynthesisCutoffV4 {
    Representations,
    Observers,
    RelationEvaluations,
}

impl ObserverSynthesisCutoffV4 {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Representations => "representation-limit",
            Self::Observers => "observer-limit",
            Self::RelationEvaluations => "relation-evaluation-limit",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObserverSynthesisLimitsV4 {
    pub representation_limit: usize,
    pub observer_limit: usize,
    pub relation_evaluation_limit: usize,
}

impl Default for ObserverSynthesisLimitsV4 {
    fn default() -> Self {
        diagnostics::event("SYNTH_V4_LIMITS_DEFAULT", "constructing v4 search limits");
        Self {
            representation_limit: MAX_V4_REPRESENTATIONS,
            observer_limit: MAX_V4_OBSERVERS,
            relation_evaluation_limit: MAX_V4_RELATION_EVALUATIONS,
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ObserverSynthesisRequestV4 {
    pub task_id: NativePartitionTaskId,
    pub grammar_profile_id: ObserverGrammarProfileId,
    pub families: Vec<RepresentationFamilyKindV4>,
    pub maximum_total_cost: usize,
    pub limits: ObserverSynthesisLimitsV4,
}

impl ObserverSynthesisRequestV4 {
    pub fn systematic(
        task_id: NativePartitionTaskId,
        grammar_profile_id: ObserverGrammarProfileId,
    ) -> Self {
        diagnostics::event(
            "SYNTH_V4_REQUEST_ENTER",
            "constructing systematic v4 request",
        );
        let result = Self {
            task_id,
            grammar_profile_id,
            families: ALL_REPRESENTATION_FAMILIES_V4.to_vec(),
            maximum_total_cost: MAX_V4_TOTAL_COST,
            limits: ObserverSynthesisLimitsV4::default(),
        };
        diagnostics::event("SYNTH_V4_REQUEST_EXIT", "systematic v4 request constructed");
        result
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ObserverSynthesisLedgerV4 {
    pub limits: ObserverSynthesisLimitsV4,
    pub representations: usize,
    pub observers: usize,
    pub admissible_pairs: usize,
    pub pair_attempts: usize,
    pub relation_evaluations: usize,
    pub cutoff: Option<ObserverSynthesisCutoffV4>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ObserverExplanationV4 {
    pub pair_obligations: usize,
    pub response_classes: usize,
    pub target_classes: usize,
    pub explanation_cost: usize,
    pub equality_partition_exact: bool,
    pub explanation_digest: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ObserverSynthesisWinnerV4 {
    pub representation_ordinal: usize,
    pub representation_family: RepresentationFamilyKindV4,
    pub representation_class: RepresentationTaskClassV4,
    pub representation_cost: usize,
    pub transport_digest: String,
    pub transport_cost: usize,
    pub observer_ordinal: usize,
    pub observer_digest: String,
    pub observer_cost: usize,
    pub explanation: ObserverExplanationV4,
    pub total_cost: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ObserverSynthesisReportV4 {
    pub schema: &'static str,
    pub optimized: bool,
    pub status: ObserverSynthesisStatusV4,
    pub detail: &'static str,
    pub ledger: ObserverSynthesisLedgerV4,
    pub winner: Option<ObserverSynthesisWinnerV4>,
    pub family_digest: String,
    pub survey_digest: String,
    pub grammar_profile_digest: String,
    pub catalog_digest: String,
    pub maximum_total_cost: usize,
    pub result_digest: String,
    pub boundary: &'static str,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ObserverSynthesisDifferentialV4 {
    pub oracle: ObserverSynthesisReportV4,
    pub optimized: ObserverSynthesisReportV4,
    pub equivalent: bool,
    pub differential_digest: String,
    pub boundary: &'static str,
}

fn validate_request(request: &ObserverSynthesisRequestV4) -> Result<(), SynthesisCoreError> {
    diagnostics::event("SYNTH_V4_VALIDATE_ENTER", "validating v4 request");
    let limits = request.limits;
    if request.families.is_empty()
        || request.families.len() > ALL_REPRESENTATION_FAMILIES_V4.len()
        || request.families.windows(2).any(|pair| pair[0] >= pair[1])
        || request.maximum_total_cost == 0
        || request.maximum_total_cost > MAX_V4_TOTAL_COST
        || limits.representation_limit == 0
        || limits.representation_limit > MAX_V4_REPRESENTATIONS
        || limits.observer_limit == 0
        || limits.observer_limit > MAX_V4_OBSERVERS
        || limits.relation_evaluation_limit == 0
        || limits.relation_evaluation_limit > MAX_V4_RELATION_EVALUATIONS
    {
        diagnostics::event("SYNTH_V4_VALIDATE_REJECT", "v4 request rejected");
        return Err(SynthesisCoreError("invalid-observer-synthesis-v4-request"));
    }
    diagnostics::event("SYNTH_V4_VALIDATE_EXIT", "v4 request validated");
    Ok(())
}

fn validate_reference_request(
    request: &ObserverSynthesisRequestV4,
) -> Result<(), SynthesisCoreError> {
    diagnostics::event(
        "SYNTH_V4_REF_VALIDATE_ENTER",
        "validating reference request",
    );
    let limits = request.limits;
    let families_valid = !request.families.is_empty()
        && request.families.len() <= ALL_REPRESENTATION_FAMILIES_V4.len()
        && request.families.windows(2).all(|pair| pair[0] < pair[1]);
    let costs_valid = (1..=MAX_V4_TOTAL_COST).contains(&request.maximum_total_cost);
    let limits_valid = (1..=MAX_V4_REPRESENTATIONS).contains(&limits.representation_limit)
        && (1..=MAX_V4_OBSERVERS).contains(&limits.observer_limit)
        && (1..=MAX_V4_RELATION_EVALUATIONS).contains(&limits.relation_evaluation_limit);
    if !(families_valid && costs_valid && limits_valid) {
        diagnostics::event("SYNTH_V4_REF_VALIDATE_REJECT", "reference request rejected");
        return Err(SynthesisCoreError("invalid-observer-synthesis-v4-request"));
    }
    diagnostics::event("SYNTH_V4_REF_VALIDATE_EXIT", "reference request validated");
    Ok(())
}

fn compiled_states(
    representation: &RepresentationCandidateV4,
) -> Result<(CompiledTransportV1, [Recurrence; 4]), SynthesisCoreError> {
    diagnostics::event("SYNTH_V4_STATES_ENTER", "compiling representation states");
    let compiled = compile_transport(&representation.term)?;
    let image = compiled.image();
    let states = [
        Recurrence::new(image[0])?,
        Recurrence::new(image[1])?,
        Recurrence::new(image[2])?,
        Recurrence::new(image[3])?,
    ];
    diagnostics::event("SYNTH_V4_STATES_EXIT", "representation states compiled");
    Ok((compiled, states))
}

fn oracle_fits(
    candidate: &ObserverCandidate,
    states: [Recurrence; 4],
    targets: [u8; 4],
) -> Result<bool, SynthesisCoreError> {
    diagnostics::event(
        "SYNTH_V4_ORACLE_ENTER",
        "evaluating exhaustive pair semantics",
    );
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
                diagnostics::event("SYNTH_V4_ORACLE_EXIT", "exhaustive pair rejected");
                return Ok(false);
            }
        }
    }
    diagnostics::event("SYNTH_V4_ORACLE_EXIT", "exhaustive pair accepted");
    Ok(true)
}

fn optimized_fits(
    candidate: &ObserverCandidate,
    states: [Recurrence; 4],
    targets: [u8; 4],
) -> Result<bool, SynthesisCoreError> {
    diagnostics::event("SYNTH_V4_OPT_ENTER", "evaluating memoized pair semantics");
    let responses = states
        .into_iter()
        .map(|state| observe(&candidate.observer, state))
        .collect::<Result<Vec<_>, _>>()?;
    for left in 0..4 {
        for right in left + 1..4 {
            let expected_same = targets[left] == targets[right];
            let actual_same = match (&responses[left], &responses[right]) {
                (Observation::Ready(left), Observation::Ready(right)) => left == right,
                _ => {
                    diagnostics::event("SYNTH_V4_OPT_EXIT", "memoized pair domain blocked");
                    return Ok(false);
                }
            };
            if actual_same != expected_same {
                diagnostics::event("SYNTH_V4_OPT_EXIT", "memoized pair rejected");
                return Ok(false);
            }
        }
    }
    diagnostics::event("SYNTH_V4_OPT_EXIT", "memoized pair accepted");
    Ok(true)
}

fn unique_target_classes(targets: [u8; 4]) -> usize {
    diagnostics::event("SYNTH_V4_TARGET_CLASSES_ENTER", "counting target classes");
    let mut classes = Vec::new();
    for target in targets {
        if !classes.contains(&target) {
            classes.push(target);
        }
    }
    diagnostics::event("SYNTH_V4_TARGET_CLASSES_EXIT", "target classes counted");
    classes.len()
}

fn optimized_explanation(
    candidate: &ObserverCandidate,
    states: [Recurrence; 4],
    targets: [u8; 4],
) -> Result<ObserverExplanationV4, SynthesisCoreError> {
    diagnostics::event(
        "SYNTH_V4_EXPLAIN_ENTER",
        "building exact finite explanation",
    );
    let mut responses: Vec<ResponseValue> = Vec::new();
    let mut values = Vec::with_capacity(4);
    for state in states {
        let Observation::Ready(value) = observe(&candidate.observer, state)? else {
            return Err(SynthesisCoreError("v4-winner-explanation-domain"));
        };
        if !responses.contains(&value) {
            responses.push(value.clone());
        }
        values.push(value);
    }
    let equality_partition_exact = (0..4).all(|left| {
        ((left + 1)..4)
            .all(|right| (values[left] == values[right]) == (targets[left] == targets[right]))
    });
    let target_classes = unique_target_classes(targets);
    let explanation_cost = target_classes;
    let body = format!(
        "6:{}:{target_classes}:{explanation_cost}:{equality_partition_exact}",
        responses.len()
    );
    let result = ObserverExplanationV4 {
        pair_obligations: 6,
        response_classes: responses.len(),
        target_classes,
        explanation_cost,
        equality_partition_exact,
        explanation_digest: domain_sha256_hex(RESULT_DOMAIN, body.as_bytes()),
    };
    diagnostics::event("SYNTH_V4_EXPLAIN_EXIT", "exact finite explanation built");
    Ok(result)
}

fn reference_explanation(
    candidate: &ObserverCandidate,
    states: [Recurrence; 4],
    targets: [u8; 4],
) -> Result<ObserverExplanationV4, SynthesisCoreError> {
    diagnostics::event(
        "SYNTH_V4_REF_EXPLAIN_ENTER",
        "building reference explanation",
    );
    let mut values = Vec::with_capacity(4);
    for state in states {
        match observe(&candidate.observer, state)? {
            Observation::Ready(value) => values.push(value),
            Observation::Blocked(_) => {
                return Err(SynthesisCoreError("v4-winner-explanation-domain"));
            }
        }
    }
    let mut response_classes = 0;
    for index in 0..values.len() {
        if values[..index]
            .iter()
            .all(|earlier| earlier != &values[index])
        {
            response_classes += 1;
        }
    }
    let mut exact = true;
    for left in 0..4 {
        for right in left + 1..4 {
            exact &= (values[left] == values[right]) == (targets[left] == targets[right]);
        }
    }
    let mut target_values = targets.to_vec();
    target_values.sort_unstable();
    target_values.dedup();
    let target_classes = target_values.len();
    let explanation_cost = target_classes;
    let body = format!("6:{response_classes}:{target_classes}:{explanation_cost}:{exact}");
    let result = ObserverExplanationV4 {
        pair_obligations: 6,
        response_classes,
        target_classes,
        explanation_cost,
        equality_partition_exact: exact,
        explanation_digest: domain_sha256_hex(RESULT_DOMAIN, body.as_bytes()),
    };
    diagnostics::event("SYNTH_V4_REF_EXPLAIN_EXIT", "reference explanation built");
    Ok(result)
}

fn oracle_order(
    representations: &[RepresentationCandidateV4],
    observers: &[ObserverCandidate],
    explanation_cost: usize,
    maximum_total_cost: usize,
) -> Vec<(usize, usize)> {
    diagnostics::event("SYNTH_V4_ORACLE_ORDER_ENTER", "ordering exhaustive product");
    let mut rows = Vec::new();
    for (representation_ordinal, representation) in representations.iter().enumerate() {
        for (observer_ordinal, observer) in observers.iter().enumerate() {
            let total = representation.representation_cost
                + representation.transport_cost
                + observer.cost
                + explanation_cost;
            if total <= maximum_total_cost {
                rows.push((representation_ordinal, observer_ordinal));
            }
        }
    }
    rows.sort_by_key(|(representation_ordinal, observer_ordinal)| {
        let representation = &representations[*representation_ordinal];
        let observer = &observers[*observer_ordinal];
        (
            representation.representation_cost
                + representation.transport_cost
                + observer.cost
                + explanation_cost,
            representation.representation_cost,
            representation.transport_cost,
            observer.cost,
            *representation_ordinal,
            *observer_ordinal,
        )
    });
    diagnostics::event("SYNTH_V4_ORACLE_ORDER_EXIT", "exhaustive product ordered");
    rows
}

fn optimized_order(
    representations: &[RepresentationCandidateV4],
    observers: &[ObserverCandidate],
    explanation_cost: usize,
    maximum_total_cost: usize,
) -> Vec<(usize, usize)> {
    diagnostics::event("SYNTH_V4_OPT_ORDER_ENTER", "bucketing optimized product");
    let mut buckets = BTreeMap::new();
    for (representation_ordinal, representation) in representations.iter().enumerate() {
        for (observer_ordinal, observer) in observers.iter().enumerate() {
            let total = representation.representation_cost
                + representation.transport_cost
                + observer.cost
                + explanation_cost;
            if total <= maximum_total_cost {
                buckets.insert(
                    (
                        total,
                        representation.representation_cost,
                        representation.transport_cost,
                        observer.cost,
                        representation_ordinal,
                        observer_ordinal,
                    ),
                    (representation_ordinal, observer_ordinal),
                );
            }
        }
    }
    let rows = buckets.into_values().collect();
    diagnostics::event("SYNTH_V4_OPT_ORDER_EXIT", "optimized product bucketed");
    rows
}

#[allow(clippy::too_many_arguments)]
fn optimized_terminal(
    status: ObserverSynthesisStatusV4,
    detail: &'static str,
    ledger: ObserverSynthesisLedgerV4,
    winner: Option<ObserverSynthesisWinnerV4>,
    family_digest: String,
    survey_digest: String,
    grammar_profile_digest: String,
    catalog_digest: String,
    maximum_total_cost: usize,
) -> ObserverSynthesisReportV4 {
    diagnostics::event("SYNTH_V4_TERMINAL_ENTER", "binding v4 terminal report");
    let winner_root = winner.as_ref().map_or_else(
        || "none".to_owned(),
        |row| {
            format!(
                "{}:{}:{}:{}:{}:{}:{}:{}:{}:{}",
                row.representation_ordinal,
                row.representation_family.as_str(),
                row.representation_class.as_str(),
                row.representation_cost,
                row.transport_digest,
                row.transport_cost,
                row.observer_ordinal,
                row.observer_digest,
                row.observer_cost,
                row.total_cost
            )
        },
    );
    let body = format!(
        "true:{}:{detail}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{family_digest}:{survey_digest}:{grammar_profile_digest}:{catalog_digest}:{maximum_total_cost}:{winner_root}",
        status.as_str(),
        ledger.limits.representation_limit,
        ledger.limits.observer_limit,
        ledger.limits.relation_evaluation_limit,
        ledger.representations,
        ledger.observers,
        ledger.admissible_pairs,
        ledger.pair_attempts,
        ledger.relation_evaluations,
        ledger.cutoff.map_or("none", ObserverSynthesisCutoffV4::as_str),
        winner.as_ref().map_or("none", |row| row.explanation.explanation_digest.as_str()),
    );
    let result = ObserverSynthesisReportV4 {
        schema: OBSERVER_SYNTHESIS_V4_SCHEMA,
        optimized: true,
        status,
        detail,
        ledger,
        winner,
        family_digest,
        survey_digest,
        grammar_profile_digest,
        catalog_digest,
        maximum_total_cost,
        result_digest: domain_sha256_hex(RESULT_DOMAIN, body.as_bytes()),
        boundary: OBSERVER_SYNTHESIS_V4_BOUNDARY,
    };
    diagnostics::event("SYNTH_V4_TERMINAL_EXIT", "v4 terminal report bound");
    result
}

#[allow(clippy::too_many_arguments)]
fn reference_terminal(
    status: ObserverSynthesisStatusV4,
    detail: &'static str,
    ledger: ObserverSynthesisLedgerV4,
    winner: Option<ObserverSynthesisWinnerV4>,
    family_digest: String,
    survey_digest: String,
    grammar_profile_digest: String,
    catalog_digest: String,
    maximum_total_cost: usize,
) -> ObserverSynthesisReportV4 {
    diagnostics::event("SYNTH_V4_REF_TERMINAL_ENTER", "binding reference terminal");
    let winner_root = match winner.as_ref() {
        None => String::from("none"),
        Some(row) => format!(
            "{}:{}:{}:{}:{}:{}:{}:{}:{}:{}",
            row.representation_ordinal,
            row.representation_family.as_str(),
            row.representation_class.as_str(),
            row.representation_cost,
            row.transport_digest,
            row.transport_cost,
            row.observer_ordinal,
            row.observer_digest,
            row.observer_cost,
            row.total_cost
        ),
    };
    let cutoff = match ledger.cutoff {
        Some(value) => value.as_str(),
        None => "none",
    };
    let explanation = match winner.as_ref() {
        Some(row) => row.explanation.explanation_digest.as_str(),
        None => "none",
    };
    let body = format!(
        "false:{}:{detail}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{family_digest}:{survey_digest}:{grammar_profile_digest}:{catalog_digest}:{maximum_total_cost}:{winner_root}",
        status.as_str(),
        ledger.limits.representation_limit,
        ledger.limits.observer_limit,
        ledger.limits.relation_evaluation_limit,
        ledger.representations,
        ledger.observers,
        ledger.admissible_pairs,
        ledger.pair_attempts,
        ledger.relation_evaluations,
        cutoff,
        explanation,
    );
    let report = ObserverSynthesisReportV4 {
        schema: OBSERVER_SYNTHESIS_V4_SCHEMA,
        optimized: false,
        status,
        detail,
        ledger,
        winner,
        family_digest,
        survey_digest,
        grammar_profile_digest,
        catalog_digest,
        maximum_total_cost,
        result_digest: domain_sha256_hex(RESULT_DOMAIN, body.as_bytes()),
        boundary: OBSERVER_SYNTHESIS_V4_BOUNDARY,
    };
    diagnostics::event("SYNTH_V4_REF_TERMINAL_EXIT", "reference terminal bound");
    report
}

fn optimized_search(
    request: &ObserverSynthesisRequestV4,
) -> Result<ObserverSynthesisReportV4, SynthesisCoreError> {
    diagnostics::event("SYNTH_V4_SEARCH_ENTER", "starting v4 synthesis search");
    validate_request(request)?;
    let family = enumerate_representation_family_v4(&request.families)?;
    let survey = survey_representation_family_v4(request.task_id, &request.families)?;
    let grammar = enumerate_observer_grammar_profile(
        request.grammar_profile_id,
        grammar_config_for_profile(request.grammar_profile_id),
    )?;
    let mut ledger = ObserverSynthesisLedgerV4 {
        limits: request.limits,
        representations: 0,
        observers: 0,
        admissible_pairs: 0,
        pair_attempts: 0,
        relation_evaluations: 0,
        cutoff: None,
    };
    if family.candidates.len() > request.limits.representation_limit {
        ledger.cutoff = Some(ObserverSynthesisCutoffV4::Representations);
        return Ok(optimized_terminal(
            ObserverSynthesisStatusV4::Cutoff,
            "representation-limit",
            ledger,
            None,
            family.family_digest,
            survey.survey_digest,
            grammar.profile.profile_digest,
            grammar.enumeration.catalog_digest,
            request.maximum_total_cost,
        ));
    }
    ledger.representations = family.candidates.len();
    if grammar.enumeration.candidates.len() > request.limits.observer_limit {
        ledger.cutoff = Some(ObserverSynthesisCutoffV4::Observers);
        return Ok(optimized_terminal(
            ObserverSynthesisStatusV4::Cutoff,
            "observer-limit",
            ledger,
            None,
            family.family_digest,
            survey.survey_digest,
            grammar.profile.profile_digest,
            grammar.enumeration.catalog_digest,
            request.maximum_total_cost,
        ));
    }
    ledger.observers = grammar.enumeration.candidates.len();
    let targets = request.task_id.target_classes();
    let explanation_cost = unique_target_classes(targets);
    let order = optimized_order(
        &family.candidates,
        &grammar.enumeration.candidates,
        explanation_cost,
        request.maximum_total_cost,
    );
    ledger.admissible_pairs = order.len();
    for (representation_ordinal, observer_ordinal) in order {
        if ledger.relation_evaluations.saturating_add(6) > request.limits.relation_evaluation_limit
        {
            ledger.cutoff = Some(ObserverSynthesisCutoffV4::RelationEvaluations);
            return Ok(optimized_terminal(
                ObserverSynthesisStatusV4::Cutoff,
                "relation-evaluation-limit",
                ledger,
                None,
                family.family_digest,
                survey.survey_digest,
                grammar.profile.profile_digest,
                grammar.enumeration.catalog_digest,
                request.maximum_total_cost,
            ));
        }
        ledger.pair_attempts += 1;
        ledger.relation_evaluations += 6;
        let representation = &family.candidates[representation_ordinal];
        let candidate = &grammar.enumeration.candidates[observer_ordinal];
        let (_, states) = compiled_states(representation)?;
        let fits = optimized_fits(candidate, states, targets)?;
        if fits {
            let explanation = optimized_explanation(candidate, states, targets)?;
            if !explanation.equality_partition_exact {
                return Err(SynthesisCoreError("v4-winner-explanation-mismatch"));
            }
            let total_cost = representation.representation_cost
                + representation.transport_cost
                + candidate.cost
                + explanation.explanation_cost;
            let winner = ObserverSynthesisWinnerV4 {
                representation_ordinal,
                representation_family: representation.family,
                representation_class: survey.rows[representation_ordinal].classification,
                representation_cost: representation.representation_cost,
                transport_digest: representation.transport_digest.clone(),
                transport_cost: representation.transport_cost,
                observer_ordinal,
                observer_digest: candidate.digest.clone(),
                observer_cost: candidate.cost,
                explanation,
                total_cost,
            };
            diagnostics::event("SYNTH_V4_SEARCH_EXIT", "v4 synthesis winner found");
            return Ok(optimized_terminal(
                ObserverSynthesisStatusV4::Found,
                "first-unified-cost-winner",
                ledger,
                Some(winner),
                family.family_digest,
                survey.survey_digest,
                grammar.profile.profile_digest,
                grammar.enumeration.catalog_digest,
                request.maximum_total_cost,
            ));
        }
    }
    diagnostics::event("SYNTH_V4_SEARCH_EXIT", "v4 admitted product exhausted");
    Ok(optimized_terminal(
        ObserverSynthesisStatusV4::Exhausted,
        "exact-admitted-product-exhausted",
        ledger,
        None,
        family.family_digest,
        survey.survey_digest,
        grammar.profile.profile_digest,
        grammar.enumeration.catalog_digest,
        request.maximum_total_cost,
    ))
}

fn reference_search(
    request: &ObserverSynthesisRequestV4,
) -> Result<ObserverSynthesisReportV4, SynthesisCoreError> {
    diagnostics::event(
        "SYNTH_V4_REF_SEARCH_ENTER",
        "starting independent exhaustive reference",
    );
    validate_reference_request(request)?;
    let family = enumerate_representation_family_v4(&request.families)?;
    let survey = survey_representation_family_v4(request.task_id, &request.families)?;
    let grammar = enumerate_observer_grammar_profile(
        request.grammar_profile_id,
        grammar_config_for_profile(request.grammar_profile_id),
    )?;
    let mut ledger = ObserverSynthesisLedgerV4 {
        limits: request.limits,
        representations: 0,
        observers: 0,
        admissible_pairs: 0,
        pair_attempts: 0,
        relation_evaluations: 0,
        cutoff: None,
    };
    if request.limits.representation_limit < family.candidates.len() {
        ledger.cutoff = Some(ObserverSynthesisCutoffV4::Representations);
        return Ok(reference_terminal(
            ObserverSynthesisStatusV4::Cutoff,
            "representation-limit",
            ledger,
            None,
            family.family_digest,
            survey.survey_digest,
            grammar.profile.profile_digest,
            grammar.enumeration.catalog_digest,
            request.maximum_total_cost,
        ));
    }
    ledger.representations = family.candidates.len();
    if request.limits.observer_limit < grammar.enumeration.candidates.len() {
        ledger.cutoff = Some(ObserverSynthesisCutoffV4::Observers);
        return Ok(reference_terminal(
            ObserverSynthesisStatusV4::Cutoff,
            "observer-limit",
            ledger,
            None,
            family.family_digest,
            survey.survey_digest,
            grammar.profile.profile_digest,
            grammar.enumeration.catalog_digest,
            request.maximum_total_cost,
        ));
    }
    ledger.observers = grammar.enumeration.candidates.len();
    let targets = request.task_id.target_classes();
    let mut target_classes = targets.to_vec();
    target_classes.sort_unstable();
    target_classes.dedup();
    let ordered_pairs = oracle_order(
        &family.candidates,
        &grammar.enumeration.candidates,
        target_classes.len(),
        request.maximum_total_cost,
    );
    ledger.admissible_pairs = ordered_pairs.len();
    for pair in ordered_pairs {
        let next_charge = match ledger.relation_evaluations.checked_add(6) {
            Some(value) => value,
            None => return Err(SynthesisCoreError("v4-reference-relation-overflow")),
        };
        if next_charge > request.limits.relation_evaluation_limit {
            ledger.cutoff = Some(ObserverSynthesisCutoffV4::RelationEvaluations);
            return Ok(reference_terminal(
                ObserverSynthesisStatusV4::Cutoff,
                "relation-evaluation-limit",
                ledger,
                None,
                family.family_digest,
                survey.survey_digest,
                grammar.profile.profile_digest,
                grammar.enumeration.catalog_digest,
                request.maximum_total_cost,
            ));
        }
        ledger.relation_evaluations = next_charge;
        ledger.pair_attempts += 1;
        let representation_ordinal = pair.0;
        let observer_ordinal = pair.1;
        let representation = &family.candidates[representation_ordinal];
        let observer = &grammar.enumeration.candidates[observer_ordinal];
        let (_, states) = compiled_states(representation)?;
        if oracle_fits(observer, states, targets)? {
            let explanation = reference_explanation(observer, states, targets)?;
            if !explanation.equality_partition_exact {
                return Err(SynthesisCoreError("v4-reference-explanation-mismatch"));
            }
            let total_cost = representation.representation_cost
                + representation.transport_cost
                + observer.cost
                + explanation.explanation_cost;
            let winner = ObserverSynthesisWinnerV4 {
                representation_ordinal,
                representation_family: representation.family,
                representation_class: survey.rows[representation_ordinal].classification,
                representation_cost: representation.representation_cost,
                transport_digest: representation.transport_digest.clone(),
                transport_cost: representation.transport_cost,
                observer_ordinal,
                observer_digest: observer.digest.clone(),
                observer_cost: observer.cost,
                explanation,
                total_cost,
            };
            diagnostics::event("SYNTH_V4_REF_SEARCH_EXIT", "reference winner found");
            return Ok(reference_terminal(
                ObserverSynthesisStatusV4::Found,
                "first-unified-cost-winner",
                ledger,
                Some(winner),
                family.family_digest,
                survey.survey_digest,
                grammar.profile.profile_digest,
                grammar.enumeration.catalog_digest,
                request.maximum_total_cost,
            ));
        }
    }
    diagnostics::event("SYNTH_V4_REF_SEARCH_EXIT", "reference product exhausted");
    Ok(reference_terminal(
        ObserverSynthesisStatusV4::Exhausted,
        "exact-admitted-product-exhausted",
        ledger,
        None,
        family.family_digest,
        survey.survey_digest,
        grammar.profile.profile_digest,
        grammar.enumeration.catalog_digest,
        request.maximum_total_cost,
    ))
}

pub fn synthesize_representation_observer_v4(
    request: &ObserverSynthesisRequestV4,
) -> Result<ObserverSynthesisReportV4, SynthesisCoreError> {
    diagnostics::event("SYNTH_V4_OPTIMIZED_ENTER", "running optimized v4 synthesis");
    let result = optimized_search(request);
    diagnostics::event(
        if result.is_ok() {
            "SYNTH_V4_OPTIMIZED_EXIT"
        } else {
            "SYNTH_V4_OPTIMIZED_REJECT"
        },
        "optimized v4 synthesis completed",
    );
    result
}

pub fn synthesize_representation_observer_v4_exhaustive(
    request: &ObserverSynthesisRequestV4,
) -> Result<ObserverSynthesisReportV4, SynthesisCoreError> {
    diagnostics::event("SYNTH_V4_ORACLE_RUN_ENTER", "running exhaustive v4 oracle");
    let result = reference_search(request);
    diagnostics::event(
        if result.is_ok() {
            "SYNTH_V4_ORACLE_RUN_EXIT"
        } else {
            "SYNTH_V4_ORACLE_RUN_REJECT"
        },
        "exhaustive v4 oracle completed",
    );
    result
}

pub fn differential_representation_observer_v4(
    request: &ObserverSynthesisRequestV4,
) -> Result<ObserverSynthesisDifferentialV4, SynthesisCoreError> {
    diagnostics::event("SYNTH_V4_DIFF_ENTER", "starting v4 differential");
    let oracle = synthesize_representation_observer_v4_exhaustive(request)?;
    let optimized = synthesize_representation_observer_v4(request)?;
    let equivalent = oracle.status == optimized.status
        && oracle.detail == optimized.detail
        && oracle.ledger == optimized.ledger
        && oracle.winner == optimized.winner
        && oracle.family_digest == optimized.family_digest
        && oracle.survey_digest == optimized.survey_digest
        && oracle.grammar_profile_digest == optimized.grammar_profile_digest
        && oracle.catalog_digest == optimized.catalog_digest
        && oracle.maximum_total_cost == optimized.maximum_total_cost;
    let body = format!(
        "{}:{}:{equivalent}",
        oracle.result_digest, optimized.result_digest
    );
    let result = ObserverSynthesisDifferentialV4 {
        oracle,
        optimized,
        equivalent,
        differential_digest: domain_sha256_hex(DIFF_DOMAIN, body.as_bytes()),
        boundary: OBSERVER_SYNTHESIS_V4_BOUNDARY,
    };
    diagnostics::event(
        if equivalent {
            "SYNTH_V4_DIFF_EXIT"
        } else {
            "SYNTH_V4_DIFF_DIVERGED"
        },
        "v4 differential completed",
    );
    Ok(result)
}
