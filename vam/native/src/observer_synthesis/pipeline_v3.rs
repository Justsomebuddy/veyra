//! Atomic observer-synthesis v3 pipeline.

use super::ast::SynthesisCoreError;
use super::diagnostics;
use super::grammar_registry::grammar_registry_v1;
use super::hash::domain_sha256_hex;
use super::joint_synthesis::JointSynthesisStatus;
use super::observer_gap_lab::{
    observer_gap_from_direct_differential, ObserverGapRequestV1, ObserverGapStatusV1,
};
use super::transport_dsl::{
    compile_transport, CompiledTransportV1, TransportInformationClassV1, TransportTermV1,
};
use super::transport_observer_search::differential_transport_observer_search;

pub const OBSERVER_SYNTHESIS_PIPELINE_V3_SCHEMA: &str =
    "veyra.observer-synthesis.atomic-pipeline.v3";
const PIPELINE_DOMAIN: &str = "veyra.observer-synthesis.atomic-pipeline.v3.binding";
const STAGE_DOMAIN: &str = "veyra.observer-synthesis.atomic-pipeline.stage.v3.binding";
const EVIDENCE_DOMAIN: &str = "veyra.observer-synthesis.atomic-pipeline.evidence.v3.binding";
const MAX_PIPELINE_TRANSPORTS: usize = 16;
pub const OBSERVER_SYNTHESIS_PIPELINE_V3_BOUNDARY: &str = "only READY carries the complete normalize, declared-transport, selected-observer, explanation, and aggregate evidence chain; the observer winner must select an exact domain-and-image transport from the declared candidate set; BLOCKED and INCOMPLETE carry no partial positive evidence; all claims remain exact and finite to the declared inputs";

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PipelineStatusV3 {
    Ready,
    Incomplete,
    Blocked,
}

