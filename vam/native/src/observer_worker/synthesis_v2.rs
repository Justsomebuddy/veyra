//! Atomic canonical receipt for the closed observer-synthesis v2 calibration wave.

use super::digest::{constant_time_eq, domain_sha256};
use super::event;
use crate::observer_synthesis::{
    enumerate_observer_grammar_profile, enumerate_representation_family,
    grammar_config_for_profile, survey_representation_family, synthesize_transform_and_observer,
    JointSynthesisLimits, JointSynthesisStatus, NativePartitionTaskId, ObserverGrammarProfileId,
    DEFAULT_CANDIDATES, DEFAULT_CANONICAL_BYTES, DEFAULT_CATALOG_DIGEST, DEFAULT_MAX_ROW_BYTES,
    LEGACY_GRAMMAR_PROFILE_DIGEST, PARITY_GRAMMAR_PROFILE_DIGEST, PARITY_INPUT_DIGEST,
    PARITY_V2_CANDIDATES, PARITY_V2_CANONICAL_BYTES, PARITY_V2_CATALOG_DIGEST,
    PARITY_V2_JOINT_ORDER_DIGEST, PARITY_V2_MAX_ROW_BYTES, PARITY_V2_XOR_TRACE_DIGEST,
    PARITY_XOR_PRESERVING_TRANSFORMS, PARITY_XOR_SURVEY_CLASSES, PARITY_XOR_SURVEY_DIGEST,
    REPRESENTATION_FAMILY_DIGEST, REPRESENTATION_TRANSFORMS, XOR_PARITY_TASK_DIGEST,
};

pub const OBSERVER_SYNTHESIS_V2_SCHEMA: &str = "veyra.native-observer-synthesis-wave.v2";
pub const OBSERVER_SYNTHESIS_V2_BOUNDARY: &str =
    "atomic exact evidence only for two closed grammar profiles, the declared 120-row representation family, one parity survey, and two finite XOR joint searches; not global representation invariance, optimality, or theorem evidence";
const RECEIPT_DOMAIN: &[u8] = b"veyra.native-observer-synthesis-wave.v2.receipt";
pub const OBSERVER_SYNTHESIS_V2_RECEIPT_DIGEST_HEX: &str =
    "0202c63f78ff8db0ea590591d0f8c338dc566c7bcfe5cc99d0814962b64c88c5";
const LEGACY_ORDER: &str = "0316e02fc41cd7ca1d7229f88434644bdfc8c80db3729ea338797cbbab37770a";
const LEGACY_TRACE: &str = "8820d9f7da46dea2ce6c37f431fe53be6a6f09bfc091501ac013504e337c7da5";
pub(crate) const MAX_V2_RECEIPT_BYTES: usize = 16 * 1024;

