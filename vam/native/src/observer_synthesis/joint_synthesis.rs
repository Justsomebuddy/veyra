//! Deterministic joint search over a closed representation family and grammar.

use super::ast::SynthesisCoreError;
use super::cegis::ExpectedRelation;
use super::diagnostics;
use super::grammar::{
    enumerate_observer_grammar_profile, grammar_config_for_profile, ObserverCandidate,
};
use super::grammar_profile::ObserverGrammarProfileId;
use super::hash::domain_sha256_hex;
use super::representation_family::{
    encoded_recurrences, enumerate_representation_family, NativeRepresentationTransformV1,
    REPRESENTATION_TRANSFORMS,
};
use super::semantics::{echo, EchoOutcome};

pub const JOINT_SYNTHESIS_SCHEMA: &str = "veyra.native-joint-transform-observer.v1";
const TASK_DOMAIN: &str = "veyra.native-joint-transform-observer.task.v1.binding";
const ORDER_DOMAIN: &str = "veyra.native-joint-transform-observer.order.v1.binding";
const TRACE_DOMAIN: &str = "veyra.native-joint-transform-observer.trace.v1.binding";
pub const MAX_JOINT_TRANSFORMS: usize = REPRESENTATION_TRANSFORMS;
pub const MAX_JOINT_CANDIDATES: usize = 2_048;
pub const MAX_JOINT_RELATION_EVALUATIONS: usize = 2_000_000;
pub const XOR_PARITY_TASK_DIGEST: &str =
    "49c5bbf241b510f7e849571a9a1e2a0cdba1f36da1d553960ad100fb6dba2b92";
pub const PARITY_V2_JOINT_ORDER_DIGEST: &str =
    "f627af07cce178fd936fc0489d75d8b7de6aaa5b74dbd694b7beebae167f1540";
pub const PARITY_V2_XOR_TRACE_DIGEST: &str =
    "77a78d91914fec0851a6b73dc4584f42f3f2d50740dd0b29a85a97682f26c2a9";
pub const PARITY_INPUT_DIGEST: &str =
    "05c33f877cdb0563d163b1315a70d23a05cc5168d44ccafc33c0298d03e16e7b";

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NativePartitionTaskId {
    OneVsThree,
    XorParity,
}

