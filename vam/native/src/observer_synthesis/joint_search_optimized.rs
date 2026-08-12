//! Stable cost-bucket joint search checked against the exhaustive reference.

use super::ast::SynthesisCoreError;
use super::cegis::ExpectedRelation;
use super::diagnostics;
use super::grammar::{
    enumerate_observer_grammar_profile, grammar_config_for_profile, ObserverCandidate,
};
use super::grammar_profile::ObserverGrammarProfileId;
use super::hash::domain_sha256_hex;
use super::joint_synthesis::{
    synthesize_transform_and_observer, JointBudgetCutoff, JointSynthesisLedger,
    JointSynthesisLimits, JointSynthesisStatus, NativeJointSynthesisReportV1, NativeJointWinnerV1,
    NativePartitionTaskId, MAX_JOINT_CANDIDATES, MAX_JOINT_RELATION_EVALUATIONS,
    MAX_JOINT_TRANSFORMS,
};
use super::representation_family::{
    encoded_recurrences, enumerate_representation_family, NativeRepresentationTransformV1,
};
use super::semantics::{observe, Observation};

pub const OPTIMIZED_JOINT_SCHEMA: &str =
    "veyra.native-joint-transform-observer.stable-cost-buckets.v1";
pub const JOINT_DIFFERENTIAL_SCHEMA: &str = "veyra.native-joint-transform-observer.differential.v1";
const OPTIMIZED_DOMAIN: &str =
    "veyra.native-joint-transform-observer.stable-cost-buckets.v1.binding";
const DIFFERENTIAL_DOMAIN: &str = "veyra.native-joint-transform-observer.differential.v1.binding";
const PAIR_ORDER_DOMAIN: &str =
    "veyra.native-joint-transform-observer.stable-cost-buckets.pairs.v1.binding";

pub const OPTIMIZED_JOINT_BOUNDARY: &str =
    "stable cost buckets remove repeated cost scans while retaining the exhaustive reference pair order; differential equivalence is finite to one task, registered profile, declared 120-row family, and exact counter limits; no asymptotic, speedup, global optimality, or theorem claim";

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum JointDifferentialVerdictV1 {
    Equivalent,
    Diverged,
}

impl JointDifferentialVerdictV1 {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Equivalent => "EQUIVALENT",
            Self::Diverged => "DIVERGED",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OptimizedJointSearchReportV1 {
    pub schema: &'static str,
    pub task_id: NativePartitionTaskId,
    pub grammar_profile_id: ObserverGrammarProfileId,
    pub grammar_profile_digest: String,
    pub catalog_digest: String,
    pub representation_family_digest: String,
    pub status: JointSynthesisStatus,
    pub detail: &'static str,
    pub ledger: JointSynthesisLedger,
    pub winner: Option<NativeJointWinnerV1>,
    pub transform_bucket_count: usize,
    pub candidate_bucket_count: usize,
    pub indexed_rows: usize,
    pub observation_cache: &'static str,
    pub pruned_higher_cost_pairs: usize,
    pub pair_order_digest: String,
    pub result_digest: String,
    pub boundary: &'static str,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct JointSearchDifferentialV1 {
    pub schema: &'static str,
    pub oracle: NativeJointSynthesisReportV1,
    pub optimized: OptimizedJointSearchReportV1,
    pub verdict: JointDifferentialVerdictV1,
    pub differential_digest: String,
    pub boundary: &'static str,
}

fn valid_limits(limits: JointSynthesisLimits) -> bool {
    diagnostics::event(
        "OPTIMIZED_LIMITS_ENTER",
        "validating optimized search limits",
    );
    let result = limits.transform_limit > 0
        && limits.transform_limit <= MAX_JOINT_TRANSFORMS
        && limits.candidate_limit > 0
        && limits.candidate_limit <= MAX_JOINT_CANDIDATES
        && limits.relation_evaluation_limit > 0
        && limits.relation_evaluation_limit <= MAX_JOINT_RELATION_EVALUATIONS;
    diagnostics::event(
        if result {
            "OPTIMIZED_LIMITS_EXIT"
        } else {
            "OPTIMIZED_LIMITS_REJECT"
        },
        "optimized search limits validated",
    );
    result
}

fn relation_satisfied(
    candidate: &ObserverCandidate,
    transform: &NativeRepresentationTransformV1,
    targets: [u8; 4],
) -> Result<bool, SynthesisCoreError> {
    diagnostics::event("OPTIMIZED_PAIR_ENTER", "evaluating one indexed pair");
    let encoded = encoded_recurrences(transform).inspect_err(|_| {
        diagnostics::event("OPTIMIZED_PAIR_REJECT", "transform encoding rejected")
    })?;
    // Memoize each exact state observation once for this pair.  The exhaustive
    // oracle calls `echo` for every obligation and therefore observes a state
    // repeatedly; this local exact vector changes no logical pair or charge.
    let mut responses = Vec::with_capacity(4);
    for recurrence in encoded {
        responses.push(observe(&candidate.observer, recurrence).inspect_err(|_| {
            diagnostics::event("OPTIMIZED_PAIR_REJECT", "observer evaluation rejected")
        })?);
    }
    for left in 0..4 {
        for right in (left + 1)..4 {
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
                diagnostics::event("OPTIMIZED_PAIR_EXIT", "indexed pair did not satisfy task");
                return Ok(false);
            }
        }
    }
    diagnostics::event("OPTIMIZED_PAIR_EXIT", "indexed pair satisfied task");
    Ok(true)
}

