//! Exact finite observer-gap experiment over explicitly named baselines.

use super::ast::SynthesisCoreError;
use super::cegis::ExpectedRelation;
use super::diagnostics;
use super::grammar::{
    enumerate_observer_grammar_profile, grammar_config_for_profile, ObserverCandidate,
};
use super::grammar_profile::ObserverGrammarProfileId;
use super::hash::domain_sha256_hex;
use super::joint_search_optimized::{
    differential_joint_search, JointDifferentialVerdictV1, JointSearchDifferentialV1,
};
use super::joint_synthesis::{
    JointSynthesisLedger, JointSynthesisLimits, JointSynthesisStatus, NativePartitionTaskId,
};
use super::representation_family::{encoded_recurrences, enumerate_representation_family};
use super::semantics::{echo, observe, EchoOutcome, Observation, ResponseValue};
use super::transport_dsl::CompiledTransportV1;
use super::transport_observer_search::DirectSearchDifferentialV3;

pub const OBSERVER_GAP_LAB_SCHEMA: &str = "veyra.observer-gap-lab.v1";
const OBSERVER_GAP_DOMAIN: &str = "veyra.observer-gap-lab.v1.binding";
const BASELINE_DOMAIN: &str = "veyra.observer-gap-lab.baselines.v1.binding";
const POLICY_DOMAIN: &str = "veyra.observer-gap-lab.policy.v1.binding";
pub const OBSERVER_GAP_LAB_BOUNDARY: &str = "the observer-gap vector is an exact finite comparison between one synthesized winner and the explicitly named baseline set over four states and six pair obligations; it does not establish hidden variables, causal structure, generalization, or superiority outside this registered task and grammar";
const MAX_BASELINES: usize = 16;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ObserverGapStatusV1 {
    Positive,
    NoGap,
    Incomplete,
    Blocked,
}

