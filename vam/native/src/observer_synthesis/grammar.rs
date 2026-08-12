//! Exact dynamic-programming enumeration of the closed R14.1 grammar.

use std::collections::HashSet;

use super::ast::{
    infer_observer_kind, ObserverExpr, PrimitiveId, ResponseKind, SynthesisCoreError,
};
use super::canonical::canonical_observer_bytes;
use super::diagnostics;
use super::hash::sha256_hex;

pub const DEFAULT_STRATA: [usize; 7] = [1, 3, 8, 27, 104, 358, 1064];
pub const DEFAULT_CANDIDATES: usize = 1_565;
pub const DEFAULT_CANONICAL_BYTES: usize = 488_550;
pub const DEFAULT_MAX_ROW_BYTES: usize = 338;
pub const DEFAULT_CATALOG_DIGEST: &str =
    "23408184aba5d55d283e4a9440e1859beaefa9d73a909d283057d59b527437cf";

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct GrammarConfig {
    pub max_cost: usize,
    pub max_depth: usize,
    pub candidate_limit: usize,
    pub canonical_bytes_limit: usize,
}

impl Default for GrammarConfig {
    fn default() -> Self {
        Self {
            max_cost: 6,
            max_depth: 4,
            candidate_limit: 2_048,
            canonical_bytes_limit: 8 * 1024 * 1024,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObserverCandidate {
    pub observer: ObserverExpr,
    pub response_kind: ResponseKind,
    pub cost: usize,
    pub depth: usize,
    pub canonical: Vec<u8>,
    pub digest: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GrammarStratum {
    pub cost: usize,
    pub candidates: Vec<ObserverCandidate>,
    pub canonical_bytes: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GrammarEnumeration {
    pub config: GrammarConfig,
    pub strata: Vec<GrammarStratum>,
    pub candidates: Vec<ObserverCandidate>,
    pub canonical_bytes: usize,
    pub max_row_bytes: usize,
    pub catalog_digest: String,
}

fn candidate(
    observer: ObserverExpr,
    cost: usize,
    depth: usize,
) -> Result<ObserverCandidate, SynthesisCoreError> {
    let response_kind = infer_observer_kind(&observer)?;
    let canonical = canonical_observer_bytes(&observer)?;
    let digest = sha256_hex(&canonical);
    Ok(ObserverCandidate {
        observer,
        response_kind,
        cost,
        depth,
        canonical,
        digest,
    })
}

fn catalog_digest(candidates: &[ObserverCandidate]) -> String {
    let mut framed = b"veyra.observer-synthesis-v2.catalog.v1\0".to_vec();
    for row in candidates {
        framed.extend_from_slice(&(row.canonical.len() as u64).to_be_bytes());
        framed.extend_from_slice(&row.canonical);
    }
    sha256_hex(&framed)
}

pub fn enumerate_observer_grammar(
    config: GrammarConfig,
) -> Result<GrammarEnumeration, SynthesisCoreError> {
    diagnostics::event(
        "GRAMMAR_ENUM_ENTER",
        "validating bounded grammar configuration",
    );
    let maxima = GrammarConfig::default();
    if config.candidate_limit == 0
        || config.canonical_bytes_limit == 0
        || config.max_cost > maxima.max_cost
        || config.max_depth > maxima.max_depth
        || config.candidate_limit > maxima.candidate_limit
        || config.canonical_bytes_limit > maxima.canonical_bytes_limit
    {
        diagnostics::event(
            "GRAMMAR_ENUM_REJECT",
            "grammar configuration is out of bounds",
        );
        return Err(SynthesisCoreError("invalid-v2-grammar-limits"));
    }
    let seed = candidate(ObserverExpr::Input, 0, 0)?;
    if seed.canonical.len() > config.canonical_bytes_limit {
        diagnostics::event("GRAMMAR_ENUM_CUTOFF", "seed exceeds canonical byte budget");
        return Err(SynthesisCoreError("v2-canonical-bytes-limit"));
    }
    let mut buckets = vec![vec![seed.clone()]];
    let mut seen: HashSet<Vec<u8>> = HashSet::from([seed.canonical.clone()]);
    let mut retained = seed.canonical.len();

    for cost in 1..=config.max_cost {
        let mut rows = Vec::new();
        for child in &buckets[cost - 1] {
            if child.response_kind != ResponseKind::Recurrence {
                continue;
            }
            let depth = child.depth + 1;
            if depth > config.max_depth {
                continue;
            }
            for primitive in [PrimitiveId::Tail, PrimitiveId::Crest] {
                let row = candidate(
                    ObserverExpr::apply(primitive, child.observer.clone()),
                    cost,
                    depth,
                )?;
                retain(&mut rows, &mut seen, &mut retained, row, config)?;
            }
        }
        for left_cost in 0..cost {
            let right_cost = cost - 1 - left_cost;
            for left in &buckets[left_cost] {
                for right in &buckets[right_cost] {
                    let depth = 1 + left.depth.max(right.depth);
                    if depth > config.max_depth {
                        continue;
                    }
                    let row = candidate(
                        ObserverExpr::pair(left.observer.clone(), right.observer.clone()),
                        cost,
                        depth,
                    )?;
                    retain(&mut rows, &mut seen, &mut retained, row, config)?;
                }
            }
        }
        rows.sort_by(|a, b| (a.depth, &a.canonical).cmp(&(b.depth, &b.canonical)));
        buckets.push(rows);
    }
    let strata: Vec<_> = buckets
        .into_iter()
        .enumerate()
        .map(|(cost, candidates)| {
            let canonical_bytes = candidates.iter().map(|row| row.canonical.len()).sum();
            GrammarStratum {
                cost,
                candidates,
                canonical_bytes,
            }
        })
        .collect();
    let candidates: Vec<_> = strata
        .iter()
        .flat_map(|row| row.candidates.iter().cloned())
        .collect();
    let max_row_bytes = candidates
        .iter()
        .map(|row| row.canonical.len())
        .max()
        .unwrap_or(0);
    let result = GrammarEnumeration {
        config,
        catalog_digest: catalog_digest(&candidates),
        strata,
        candidates,
        canonical_bytes: retained,
        max_row_bytes,
    };
    if config == GrammarConfig::default() {
        let actual: Vec<_> = result
            .strata
            .iter()
            .map(|row| row.candidates.len())
            .collect();
        if actual != DEFAULT_STRATA
            || result.candidates.len() != DEFAULT_CANDIDATES
            || result.canonical_bytes != DEFAULT_CANONICAL_BYTES
            || result.max_row_bytes != DEFAULT_MAX_ROW_BYTES
            || result.catalog_digest != DEFAULT_CATALOG_DIGEST
        {
            diagnostics::event("GRAMMAR_ENUM_REJECT", "default catalog pin mismatch");
            return Err(SynthesisCoreError("default-v2-grammar-pin-mismatch"));
        }
    }
    diagnostics::event("GRAMMAR_ENUM_EXIT", "bounded catalog enumeration completed");
    Ok(result)
}

fn retain(
    rows: &mut Vec<ObserverCandidate>,
    seen: &mut HashSet<Vec<u8>>,
    retained: &mut usize,
    row: ObserverCandidate,
    config: GrammarConfig,
) -> Result<(), SynthesisCoreError> {
    if seen.len() >= config.candidate_limit {
        diagnostics::event("GRAMMAR_ENUM_CUTOFF", "candidate budget exhausted");
        return Err(SynthesisCoreError("v2-candidate-limit"));
    }
    if seen.contains(&row.canonical) {
        diagnostics::event(
            "GRAMMAR_ENUM_REJECT",
            "duplicate canonical candidate encountered",
        );
        return Err(SynthesisCoreError("duplicate-v2-observer-candidate"));
    }
    if row.canonical.len() > config.canonical_bytes_limit.saturating_sub(*retained) {
        diagnostics::event("GRAMMAR_ENUM_CUTOFF", "canonical byte budget exhausted");
        return Err(SynthesisCoreError("v2-canonical-bytes-limit"));
    }
    *retained += row.canonical.len();
    seen.insert(row.canonical.clone());
    rows.push(row);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_catalog_matches_every_python_pin() {
        let report = enumerate_observer_grammar(GrammarConfig::default()).unwrap();
        assert_eq!(
            report
                .strata
                .iter()
                .map(|row| row.candidates.len())
                .collect::<Vec<_>>(),
            DEFAULT_STRATA
        );
        assert_eq!(
            report.candidates[0].digest,
            "5eb21cbbf9ace8fb6c9264119177bf610a4c6f3dcaec5cad5820f8f2729542c4"
        );
        assert_eq!(
            report.candidates[1].digest,
            "7eb8dcdbd11c47eb2f8553c26ca2cd4f4a09027deccb2a2a69bee881f927e502"
        );
        assert_eq!(report.catalog_digest, DEFAULT_CATALOG_DIGEST);
    }

    #[test]
    fn lower_limits_fail_closed() {
        let config = GrammarConfig {
            candidate_limit: 1,
            ..GrammarConfig::default()
        };
        assert_eq!(
            enumerate_observer_grammar(config).unwrap_err().0,
            "v2-candidate-limit"
        );
        let config = GrammarConfig {
            max_cost: 0,
            max_depth: 0,
            candidate_limit: 1,
            canonical_bytes_limit: 1,
        };
        assert_eq!(
            enumerate_observer_grammar(config).unwrap_err().0,
            "v2-canonical-bytes-limit"
        );
    }
}