fn pair_order_digest(pairs: &[(usize, usize)]) -> String {
    diagnostics::event("OPTIMIZED_PAIR_ROOT_ENTER", "binding logical pair order");
    let mut bytes = Vec::with_capacity(pairs.len().saturating_mul(16));
    for (transform, observer) in pairs {
        bytes.extend_from_slice(&(*transform as u64).to_be_bytes());
        bytes.extend_from_slice(&(*observer as u64).to_be_bytes());
    }
    let result = domain_sha256_hex(PAIR_ORDER_DOMAIN, &bytes);
    diagnostics::event("OPTIMIZED_PAIR_ROOT_EXIT", "logical pair order bound");
    result
}

#[allow(clippy::too_many_arguments)]
fn terminal(
    task_id: NativePartitionTaskId,
    grammar_profile_id: ObserverGrammarProfileId,
    grammar_profile_digest: String,
    catalog_digest: String,
    family_digest: String,
    status: JointSynthesisStatus,
    detail: &'static str,
    ledger: JointSynthesisLedger,
    winner: Option<NativeJointWinnerV1>,
    transform_bucket_count: usize,
    candidate_bucket_count: usize,
    indexed_rows: usize,
    pruned_higher_cost_pairs: usize,
    pairs: &[(usize, usize)],
) -> OptimizedJointSearchReportV1 {
    diagnostics::event("OPTIMIZED_TERMINAL_ENTER", "binding optimized terminal");
    let pair_order_digest = pair_order_digest(pairs);
    let winner_root = winner.as_ref().map_or_else(
        || "null".to_owned(),
        |row| {
            format!(
                "{}:{}:{}:{}",
                row.transform_ordinal,
                row.observer_ordinal,
                row.transform_digest,
                row.observer_digest
            )
        },
    );
    let body = format!(
        "{{\"candidate_buckets\":{candidate_bucket_count},\"candidate_count\":{},\"candidate_limit\":{},\"catalog_digest\":\"{catalog_digest}\",\"cutoff\":\"{}\",\"detail\":\"{detail}\",\"family_digest\":\"{family_digest}\",\"indexed_rows\":{indexed_rows},\"observation_cache\":\"exact-four-state-response-vector\",\"pair_order_digest\":\"{pair_order_digest}\",\"pairs\":{},\"profile_digest\":\"{grammar_profile_digest}\",\"pruned_higher_cost_pairs\":{pruned_higher_cost_pairs},\"relation_charges\":{},\"relation_limit\":{},\"schema\":\"{OPTIMIZED_JOINT_SCHEMA}\",\"status\":\"{}\",\"task\":\"{}\",\"transform_buckets\":{transform_bucket_count},\"transform_count\":{},\"transform_limit\":{},\"winner\":\"{winner_root}\"}}",
        ledger.candidates,
        ledger.limits.candidate_limit,
        ledger.cutoff.map_or("none", JointBudgetCutoff::as_str),
        ledger.pair_attempts,
        ledger.relation_evaluations,
        ledger.limits.relation_evaluation_limit,
        status.as_str(),
        task_id.as_str(),
        ledger.transforms,
        ledger.limits.transform_limit,
    );
    let result = OptimizedJointSearchReportV1 {
        schema: OPTIMIZED_JOINT_SCHEMA,
        task_id,
        grammar_profile_id,
        grammar_profile_digest,
        catalog_digest,
        representation_family_digest: family_digest,
        status,
        detail,
        ledger,
        winner,
        transform_bucket_count,
        candidate_bucket_count,
        indexed_rows,
        observation_cache: "exact-four-state-response-vector",
        pruned_higher_cost_pairs,
        pair_order_digest,
        result_digest: domain_sha256_hex(OPTIMIZED_DOMAIN, body.as_bytes()),
        boundary: OPTIMIZED_JOINT_BOUNDARY,
    };
    diagnostics::event("OPTIMIZED_TERMINAL_EXIT", "optimized terminal bound");
    result
}