fn reject(reason: &'static str) -> &'static str {
    event("V2_RECEIPT_REJECT", reason);
    reason
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObserverSynthesisV2Receipt {
    pub canonical: Vec<u8>,
    pub receipt_digest: [u8; 32],
}

pub(crate) fn validate_observer_synthesis_v2_canonical(canonical: &[u8]) -> bool {
    event(
        "V2_CANONICAL_VALIDATE_ENTER",
        "validating pinned v2 artifact bytes",
    );
    let result = canonical.len() == 1_941
        && hex_digest(domain_sha256(RECEIPT_DOMAIN, canonical))
            == OBSERVER_SYNTHESIS_V2_RECEIPT_DIGEST_HEX;
    event(
        if result {
            "V2_CANONICAL_VALIDATE_EXIT"
        } else {
            "V2_CANONICAL_VALIDATE_REJECT"
        },
        "pinned v2 artifact bytes validated",
    );
    result
}

pub fn build_observer_synthesis_v2_receipt() -> Result<ObserverSynthesisV2Receipt, &'static str> {
    event(
        "V2_RECEIPT_ENTER",
        "building atomic observer-synthesis v2 receipt",
    );
    let legacy = enumerate_observer_grammar_profile(
        ObserverGrammarProfileId::LegacyV1,
        grammar_config_for_profile(ObserverGrammarProfileId::LegacyV1),
    )
    .map_err(|_| reject("v2-legacy-catalog"))?;
    let parity = enumerate_observer_grammar_profile(
        ObserverGrammarProfileId::ParityV2,
        grammar_config_for_profile(ObserverGrammarProfileId::ParityV2),
    )
    .map_err(|_| reject("v2-parity-catalog"))?;
    let family =
        enumerate_representation_family().map_err(|_| reject("v2-representation-family"))?;
    let survey = survey_representation_family(
        ObserverGrammarProfileId::ParityV2,
        2,
        NativePartitionTaskId::XorParity.target_classes(),
    )
    .map_err(|_| reject("v2-representation-survey"))?;
    let parity_joint = synthesize_transform_and_observer(
        NativePartitionTaskId::XorParity,
        ObserverGrammarProfileId::ParityV2,
        JointSynthesisLimits::default(),
    )
    .map_err(|_| reject("v2-parity-joint"))?;
    let legacy_joint = synthesize_transform_and_observer(
        NativePartitionTaskId::XorParity,
        ObserverGrammarProfileId::LegacyV1,
        JointSynthesisLimits::default(),
    )
    .map_err(|_| reject("v2-legacy-joint"))?;

    if legacy.profile.profile_digest != LEGACY_GRAMMAR_PROFILE_DIGEST
        || legacy.enumeration.catalog_digest != DEFAULT_CATALOG_DIGEST
        || legacy.enumeration.candidates.len() != DEFAULT_CANDIDATES
        || legacy.enumeration.canonical_bytes != DEFAULT_CANONICAL_BYTES
        || legacy.enumeration.max_row_bytes != DEFAULT_MAX_ROW_BYTES
        || parity.profile.profile_digest != PARITY_GRAMMAR_PROFILE_DIGEST
        || parity.enumeration.catalog_digest != PARITY_V2_CATALOG_DIGEST
        || parity.enumeration.candidates.len() != PARITY_V2_CANDIDATES
        || parity.enumeration.canonical_bytes != PARITY_V2_CANONICAL_BYTES
        || parity.enumeration.max_row_bytes != PARITY_V2_MAX_ROW_BYTES
        || family.family_digest != REPRESENTATION_FAMILY_DIGEST
        || family.transforms.len() != REPRESENTATION_TRANSFORMS
        || survey.survey_digest != PARITY_XOR_SURVEY_DIGEST
        || survey.transform_count != REPRESENTATION_TRANSFORMS
        || survey.equivalence_classes.len() != PARITY_XOR_SURVEY_CLASSES
        || survey.preserving_transform_count != PARITY_XOR_PRESERVING_TRANSFORMS
        || survey.observer_digest != PARITY_INPUT_DIGEST
        || parity_joint.status != JointSynthesisStatus::Found
        || parity_joint.task_digest != XOR_PARITY_TASK_DIGEST
        || parity_joint.search_order_digest != PARITY_V2_JOINT_ORDER_DIGEST
        || parity_joint.trace_digest != PARITY_V2_XOR_TRACE_DIGEST
        || parity_joint.ledger.cutoff.is_some()
        || parity_joint.winner.is_none()
        || legacy_joint.status != JointSynthesisStatus::Exhausted
        || legacy_joint.search_order_digest != LEGACY_ORDER
        || legacy_joint.trace_digest != LEGACY_TRACE
        || legacy_joint.ledger.cutoff.is_some()
        || legacy_joint.winner.is_some()
    {
        return Err(reject("v2-pin-mismatch"));
    }
    let winner = parity_joint
        .winner
        .as_ref()
        .ok_or_else(|| reject("v2-parity-winner"))?;
    let canonical = format!(
        "schema={OBSERVER_SYNTHESIS_V2_SCHEMA}\nlegacy_profile={}\nlegacy_catalog={}\nlegacy_candidates={}\nlegacy_canonical_bytes={}\nlegacy_max_row_bytes={}\nparity_profile={}\nparity_catalog={}\nparity_candidates={}\nparity_canonical_bytes={}\nparity_max_row_bytes={}\nfamily_digest={}\nfamily_transforms={}\nsurvey_digest={}\nsurvey_classes={}\nsurvey_preserving={}\nsurvey_observer={}\nparity_task={}\nparity_order={}\nparity_trace={}\nparity_status={}\nparity_transform_limit={}\nparity_candidate_limit={}\nparity_evaluation_limit={}\nparity_pairs={}\nparity_evaluation_charges={}\nparity_winner_transform={}\nparity_winner_observer={}\nlegacy_order={}\nlegacy_trace={}\nlegacy_status={}\nlegacy_transform_limit={}\nlegacy_candidate_limit={}\nlegacy_evaluation_limit={}\nlegacy_pairs={}\nlegacy_evaluation_charges={}\nboundary={OBSERVER_SYNTHESIS_V2_BOUNDARY}\n",
        legacy.profile.profile_digest,
        legacy.enumeration.catalog_digest,
        legacy.enumeration.candidates.len(),
        legacy.enumeration.canonical_bytes,
        legacy.enumeration.max_row_bytes,
        parity.profile.profile_digest,
        parity.enumeration.catalog_digest,
        parity.enumeration.candidates.len(),
        parity.enumeration.canonical_bytes,
        parity.enumeration.max_row_bytes,
        family.family_digest,
        family.transforms.len(),
        survey.survey_digest,
        survey.equivalence_classes.len(),
        survey.preserving_transform_count,
        survey.observer_digest,
        parity_joint.task_digest,
        parity_joint.search_order_digest,
        parity_joint.trace_digest,
        parity_joint.status.as_str(),
        parity_joint.ledger.limits.transform_limit,
        parity_joint.ledger.limits.candidate_limit,
        parity_joint.ledger.limits.relation_evaluation_limit,
        parity_joint.ledger.pair_attempts,
        parity_joint.ledger.relation_evaluations,
        winner.transform_digest,
        winner.observer_digest,
        legacy_joint.search_order_digest,
        legacy_joint.trace_digest,
        legacy_joint.status.as_str(),
        legacy_joint.ledger.limits.transform_limit,
        legacy_joint.ledger.limits.candidate_limit,
        legacy_joint.ledger.limits.relation_evaluation_limit,
        legacy_joint.ledger.pair_attempts,
        legacy_joint.ledger.relation_evaluations,
    )
    .into_bytes();
    if canonical.len() > MAX_V2_RECEIPT_BYTES {
        return Err(reject("v2-receipt-size"));
    }
    let receipt = ObserverSynthesisV2Receipt {
        receipt_digest: domain_sha256(RECEIPT_DOMAIN, &canonical),
        canonical,
    };
    if hex_digest(receipt.receipt_digest) != OBSERVER_SYNTHESIS_V2_RECEIPT_DIGEST_HEX {
        return Err(reject("v2-receipt-pin-mismatch"));
    }
    event(
        "V2_RECEIPT_EXIT",
        "atomic observer-synthesis v2 receipt built",
    );
    Ok(receipt)
}

fn hex_digest(digest: [u8; 32]) -> String {
    let mut output = String::with_capacity(64);
    for byte in digest {
        use std::fmt::Write;
        write!(&mut output, "{byte:02x}").expect("writing to String cannot fail");
    }
    output
}

pub fn replay_observer_synthesis_v2_receipt(
    receipt: &ObserverSynthesisV2Receipt,
) -> Result<ObserverSynthesisV2Receipt, &'static str> {
    event(
        "V2_REPLAY_ENTER",
        "fresh-replaying observer-synthesis v2 receipt",
    );
    if receipt.canonical.len() > MAX_V2_RECEIPT_BYTES
        || !constant_time_eq(
            &receipt.receipt_digest,
            &domain_sha256(RECEIPT_DOMAIN, &receipt.canonical),
        )
    {
        return Err(reject("v2-receipt-digest"));
    }
    let fresh =
        build_observer_synthesis_v2_receipt().map_err(|_| reject("v2-receipt-fresh-build"))?;
    if !constant_time_eq(&receipt.canonical, &fresh.canonical)
        || !constant_time_eq(&receipt.receipt_digest, &fresh.receipt_digest)
    {
        return Err(reject("v2-receipt-replay-mismatch"));
    }
    event(
        "V2_REPLAY_EXIT",
        "observer-synthesis v2 receipt replayed exactly",
    );
    Ok(fresh)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::observer_synthesis::{synthesize_transform_and_observer, JointBudgetCutoff};

    #[test]
    fn atomic_receipt_replays_and_tampering_fails() {
        let receipt = build_observer_synthesis_v2_receipt().unwrap();
        assert_eq!(receipt.canonical.len(), 1_941);
        assert_eq!(
            replay_observer_synthesis_v2_receipt(&receipt).unwrap(),
            receipt
        );
        let mut tampered = receipt;
        tampered.canonical[0] ^= 1;
        assert!(replay_observer_synthesis_v2_receipt(&tampered).is_err());
    }

    #[test]
    fn cutoff_is_incomplete_and_cannot_mint_atomic_receipt() {
        let cutoff = synthesize_transform_and_observer(
            NativePartitionTaskId::XorParity,
            ObserverGrammarProfileId::ParityV2,
            JointSynthesisLimits {
                relation_evaluation_limit: 131,
                ..JointSynthesisLimits::default()
            },
        )
        .unwrap();
        assert_eq!(cutoff.status, JointSynthesisStatus::Incomplete);
        assert_eq!(
            cutoff.ledger.cutoff,
            Some(JointBudgetCutoff::RelationEvaluations)
        );
        assert!(cutoff.winner.is_none());
        assert_ne!(cutoff.trace_digest, PARITY_V2_XOR_TRACE_DIGEST);
    }
}
