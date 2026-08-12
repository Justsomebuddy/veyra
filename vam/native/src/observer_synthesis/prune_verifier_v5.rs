//! Independent proof-ledger verifier for discovery-v5 branch-and-bound.

use super::ast::SynthesisCoreError;
use super::diagnostics;
use super::discovery_benchmark_v5::discovery_benchmark_v5;
use super::grammar_v5::{
    enumerate_discovery_grammar_v5, DiscoveryObserverCandidateV5, DiscoveryObserverTermV5,
};
use super::hash::domain_sha256_hex;
use super::synthesis_v5::{
    discovery_result_v5_root, synthesize_discovery_v5_exhaustive, DiscoverySearchRequestV5,
    DiscoverySearchResultV5, DiscoverySearchStatusV5, DiscoveryWinnerV5,
    DISCOVERY_SYNTHESIS_V5_BOUNDARY, DISCOVERY_SYNTHESIS_V5_SCHEMA, MAX_DISCOVERY_V5_CANDIDATES,
    MAX_DISCOVERY_V5_PAIR_DISPOSITIONS, MAX_DISCOVERY_V5_TOTAL_COST,
};

const RESULT_DOMAIN: &str = "veyra.discovery-observer-synthesis.result.v5.binding";
const LOWER_BOUND_DOMAIN: &str = "veyra.discovery-observer-synthesis.lower-bound.v5.binding";
const PRUNE_PROOF_DOMAIN: &str = "veyra.discovery-observer-synthesis.prune-proof.v5.binding";
const PAIR_OBLIGATIONS: usize = 120;

fn valid_request(request: &DiscoverySearchRequestV5) -> bool {
    request.maximum_total_cost > 0
        && request.maximum_total_cost <= MAX_DISCOVERY_V5_TOTAL_COST
        && request.limits.candidate_limit > 0
        && request.limits.candidate_limit <= MAX_DISCOVERY_V5_CANDIDATES
        && request.limits.pair_disposition_limit > 0
        && request.limits.pair_disposition_limit <= MAX_DISCOVERY_V5_PAIR_DISPOSITIONS
}

fn partition(values: [u8; 16]) -> [u8; 16] {
    let mut labels = [u8::MAX; 16];
    let mut next = 0u8;
    std::array::from_fn(|index| {
        let value = values[index] as usize;
        if labels[value] == u8::MAX {
            labels[value] = next;
            next += 1;
        }
        labels[value]
    })
}

fn fits(candidate: &DiscoveryObserverCandidateV5, targets: [u8; 16]) -> bool {
    partition(candidate.responses()) == partition(targets)
}

fn lower_bound_digest(admitted: &[&DiscoveryObserverCandidateV5]) -> String {
    let body = admitted
        .iter()
        .map(|row| format!("{}:{}:{}", row.ordinal, row.cost, row.candidate_digest))
        .collect::<Vec<_>>()
        .join(":");
    domain_sha256_hex(LOWER_BOUND_DOMAIN, body.as_bytes())
}

fn prune_digest(
    admitted: &[&DiscoveryObserverCandidateV5],
    evaluated: usize,
    winner: Option<&DiscoveryWinnerV5>,
) -> String {
    let suffix = admitted
        .iter()
        .skip(evaluated)
        .map(|row| format!("{}:{}:{}", row.ordinal, row.cost, row.candidate_digest))
        .collect::<Vec<_>>()
        .join(":");
    let incumbent = winner.map_or_else(
        || "none".to_owned(),
        |row| format!("{}:{}", row.candidate_ordinal, row.total_cost),
    );
    domain_sha256_hex(
        PRUNE_PROOF_DOMAIN,
        format!("{evaluated}:{incumbent}:{suffix}").as_bytes(),
    )
}

fn representation_digest(candidate: &DiscoveryObserverCandidateV5, task: &str) -> String {
    let (multiplier, shift) = match candidate.term {
        DiscoveryObserverTermV5::AffineBitParity {
            multiplier, shift, ..
        }
        | DiscoveryObserverTermV5::AffineReflectionOrbit { multiplier, shift } => {
            (multiplier, shift)
        }
    };
    domain_sha256_hex(
        RESULT_DOMAIN,
        format!("affine-representation:{multiplier}:{shift}:{task}").as_bytes(),
    )
}

fn expected_winner(
    candidate: &DiscoveryObserverCandidateV5,
    admitted: &[&DiscoveryObserverCandidateV5],
    targets: [u8; 16],
    task: &str,
) -> DiscoveryWinnerV5 {
    let alternatives = admitted
        .iter()
        .filter(|row| row.cost == candidate.cost && fits(row, targets))
        .count()
        .saturating_sub(1);
    DiscoveryWinnerV5 {
        candidate_ordinal: candidate.ordinal,
        candidate_digest: candidate.candidate_digest.clone(),
        total_cost: candidate.cost,
        observer_gap: candidate
            .cost
            .saturating_sub(admitted.first().map_or(candidate.cost, |row| row.cost)),
        alternatives_at_same_cost: alternatives,
        representation_digest: representation_digest(candidate, task),
        explanation_digest: domain_sha256_hex(
            RESULT_DOMAIN,
            format!(
                "exact-equality-partition:{}:{task}",
                candidate.response_digest
            )
            .as_bytes(),
        ),
        witness_digest: domain_sha256_hex(
            RESULT_DOMAIN,
            format!("{}:{task}:exact-partition", candidate.candidate_digest).as_bytes(),
        ),
    }
}