pub fn synthesize_transform_and_observer_optimized(
    task_id: NativePartitionTaskId,
    grammar_profile_id: ObserverGrammarProfileId,
    limits: JointSynthesisLimits,
) -> Result<OptimizedJointSearchReportV1, SynthesisCoreError> {
    diagnostics::event(
        "OPTIMIZED_SEARCH_ENTER",
        "starting stable cost-bucket search",
    );
    if !valid_limits(limits) {
        diagnostics::event("OPTIMIZED_SEARCH_REJECT", "optimized limits rejected");
        return Err(SynthesisCoreError("invalid-optimized-joint-limits"));
    }
    let family = enumerate_representation_family().inspect_err(|_| {
        diagnostics::event("OPTIMIZED_SEARCH_REJECT", "representation family rejected")
    })?;
    let profiled = enumerate_observer_grammar_profile(
        grammar_profile_id,
        grammar_config_for_profile(grammar_profile_id),
    )
    .inspect_err(|_| diagnostics::event("OPTIMIZED_SEARCH_REJECT", "profile rejected"))?;
    let mut ledger = JointSynthesisLedger {
        limits,
        transforms: 0,
        candidates: 0,
        pair_attempts: 0,
        relation_evaluations: 0,
        cutoff: None,
    };
    if family.transforms.len() > limits.transform_limit {
        ledger.cutoff = Some(JointBudgetCutoff::Transforms);
        diagnostics::event(
            "OPTIMIZED_SEARCH_INCOMPLETE",
            "transform precharge reached limit",
        );
        return Ok(terminal(
            task_id,
            grammar_profile_id,
            profiled.profile.profile_digest,
            profiled.enumeration.catalog_digest,
            family.family_digest,
            JointSynthesisStatus::Incomplete,
            "transform-limit",
            ledger,
            None,
            0,
            0,
            0,
            0,
            &[],
        ));
    }
    ledger.transforms = family.transforms.len();
    if profiled.enumeration.candidates.len() > limits.candidate_limit {
        ledger.cutoff = Some(JointBudgetCutoff::Candidates);
        diagnostics::event(
            "OPTIMIZED_SEARCH_INCOMPLETE",
            "candidate precharge reached limit",
        );
        return Ok(terminal(
            task_id,
            grammar_profile_id,
            profiled.profile.profile_digest,
            profiled.enumeration.catalog_digest,
            family.family_digest,
            JointSynthesisStatus::Incomplete,
            "candidate-limit",
            ledger,
            None,
            0,
            0,
            0,
            0,
            &[],
        ));
    }
    ledger.candidates = profiled.enumeration.candidates.len();

    let max_transform_cost = family
        .transforms
        .iter()
        .map(NativeRepresentationTransformV1::cost)
        .max()
        .unwrap_or(0);
    let max_candidate_cost = profiled
        .enumeration
        .candidates
        .iter()
        .map(|row| row.cost)
        .max()
        .unwrap_or(0);
    let mut transform_buckets = vec![Vec::new(); max_transform_cost + 1];
    for transform in &family.transforms {
        transform_buckets[transform.cost()].push(transform);
    }
    let mut candidate_buckets = vec![Vec::new(); max_candidate_cost + 1];
    for (ordinal, candidate) in profiled.enumeration.candidates.iter().enumerate() {
        candidate_buckets[candidate.cost].push((ordinal, candidate));
    }
    let indexed_rows = family.transforms.len() + profiled.enumeration.candidates.len();
    let mut pairs = Vec::new();

    for joint_cost in 0..=max_transform_cost + max_candidate_cost {
        for transform_cost in 0..=joint_cost {
            let candidate_cost = joint_cost - transform_cost;
            let Some(transforms) = transform_buckets.get(transform_cost) else {
                continue;
            };
            let Some(candidates) = candidate_buckets.get(candidate_cost) else {
                continue;
            };
            for transform in transforms {
                for (candidate_ordinal, candidate) in candidates {
                    let updated = ledger.relation_evaluations.checked_add(6).ok_or_else(|| {
                        diagnostics::event(
                            "OPTIMIZED_SEARCH_REJECT",
                            "relation counter overflowed",
                        );
                        SynthesisCoreError("optimized-joint-evaluation-overflow")
                    })?;
                    if updated > limits.relation_evaluation_limit {
                        ledger.cutoff = Some(JointBudgetCutoff::RelationEvaluations);
                        diagnostics::event(
                            "OPTIMIZED_SEARCH_INCOMPLETE",
                            "relation precharge reached limit",
                        );
                        return Ok(terminal(
                            task_id,
                            grammar_profile_id,
                            profiled.profile.profile_digest,
                            profiled.enumeration.catalog_digest,
                            family.family_digest,
                            JointSynthesisStatus::Incomplete,
                            "relation-evaluation-limit",
                            ledger,
                            None,
                            transform_buckets.len(),
                            candidate_buckets.len(),
                            indexed_rows,
                            0,
                            &pairs,
                        ));
                    }
                    ledger.relation_evaluations = updated;
                    ledger.pair_attempts += 1;
                    pairs.push((transform.ordinal(), *candidate_ordinal));
                    if relation_satisfied(candidate, transform, task_id.target_classes())? {
                        let pruned_higher_cost_pairs = family
                            .transforms
                            .iter()
                            .map(|future_transform| {
                                profiled
                                    .enumeration
                                    .candidates
                                    .iter()
                                    .filter(|future_candidate| {
                                        future_transform.cost() + future_candidate.cost > joint_cost
                                    })
                                    .count()
                            })
                            .sum();
                        let winner = NativeJointWinnerV1 {
                            joint_cost,
                            transform_ordinal: transform.ordinal(),
                            transform_cost,
                            transform_digest: transform.transform_digest().to_owned(),
                            observer_ordinal: *candidate_ordinal,
                            observer_cost: candidate_cost,
                            observer_depth: candidate.depth,
                            observer_digest: candidate.digest.clone(),
                            observer_canonical: candidate.canonical.clone(),
                        };
                        diagnostics::event("OPTIMIZED_SEARCH_EXIT", "indexed winner found");
                        return Ok(terminal(
                            task_id,
                            grammar_profile_id,
                            profiled.profile.profile_digest,
                            profiled.enumeration.catalog_digest,
                            family.family_digest,
                            JointSynthesisStatus::Found,
                            "first-joint-cost-ordered-winner",
                            ledger,
                            Some(winner),
                            transform_buckets.len(),
                            candidate_buckets.len(),
                            indexed_rows,
                            pruned_higher_cost_pairs,
                            &pairs,
                        ));
                    }
                }
            }
        }
    }
    diagnostics::event("OPTIMIZED_SEARCH_EXIT", "indexed product exhausted");
    Ok(terminal(
        task_id,
        grammar_profile_id,
        profiled.profile.profile_digest,
        profiled.enumeration.catalog_digest,
        family.family_digest,
        JointSynthesisStatus::Exhausted,
        "exact-joint-product-exhausted",
        ledger,
        None,
        transform_buckets.len(),
        candidate_buckets.len(),
        indexed_rows,
        0,
        &pairs,
    ))
}

