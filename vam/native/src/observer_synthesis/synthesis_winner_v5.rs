//! Producer-side winner binding for represented discovery-v5 tasks.

use super::diagnostics;
use super::grammar_v5::{DiscoveryObserverCandidateV5, DiscoveryObserverTermV5};
use super::hash::domain_sha256_hex;
use super::synthesis_v5::DiscoveryWinnerV5;

const RESULT_DOMAIN: &str = "veyra.discovery-observer-synthesis.result.v5.binding";

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

fn explanation_digest(
    candidate: &DiscoveryObserverCandidateV5,
    surface_states: &[u8; 16],
    task: &str,
) -> String {
    diagnostics::event(
        "SYNTH_V5_EXPLANATION_ENTER",
        "binding represented response explanation",
    );
    let represented: [u8; 16] =
        std::array::from_fn(|index| candidate.term.response(surface_states[index]));
    let response_digest = domain_sha256_hex(RESULT_DOMAIN, &represented);
    let result = domain_sha256_hex(
        RESULT_DOMAIN,
        format!("exact-represented-equality-partition:{response_digest}:{task}").as_bytes(),
    );
    diagnostics::event(
        "SYNTH_V5_EXPLANATION_EXIT",
        "represented response explanation bound",
    );
    result
}

pub(super) fn winner_for(
    candidate: &DiscoveryObserverCandidateV5,
    admitted: &[&DiscoveryObserverCandidateV5],
    alternatives_at_same_cost: usize,
    surface_states: &[u8; 16],
    task: &str,
) -> DiscoveryWinnerV5 {
    diagnostics::event(
        "SYNTH_V5_WINNER_ENTER",
        "constructing represented-task winner",
    );
    let result = DiscoveryWinnerV5 {
        candidate_ordinal: candidate.ordinal,
        candidate_digest: candidate.candidate_digest.clone(),
        total_cost: candidate.cost,
        observer_gap: candidate
            .cost
            .saturating_sub(admitted.first().map_or(candidate.cost, |row| row.cost)),
        alternatives_at_same_cost,
        representation_digest: representation_digest(candidate, task),
        explanation_digest: explanation_digest(candidate, surface_states, task),
        witness_digest: domain_sha256_hex(
            RESULT_DOMAIN,
            format!("{}:{task}:exact-partition", candidate.candidate_digest).as_bytes(),
        ),
    };
    diagnostics::event(
        "SYNTH_V5_WINNER_EXIT",
        "represented-task winner constructed",
    );
    result
}
