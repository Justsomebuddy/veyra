//! Proof-carrying branch-and-bound over the generated discovery-v5 tasks.

use super::ast::SynthesisCoreError;
use super::diagnostics;
use super::discovery_benchmark_v5::{
    discovery_benchmark_v5, DiscoveryBenchmarkIdV5, DiscoveryBenchmarkSplitV5,
};
use super::grammar_v5::{
    enumerate_discovery_grammar_v5, DiscoveryGrammarProfileIdV5, DiscoveryObserverCandidateV5,
};
use super::hash::domain_sha256_hex;

pub const DISCOVERY_SYNTHESIS_V5_SCHEMA: &str = "veyra.discovery-observer-synthesis.v5";
const REQUEST_DOMAIN: &str = "veyra.discovery-observer-synthesis.request.v5.binding";
const RESULT_DOMAIN: &str = "veyra.discovery-observer-synthesis.result.v5.binding";
const LOWER_BOUND_DOMAIN: &str = "veyra.discovery-observer-synthesis.lower-bound.v5.binding";
const PRUNE_PROOF_DOMAIN: &str = "veyra.discovery-observer-synthesis.prune-proof.v5.binding";
const DIFFERENTIAL_DOMAIN: &str = "veyra.discovery-observer-synthesis.differential.v5.binding";
pub const MAX_DISCOVERY_V5_CANDIDATES: usize = 2_048;
pub const MAX_DISCOVERY_V5_PAIR_DISPOSITIONS: usize = 245_760;
pub const MAX_DISCOVERY_V5_TOTAL_COST: usize = 64;
pub const DISCOVERY_BENCHMARK_RUN_V5_DIGEST: &str =
    "a53dd8ad4fde38a5e48a5ef9d3bdd218802a6335ccd4643c627ea7a294e9c956";
const PAIR_OBLIGATIONS: usize = 120;
pub const DISCOVERY_SYNTHESIS_V5_BOUNDARY: &str = "FOUND is the first minimum (declared cost, catalog ordinal) exact partition witness for one generated task; EXHAUSTED means every cost-admitted catalog candidate was evaluated; CUTOFF is decided before search whenever physical counters cannot cover the complete admitted product; branch-and-bound pruning is justified only by the catalog's monotone intrinsic-cost lower bound and independently checked against an exhaustive implementation";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum DiscoverySearchStatusV5 {
    Found,
    Exhausted,
    Cutoff,
}