fn semantically_equal(
    oracle: &NativeJointSynthesisReportV1,
    optimized: &OptimizedJointSearchReportV1,
) -> bool {
    diagnostics::event("DIFFERENTIAL_COMPARE_ENTER", "comparing search terminals");
    let result = oracle.task_id == optimized.task_id
        && oracle.grammar_profile_id == optimized.grammar_profile_id
        && oracle.grammar_profile_digest == optimized.grammar_profile_digest
        && oracle.catalog_digest == optimized.catalog_digest
        && oracle.representation_family_digest == optimized.representation_family_digest
        && oracle.status == optimized.status
        && oracle.detail == optimized.detail
        && oracle.ledger == optimized.ledger
        && oracle.winner == optimized.winner;
    diagnostics::event(
        if result {
            "DIFFERENTIAL_COMPARE_EXIT"
        } else {
            "DIFFERENTIAL_COMPARE_REJECT"
        },
        "search terminals compared",
    );
    result
}

pub fn differential_joint_search(
    task_id: NativePartitionTaskId,
    grammar_profile_id: ObserverGrammarProfileId,
    limits: JointSynthesisLimits,
) -> Result<JointSearchDifferentialV1, SynthesisCoreError> {
    diagnostics::event(
        "DIFFERENTIAL_ENTER",
        "running independent search differential",
    );
    let oracle = synthesize_transform_and_observer(task_id, grammar_profile_id, limits)
        .inspect_err(|_| diagnostics::event("DIFFERENTIAL_REJECT", "oracle search rejected"))?;
    let optimized =
        synthesize_transform_and_observer_optimized(task_id, grammar_profile_id, limits)
            .inspect_err(|_| {
                diagnostics::event("DIFFERENTIAL_REJECT", "optimized search rejected")
            })?;
    let verdict = if semantically_equal(&oracle, &optimized) {
        JointDifferentialVerdictV1::Equivalent
    } else {
        JointDifferentialVerdictV1::Diverged
    };
    let body = format!(
        "{{\"optimized_digest\":\"{}\",\"oracle_trace_digest\":\"{}\",\"schema\":\"{JOINT_DIFFERENTIAL_SCHEMA}\",\"verdict\":\"{}\"}}",
        optimized.result_digest,
        oracle.trace_digest,
        verdict.as_str(),
    );
    let result = JointSearchDifferentialV1 {
        schema: JOINT_DIFFERENTIAL_SCHEMA,
        oracle,
        optimized,
        verdict,
        differential_digest: domain_sha256_hex(DIFFERENTIAL_DOMAIN, body.as_bytes()),
        boundary: OPTIMIZED_JOINT_BOUNDARY,
    };
    diagnostics::event(
        if verdict == JointDifferentialVerdictV1::Equivalent {
            "DIFFERENTIAL_EXIT"
        } else {
            "DIFFERENTIAL_DIVERGED"
        },
        "independent search differential completed",
    );
    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parity_and_cutoff_match_the_exhaustive_reference() {
        for limits in [
            JointSynthesisLimits::default(),
            JointSynthesisLimits {
                relation_evaluation_limit: 131,
                ..JointSynthesisLimits::default()
            },
            JointSynthesisLimits {
                transform_limit: 119,
                ..JointSynthesisLimits::default()
            },
        ] {
            let report = differential_joint_search(
                NativePartitionTaskId::XorParity,
                ObserverGrammarProfileId::ParityV2,
                limits,
            )
            .unwrap();
            assert_eq!(report.verdict, JointDifferentialVerdictV1::Equivalent);
        }
    }
}