impl ObserverGapStatusV1 {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Positive => "POSITIVE",
            Self::NoGap => "NO_GAP",
            Self::Incomplete => "INCOMPLETE",
            Self::Blocked => "BLOCKED",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ObserverGapPolicyV1 {
    pub minimum_fit_gain: i32,
    pub minimum_class_saving_gain: i32,
    pub maximum_cost_delta: i32,
    pub permit_information_loss: bool,
}

impl Default for ObserverGapPolicyV1 {
    fn default() -> Self {
        diagnostics::event("GAP_POLICY_DEFAULT_ENTER", "constructing finite gap policy");
        let result = Self {
            minimum_fit_gain: 1,
            minimum_class_saving_gain: 1,
            maximum_cost_delta: 16,
            permit_information_loss: false,
        };
        diagnostics::event("GAP_POLICY_DEFAULT_EXIT", "finite gap policy constructed");
        result
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NamedObserverBaselineV1 {
    pub name: String,
    pub observer_ordinal: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObserverGapRequestV1 {
    pub task_id: NativePartitionTaskId,
    pub grammar_profile_id: ObserverGrammarProfileId,
    pub joint_limits: JointSynthesisLimits,
    pub baselines: Vec<NamedObserverBaselineV1>,
    pub policy: ObserverGapPolicyV1,
    pub information_loss_penalty: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObserverGapVectorV1 {
    pub obligations: usize,
    pub baseline_name: String,
    pub baseline_ordinal: usize,
    pub baseline_hits: usize,
    pub winner_hits: usize,
    pub fit_gain: i32,
    pub baseline_response_classes: usize,
    pub winner_response_classes: usize,
    pub class_saving_gain: i32,
    pub cost_delta: i32,
    pub transform_cost: usize,
    pub observer_cost: usize,
    pub explanation_cost: usize,
    pub total_cost: usize,
    pub information_loss_penalty: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObserverGapWitnessV1 {
    pub transform_ordinal: usize,
    pub transform_digest: String,
    pub observer_ordinal: usize,
    pub observer_digest: String,
    pub vector: ObserverGapVectorV1,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObserverGapReceiptV1 {
    pub schema: &'static str,
    pub status: ObserverGapStatusV1,
    pub detail: &'static str,
    pub task_id: NativePartitionTaskId,
    pub grammar_profile_id: ObserverGrammarProfileId,
    pub differential_digest: String,
    pub baseline_set_digest: String,
    pub policy_digest: String,
    pub joint_ledger: JointSynthesisLedger,
    pub baseline_relation_evaluations: usize,
    pub witness: Option<ObserverGapWitnessV1>,
    pub receipt_digest: String,
    pub boundary: &'static str,
}

fn push_len_bytes(target: &mut Vec<u8>, bytes: &[u8]) {
    diagnostics::event("GAP_BIND_FIELD_ENTER", "binding one length-framed field");
    target.extend_from_slice(&(bytes.len() as u64).to_be_bytes());
    target.extend_from_slice(bytes);
    diagnostics::event("GAP_BIND_FIELD_EXIT", "length-framed field bound");
}

fn validate_and_bind_baselines(
    baselines: &[NamedObserverBaselineV1],
    candidate_count: usize,
) -> Result<String, SynthesisCoreError> {
    diagnostics::event("GAP_BASELINES_ENTER", "validating named baseline set");
    if baselines.is_empty() || baselines.len() > MAX_BASELINES {
        diagnostics::event("GAP_BASELINES_REJECT", "baseline count rejected");
        return Err(SynthesisCoreError("invalid-observer-gap-baseline-count"));
    }
    let mut previous: Option<&str> = None;
    let mut bytes = Vec::new();
    for baseline in baselines {
        if baseline.name.is_empty()
            || baseline.name.len() > 64
            || baseline.name.as_bytes().contains(&0)
            || previous.is_some_and(|name| name >= baseline.name.as_str())
            || baseline.observer_ordinal >= candidate_count
        {
            diagnostics::event("GAP_BASELINES_REJECT", "baseline row rejected");
            return Err(SynthesisCoreError("invalid-observer-gap-baseline"));
        }
        previous = Some(&baseline.name);
        push_len_bytes(&mut bytes, baseline.name.as_bytes());
        bytes.extend_from_slice(&(baseline.observer_ordinal as u64).to_be_bytes());
    }
    let result = domain_sha256_hex(BASELINE_DOMAIN, &bytes);
    diagnostics::event("GAP_BASELINES_EXIT", "named baseline set validated");
    Ok(result)
}

fn bind_policy(policy: ObserverGapPolicyV1) -> Result<String, SynthesisCoreError> {
    diagnostics::event("GAP_POLICY_ENTER", "validating gap policy");
    if policy.minimum_fit_gain < 0
        || policy.minimum_fit_gain > 6
        || policy.minimum_class_saving_gain < 0
        || policy.minimum_class_saving_gain > 3
        || policy.maximum_cost_delta < 0
        || policy.maximum_cost_delta > 1_000
    {
        diagnostics::event("GAP_POLICY_REJECT", "gap policy rejected");
        return Err(SynthesisCoreError("invalid-observer-gap-policy"));
    }
    let bytes = format!(
        "{}:{}:{}:{}",
        policy.minimum_fit_gain,
        policy.minimum_class_saving_gain,
        policy.maximum_cost_delta,
        policy.permit_information_loss
    );
    let result = domain_sha256_hex(POLICY_DOMAIN, bytes.as_bytes());
    diagnostics::event("GAP_POLICY_EXIT", "gap policy validated");
    Ok(result)
}

fn candidate_measure(
    candidate: &ObserverCandidate,
    encoded: &[super::semantics::Recurrence; 4],
    targets: [u8; 4],
) -> Result<Option<(usize, usize)>, SynthesisCoreError> {
    diagnostics::event(
        "GAP_MEASURE_ENTER",
        "measuring observer on exact finite task",
    );
    let mut hits = 0;
    for left in 0..4 {
        for right in (left + 1)..4 {
            let expected = if targets[left] == targets[right] {
                ExpectedRelation::Echo
            } else {
                ExpectedRelation::Separate
            };
            let actual = match echo(&candidate.observer, encoded[left], encoded[right])
                .inspect_err(|_| diagnostics::event("GAP_MEASURE_REJECT", "echo rejected"))?
            {
                EchoOutcome::Echo(_) => ExpectedRelation::Echo,
                EchoOutcome::Mismatch { .. } => ExpectedRelation::Separate,
                EchoOutcome::DomainBlocked { .. } => ExpectedRelation::DomainBlocked,
            };
            hits += usize::from(actual == expected);
        }
    }
    let mut classes: Vec<ResponseValue> = Vec::new();
    for recurrence in encoded {
        match observe(&candidate.observer, *recurrence)
            .inspect_err(|_| diagnostics::event("GAP_MEASURE_REJECT", "observe rejected"))?
        {
            Observation::Ready(value) => {
                if !classes.contains(&value) {
                    classes.push(value);
                }
            }
            Observation::Blocked(_) => {
                diagnostics::event("GAP_MEASURE_BLOCKED", "observer is partial on task domain");
                return Ok(None);
            }
        }
    }
    diagnostics::event("GAP_MEASURE_EXIT", "observer measurement completed");
    Ok(Some((hits, classes.len())))
}

fn terminal(
    request: &ObserverGapRequestV1,
    differential: &JointSearchDifferentialV1,
    baseline_set_digest: String,
    policy_digest: String,
    status: ObserverGapStatusV1,
    detail: &'static str,
    baseline_relation_evaluations: usize,
    witness: Option<ObserverGapWitnessV1>,
) -> ObserverGapReceiptV1 {
    diagnostics::event("GAP_TERMINAL_ENTER", "binding observer-gap terminal");
    let witness_root = witness_binding(witness.as_ref());
    let body = format!(
        "{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}",
        differential.differential_digest,
        baseline_set_digest,
        policy_digest,
        status.as_str(),
        detail,
        baseline_relation_evaluations,
        request.task_id.as_str(),
        differential.oracle.ledger.relation_evaluations,
        differential.oracle.ledger.pair_attempts,
        request.information_loss_penalty,
        witness_root,
    );
    let result = ObserverGapReceiptV1 {
        schema: OBSERVER_GAP_LAB_SCHEMA,
        status,
        detail,
        task_id: request.task_id,
        grammar_profile_id: request.grammar_profile_id,
        differential_digest: differential.differential_digest.clone(),
        baseline_set_digest,
        policy_digest,
        joint_ledger: differential.oracle.ledger,
        baseline_relation_evaluations,
        witness,
        receipt_digest: domain_sha256_hex(OBSERVER_GAP_DOMAIN, body.as_bytes()),
        boundary: OBSERVER_GAP_LAB_BOUNDARY,
    };
    diagnostics::event("GAP_TERMINAL_EXIT", "observer-gap terminal bound");
    result
}

fn witness_binding(witness: Option<&ObserverGapWitnessV1>) -> String {
    diagnostics::event("GAP_WITNESS_BIND_ENTER", "binding complete gap witness");
    let result = witness.map_or_else(
        || "null".to_owned(),
        |row| {
            format!(
                "{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}",
                row.transform_ordinal,
                row.transform_digest,
                row.observer_ordinal,
                row.observer_digest,
                row.vector.baseline_name,
                row.vector.baseline_ordinal,
                row.vector.obligations,
                row.vector.baseline_hits,
                row.vector.winner_hits,
                row.vector.fit_gain,
                row.vector.baseline_response_classes,
                row.vector.winner_response_classes,
                row.vector.class_saving_gain,
                row.vector.cost_delta,
                row.vector.transform_cost,
                row.vector.observer_cost,
                row.vector.explanation_cost,
                row.vector.total_cost,
                row.vector.information_loss_penalty
            )
        },
    );
    diagnostics::event("GAP_WITNESS_BIND_EXIT", "complete gap witness bound");
    result
}

pub(crate) fn observer_gap_from_differential(
    request: &ObserverGapRequestV1,
    differential: &JointSearchDifferentialV1,
) -> Result<ObserverGapReceiptV1, SynthesisCoreError> {
    diagnostics::event(
        "GAP_EVALUATE_ENTER",
        "evaluating observer gap from differential",
    );
    let profiled = enumerate_observer_grammar_profile(
        request.grammar_profile_id,
        grammar_config_for_profile(request.grammar_profile_id),
    )
    .inspect_err(|_| diagnostics::event("GAP_EVALUATE_REJECT", "profile rejected"))?;
    let baseline_set_digest =
        validate_and_bind_baselines(&request.baselines, profiled.enumeration.candidates.len())?;
    let policy_digest = bind_policy(request.policy)?;
    if differential.verdict != JointDifferentialVerdictV1::Equivalent {
        diagnostics::event("GAP_EVALUATE_BLOCKED", "search differential diverged");
        return Ok(terminal(
            request,
            differential,
            baseline_set_digest,
            policy_digest,
            ObserverGapStatusV1::Blocked,
            "search-differential-diverged",
            0,
            None,
        ));
    }
    if differential.oracle.status == JointSynthesisStatus::Incomplete {
        diagnostics::event("GAP_EVALUATE_INCOMPLETE", "joint search was incomplete");
        return Ok(terminal(
            request,
            differential,
            baseline_set_digest,
            policy_digest,
            ObserverGapStatusV1::Incomplete,
            "joint-search-incomplete",
            0,
            None,
        ));
    }
    let Some(winner) = differential.oracle.winner.as_ref() else {
        diagnostics::event("GAP_EVALUATE_EXIT", "joint product had no winner");
        return Ok(terminal(
            request,
            differential,
            baseline_set_digest,
            policy_digest,
            ObserverGapStatusV1::NoGap,
            "joint-product-has-no-winner",
            0,
            None,
        ));
    };
    let family = enumerate_representation_family().inspect_err(|_| {
        diagnostics::event("GAP_EVALUATE_REJECT", "representation family rejected")
    })?;
    let transform = family
        .transforms
        .get(winner.transform_ordinal)
        .ok_or_else(|| {
            diagnostics::event("GAP_EVALUATE_REJECT", "winner transform ordinal rejected");
            SynthesisCoreError("observer-gap-transform-ordinal")
        })?;
    let winner_candidate = profiled
        .enumeration
        .candidates
        .get(winner.observer_ordinal)
        .ok_or_else(|| {
            diagnostics::event("GAP_EVALUATE_REJECT", "winner observer ordinal rejected");
            SynthesisCoreError("observer-gap-winner-ordinal")
        })?;
    let encoded = encoded_recurrences(transform)
        .inspect_err(|_| diagnostics::event("GAP_EVALUATE_REJECT", "encoding rejected"))?;
    let targets = request.task_id.target_classes();
    let Some((winner_hits, winner_classes)) =
        candidate_measure(winner_candidate, &encoded, targets)?
    else {
        diagnostics::event("GAP_EVALUATE_BLOCKED", "winner is partial on task domain");
        return Ok(terminal(
            request,
            differential,
            baseline_set_digest,
            policy_digest,
            ObserverGapStatusV1::Blocked,
            "winner-domain-blocked",
            6,
            None,
        ));
    };

    let mut best: Option<(&NamedObserverBaselineV1, usize, usize, usize)> = None;
    let mut evaluated = 6;
    for baseline in &request.baselines {
        let candidate = &profiled.enumeration.candidates[baseline.observer_ordinal];
        evaluated += 6;
        let Some((hits, classes)) = candidate_measure(candidate, &encoded, targets)? else {
            diagnostics::event("GAP_EVALUATE_BLOCKED", "named baseline is partial");
            return Ok(terminal(
                request,
                differential,
                baseline_set_digest,
                policy_digest,
                ObserverGapStatusV1::Blocked,
                "baseline-domain-blocked",
                evaluated,
                None,
            ));
        };
        let rank = (
            hits,
            4usize.saturating_sub(classes),
            usize::MAX - candidate.cost,
        );
        if best.is_none_or(|(_, best_hits, best_classes, best_cost)| {
            rank > (
                best_hits,
                4usize.saturating_sub(best_classes),
                usize::MAX - best_cost,
            )
        }) {
            best = Some((baseline, hits, classes, candidate.cost));
        }
    }
    let (baseline, baseline_hits, baseline_classes, baseline_cost) = best.ok_or_else(|| {
        diagnostics::event("GAP_EVALUATE_REJECT", "baseline selection failed");
        SynthesisCoreError("observer-gap-baseline-selection")
    })?;
    let fit_gain = winner_hits as i32 - baseline_hits as i32;
    let class_saving_gain = baseline_classes as i32 - winner_classes as i32;
    let cost_delta = winner_candidate.cost as i32 - baseline_cost as i32;
    let explanation_cost = evaluated;
    let total_cost = winner
        .transform_cost
        .checked_add(winner.observer_cost)
        .and_then(|value| value.checked_add(explanation_cost))
        .ok_or_else(|| {
            diagnostics::event("GAP_EVALUATE_REJECT", "gap cost overflowed");
            SynthesisCoreError("observer-gap-cost-overflow")
        })?;
    let status = if fit_gain >= request.policy.minimum_fit_gain
        && class_saving_gain >= request.policy.minimum_class_saving_gain
        && cost_delta <= request.policy.maximum_cost_delta
        && request.information_loss_penalty == 0
    {
        ObserverGapStatusV1::Positive
    } else {
        ObserverGapStatusV1::NoGap
    };
    let witness = ObserverGapWitnessV1 {
        transform_ordinal: winner.transform_ordinal,
        transform_digest: winner.transform_digest.clone(),
        observer_ordinal: winner.observer_ordinal,
        observer_digest: winner.observer_digest.clone(),
        vector: ObserverGapVectorV1 {
            obligations: 6,
            baseline_name: baseline.name.clone(),
            baseline_ordinal: baseline.observer_ordinal,
            baseline_hits,
            winner_hits,
            fit_gain,
            baseline_response_classes: baseline_classes,
            winner_response_classes: winner_classes,
            class_saving_gain,
            cost_delta,
            transform_cost: winner.transform_cost,
            observer_cost: winner.observer_cost,
            explanation_cost,
            total_cost,
            information_loss_penalty: request.information_loss_penalty,
        },
    };
    diagnostics::event("GAP_EVALUATE_EXIT", "observer gap evaluated");
    Ok(terminal(
        request,
        differential,
        baseline_set_digest,
        policy_digest,
        status,
        if status == ObserverGapStatusV1::Positive {
            "policy-thresholds-satisfied"
        } else {
            "policy-thresholds-not-satisfied"
        },
        evaluated,
        Some(witness),
    ))
}

#[allow(clippy::too_many_arguments)]
fn direct_terminal(
    request: &ObserverGapRequestV1,
    differential: &DirectSearchDifferentialV3,
    baseline_set_digest: String,
    policy_digest: String,
    status: ObserverGapStatusV1,
    detail: &'static str,
    evaluated: usize,
    witness: Option<ObserverGapWitnessV1>,
) -> ObserverGapReceiptV1 {
    diagnostics::event("DIRECT_GAP_TERMINAL_ENTER", "binding direct gap terminal");
    let witness_root = witness_binding(witness.as_ref());
    let body = format!(
        "{}:{}:{}:{}:{}:{}:{}:{}",
        differential.differential_digest,
        baseline_set_digest,
        policy_digest,
        status.as_str(),
        detail,
        evaluated,
        request.information_loss_penalty,
        witness_root
    );
    let result = ObserverGapReceiptV1 {
        schema: OBSERVER_GAP_LAB_SCHEMA,
        status,
        detail,
        task_id: request.task_id,
        grammar_profile_id: request.grammar_profile_id,
        differential_digest: differential.differential_digest.clone(),
        baseline_set_digest,
        policy_digest,
        joint_ledger: differential.oracle.ledger,
        baseline_relation_evaluations: evaluated,
        witness,
        receipt_digest: domain_sha256_hex(OBSERVER_GAP_DOMAIN, body.as_bytes()),
        boundary: OBSERVER_GAP_LAB_BOUNDARY,
    };
    diagnostics::event("DIRECT_GAP_TERMINAL_EXIT", "direct gap terminal bound");
    result
}

pub(crate) fn observer_gap_from_direct_differential(
    request: &ObserverGapRequestV1,
    differential: &DirectSearchDifferentialV3,
    selected: &CompiledTransportV1,
) -> Result<ObserverGapReceiptV1, SynthesisCoreError> {
    diagnostics::event(
        "DIRECT_GAP_ENTER",
        "evaluating direct transport observer gap",
    );
    let profiled = enumerate_observer_grammar_profile(
        request.grammar_profile_id,
        grammar_config_for_profile(request.grammar_profile_id),
    )?;
    let baseline_set_digest =
        validate_and_bind_baselines(&request.baselines, profiled.enumeration.candidates.len())?;
    let policy_digest = bind_policy(request.policy)?;
    if !differential.equivalent {
        return Ok(direct_terminal(
            request,
            differential,
            baseline_set_digest,
            policy_digest,
            ObserverGapStatusV1::Blocked,
            "search-differential-diverged",
            0,
            None,
        ));
    }
    if differential.oracle.status == JointSynthesisStatus::Incomplete {
        return Ok(direct_terminal(
            request,
            differential,
            baseline_set_digest,
            policy_digest,
            ObserverGapStatusV1::Incomplete,
            "joint-search-incomplete",
            0,
            None,
        ));
    }
    let Some(winner) = differential.oracle.winner.as_ref() else {
        return Ok(direct_terminal(
            request,
            differential,
            baseline_set_digest,
            policy_digest,
            ObserverGapStatusV1::NoGap,
            "joint-product-has-no-winner",
            0,
            None,
        ));
    };
    if winner.transport_digest != selected.digest()
        || request.information_loss_penalty != selected.collision_count()
    {
        diagnostics::event("DIRECT_GAP_REJECT", "selected transport binding rejected");
        return Err(SynthesisCoreError("direct-gap-selected-transport-binding"));
    }
    let candidate = profiled
        .enumeration
        .candidates
        .get(winner.observer_ordinal)
        .ok_or(SynthesisCoreError("direct-gap-winner-ordinal"))?;
    let image = selected.image();
    let encoded = [
        super::semantics::Recurrence::new(image[0])?,
        super::semantics::Recurrence::new(image[1])?,
        super::semantics::Recurrence::new(image[2])?,
        super::semantics::Recurrence::new(image[3])?,
    ];
    let targets = request.task_id.target_classes();
    let Some((winner_hits, winner_classes)) = candidate_measure(candidate, &encoded, targets)?
    else {
        return Ok(direct_terminal(
            request,
            differential,
            baseline_set_digest,
            policy_digest,
            ObserverGapStatusV1::Blocked,
            "winner-domain-blocked",
            6,
            None,
        ));
    };
    let mut best: Option<(&NamedObserverBaselineV1, usize, usize, usize)> = None;
    let mut evaluated = 6;
    for baseline in &request.baselines {
        let row = &profiled.enumeration.candidates[baseline.observer_ordinal];
        evaluated += 6;
        let Some((hits, classes)) = candidate_measure(row, &encoded, targets)? else {
            return Ok(direct_terminal(
                request,
                differential,
                baseline_set_digest,
                policy_digest,
                ObserverGapStatusV1::Blocked,
                "baseline-domain-blocked",
                evaluated,
                None,
            ));
        };
        let rank = (hits, 4usize.saturating_sub(classes), usize::MAX - row.cost);
        if best.is_none_or(|(_, old_hits, old_classes, old_cost)| {
            rank > (
                old_hits,
                4usize.saturating_sub(old_classes),
                usize::MAX - old_cost,
            )
        }) {
            best = Some((baseline, hits, classes, row.cost));
        }
    }
    let (baseline, baseline_hits, baseline_classes, baseline_cost) =
        best.ok_or(SynthesisCoreError("direct-gap-baseline-selection"))?;
    let fit_gain = winner_hits as i32 - baseline_hits as i32;
    let class_saving_gain = baseline_classes as i32 - winner_classes as i32;
    let cost_delta = winner.observer_cost as i32 - baseline_cost as i32;
    let total_cost = winner
        .joint_cost
        .checked_add(evaluated)
        .ok_or(SynthesisCoreError("direct-gap-cost-overflow"))?;
    let status = if fit_gain >= request.policy.minimum_fit_gain
        && class_saving_gain >= request.policy.minimum_class_saving_gain
        && cost_delta <= request.policy.maximum_cost_delta
        && request.information_loss_penalty == 0
    {
        ObserverGapStatusV1::Positive
    } else {
        ObserverGapStatusV1::NoGap
    };
    let witness = ObserverGapWitnessV1 {
        transform_ordinal: winner.transport_ordinal,
        transform_digest: winner.transport_digest.clone(),
        observer_ordinal: winner.observer_ordinal,
        observer_digest: winner.observer_digest.clone(),
        vector: ObserverGapVectorV1 {
            obligations: 6,
            baseline_name: baseline.name.clone(),
            baseline_ordinal: baseline.observer_ordinal,
            baseline_hits,
            winner_hits,
            fit_gain,
            baseline_response_classes: baseline_classes,
            winner_response_classes: winner_classes,
            class_saving_gain,
            cost_delta,
            transform_cost: winner.transport_cost,
            observer_cost: winner.observer_cost,
            explanation_cost: evaluated,
            total_cost,
            information_loss_penalty: request.information_loss_penalty,
        },
    };
    diagnostics::event("DIRECT_GAP_EXIT", "direct transport observer gap evaluated");
    Ok(direct_terminal(
        request,
        differential,
        baseline_set_digest,
        policy_digest,
        status,
        if status == ObserverGapStatusV1::Positive {
            "policy-thresholds-satisfied"
        } else {
            "policy-thresholds-not-satisfied"
        },
        evaluated,
        Some(witness),
    ))
}

pub fn run_observer_gap_lab(
    request: &ObserverGapRequestV1,
) -> Result<ObserverGapReceiptV1, SynthesisCoreError> {
    diagnostics::event("GAP_RUN_ENTER", "starting observer-gap lab");
    let differential = differential_joint_search(
        request.task_id,
        request.grammar_profile_id,
        request.joint_limits,
    )
    .inspect_err(|_| diagnostics::event("GAP_RUN_REJECT", "search differential rejected"))?;
    let result = observer_gap_from_differential(request, &differential)
        .inspect_err(|_| diagnostics::event("GAP_RUN_REJECT", "gap evaluation rejected"))?;
    diagnostics::event("GAP_RUN_EXIT", "observer-gap lab completed");
    Ok(result)
}

/// Build deterministic positive and negative calibration controls.
pub fn observer_gap_calibration_requests(
    limits: JointSynthesisLimits,
) -> Result<(ObserverGapRequestV1, ObserverGapRequestV1), SynthesisCoreError> {
    diagnostics::event("GAP_CONTROLS_ENTER", "building deterministic gap controls");
    let differential = differential_joint_search(
        NativePartitionTaskId::XorParity,
        ObserverGrammarProfileId::ParityV2,
        limits,
    )
    .inspect_err(|_| diagnostics::event("GAP_CONTROLS_REJECT", "control search rejected"))?;
    if differential.verdict != JointDifferentialVerdictV1::Equivalent {
        diagnostics::event("GAP_CONTROLS_REJECT", "control differential diverged");
        return Err(SynthesisCoreError("observer-gap-control-diverged"));
    }
    let winner = differential.oracle.winner.ok_or_else(|| {
        diagnostics::event("GAP_CONTROLS_REJECT", "control winner unavailable");
        SynthesisCoreError("observer-gap-control-winner-unavailable")
    })?;
    let positive = ObserverGapRequestV1 {
        task_id: NativePartitionTaskId::XorParity,
        grammar_profile_id: ObserverGrammarProfileId::ParityV2,
        joint_limits: limits,
        baselines: vec![NamedObserverBaselineV1 {
            name: "input".to_owned(),
            observer_ordinal: 0,
        }],
        policy: ObserverGapPolicyV1::default(),
        information_loss_penalty: 0,
    };
    let negative = ObserverGapRequestV1 {
        baselines: vec![NamedObserverBaselineV1 {
            name: "winner-control".to_owned(),
            observer_ordinal: winner.observer_ordinal,
        }],
        ..positive.clone()
    };
    diagnostics::event("GAP_CONTROLS_EXIT", "deterministic gap controls built");
    Ok((positive, negative))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn request(baseline: usize) -> ObserverGapRequestV1 {
        ObserverGapRequestV1 {
            task_id: NativePartitionTaskId::XorParity,
            grammar_profile_id: ObserverGrammarProfileId::ParityV2,
            joint_limits: JointSynthesisLimits::default(),
            baselines: vec![NamedObserverBaselineV1 {
                name: "input".to_owned(),
                observer_ordinal: baseline,
            }],
            policy: ObserverGapPolicyV1::default(),
            information_loss_penalty: 0,
        }
    }

    #[test]
    fn finite_positive_gap_is_reproducible() {
        let first = run_observer_gap_lab(&request(0)).unwrap();
        let second = run_observer_gap_lab(&request(0)).unwrap();
        assert_eq!(first, second);
        assert_eq!(first.status, ObserverGapStatusV1::Positive);
        assert_eq!(first.witness.unwrap().vector.fit_gain, 2);
    }

    #[test]
    fn the_winner_as_baseline_is_a_negative_control() {
        let (_, negative) =
            observer_gap_calibration_requests(JointSynthesisLimits::default()).unwrap();
        let report = run_observer_gap_lab(&negative).unwrap();
        assert_eq!(report.status, ObserverGapStatusV1::NoGap);
        assert_eq!(report.witness.unwrap().vector.fit_gain, 0);
    }

    #[test]
    fn information_loss_is_denied_by_default() {
        let mut lossy = request(0);
        lossy.information_loss_penalty = 1;
        let report = run_observer_gap_lab(&lossy).unwrap();
        assert_eq!(report.status, ObserverGapStatusV1::NoGap);
        assert_eq!(report.witness.unwrap().vector.information_loss_penalty, 1);
    }

    #[test]
    fn complete_witness_binding_changes_for_every_public_vector_field() {
        let original = run_observer_gap_lab(&request(0)).unwrap().witness.unwrap();
        let root = witness_binding(Some(&original));
        let mut mutations = Vec::new();
        macro_rules! changed {
            ($field:ident, $value:expr) => {{
                let mut row = original.clone();
                row.vector.$field = $value;
                mutations.push(row);
            }};
        }
        changed!(obligations, original.vector.obligations + 1);
        changed!(
            baseline_name,
            format!("{}-mutated", original.vector.baseline_name)
        );
        changed!(baseline_ordinal, original.vector.baseline_ordinal + 1);
        changed!(baseline_hits, original.vector.baseline_hits + 1);
        changed!(winner_hits, original.vector.winner_hits + 1);
        changed!(fit_gain, original.vector.fit_gain + 1);
        changed!(
            baseline_response_classes,
            original.vector.baseline_response_classes + 1
        );
        changed!(
            winner_response_classes,
            original.vector.winner_response_classes + 1
        );
        changed!(class_saving_gain, original.vector.class_saving_gain + 1);
        changed!(cost_delta, original.vector.cost_delta + 1);
        changed!(transform_cost, original.vector.transform_cost + 1);
        changed!(observer_cost, original.vector.observer_cost + 1);
        changed!(explanation_cost, original.vector.explanation_cost + 1);
        changed!(total_cost, original.vector.total_cost + 1);
        changed!(
            information_loss_penalty,
            original.vector.information_loss_penalty + 1
        );
        assert!(mutations
            .iter()
            .all(|row| witness_binding(Some(row)) != root));
    }
}