impl PipelineStatusV3 {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Ready => "READY",
            Self::Incomplete => "INCOMPLETE",
            Self::Blocked => "BLOCKED",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PipelineStageV3 {
    Normalize,
    Transport,
    Observer,
    Explanation,
    Aggregate,
}

impl PipelineStageV3 {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Normalize => "NORMALIZE",
            Self::Transport => "TRANSPORT",
            Self::Observer => "OBSERVER",
            Self::Explanation => "EXPLANATION",
            Self::Aggregate => "AGGREGATE",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObserverSynthesisPipelineRequestV3 {
    pub gap_request: ObserverGapRequestV1,
    pub transports: Vec<TransportTermV1>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PipelineStageReceiptV3 {
    pub ordinal: usize,
    pub stage: PipelineStageV3,
    pub predecessor_digest: Option<String>,
    pub output_digest: String,
    pub cost: usize,
    pub limit: usize,
    pub stage_digest: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TransportEvidenceV3 {
    pub ordinal: usize,
    pub transport_digest: String,
    pub information_class: TransportInformationClassV1,
    pub collision_count: u32,
    pub cost: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObserverSynthesisPipelineEvidenceV3 {
    pub grammar_registry_digest: String,
    pub transports: Vec<TransportEvidenceV3>,
    pub differential_digest: String,
    pub selected_transport_ordinal: usize,
    pub selected_transport_digest: String,
    pub selected_transport_information_class: TransportInformationClassV1,
    pub selected_transport_collision_count: u32,
    pub selected_observer_ordinal: usize,
    pub selected_observer_digest: String,
    pub selected_joint_cost: usize,
    pub observer_gap_receipt_digest: String,
    pub observer_gap_status: ObserverGapStatusV1,
    pub stages: Vec<PipelineStageReceiptV3>,
    pub evidence_digest: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObserverSynthesisPipelineResultV3 {
    pub schema: &'static str,
    pub status: PipelineStatusV3,
    pub failed_stage: Option<PipelineStageV3>,
    pub obstruction: Option<&'static str>,
    pub evidence: Option<ObserverSynthesisPipelineEvidenceV3>,
    pub audit_digest: String,
    pub boundary: &'static str,
}

fn stage_receipt(
    ordinal: usize,
    stage: PipelineStageV3,
    predecessor: Option<&str>,
    output: &str,
    cost: usize,
    limit: usize,
) -> PipelineStageReceiptV3 {
    diagnostics::event("PIPELINE_STAGE_ENTER", "binding atomic pipeline stage");
    let body = format!(
        "{}:{}:{}:{}:{}:{}",
        ordinal,
        stage.as_str(),
        predecessor.unwrap_or("genesis"),
        output,
        cost,
        limit
    );
    let result = PipelineStageReceiptV3 {
        ordinal,
        stage,
        predecessor_digest: predecessor.map(str::to_owned),
        output_digest: output.to_owned(),
        cost,
        limit,
        stage_digest: domain_sha256_hex(STAGE_DOMAIN, body.as_bytes()),
    };
    diagnostics::event("PIPELINE_STAGE_EXIT", "atomic pipeline stage bound");
    result
}

fn terminal(
    status: PipelineStatusV3,
    failed_stage: Option<PipelineStageV3>,
    obstruction: Option<&'static str>,
    evidence: Option<ObserverSynthesisPipelineEvidenceV3>,
    completed_chain_root: &str,
) -> ObserverSynthesisPipelineResultV3 {
    diagnostics::event(
        "PIPELINE_TERMINAL_ENTER",
        "binding atomic pipeline terminal",
    );
    let evidence_root = evidence
        .as_ref()
        .map_or("null", |value| value.evidence_digest.as_str());
    let body = format!(
        "{}:{}:{}:{}:{}",
        status.as_str(),
        failed_stage.map_or("none", PipelineStageV3::as_str),
        obstruction.unwrap_or("none"),
        evidence_root,
        completed_chain_root
    );
    let result = ObserverSynthesisPipelineResultV3 {
        schema: OBSERVER_SYNTHESIS_PIPELINE_V3_SCHEMA,
        status,
        failed_stage,
        obstruction,
        evidence,
        audit_digest: domain_sha256_hex(PIPELINE_DOMAIN, body.as_bytes()),
        boundary: OBSERVER_SYNTHESIS_PIPELINE_V3_BOUNDARY,
    };
    diagnostics::event("PIPELINE_TERMINAL_EXIT", "atomic pipeline terminal bound");
    result
}

fn last_root(stages: &[PipelineStageReceiptV3]) -> &str {
    diagnostics::event("PIPELINE_ROOT_ENTER", "reading completed stage root");
    let result = stages
        .last()
        .map_or("genesis", |row| row.stage_digest.as_str());
    diagnostics::event("PIPELINE_ROOT_EXIT", "completed stage root read");
    result
}

fn transport_evidence_binding(rows: &[TransportEvidenceV3]) -> String {
    diagnostics::event(
        "PIPELINE_TRANSPORT_BIND_ENTER",
        "binding complete transport evidence",
    );
    let body = rows
        .iter()
        .map(|row| {
            format!(
                "{}:{}:{}:{}:{}",
                row.ordinal,
                row.transport_digest,
                row.information_class.as_str(),
                row.collision_count,
                row.cost,
            )
        })
        .collect::<Vec<_>>()
        .join("|");
    let result = domain_sha256_hex(STAGE_DOMAIN, body.as_bytes());
    diagnostics::event(
        "PIPELINE_TRANSPORT_BIND_EXIT",
        "complete transport evidence bound",
    );
    result
}

pub fn run_observer_synthesis_pipeline_v3(
    request: &ObserverSynthesisPipelineRequestV3,
) -> Result<ObserverSynthesisPipelineResultV3, SynthesisCoreError> {
    diagnostics::event(
        "PIPELINE_ENTER",
        "starting atomic observer-synthesis pipeline",
    );
    if request.transports.is_empty() || request.transports.len() > MAX_PIPELINE_TRANSPORTS {
        diagnostics::event("PIPELINE_REJECT", "transport count rejected");
        return Err(SynthesisCoreError("invalid-pipeline-transport-count"));
    }
    if request.gap_request.information_loss_penalty != 0 {
        diagnostics::event("PIPELINE_REJECT", "caller supplied derived loss penalty");
        return Err(SynthesisCoreError(
            "pipeline-untrusted-information-loss-penalty",
        ));
    }
    let mut stages = Vec::with_capacity(5);
    let registry = match grammar_registry_v1() {
        Ok(value) => value,
        Err(_) => {
            diagnostics::event("PIPELINE_BLOCKED", "grammar registry rejected");
            return Ok(terminal(
                PipelineStatusV3::Blocked,
                Some(PipelineStageV3::Normalize),
                Some("grammar-registry-rejected"),
                None,
                last_root(&stages),
            ));
        }
    };
    let selected_profile = registry
        .entries
        .iter()
        .find(|entry| entry.profile_id() == request.gap_request.grammar_profile_id.as_str());
    let Some(selected_profile) = selected_profile else {
        diagnostics::event(
            "PIPELINE_BLOCKED",
            "requested grammar profile is not registered",
        );
        return Ok(terminal(
            PipelineStatusV3::Blocked,
            Some(PipelineStageV3::Normalize),
            Some("grammar-profile-not-registered"),
            None,
            last_root(&stages),
        ));
    };
    let normalize_output = domain_sha256_hex(
        STAGE_DOMAIN,
        format!(
            "{}:{}:{}:{}",
            registry.registry_digest,
            selected_profile.ordinal(),
            selected_profile.profile_digest(),
            selected_profile.catalog_digest()
        )
        .as_bytes(),
    );
    stages.push(stage_receipt(
        0,
        PipelineStageV3::Normalize,
        None,
        &normalize_output,
        registry.entries.len(),
        registry.entries.len(),
    ));

    let mut transport_evidence = Vec::with_capacity(request.transports.len());
    let mut compiled_transports: Vec<CompiledTransportV1> =
        Vec::with_capacity(request.transports.len());
    for (ordinal, term) in request.transports.iter().enumerate() {
        let compiled = match compile_transport(term) {
            Ok(value) => value,
            Err(_) => {
                diagnostics::event("PIPELINE_BLOCKED", "finite transport rejected");
                return Ok(terminal(
                    PipelineStatusV3::Blocked,
                    Some(PipelineStageV3::Transport),
                    Some("finite-transport-rejected"),
                    None,
                    last_root(&stages),
                ));
            }
        };
        transport_evidence.push(TransportEvidenceV3 {
            ordinal,
            transport_digest: compiled.digest().to_owned(),
            information_class: compiled.information_class(),
            collision_count: compiled.collision_count(),
            cost: compiled.cost(),
        });
        compiled_transports.push(compiled);
    }
    let transport_root = transport_evidence_binding(&transport_evidence);
    let declared_transport_cost = transport_evidence.iter().map(|row| row.cost as usize).sum();
    stages.push(stage_receipt(
        1,
        PipelineStageV3::Transport,
        Some(last_root(&stages)),
        &transport_root,
        declared_transport_cost,
        MAX_PIPELINE_TRANSPORTS * usize::from(super::transport_dsl::MAX_TRANSPORT_COMPOSITION_COST),
    ));

    let differential = match differential_transport_observer_search(
        request.gap_request.task_id,
        request.gap_request.grammar_profile_id,
        &request.transports,
        request.gap_request.joint_limits,
    ) {
        Ok(value) => value,
        Err(_) => {
            diagnostics::event("PIPELINE_BLOCKED", "joint differential rejected");
            return Ok(terminal(
                PipelineStatusV3::Blocked,
                Some(PipelineStageV3::Observer),
                Some("joint-differential-rejected"),
                None,
                last_root(&stages),
            ));
        }
    };
    if !differential.equivalent {
        diagnostics::event("PIPELINE_BLOCKED", "joint differential diverged");
        return Ok(terminal(
            PipelineStatusV3::Blocked,
            Some(PipelineStageV3::Observer),
            Some("joint-differential-diverged"),
            None,
            last_root(&stages),
        ));
    }
    if differential.oracle.status == JointSynthesisStatus::Incomplete {
        diagnostics::event("PIPELINE_INCOMPLETE", "joint differential is incomplete");
        return Ok(terminal(
            PipelineStatusV3::Incomplete,
            Some(PipelineStageV3::Observer),
            Some("joint-search-incomplete"),
            None,
            last_root(&stages),
        ));
    }
    let Some(winner) = differential.oracle.winner.as_ref() else {
        diagnostics::event("PIPELINE_BLOCKED", "joint differential has no winner");
        return Ok(terminal(
            PipelineStatusV3::Blocked,
            Some(PipelineStageV3::Observer),
            Some("joint-search-has-no-winner"),
            None,
            last_root(&stages),
        ));
    };
    let selected_transport_ordinal = winner.transport_ordinal;
    let selected = compiled_transports
        .get(selected_transport_ordinal)
        .ok_or_else(|| {
            diagnostics::event(
                "PIPELINE_REJECT",
                "direct winner transport ordinal rejected",
            );
            SynthesisCoreError("pipeline-direct-winner-transport-ordinal")
        })?;
    let selected_transport_digest = transport_evidence[selected_transport_ordinal]
        .transport_digest
        .clone();
    let observer_output = domain_sha256_hex(
        STAGE_DOMAIN,
        format!(
            "{}:{}:{}",
            differential.differential_digest, selected_transport_ordinal, selected_transport_digest
        )
        .as_bytes(),
    );
    stages.push(stage_receipt(
        2,
        PipelineStageV3::Observer,
        Some(last_root(&stages)),
        &observer_output,
        differential.oracle.ledger.relation_evaluations,
        request.gap_request.joint_limits.relation_evaluation_limit,
    ));

    let mut bound_gap_request = request.gap_request.clone();
    bound_gap_request.information_loss_penalty =
        transport_evidence[selected_transport_ordinal].collision_count;
    let gap =
        match observer_gap_from_direct_differential(&bound_gap_request, &differential, selected) {
            Ok(value) => value,
            Err(_) => {
                diagnostics::event("PIPELINE_BLOCKED", "observer-gap experiment rejected");
                return Ok(terminal(
                    PipelineStatusV3::Blocked,
                    Some(PipelineStageV3::Explanation),
                    Some("observer-gap-rejected"),
                    None,
                    last_root(&stages),
                ));
            }
        };
    match gap.status {
        ObserverGapStatusV1::Blocked => {
            diagnostics::event("PIPELINE_BLOCKED", "observer-gap experiment blocked");
            return Ok(terminal(
                PipelineStatusV3::Blocked,
                Some(PipelineStageV3::Explanation),
                Some("observer-gap-blocked"),
                None,
                last_root(&stages),
            ));
        }
        ObserverGapStatusV1::Incomplete => {
            diagnostics::event("PIPELINE_INCOMPLETE", "observer-gap experiment incomplete");
            return Ok(terminal(
                PipelineStatusV3::Incomplete,
                Some(PipelineStageV3::Explanation),
                Some("observer-gap-incomplete"),
                None,
                last_root(&stages),
            ));
        }
        ObserverGapStatusV1::Positive | ObserverGapStatusV1::NoGap => {}
    }
    stages.push(stage_receipt(
        3,
        PipelineStageV3::Explanation,
        Some(last_root(&stages)),
        &gap.receipt_digest,
        gap.baseline_relation_evaluations,
        6 * (request.gap_request.baselines.len() + 1),
    ));
    let aggregate_body = format!(
        "{}:{}:{}:{}:{}:{}:{}:{}:{}:{}:{}",
        registry.registry_digest,
        transport_root,
        observer_output,
        selected_transport_ordinal,
        selected_transport_digest,
        winner.information_class.as_str(),
        winner.collision_count,
        winner.observer_ordinal,
        winner.observer_digest,
        winner.joint_cost,
        gap.receipt_digest
    );
    let aggregate_root = domain_sha256_hex(EVIDENCE_DOMAIN, aggregate_body.as_bytes());
    stages.push(stage_receipt(
        4,
        PipelineStageV3::Aggregate,
        Some(last_root(&stages)),
        &aggregate_root,
        4,
        4,
    ));
    let evidence_body = format!("{}:{}", aggregate_root, last_root(&stages));
    let evidence = ObserverSynthesisPipelineEvidenceV3 {
        grammar_registry_digest: registry.registry_digest,
        transports: transport_evidence,
        differential_digest: differential.differential_digest,
        selected_transport_ordinal,
        selected_transport_digest,
        selected_transport_information_class: winner.information_class,
        selected_transport_collision_count: winner.collision_count,
        selected_observer_ordinal: winner.observer_ordinal,
        selected_observer_digest: winner.observer_digest.clone(),
        selected_joint_cost: winner.joint_cost,
        observer_gap_receipt_digest: gap.receipt_digest,
        observer_gap_status: gap.status,
        stages,
        evidence_digest: domain_sha256_hex(EVIDENCE_DOMAIN, evidence_body.as_bytes()),
    };
    diagnostics::event("PIPELINE_EXIT", "atomic observer-synthesis evidence ready");
    Ok(terminal(
        PipelineStatusV3::Ready,
        None,
        None,
        Some(evidence),
        &aggregate_root,
    ))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::observer_synthesis::{
        differential_joint_search, enumerate_representation_family, FiniteDomainV1,
        JointSynthesisLimits, NamedObserverBaselineV1, NativePartitionTaskId, ObserverGapPolicyV1,
        ObserverGrammarProfileId, TransportOpV1,
    };

    fn winner_transport() -> TransportTermV1 {
        let differential = differential_joint_search(
            NativePartitionTaskId::XorParity,
            ObserverGrammarProfileId::ParityV2,
            JointSynthesisLimits::default(),
        )
        .unwrap();
        let ordinal = differential.oracle.winner.unwrap().transform_ordinal;
        let family = enumerate_representation_family().unwrap();
        let transform = &family.transforms[ordinal];
        TransportTermV1 {
            source: FiniteDomainV1::new("legacy-four-abstract-states-v1", 4).unwrap(),
            target: FiniteDomainV1::new("bounded-recurrence-encoding-0-8-v1", 9).unwrap(),
            op: TransportOpV1::CanonicalEncode(
                transform
                    .permutation()
                    .into_iter()
                    .map(|value| u16::from(value) + u16::from(transform.shift()))
                    .collect(),
            ),
        }
    }

    fn request(limits: JointSynthesisLimits) -> ObserverSynthesisPipelineRequestV3 {
        ObserverSynthesisPipelineRequestV3 {
            gap_request: ObserverGapRequestV1 {
                task_id: NativePartitionTaskId::XorParity,
                grammar_profile_id: ObserverGrammarProfileId::ParityV2,
                joint_limits: limits,
                baselines: vec![NamedObserverBaselineV1 {
                    name: "input".to_owned(),
                    observer_ordinal: 0,
                }],
                policy: ObserverGapPolicyV1::default(),
                information_loss_penalty: 0,
            },
            transports: vec![winner_transport()],
        }
    }

    #[test]
    fn ready_is_atomic_and_reproducible() {
        let first =
            run_observer_synthesis_pipeline_v3(&request(JointSynthesisLimits::default())).unwrap();
        let second =
            run_observer_synthesis_pipeline_v3(&request(JointSynthesisLimits::default())).unwrap();
        assert_eq!(first, second);
        assert_eq!(first.status, PipelineStatusV3::Ready);
        let evidence = first.evidence.unwrap();
        assert_eq!(evidence.selected_transport_ordinal, 0);
        assert_eq!(evidence.stages.len(), 5);
        for (ordinal, stage) in evidence.stages.iter().enumerate() {
            assert_eq!(stage.ordinal, ordinal);
            if ordinal > 0 {
                assert_eq!(
                    stage.predecessor_digest.as_deref(),
                    Some(evidence.stages[ordinal - 1].stage_digest.as_str())
                );
            }
        }
    }

    #[test]
    fn incomplete_has_no_partial_positive_evidence() {
        let report = run_observer_synthesis_pipeline_v3(&request(JointSynthesisLimits {
            relation_evaluation_limit: 5,
            ..JointSynthesisLimits::default()
        }))
        .unwrap();
        assert_eq!(report.status, PipelineStatusV3::Incomplete);
        assert!(report.evidence.is_none());
    }

    #[test]
    fn undeclared_winner_transport_blocks_atomically() {
        let mut nonmatching = request(JointSynthesisLimits::default());
        nonmatching.transports = vec![TransportTermV1 {
            source: FiniteDomainV1::new("not-the-legacy-source", 4).unwrap(),
            target: FiniteDomainV1::new("not-the-legacy-target", 4).unwrap(),
            op: TransportOpV1::Identity,
        }];
        let report = run_observer_synthesis_pipeline_v3(&nonmatching).unwrap();
        assert_eq!(report.status, PipelineStatusV3::Blocked);
        assert_eq!(report.failed_stage, Some(PipelineStageV3::Observer));
        assert_eq!(report.obstruction, Some("joint-search-has-no-winner"));
        assert!(report.evidence.is_none());
    }

    #[test]
    fn transport_root_binds_every_public_evidence_field() {
        let original = TransportEvidenceV3 {
            ordinal: 0,
            transport_digest: "transport-root".to_owned(),
            information_class: TransportInformationClassV1::Injection,
            collision_count: 0,
            cost: 2,
        };
        let root = transport_evidence_binding(std::slice::from_ref(&original));
        let mutations = [
            TransportEvidenceV3 {
                ordinal: 1,
                ..original.clone()
            },
            TransportEvidenceV3 {
                transport_digest: "different-root".to_owned(),
                ..original.clone()
            },
            TransportEvidenceV3 {
                information_class: TransportInformationClassV1::Loss,
                ..original.clone()
            },
            TransportEvidenceV3 {
                collision_count: 1,
                ..original.clone()
            },
            TransportEvidenceV3 {
                cost: 3,
                ..original
            },
        ];
        assert!(mutations
            .iter()
            .all(|row| { transport_evidence_binding(std::slice::from_ref(row)) != root }));
    }
}