impl NativePartitionTaskId {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::OneVsThree => "one-vs-three-v1",
            Self::XorParity => "xor-parity-v1",
        }
    }

    pub const fn target_classes(self) -> [u8; 4] {
        match self {
            Self::OneVsThree => [0, 1, 1, 1],
            Self::XorParity => [0, 1, 1, 0],
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum JointSynthesisStatus {
    Found,
    Exhausted,
    Incomplete,
}

impl JointSynthesisStatus {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Found => "FOUND",
            Self::Exhausted => "EXHAUSTED",
            Self::Incomplete => "INCOMPLETE",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum JointBudgetCutoff {
    Transforms,
    Candidates,
    RelationEvaluations,
}

impl JointBudgetCutoff {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Transforms => "transform-limit",
            Self::Candidates => "candidate-limit",
            Self::RelationEvaluations => "relation-evaluation-limit",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct JointSynthesisLimits {
    pub transform_limit: usize,
    pub candidate_limit: usize,
    pub relation_evaluation_limit: usize,
}

impl Default for JointSynthesisLimits {
    fn default() -> Self {
        Self {
            transform_limit: MAX_JOINT_TRANSFORMS,
            candidate_limit: MAX_JOINT_CANDIDATES,
            relation_evaluation_limit: MAX_JOINT_RELATION_EVALUATIONS,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct JointSynthesisLedger {
    pub limits: JointSynthesisLimits,
    pub transforms: usize,
    pub candidates: usize,
    pub pair_attempts: usize,
    pub relation_evaluations: usize,
    pub cutoff: Option<JointBudgetCutoff>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NativeJointWinnerV1 {
    pub joint_cost: usize,
    pub transform_ordinal: usize,
    pub transform_cost: usize,
    pub transform_digest: String,
    pub observer_ordinal: usize,
    pub observer_cost: usize,
    pub observer_depth: usize,
    pub observer_digest: String,
    pub observer_canonical: Vec<u8>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NativeJointSynthesisReportV1 {
    pub schema: &'static str,
    pub task_id: NativePartitionTaskId,
    pub task_digest: String,
    pub grammar_profile_id: ObserverGrammarProfileId,
    pub grammar_profile_digest: String,
    pub catalog_digest: String,
    pub representation_family_digest: String,
    pub search_order_digest: String,
    pub status: JointSynthesisStatus,
    pub detail: &'static str,
    pub ledger: JointSynthesisLedger,
    pub winner: Option<NativeJointWinnerV1>,
    pub trace_digest: String,
    pub boundary: &'static str,
}

fn valid_limits(limits: JointSynthesisLimits) -> bool {
    diagnostics::event("JOINT_LIMITS_ENTER", "validating joint counter limits");
    let result = limits.transform_limit > 0
        && limits.transform_limit <= MAX_JOINT_TRANSFORMS
        && limits.candidate_limit > 0
        && limits.candidate_limit <= MAX_JOINT_CANDIDATES
        && limits.relation_evaluation_limit > 0
        && limits.relation_evaluation_limit <= MAX_JOINT_RELATION_EVALUATIONS;
    diagnostics::event(
        if result {
            "JOINT_LIMITS_EXIT"
        } else {
            "JOINT_LIMITS_REJECT"
        },
        "joint counter limits validated",
    );
    result
}

fn task_digest(task_id: NativePartitionTaskId) -> String {
    diagnostics::event("JOINT_TASK_ENTER", "binding finite partition task");
    let classes = task_id.target_classes();
    let body = format!(
        "{{\"abstract_ordinals\":[0,1,2,3],\"schema\":\"veyra.native-joint-transform-observer.task.v1\",\"target_classes\":[{},{},{},{}],\"task_id\":\"{}\"}}",
        classes[0], classes[1], classes[2], classes[3], task_id.as_str(),
    );
    let result = domain_sha256_hex(TASK_DOMAIN, body.as_bytes());
    diagnostics::event("JOINT_TASK_EXIT", "finite partition task bound");
    result
}

fn order_digest(profile_digest: &str, catalog_digest: &str, family_digest: &str) -> String {
    diagnostics::event("JOINT_ORDER_ENTER", "binding exact joint search order");
    let body = format!(
        "{{\"catalog_digest\":\"{catalog_digest}\",\"family_digest\":\"{family_digest}\",\"key\":[\"joint_cost\",\"transform_cost\",\"observer_cost\",\"transform_ordinal\",\"observer_ordinal\"],\"profile_digest\":\"{profile_digest}\",\"schema\":\"veyra.native-joint-transform-observer.order.v1\"}}"
    );
    let result = domain_sha256_hex(ORDER_DOMAIN, body.as_bytes());
    diagnostics::event("JOINT_ORDER_EXIT", "exact joint search order bound");
    result
}

fn satisfies_partition(
    candidate: &ObserverCandidate,
    transform: &NativeRepresentationTransformV1,
    targets: [u8; 4],
) -> Result<bool, SynthesisCoreError> {
    diagnostics::event("JOINT_PAIR_ENTER", "evaluating transform-observer pair");
    let encoded = encoded_recurrences(transform)
        .inspect_err(|_| diagnostics::event("JOINT_PAIR_REJECT", "transform encoding rejected"))?;
    for left in 0..4 {
        for right in (left + 1)..4 {
            let expected = if targets[left] == targets[right] {
                ExpectedRelation::Echo
            } else {
                ExpectedRelation::Separate
            };
            let actual = match echo(&candidate.observer, encoded[left], encoded[right])
                .inspect_err(|_| {
                    diagnostics::event("JOINT_PAIR_REJECT", "observer evaluation rejected")
                })? {
                EchoOutcome::Echo(_) => ExpectedRelation::Echo,
                EchoOutcome::Mismatch { .. } => ExpectedRelation::Separate,
                EchoOutcome::DomainBlocked { .. } => ExpectedRelation::DomainBlocked,
            };
            if actual != expected {
                diagnostics::event("JOINT_PAIR_EXIT", "joint pair does not fit partition");
                return Ok(false);
            }
        }
    }
    diagnostics::event("JOINT_PAIR_EXIT", "joint pair fits partition");
    Ok(true)
}

fn terminal(
    task_id: NativePartitionTaskId,
    grammar_profile_id: ObserverGrammarProfileId,
    grammar_profile_digest: String,
    catalog_digest: String,
    representation_family_digest: String,
    search_order_digest: String,
    status: JointSynthesisStatus,
    detail: &'static str,
    ledger: JointSynthesisLedger,
    winner: Option<NativeJointWinnerV1>,
) -> NativeJointSynthesisReportV1 {
    diagnostics::event("JOINT_TERMINAL_ENTER", "binding joint terminal report");
    let task_digest = task_digest(task_id);
    let winner_root = winner.as_ref().map_or_else(
        || "null".to_owned(),
        |row| {
            format!(
                "{}:{}:{}:{}:{}:{}:{}:{}:{}",
                row.joint_cost,
                row.transform_ordinal,
                row.transform_cost,
                row.transform_digest,
                row.observer_ordinal,
                row.observer_cost,
                row.observer_depth,
                row.observer_digest,
                domain_sha256_hex(
                    "veyra.native-joint-transform-observer.winner-canonical.v1.binding",
                    &row.observer_canonical,
                ),
            )
        },
    );
    let trace_body = format!(
        "{{\"boundary\":\"closed-profile-family-only\",\"candidate_count\":{},\"candidate_limit\":{},\"catalog_digest\":\"{}\",\"cutoff\":\"{}\",\"detail\":\"{detail}\",\"relation_evaluation_charges\":{},\"relation_evaluation_limit\":{},\"family_digest\":\"{}\",\"pair_attempts\":{},\"profile_digest\":\"{}\",\"schema\":\"{JOINT_SYNTHESIS_SCHEMA}\",\"search_order_digest\":\"{}\",\"status\":\"{}\",\"task_digest\":\"{task_digest}\",\"transform_count\":{},\"transform_limit\":{},\"winner_root\":\"{winner_root}\"}}",
        ledger.candidates,
        ledger.limits.candidate_limit,
        catalog_digest,
        ledger.cutoff.map_or("none", JointBudgetCutoff::as_str),
        ledger.relation_evaluations,
        ledger.limits.relation_evaluation_limit,
        representation_family_digest,
        ledger.pair_attempts,
        grammar_profile_digest,
        search_order_digest,
        status.as_str(),
        ledger.transforms,
        ledger.limits.transform_limit,
    );
    let result = NativeJointSynthesisReportV1 {
        schema: JOINT_SYNTHESIS_SCHEMA,
        task_id,
        task_digest,
        grammar_profile_id,
        grammar_profile_digest,
        catalog_digest,
        representation_family_digest,
        search_order_digest,
        status,
        detail,
        ledger,
        winner,
        trace_digest: domain_sha256_hex(TRACE_DOMAIN, trace_body.as_bytes()),
        boundary: "complete only for one closed grammar profile crossed with the exact 120-row shift/permutation family under counter limits; relation_evaluations records six precharged upper-bound units per pair, not short-circuited runtime calls; no global representation, optimality, or theorem claim",
    };
    diagnostics::event("JOINT_TERMINAL_EXIT", "joint terminal report bound");
    result
}

pub fn synthesize_transform_and_observer(
    task_id: NativePartitionTaskId,
    grammar_profile_id: ObserverGrammarProfileId,
    limits: JointSynthesisLimits,
) -> Result<NativeJointSynthesisReportV1, SynthesisCoreError> {
    diagnostics::event("JOINT_SYNTHESIS_ENTER", "starting bounded joint synthesis");
    if !valid_limits(limits) {
        diagnostics::event("JOINT_SYNTHESIS_REJECT", "joint limits are invalid");
        return Err(SynthesisCoreError("invalid-joint-synthesis-limits"));
    }
    let family = enumerate_representation_family().inspect_err(|_| {
        diagnostics::event("JOINT_SYNTHESIS_REJECT", "representation family rejected")
    })?;
    let profiled = enumerate_observer_grammar_profile(
        grammar_profile_id,
        grammar_config_for_profile(grammar_profile_id),
    )
    .inspect_err(|_| diagnostics::event("JOINT_SYNTHESIS_REJECT", "grammar profile rejected"))?;
    let mut ledger = JointSynthesisLedger {
        limits,
        transforms: 0,
        candidates: 0,
        pair_attempts: 0,
        relation_evaluations: 0,
        cutoff: None,
    };
    let search_order_digest = order_digest(
        &profiled.profile.profile_digest,
        &profiled.enumeration.catalog_digest,
        &family.family_digest,
    );
    if family.transforms.len() > limits.transform_limit {
        ledger.cutoff = Some(JointBudgetCutoff::Transforms);
        diagnostics::event("JOINT_SYNTHESIS_INCOMPLETE", "transform precharge cut off");
        return Ok(terminal(
            task_id,
            grammar_profile_id,
            profiled.profile.profile_digest,
            profiled.enumeration.catalog_digest,
            family.family_digest,
            search_order_digest,
            JointSynthesisStatus::Incomplete,
            "transform-limit",
            ledger,
            None,
        ));
    }
    ledger.transforms = family.transforms.len();
    if profiled.enumeration.candidates.len() > limits.candidate_limit {
        ledger.cutoff = Some(JointBudgetCutoff::Candidates);
        diagnostics::event("JOINT_SYNTHESIS_INCOMPLETE", "candidate precharge cut off");
        return Ok(terminal(
            task_id,
            grammar_profile_id,
            profiled.profile.profile_digest,
            profiled.enumeration.catalog_digest,
            family.family_digest,
            search_order_digest,
            JointSynthesisStatus::Incomplete,
            "candidate-limit",
            ledger,
            None,
        ));
    }
    ledger.candidates = profiled.enumeration.candidates.len();
    let max_transform_cost = family
        .transforms
        .iter()
        .map(NativeRepresentationTransformV1::cost)
        .max()
        .unwrap_or(0);
    let max_observer_cost = profiled
        .enumeration
        .candidates
        .iter()
        .map(|row| row.cost)
        .max()
        .unwrap_or(0);
    for joint_cost in 0..=max_transform_cost + max_observer_cost {
        for transform_cost in 0..=joint_cost {
            let observer_cost = joint_cost - transform_cost;
            for transform in family
                .transforms
                .iter()
                .filter(|row| row.cost() == transform_cost)
            {
                for (observer_ordinal, candidate) in profiled
                    .enumeration
                    .candidates
                    .iter()
                    .enumerate()
                    .filter(|(_, row)| row.cost == observer_cost)
                {
                    let Some(updated) = ledger.relation_evaluations.checked_add(6) else {
                        diagnostics::event(
                            "JOINT_SYNTHESIS_REJECT",
                            "relation evaluation counter overflowed",
                        );
                        return Err(SynthesisCoreError("joint-evaluation-overflow"));
                    };
                    if updated > limits.relation_evaluation_limit {
                        ledger.cutoff = Some(JointBudgetCutoff::RelationEvaluations);
                        diagnostics::event(
                            "JOINT_SYNTHESIS_INCOMPLETE",
                            "relation evaluation precharge cut off",
                        );
                        return Ok(terminal(
                            task_id,
                            grammar_profile_id,
                            profiled.profile.profile_digest,
                            profiled.enumeration.catalog_digest,
                            family.family_digest,
                            search_order_digest,
                            JointSynthesisStatus::Incomplete,
                            "relation-evaluation-limit",
                            ledger,
                            None,
                        ));
                    }
                    ledger.relation_evaluations = updated;
                    ledger.pair_attempts += 1;
                    if satisfies_partition(candidate, transform, task_id.target_classes())
                        .inspect_err(|_| {
                            diagnostics::event(
                                "JOINT_SYNTHESIS_REJECT",
                                "joint pair evaluation rejected",
                            )
                        })?
                    {
                        let winner = NativeJointWinnerV1 {
                            joint_cost,
                            transform_ordinal: transform.ordinal(),
                            transform_cost,
                            transform_digest: transform.transform_digest().to_owned(),
                            observer_ordinal,
                            observer_cost,
                            observer_depth: candidate.depth,
                            observer_digest: candidate.digest.clone(),
                            observer_canonical: candidate.canonical.clone(),
                        };
                        diagnostics::event("JOINT_SYNTHESIS_EXIT", "joint winner found");
                        return Ok(terminal(
                            task_id,
                            grammar_profile_id,
                            profiled.profile.profile_digest,
                            profiled.enumeration.catalog_digest,
                            family.family_digest,
                            search_order_digest,
                            JointSynthesisStatus::Found,
                            "first-joint-cost-ordered-winner",
                            ledger,
                            Some(winner),
                        ));
                    }
                }
            }
        }
    }
    diagnostics::event(
        "JOINT_SYNTHESIS_EXHAUSTED",
        "joint product exhausted exactly",
    );
    Ok(terminal(
        task_id,
        grammar_profile_id,
        profiled.profile.profile_digest,
        profiled.enumeration.catalog_digest,
        family.family_digest,
        search_order_digest,
        JointSynthesisStatus::Exhausted,
        "exact-joint-product-exhausted",
        ledger,
        None,
    ))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parity_profile_finds_xor_after_the_exact_minimum_cost_transform() {
        let report = synthesize_transform_and_observer(
            NativePartitionTaskId::XorParity,
            ObserverGrammarProfileId::ParityV2,
            JointSynthesisLimits::default(),
        )
        .unwrap();
        assert_eq!(report.status, JointSynthesisStatus::Found);
        let winner = report.winner.unwrap();
        assert_eq!(report.task_digest, XOR_PARITY_TASK_DIGEST);
        assert_eq!(report.search_order_digest, PARITY_V2_JOINT_ORDER_DIGEST);
        assert_eq!(report.trace_digest, PARITY_V2_XOR_TRACE_DIGEST);
        assert_eq!(winner.observer_digest, PARITY_INPUT_DIGEST);
        assert_eq!(report.ledger.pair_attempts, 22);
        assert_eq!(report.ledger.relation_evaluations, 132);
        assert_eq!(winner.joint_cost, 2);
        assert_eq!(winner.transform_ordinal, 1);
        assert_eq!(winner.transform_cost, 1);
        assert_eq!(winner.observer_cost, 1);
    }

    #[test]
    fn legacy_profile_exhausts_xor_over_the_complete_transform_product() {
        let report = synthesize_transform_and_observer(
            NativePartitionTaskId::XorParity,
            ObserverGrammarProfileId::LegacyV1,
            JointSynthesisLimits::default(),
        )
        .unwrap();
        assert_eq!(report.status, JointSynthesisStatus::Exhausted);
        assert!(report.winner.is_none());
        assert_eq!(report.ledger.transforms, 120);
        assert_eq!(report.ledger.candidates, 1_565);
        assert_eq!(report.ledger.pair_attempts, 120 * 1_565);
        assert_eq!(report.ledger.relation_evaluations, 6 * 120 * 1_565);
        assert_eq!(
            report.trace_digest,
            "8820d9f7da46dea2ce6c37f431fe53be6a6f09bfc091501ac013504e337c7da5"
        );
    }

    #[test]
    fn joint_cutoffs_are_incomplete_and_never_exhaustion() {
        let report = synthesize_transform_and_observer(
            NativePartitionTaskId::XorParity,
            ObserverGrammarProfileId::ParityV2,
            JointSynthesisLimits {
                relation_evaluation_limit: 1,
                ..JointSynthesisLimits::default()
            },
        )
        .unwrap();
        assert_eq!(report.status, JointSynthesisStatus::Incomplete);
        assert_eq!(
            report.ledger.cutoff,
            Some(JointBudgetCutoff::RelationEvaluations)
        );
        assert!(report.winner.is_none());
    }
}