impl DiscoverySearchStatusV5 {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Found => "FOUND",
            Self::Exhausted => "EXHAUSTED",
            Self::Cutoff => "CUTOFF",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct DiscoverySearchLimitsV5 {
    pub candidate_limit: usize,
    pub pair_disposition_limit: usize,
}

impl Default for DiscoverySearchLimitsV5 {
    fn default() -> Self {
        diagnostics::event("SYNTH_V5_LIMITS_ENTER", "constructing v5 limits");
        let result = Self {
            candidate_limit: MAX_DISCOVERY_V5_CANDIDATES,
            pair_disposition_limit: MAX_DISCOVERY_V5_PAIR_DISPOSITIONS,
        };
        diagnostics::event("SYNTH_V5_LIMITS_EXIT", "v5 limits constructed");
        result
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DiscoverySearchRequestV5 {
    pub benchmark_id: DiscoveryBenchmarkIdV5,
    pub profile_id: DiscoveryGrammarProfileIdV5,
    pub maximum_total_cost: usize,
    pub limits: DiscoverySearchLimitsV5,
}

impl DiscoverySearchRequestV5 {
    pub fn systematic(benchmark_id: DiscoveryBenchmarkIdV5) -> Self {
        diagnostics::event(
            "SYNTH_V5_REQUEST_ENTER",
            "constructing systematic v5 request",
        );
        let result = Self {
            benchmark_id,
            profile_id: DiscoveryGrammarProfileIdV5::AffineParityReflectionV5,
            maximum_total_cost: MAX_DISCOVERY_V5_TOTAL_COST,
            limits: DiscoverySearchLimitsV5::default(),
        };
        diagnostics::event("SYNTH_V5_REQUEST_EXIT", "systematic v5 request constructed");
        result
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DiscoveryPruneLedgerV5 {
    pub limits: DiscoverySearchLimitsV5,
    pub candidates: usize,
    pub admissible_pairs: usize,
    pub evaluated_pairs: usize,
    pub pruned_pairs: usize,
    pub cutoff: bool,
    pub incumbent_cost: Option<usize>,
    pub first_pruned_cost_lower_bound: Option<usize>,
    pub bound_admissible: bool,
    pub lower_bound_digest: String,
    pub prune_proof_digest: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DiscoveryWinnerV5 {
    pub candidate_ordinal: usize,
    pub candidate_digest: String,
    pub total_cost: usize,
    pub observer_gap: usize,
    pub alternatives_at_same_cost: usize,
    pub representation_digest: String,
    pub explanation_digest: String,
    pub witness_digest: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DiscoverySearchResultV5 {
    pub schema: &'static str,
    pub optimized: bool,
    pub status: DiscoverySearchStatusV5,
    pub detail: &'static str,
    pub ledger: DiscoveryPruneLedgerV5,
    pub winner: Option<DiscoveryWinnerV5>,
    pub benchmark_digest: String,
    pub benchmark_split: DiscoveryBenchmarkSplitV5,
    pub grammar_profile_digest: String,
    pub catalog_digest: String,
    pub maximum_total_cost: usize,
    pub result_digest: String,
    pub boundary: &'static str,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DiscoverySearchDifferentialV5 {
    pub reference: DiscoverySearchResultV5,
    pub optimized: DiscoverySearchResultV5,
    pub equivalent: bool,
    pub differential_digest: String,
    pub boundary: &'static str,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DiscoveryBenchmarkRunV5 {
    pub rows: Vec<DiscoverySearchDifferentialV5>,
    pub found: usize,
    pub exhausted: usize,
    pub cutoff: usize,
    pub run_digest: String,
    pub boundary: &'static str,
}

pub fn canonical_discovery_request_v5_bytes(
    request: &DiscoverySearchRequestV5,
) -> Result<Vec<u8>, SynthesisCoreError> {
    diagnostics::event(
        "SYNTH_V5_REQUEST_CODEC_ENTER",
        "encoding canonical v5 request",
    );
    validate_request(request)?;
    let result = format!(
        "{DISCOVERY_SYNTHESIS_V5_SCHEMA}\0{}\0{}\0{}\0{}\0{}",
        request.benchmark_id.as_str(),
        request.profile_id.as_str(),
        request.maximum_total_cost,
        request.limits.candidate_limit,
        request.limits.pair_disposition_limit,
    )
    .into_bytes();
    diagnostics::event(
        "SYNTH_V5_REQUEST_CODEC_EXIT",
        "canonical v5 request encoded",
    );
    Ok(result)
}

fn parse_usize_v5(value: &str) -> Result<usize, SynthesisCoreError> {
    if value.is_empty() || (value.len() > 1 && value.starts_with('0')) {
        return Err(SynthesisCoreError("noncanonical-discovery-v5-integer"));
    }
    value
        .parse()
        .map_err(|_| SynthesisCoreError("invalid-discovery-v5-integer"))
}

fn benchmark_id_v5(value: &str) -> Result<DiscoveryBenchmarkIdV5, SynthesisCoreError> {
    match value {
        "hidden-affine-v5" => Ok(DiscoveryBenchmarkIdV5::HiddenAffine),
        "reflection-symmetry-v5" => Ok(DiscoveryBenchmarkIdV5::ReflectionSymmetry),
        "misrepresentation-recovery-v5" => Ok(DiscoveryBenchmarkIdV5::MisrepresentationRecovery),
        "diagonal-negative-control-v5" => Ok(DiscoveryBenchmarkIdV5::DiagonalNegativeControl),
        "held-out-affine-v5" => Ok(DiscoveryBenchmarkIdV5::HeldOutAffine),
        _ => Err(SynthesisCoreError("unknown-discovery-benchmark-v5")),
    }
}

pub fn decode_discovery_request_v5_bytes(
    bytes: &[u8],
) -> Result<DiscoverySearchRequestV5, SynthesisCoreError> {
    diagnostics::event(
        "SYNTH_V5_REQUEST_DECODE_ENTER",
        "decoding canonical v5 request",
    );
    if bytes.len() > 1_024 {
        diagnostics::event(
            "SYNTH_V5_REQUEST_DECODE_REJECT",
            "v5 request bytes exceed bound",
        );
        return Err(SynthesisCoreError("discovery-v5-request-bytes-limit"));
    }
    let text = std::str::from_utf8(bytes)
        .map_err(|_| SynthesisCoreError("invalid-discovery-v5-request-utf8"))?;
    let fields: Vec<_> = text.split('\0').collect();
    if fields.len() != 6 || fields[0] != DISCOVERY_SYNTHESIS_V5_SCHEMA {
        diagnostics::event(
            "SYNTH_V5_REQUEST_DECODE_REJECT",
            "v5 request shape rejected",
        );
        return Err(SynthesisCoreError("invalid-discovery-v5-request-shape"));
    }
    let profile_id = match fields[2] {
        super::grammar_v5::DISCOVERY_GRAMMAR_V5_PROFILE_ID => {
            DiscoveryGrammarProfileIdV5::AffineParityReflectionV5
        }
        _ => return Err(SynthesisCoreError("unknown-discovery-grammar-profile-v5")),
    };
    let request = DiscoverySearchRequestV5 {
        benchmark_id: benchmark_id_v5(fields[1])?,
        profile_id,
        maximum_total_cost: parse_usize_v5(fields[3])?,
        limits: DiscoverySearchLimitsV5 {
            candidate_limit: parse_usize_v5(fields[4])?,
            pair_disposition_limit: parse_usize_v5(fields[5])?,
        },
    };
    validate_request(&request)?;
    if canonical_discovery_request_v5_bytes(&request)? != bytes {
        diagnostics::event(
            "SYNTH_V5_REQUEST_DECODE_REJECT",
            "v5 request is not canonical",
        );
        return Err(SynthesisCoreError("noncanonical-discovery-v5-request"));
    }
    diagnostics::event(
        "SYNTH_V5_REQUEST_DECODE_EXIT",
        "canonical v5 request decoded",
    );
    Ok(request)
}

pub fn discovery_request_v5_root(
    request: &DiscoverySearchRequestV5,
) -> Result<String, SynthesisCoreError> {
    diagnostics::event("SYNTH_V5_REQUEST_ROOT_ENTER", "binding v5 request root");
    let result = domain_sha256_hex(
        REQUEST_DOMAIN,
        &canonical_discovery_request_v5_bytes(request)?,
    );
    diagnostics::event("SYNTH_V5_REQUEST_ROOT_EXIT", "v5 request root bound");
    Ok(result)
}

pub fn canonical_discovery_result_v5_bytes(
    result: &DiscoverySearchResultV5,
) -> Result<Vec<u8>, SynthesisCoreError> {
    diagnostics::event(
        "SYNTH_V5_RESULT_CODEC_ENTER",
        "encoding canonical v5 result",
    );
    let winner = result.winner.as_ref().map_or_else(
        || "none".to_owned(),
        |row| {
            format!(
                "{}:{}:{}:{}:{}:{}:{}:{}",
                row.candidate_ordinal,
                row.candidate_digest,
                row.total_cost,
                row.observer_gap,
                row.alternatives_at_same_cost,
                row.representation_digest,
                row.explanation_digest,
                row.witness_digest
            )
        },
    );
    let bytes = format!(
        "{}\0{}\0{}\0{}\0{}\0{}\0{}\0{}\0{}\0{}\0{}\0{}\0{}\0{}\0{}\0{}\0{}\0{}\0{}\0{}\0{}\0{}\0{}",
        result.schema,
        result.optimized,
        result.status.as_str(),
        result.detail,
        result.ledger.limits.candidate_limit,
        result.ledger.limits.pair_disposition_limit,
        result.ledger.candidates,
        result.ledger.admissible_pairs,
        result.ledger.evaluated_pairs,
        result.ledger.pruned_pairs,
        result.ledger.cutoff,
        result
            .ledger
            .incumbent_cost
            .map_or_else(|| "none".to_owned(), |value| value.to_string()),
        result
            .ledger
            .first_pruned_cost_lower_bound
            .map_or_else(|| "none".to_owned(), |value| value.to_string()),
        result.ledger.bound_admissible,
        result.ledger.lower_bound_digest,
        result.ledger.prune_proof_digest,
        winner,
        result.benchmark_digest,
        result.benchmark_split.as_str(),
        result.grammar_profile_digest,
        result.catalog_digest,
        result.maximum_total_cost,
        result.boundary,
    )
    .into_bytes();
    diagnostics::event("SYNTH_V5_RESULT_CODEC_EXIT", "canonical v5 result encoded");
    Ok(bytes)
}

fn parse_bool_v5(value: &str) -> Result<bool, SynthesisCoreError> {
    match value {
        "true" => Ok(true),
        "false" => Ok(false),
        _ => Err(SynthesisCoreError("invalid-discovery-v5-boolean")),
    }
}

fn status_v5(value: &str) -> Result<DiscoverySearchStatusV5, SynthesisCoreError> {
    match value {
        "FOUND" => Ok(DiscoverySearchStatusV5::Found),
        "EXHAUSTED" => Ok(DiscoverySearchStatusV5::Exhausted),
        "CUTOFF" => Ok(DiscoverySearchStatusV5::Cutoff),
        _ => Err(SynthesisCoreError("invalid-discovery-v5-status")),
    }
}

fn valid_digest(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

pub fn decode_discovery_result_v5_bytes(
    bytes: &[u8],
) -> Result<DiscoverySearchResultV5, SynthesisCoreError> {
    diagnostics::event(
        "SYNTH_V5_RESULT_DECODE_ENTER",
        "decoding canonical v5 result",
    );
    if bytes.len() > 8 * 1024 {
        diagnostics::event(
            "SYNTH_V5_RESULT_DECODE_REJECT",
            "v5 result bytes exceed bound",
        );
        return Err(SynthesisCoreError("discovery-v5-result-bytes-limit"));
    }
    let text = std::str::from_utf8(bytes)
        .map_err(|_| SynthesisCoreError("invalid-discovery-v5-result-utf8"))?;
    let fields: Vec<_> = text.split('\0').collect();
    if fields.len() != 23 || fields[0] != DISCOVERY_SYNTHESIS_V5_SCHEMA {
        diagnostics::event("SYNTH_V5_RESULT_DECODE_REJECT", "v5 result shape rejected");
        return Err(SynthesisCoreError("invalid-discovery-v5-result-shape"));
    }
    let status = status_v5(fields[2])?;
    let detail = match fields[3] {
        "minimum-catalog-relative-witness" => "minimum-catalog-relative-witness",
        "complete-cost-admitted-catalog-exhausted" => "complete-cost-admitted-catalog-exhausted",
        "complete-admitted-product-exceeds-limits" => "complete-admitted-product-exceeds-limits",
        _ => return Err(SynthesisCoreError("invalid-discovery-v5-detail")),
    };
    let winner = if fields[16] == "none" {
        None
    } else {
        let parts: Vec<_> = fields[16].split(':').collect();
        if parts.len() != 8
            || !valid_digest(parts[1])
            || !valid_digest(parts[5])
            || !valid_digest(parts[6])
            || !valid_digest(parts[7])
        {
            return Err(SynthesisCoreError("invalid-discovery-v5-winner"));
        }
        Some(DiscoveryWinnerV5 {
            candidate_ordinal: parse_usize_v5(parts[0])?,
            candidate_digest: parts[1].to_owned(),
            total_cost: parse_usize_v5(parts[2])?,
            observer_gap: parse_usize_v5(parts[3])?,
            alternatives_at_same_cost: parse_usize_v5(parts[4])?,
            representation_digest: parts[5].to_owned(),
            explanation_digest: parts[6].to_owned(),
            witness_digest: parts[7].to_owned(),
        })
    };
    if ![fields[14], fields[15], fields[17], fields[19], fields[20]]
        .into_iter()
        .all(valid_digest)
        || fields[22] != DISCOVERY_SYNTHESIS_V5_BOUNDARY
    {
        return Err(SynthesisCoreError("invalid-discovery-v5-result-binding"));
    }
    let result = DiscoverySearchResultV5 {
        schema: DISCOVERY_SYNTHESIS_V5_SCHEMA,
        optimized: parse_bool_v5(fields[1])?,
        status,
        detail,
        ledger: DiscoveryPruneLedgerV5 {
            limits: DiscoverySearchLimitsV5 {
                candidate_limit: parse_usize_v5(fields[4])?,
                pair_disposition_limit: parse_usize_v5(fields[5])?,
            },
            candidates: parse_usize_v5(fields[6])?,
            admissible_pairs: parse_usize_v5(fields[7])?,
            evaluated_pairs: parse_usize_v5(fields[8])?,
            pruned_pairs: parse_usize_v5(fields[9])?,
            cutoff: parse_bool_v5(fields[10])?,
            incumbent_cost: if fields[11] == "none" {
                None
            } else {
                Some(parse_usize_v5(fields[11])?)
            },
            first_pruned_cost_lower_bound: if fields[12] == "none" {
                None
            } else {
                Some(parse_usize_v5(fields[12])?)
            },
            bound_admissible: parse_bool_v5(fields[13])?,
            lower_bound_digest: fields[14].to_owned(),
            prune_proof_digest: fields[15].to_owned(),
        },
        winner,
        benchmark_digest: fields[17].to_owned(),
        benchmark_split: match fields[18] {
            "CALIBRATION" => DiscoveryBenchmarkSplitV5::Calibration,
            "SYNTHETIC_HELD_OUT" => DiscoveryBenchmarkSplitV5::SyntheticHeldOut,
            _ => return Err(SynthesisCoreError("invalid-discovery-v5-benchmark-split")),
        },
        grammar_profile_digest: fields[19].to_owned(),
        catalog_digest: fields[20].to_owned(),
        maximum_total_cost: parse_usize_v5(fields[21])?,
        result_digest: String::new(),
        boundary: DISCOVERY_SYNTHESIS_V5_BOUNDARY,
    };
    if result.ledger.candidates > MAX_DISCOVERY_V5_CANDIDATES
        || result.ledger.admissible_pairs > MAX_DISCOVERY_V5_PAIR_DISPOSITIONS
        || result.ledger.evaluated_pairs > result.ledger.admissible_pairs
        || result.ledger.pruned_pairs > result.ledger.admissible_pairs
        || result.maximum_total_cost > MAX_DISCOVERY_V5_TOTAL_COST
        || canonical_discovery_result_v5_bytes(&result)? != bytes
    {
        diagnostics::event("SYNTH_V5_RESULT_DECODE_REJECT", "v5 result bounds rejected");
        return Err(SynthesisCoreError("noncanonical-discovery-v5-result"));
    }
    let mut result = result;
    result.result_digest = discovery_result_v5_root(&result)?;
    diagnostics::event("SYNTH_V5_RESULT_DECODE_EXIT", "canonical v5 result decoded");
    Ok(result)
}

pub fn discovery_result_v5_root(
    result: &DiscoverySearchResultV5,
) -> Result<String, SynthesisCoreError> {
    diagnostics::event("SYNTH_V5_RESULT_ROOT_ENTER", "binding v5 result root");
    let root = domain_sha256_hex(RESULT_DOMAIN, &canonical_discovery_result_v5_bytes(result)?);
    diagnostics::event("SYNTH_V5_RESULT_ROOT_EXIT", "v5 result root bound");
    Ok(root)
}

fn validate_request(request: &DiscoverySearchRequestV5) -> Result<(), SynthesisCoreError> {
    diagnostics::event("SYNTH_V5_VALIDATE_ENTER", "validating v5 request");
    if request.maximum_total_cost == 0
        || request.maximum_total_cost > MAX_DISCOVERY_V5_TOTAL_COST
        || request.limits.candidate_limit == 0
        || request.limits.candidate_limit > MAX_DISCOVERY_V5_CANDIDATES
        || request.limits.pair_disposition_limit == 0
        || request.limits.pair_disposition_limit > MAX_DISCOVERY_V5_PAIR_DISPOSITIONS
    {
        diagnostics::event("SYNTH_V5_VALIDATE_REJECT", "v5 request rejected");
        return Err(SynthesisCoreError("invalid-discovery-synthesis-v5-request"));
    }
    diagnostics::event("SYNTH_V5_VALIDATE_EXIT", "v5 request validated");
    Ok(())
}

fn optimized_fits(candidate: &DiscoveryObserverCandidateV5, targets: &[u8; 16]) -> bool {
    diagnostics::event(
        "SYNTH_V5_OPT_FIT_ENTER",
        "evaluating optimized partition fit",
    );
    let responses = candidate.responses();
    for left in 0..16 {
        for right in left + 1..16 {
            if (responses[left] == responses[right]) != (targets[left] == targets[right]) {
                diagnostics::event("SYNTH_V5_OPT_FIT_EXIT", "optimized candidate rejected");
                return false;
            }
        }
    }
    diagnostics::event("SYNTH_V5_OPT_FIT_EXIT", "optimized candidate accepted");
    true
}

fn canonical_partition(values: [u8; 16]) -> [u8; 16] {
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

fn reference_fits(candidate: &DiscoveryObserverCandidateV5, targets: &[u8; 16]) -> bool {
    diagnostics::event(
        "SYNTH_V5_REF_FIT_ENTER",
        "evaluating reference partition fit",
    );
    let actual = canonical_partition(candidate.responses());
    let expected = canonical_partition(*targets);
    let result = actual == expected;
    diagnostics::event("SYNTH_V5_REF_FIT_EXIT", "reference partition fit evaluated");
    result
}

fn witness_digest(candidate: &DiscoveryObserverCandidateV5, task_digest: &str) -> String {
    let body = format!(
        "{}:{task_digest}:exact-partition",
        candidate.candidate_digest
    );
    domain_sha256_hex(RESULT_DOMAIN, body.as_bytes())
}

fn representation_digest(
    candidate: &DiscoveryObserverCandidateV5,
    benchmark_digest: &str,
) -> String {
    let (multiplier, shift) = match candidate.term {
        super::grammar_v5::DiscoveryObserverTermV5::AffineBitParity {
            multiplier, shift, ..
        }
        | super::grammar_v5::DiscoveryObserverTermV5::AffineReflectionOrbit { multiplier, shift } => {
            (multiplier, shift)
        }
    };
    domain_sha256_hex(
        RESULT_DOMAIN,
        format!("affine-representation:{multiplier}:{shift}:{benchmark_digest}").as_bytes(),
    )
}

fn explanation_digest(candidate: &DiscoveryObserverCandidateV5, task_digest: &str) -> String {
    domain_sha256_hex(
        RESULT_DOMAIN,
        format!(
            "exact-equality-partition:{}:{task_digest}",
            candidate.response_digest
        )
        .as_bytes(),
    )
}

fn winner_for(
    candidate: &DiscoveryObserverCandidateV5,
    admitted: &[&DiscoveryObserverCandidateV5],
    alternatives_at_same_cost: usize,
    task_digest: &str,
) -> DiscoveryWinnerV5 {
    DiscoveryWinnerV5 {
        candidate_ordinal: candidate.ordinal,
        candidate_digest: candidate.candidate_digest.clone(),
        total_cost: candidate.cost,
        observer_gap: candidate
            .cost
            .saturating_sub(admitted.first().map_or(candidate.cost, |row| row.cost)),
        alternatives_at_same_cost,
        representation_digest: representation_digest(candidate, task_digest),
        explanation_digest: explanation_digest(candidate, task_digest),
        witness_digest: witness_digest(candidate, task_digest),
    }
}

fn lower_bound_digest(admitted: &[&DiscoveryObserverCandidateV5]) -> String {
    let body = admitted
        .iter()
        .map(|row| format!("{}:{}:{}", row.ordinal, row.cost, row.candidate_digest))
        .collect::<Vec<_>>()
        .join(":");
    domain_sha256_hex(LOWER_BOUND_DOMAIN, body.as_bytes())
}

fn prune_proof_digest(
    admitted: &[&DiscoveryObserverCandidateV5],
    evaluated: usize,
    incumbent: Option<&DiscoveryWinnerV5>,
) -> String {
    let suffix = admitted
        .iter()
        .skip(evaluated)
        .map(|row| format!("{}:{}:{}", row.ordinal, row.cost, row.candidate_digest))
        .collect::<Vec<_>>()
        .join(":");
    let incumbent = incumbent.map_or_else(
        || "none".to_owned(),
        |row| format!("{}:{}", row.candidate_ordinal, row.total_cost),
    );
    domain_sha256_hex(
        PRUNE_PROOF_DOMAIN,
        format!("{evaluated}:{incumbent}:{suffix}").as_bytes(),
    )
}

#[allow(clippy::too_many_arguments)]
fn terminal(
    optimized: bool,
    status: DiscoverySearchStatusV5,
    detail: &'static str,
    limits: DiscoverySearchLimitsV5,
    candidate_count: usize,
    admitted: &[&DiscoveryObserverCandidateV5],
    evaluated_candidates: usize,
    winner: Option<DiscoveryWinnerV5>,
    benchmark_digest: String,
    benchmark_split: DiscoveryBenchmarkSplitV5,
    grammar_profile_digest: String,
    catalog_digest: String,
    maximum_total_cost: usize,
    cutoff: bool,
) -> Result<DiscoverySearchResultV5, SynthesisCoreError> {
    diagnostics::event("SYNTH_V5_TERMINAL_ENTER", "binding v5 terminal result");
    let pruned_candidates = if optimized && winner.is_some() {
        admitted.len().saturating_sub(evaluated_candidates)
    } else {
        0
    };
    let incumbent_cost = winner.as_ref().map(|row| row.total_cost);
    let first_pruned_cost_lower_bound = if pruned_candidates > 0 {
        admitted.get(evaluated_candidates).map(|row| row.cost)
    } else {
        None
    };
    let bound_admissible = match (incumbent_cost, first_pruned_cost_lower_bound) {
        (Some(incumbent), Some(lower_bound)) => lower_bound >= incumbent,
        (_, None) => true,
        (None, Some(_)) => false,
    };
    let ledger = DiscoveryPruneLedgerV5 {
        limits,
        candidates: candidate_count,
        admissible_pairs: admitted.len().saturating_mul(PAIR_OBLIGATIONS),
        evaluated_pairs: evaluated_candidates.saturating_mul(PAIR_OBLIGATIONS),
        pruned_pairs: pruned_candidates.saturating_mul(PAIR_OBLIGATIONS),
        cutoff,
        incumbent_cost,
        first_pruned_cost_lower_bound,
        bound_admissible,
        lower_bound_digest: lower_bound_digest(admitted),
        prune_proof_digest: prune_proof_digest(admitted, evaluated_candidates, winner.as_ref()),
    };
    let mut result = DiscoverySearchResultV5 {
        schema: DISCOVERY_SYNTHESIS_V5_SCHEMA,
        optimized,
        status,
        detail,
        ledger,
        winner,
        benchmark_digest,
        benchmark_split,
        grammar_profile_digest,
        catalog_digest,
        maximum_total_cost,
        result_digest: String::new(),
        boundary: DISCOVERY_SYNTHESIS_V5_BOUNDARY,
    };
    result.result_digest = discovery_result_v5_root(&result)?;
    diagnostics::event("SYNTH_V5_TERMINAL_EXIT", "v5 terminal result bound");
    Ok(result)
}

fn prepared<'a>(
    request: &DiscoverySearchRequestV5,
    catalog: &'a super::grammar_v5::DiscoveryGrammarCatalogV5,
) -> Vec<&'a DiscoveryObserverCandidateV5> {
    catalog
        .candidates
        .iter()
        .filter(|row| row.cost <= request.maximum_total_cost)
        .collect()
}

fn optimized_search(
    request: &DiscoverySearchRequestV5,
) -> Result<DiscoverySearchResultV5, SynthesisCoreError> {
    diagnostics::event("SYNTH_V5_OPT_ENTER", "starting branch-and-bound search");
    validate_request(request)?;
    let benchmark = discovery_benchmark_v5(request.benchmark_id)?;
    let catalog = enumerate_discovery_grammar_v5(request.profile_id)?;
    let admitted = prepared(request, &catalog);
    let dispositions = admitted.len().saturating_mul(PAIR_OBLIGATIONS);
    if catalog.candidates.len() > request.limits.candidate_limit
        || dispositions > request.limits.pair_disposition_limit
    {
        diagnostics::event("SYNTH_V5_OPT_CUTOFF", "v5 physical preflight cutoff");
        return terminal(
            true,
            DiscoverySearchStatusV5::Cutoff,
            "complete-admitted-product-exceeds-limits",
            request.limits,
            catalog.candidates.len(),
            &admitted,
            0,
            None,
            benchmark.task_digest,
            benchmark.split,
            catalog.profile.profile_digest.clone(),
            catalog.catalog_digest.clone(),
            request.maximum_total_cost,
            true,
        );
    }
    for (index, candidate) in admitted.iter().enumerate() {
        if optimized_fits(candidate, &benchmark.target_classes) {
            let alternatives = admitted
                .iter()
                .filter(|row| row.cost == candidate.cost)
                .filter(|row| optimized_fits(row, &benchmark.target_classes))
                .count()
                .saturating_sub(1);
            let winner = winner_for(candidate, &admitted, alternatives, &benchmark.task_digest);
            diagnostics::event("SYNTH_V5_OPT_PRUNE", "incumbent prunes monotone suffix");
            return terminal(
                true,
                DiscoverySearchStatusV5::Found,
                "minimum-catalog-relative-witness",
                request.limits,
                catalog.candidates.len(),
                &admitted,
                index + 1,
                Some(winner),
                benchmark.task_digest,
                benchmark.split,
                catalog.profile.profile_digest.clone(),
                catalog.catalog_digest.clone(),
                request.maximum_total_cost,
                false,
            );
        }
    }
    diagnostics::event("SYNTH_V5_OPT_EXIT", "v5 admitted catalog exhausted");
    terminal(
        true,
        DiscoverySearchStatusV5::Exhausted,
        "complete-cost-admitted-catalog-exhausted",
        request.limits,
        catalog.candidates.len(),
        &admitted,
        admitted.len(),
        None,
        benchmark.task_digest,
        benchmark.split,
        catalog.profile.profile_digest.clone(),
        catalog.catalog_digest.clone(),
        request.maximum_total_cost,
        false,
    )
}

fn reference_search(
    request: &DiscoverySearchRequestV5,
) -> Result<DiscoverySearchResultV5, SynthesisCoreError> {
    diagnostics::event(
        "SYNTH_V5_REF_ENTER",
        "starting independent exhaustive search",
    );
    validate_request(request)?;
    let benchmark = discovery_benchmark_v5(request.benchmark_id)?;
    let catalog = enumerate_discovery_grammar_v5(request.profile_id)?;
    let admitted: Vec<_> = catalog
        .candidates
        .iter()
        .filter(|candidate| candidate.cost <= request.maximum_total_cost)
        .collect();
    let dispositions = admitted
        .len()
        .checked_mul(PAIR_OBLIGATIONS)
        .ok_or(SynthesisCoreError("discovery-v5-pair-count-overflow"))?;
    if request.limits.candidate_limit < catalog.candidates.len()
        || request.limits.pair_disposition_limit < dispositions
    {
        diagnostics::event("SYNTH_V5_REF_CUTOFF", "reference physical preflight cutoff");
        return terminal(
            false,
            DiscoverySearchStatusV5::Cutoff,
            "complete-admitted-product-exceeds-limits",
            request.limits,
            catalog.candidates.len(),
            &admitted,
            0,
            None,
            benchmark.task_digest,
            benchmark.split,
            catalog.profile.profile_digest,
            catalog.catalog_digest,
            request.maximum_total_cost,
            true,
        );
    }
    let mut best: Option<DiscoveryWinnerV5> = None;
    for candidate in &admitted {
        if reference_fits(candidate, &benchmark.target_classes) {
            let alternatives = admitted
                .iter()
                .filter(|row| row.cost == candidate.cost)
                .filter(|row| reference_fits(row, &benchmark.target_classes))
                .count()
                .saturating_sub(1);
            let proposed = winner_for(candidate, &admitted, alternatives, &benchmark.task_digest);
            if best.as_ref().map_or(true, |current| {
                (proposed.total_cost, proposed.candidate_ordinal)
                    < (current.total_cost, current.candidate_ordinal)
            }) {
                best = Some(proposed);
            }
        }
    }
    let (status, detail) = if best.is_some() {
        (
            DiscoverySearchStatusV5::Found,
            "minimum-catalog-relative-witness",
        )
    } else {
        (
            DiscoverySearchStatusV5::Exhausted,
            "complete-cost-admitted-catalog-exhausted",
        )
    };
    diagnostics::event(
        "SYNTH_V5_REF_EXIT",
        "independent exhaustive search completed",
    );
    terminal(
        false,
        status,
        detail,
        request.limits,
        catalog.candidates.len(),
        &admitted,
        admitted.len(),
        best,
        benchmark.task_digest,
        benchmark.split,
        catalog.profile.profile_digest,
        catalog.catalog_digest,
        request.maximum_total_cost,
        false,
    )
}

pub fn synthesize_discovery_v5(
    request: &DiscoverySearchRequestV5,
) -> Result<DiscoverySearchResultV5, SynthesisCoreError> {
    optimized_search(request)
}

pub fn synthesize_discovery_v5_exhaustive(
    request: &DiscoverySearchRequestV5,
) -> Result<DiscoverySearchResultV5, SynthesisCoreError> {
    reference_search(request)
}

pub fn verify_branch_bound_proof_v5(
    request: &DiscoverySearchRequestV5,
    claimed: &DiscoverySearchResultV5,
) -> Result<bool, SynthesisCoreError> {
    super::prune_verifier_v5::verify_branch_bound_proof_independent_v5(request, claimed)
}

pub fn differential_discovery_v5(
    request: &DiscoverySearchRequestV5,
) -> Result<DiscoverySearchDifferentialV5, SynthesisCoreError> {
    diagnostics::event("SYNTH_V5_DIFF_ENTER", "running v5 differential");
    let reference = reference_search(request)?;
    let optimized = optimized_search(request)?;
    let equivalent = reference.status == optimized.status
        && reference.detail == optimized.detail
        && reference.winner == optimized.winner
        && reference.benchmark_digest == optimized.benchmark_digest
        && reference.benchmark_split == optimized.benchmark_split
        && reference.grammar_profile_digest == optimized.grammar_profile_digest
        && reference.catalog_digest == optimized.catalog_digest
        && reference.maximum_total_cost == optimized.maximum_total_cost
        && verify_branch_bound_proof_v5(request, &optimized)?;
    let body = format!(
        "{}:{}:{equivalent}",
        reference.result_digest, optimized.result_digest
    );
    let result = DiscoverySearchDifferentialV5 {
        reference,
        optimized,
        equivalent,
        differential_digest: domain_sha256_hex(DIFFERENTIAL_DOMAIN, body.as_bytes()),
        boundary: DISCOVERY_SYNTHESIS_V5_BOUNDARY,
    };
    diagnostics::event(
        if equivalent {
            "SYNTH_V5_DIFF_EXIT"
        } else {
            "SYNTH_V5_DIFF_DIVERGED"
        },
        "v5 differential completed",
    );
    Ok(result)
}

pub fn run_discovery_benchmark_v5() -> Result<DiscoveryBenchmarkRunV5, SynthesisCoreError> {
    diagnostics::event("SYNTH_V5_RUN_ENTER", "running discovery benchmark family");
    let rows: Vec<_> = super::discovery_benchmark_v5::ALL_DISCOVERY_BENCHMARKS_V5
        .into_iter()
        .map(|benchmark_id| {
            differential_discovery_v5(&DiscoverySearchRequestV5::systematic(benchmark_id))
        })
        .collect::<Result<_, _>>()?;
    let found = rows
        .iter()
        .filter(|row| row.optimized.status == DiscoverySearchStatusV5::Found)
        .count();
    let exhausted = rows
        .iter()
        .filter(|row| row.optimized.status == DiscoverySearchStatusV5::Exhausted)
        .count();
    let cutoff = rows.len() - found - exhausted;
    let body = rows
        .iter()
        .map(|row| row.differential_digest.as_str())
        .collect::<Vec<_>>()
        .join(":");
    let result = DiscoveryBenchmarkRunV5 {
        rows,
        found,
        exhausted,
        cutoff,
        run_digest: domain_sha256_hex(DIFFERENTIAL_DOMAIN, body.as_bytes()),
        boundary: DISCOVERY_SYNTHESIS_V5_BOUNDARY,
    };
    if result.run_digest != DISCOVERY_BENCHMARK_RUN_V5_DIGEST {
        diagnostics::event("SYNTH_V5_RUN_REJECT", "discovery benchmark run drifted");
        return Err(SynthesisCoreError("discovery-benchmark-run-v5-drift"));
    }
    diagnostics::event("SYNTH_V5_RUN_EXIT", "discovery benchmark family completed");
    Ok(result)
}
