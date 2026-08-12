//! Deterministic product CLI for the bounded discovery-v5 search.

use std::io::{self, Read};
use std::process::ExitCode;

use vam_native::observer_synthesis::{
    canonical_discovery_request_v5_bytes, decode_discovery_request_v5_bytes,
    differential_discovery_v5, discovery_request_v5_root, discovery_result_v5_root,
    DiscoveryBenchmarkIdV5, DiscoverySearchRequestV5,
};

const MAX_STDIN_BYTES: u64 = 1_025;

fn benchmark_id(value: &str) -> Option<DiscoveryBenchmarkIdV5> {
    match value {
        "hidden-affine-v5" => Some(DiscoveryBenchmarkIdV5::HiddenAffine),
        "reflection-symmetry-v5" => Some(DiscoveryBenchmarkIdV5::ReflectionSymmetry),
        "misrepresentation-recovery-v5" => Some(DiscoveryBenchmarkIdV5::MisrepresentationRecovery),
        "diagonal-negative-control-v5" => Some(DiscoveryBenchmarkIdV5::DiagonalNegativeControl),
        "held-out-affine-v5" => Some(DiscoveryBenchmarkIdV5::HeldOutAffine),
        _ => None,
    }
}

fn usage() -> &'static str {
    "usage: vam-observer-discover-v5 --benchmark <exact-id> | --request-stdin\n\
     exact ids: hidden-affine-v5, reflection-symmetry-v5, \
     misrepresentation-recovery-v5, diagonal-negative-control-v5, held-out-affine-v5\n\
     --request-stdin consumes canonical request bytes (maximum 1024 bytes).\n\
     This CLI performs unsigned discovery only; VOR5 signing remains at the library trust API, \
     where key material is supplied as bytes rather than command-line arguments."
}

fn parse_request() -> Result<DiscoverySearchRequestV5, &'static str> {
    let arguments: Vec<_> = std::env::args().skip(1).collect();
    match arguments.as_slice() {
        [flag] if flag == "--help" || flag == "-h" => Err("help"),
        [flag, value] if flag == "--benchmark" => benchmark_id(value)
            .map(DiscoverySearchRequestV5::systematic)
            .ok_or("unknown-benchmark-id"),
        [flag] if flag == "--request-stdin" => {
            let mut bytes = Vec::new();
            io::stdin()
                .take(MAX_STDIN_BYTES)
                .read_to_end(&mut bytes)
                .map_err(|_| "request-read-failed")?;
            if bytes.len() > 1_024 {
                return Err("request-bytes-limit");
            }
            decode_discovery_request_v5_bytes(&bytes).map_err(|_| "invalid-canonical-request")
        }
        _ => Err("invalid-arguments"),
    }
}

fn emit_error(kind: &str) {
    eprintln!(
        "{{\"schema\":\"veyra.observer-discover-cli.v5\",\"ok\":false,\"error\":\"{kind}\"}}"
    );
}

fn run() -> Result<String, &'static str> {
    let request = parse_request()?;
    let request_bytes =
        canonical_discovery_request_v5_bytes(&request).map_err(|_| "request-encoding-failed")?;
    let request_root = discovery_request_v5_root(&request).map_err(|_| "request-root-failed")?;
    let differential = differential_discovery_v5(&request).map_err(|_| "search-failed")?;
    if !differential.equivalent {
        return Err("optimized-reference-divergence");
    }
    let result = &differential.optimized;
    let result_root = discovery_result_v5_root(result).map_err(|_| "result-root-failed")?;
    let winner = result.winner.as_ref().map_or_else(
        || "null".to_owned(),
        |row| {
            format!(
                "{{\"candidate_ordinal\":{},\"observer_root\":\"{}\",\"representation_root\":\"{}\",\"explanation_root\":\"{}\",\"witness_root\":\"{}\",\"total_cost\":{},\"observer_gap\":{},\"alternatives_at_same_cost\":{}}}",
                row.candidate_ordinal,
                row.candidate_digest,
                row.representation_digest,
                row.explanation_digest,
                row.witness_digest,
                row.total_cost,
                row.observer_gap,
                row.alternatives_at_same_cost,
            )
        },
    );
    Ok(format!(
        "{{\"schema\":\"veyra.observer-discover-cli.v5\",\"ok\":true,\"package_mode\":false,\"benchmark_id\":\"{}\",\"benchmark_split\":\"{}\",\"status\":\"{}\",\"detail\":\"{}\",\"equivalent\":true,\"request_bytes\":{},\"request_root\":\"{}\",\"result_root\":\"{}\",\"differential_root\":\"{}\",\"benchmark_root\":\"{}\",\"grammar_profile_root\":\"{}\",\"catalog_root\":\"{}\",\"winner\":{},\"ledger\":{{\"candidates\":{},\"admissible_pairs\":{},\"evaluated_pairs\":{},\"pruned_pairs\":{},\"cutoff\":{},\"incumbent_cost\":{},\"first_pruned_cost_lower_bound\":{},\"bound_admissible\":{},\"lower_bound_root\":\"{}\",\"prune_proof_root\":\"{}\"}},\"boundary\":\"synthetic finite task/catalog/cost-relative discovery; no statistical or external validation; signing is library-only\"}}",
        request.benchmark_id.as_str(),
        result.benchmark_split.as_str(),
        result.status.as_str(),
        result.detail,
        request_bytes.len(),
        request_root,
        result_root,
        differential.differential_digest,
        result.benchmark_digest,
        result.grammar_profile_digest,
        result.catalog_digest,
        winner,
        result.ledger.candidates,
        result.ledger.admissible_pairs,
        result.ledger.evaluated_pairs,
        result.ledger.pruned_pairs,
        result.ledger.cutoff,
        result.ledger.incumbent_cost.map_or_else(|| "null".to_owned(), |value| value.to_string()),
        result.ledger.first_pruned_cost_lower_bound.map_or_else(|| "null".to_owned(), |value| value.to_string()),
        result.ledger.bound_admissible,
        result.ledger.lower_bound_digest,
        result.ledger.prune_proof_digest,
    ))
}

fn main() -> ExitCode {
    match run() {
        Ok(summary) => {
            println!("{summary}");
            ExitCode::SUCCESS
        }
        Err("help") => {
            println!("{}", usage());
            ExitCode::SUCCESS
        }
        Err(error) => {
            emit_error(error);
            ExitCode::from(2)
        }
    }
}