pub(super) fn verify_branch_bound_proof_independent_v5(
    request: &DiscoverySearchRequestV5,
    claimed: &DiscoverySearchResultV5,
) -> Result<bool, SynthesisCoreError> {
    diagnostics::event(
        "PRUNE_V5_VERIFY_ENTER",
        "independently verifying v5 prune proof",
    );
    if !valid_request(request)
        || !claimed.optimized
        || claimed.schema != DISCOVERY_SYNTHESIS_V5_SCHEMA
        || claimed.boundary != DISCOVERY_SYNTHESIS_V5_BOUNDARY
        || claimed.maximum_total_cost != request.maximum_total_cost
        || claimed.ledger.limits != request.limits
        || claimed.result_digest != discovery_result_v5_root(claimed)?
    {
        diagnostics::event("PRUNE_V5_VERIFY_REJECT", "v5 outer proof binding rejected");
        return Ok(false);
    }
    let benchmark = discovery_benchmark_v5(request.benchmark_id)?;
    let catalog = enumerate_discovery_grammar_v5(request.profile_id)?;
    let admitted: Vec<_> = catalog
        .candidates
        .iter()
        .filter(|row| row.cost <= request.maximum_total_cost)
        .collect();
    let admissible_pairs = admitted
        .len()
        .checked_mul(PAIR_OBLIGATIONS)
        .ok_or(SynthesisCoreError("discovery-v5-verifier-pair-overflow"))?;
    if claimed.benchmark_digest != benchmark.task_digest
        || claimed.benchmark_split != benchmark.split
        || claimed.grammar_profile_digest != catalog.profile.profile_digest
        || claimed.catalog_digest != catalog.catalog_digest
        || claimed.ledger.candidates != catalog.candidates.len()
        || claimed.ledger.admissible_pairs != admissible_pairs
        || claimed.ledger.lower_bound_digest != lower_bound_digest(&admitted)
    {
        diagnostics::event("PRUNE_V5_VERIFY_REJECT", "v5 catalog ledger rejected");
        return Ok(false);
    }
    let cutoff = catalog.candidates.len() > request.limits.candidate_limit
        || admissible_pairs > request.limits.pair_disposition_limit;
    if cutoff {
        let valid = claimed.status == DiscoverySearchStatusV5::Cutoff
            && claimed.detail == "complete-admitted-product-exceeds-limits"
            && claimed.winner.is_none()
            && claimed.ledger.cutoff
            && claimed.ledger.evaluated_pairs == 0
            && claimed.ledger.pruned_pairs == 0
            && claimed.ledger.incumbent_cost.is_none()
            && claimed.ledger.first_pruned_cost_lower_bound.is_none()
            && claimed.ledger.bound_admissible
            && claimed.ledger.prune_proof_digest == prune_digest(&admitted, 0, None);
        diagnostics::event(
            if valid {
                "PRUNE_V5_VERIFY_EXIT"
            } else {
                "PRUNE_V5_VERIFY_REJECT"
            },
            "v5 cutoff proof checked",
        );
        return Ok(valid);
    }
    if claimed.ledger.cutoff || claimed.ledger.evaluated_pairs % PAIR_OBLIGATIONS != 0 {
        diagnostics::event(
            "PRUNE_V5_VERIFY_REJECT",
            "v5 non-cutoff accounting rejected",
        );
        return Ok(false);
    }
    let evaluated = claimed.ledger.evaluated_pairs / PAIR_OBLIGATIONS;
    let first_fit = admitted
        .iter()
        .position(|row| fits(row, benchmark.target_classes));
    let (status, detail, expected_winner, expected_evaluated, expected_pruned) = match first_fit {
        Some(index) => {
            let winner = expected_winner(
                admitted[index],
                &admitted,
                benchmark.target_classes,
                &benchmark.task_digest,
            );
            (
                DiscoverySearchStatusV5::Found,
                "minimum-catalog-relative-witness",
                Some(winner),
                index + 1,
                admitted.len() - index - 1,
            )
        }
        None => (
            DiscoverySearchStatusV5::Exhausted,
            "complete-cost-admitted-catalog-exhausted",
            None,
            admitted.len(),
            0,
        ),
    };
    let expected_incumbent = expected_winner.as_ref().map(|row| row.total_cost);
    let expected_suffix_bound = admitted.get(expected_evaluated).map(|row| row.cost);
    let bound_admissible = match (expected_incumbent, expected_suffix_bound) {
        (Some(incumbent), Some(bound)) => bound >= incumbent,
        (_, None) => true,
        (None, Some(_)) => false,
    };
    let exhaustive = synthesize_discovery_v5_exhaustive(request)?;
    let valid = claimed.status == status
        && claimed.detail == detail
        && claimed.winner == expected_winner
        && evaluated == expected_evaluated
        && claimed.ledger.evaluated_pairs == expected_evaluated * PAIR_OBLIGATIONS
        && claimed.ledger.pruned_pairs == expected_pruned * PAIR_OBLIGATIONS
        && claimed.ledger.evaluated_pairs + claimed.ledger.pruned_pairs == admissible_pairs
        && claimed.ledger.incumbent_cost == expected_incumbent
        && claimed.ledger.first_pruned_cost_lower_bound == expected_suffix_bound
        && claimed.ledger.bound_admissible == bound_admissible
        && bound_admissible
        && claimed.ledger.prune_proof_digest
            == prune_digest(&admitted, expected_evaluated, expected_winner.as_ref())
        && exhaustive.status == status
        && exhaustive.detail == detail
        && exhaustive.winner == expected_winner;
    diagnostics::event(
        if valid {
            "PRUNE_V5_VERIFY_EXIT"
        } else {
            "PRUNE_V5_VERIFY_REJECT"
        },
        "independent v5 prune proof checked",
    );
    Ok(valid)
}
