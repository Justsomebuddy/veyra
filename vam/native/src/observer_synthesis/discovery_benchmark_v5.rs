//! Deterministically generated scientific calibration tasks for discovery v5.

use std::collections::HashSet;

use super::ast::SynthesisCoreError;
use super::diagnostics;
use super::grammar_v5::{
    enumerate_discovery_grammar_v5, DiscoveryGrammarProfileIdV5, DiscoveryObserverCandidateV5,
    DiscoveryObserverTermV5,
};
use super::hash::domain_sha256_hex;

pub const DISCOVERY_BENCHMARK_V5_SCHEMA: &str = "veyra.synthetic-discovery-benchmark.v5";
pub const DISCOVERY_BENCHMARK_V5_FAMILY_DIGEST: &str =
    "9c307dc3d06b183cf9d59189e4539fba072b7d1b19c33ac5a23105677c38b86e";
const GENERATOR_DOMAIN: &str = "veyra.synthetic-discovery-benchmark.generator.v5.binding";
const HELD_OUT_GENERATOR_DOMAIN: &str =
    "veyra.synthetic-discovery-benchmark.held-out-generator.v5.binding";
const TASK_DOMAIN: &str = "veyra.synthetic-discovery-benchmark.task.v5.binding";
const FAMILY_DOMAIN: &str = "veyra.synthetic-discovery-benchmark.family.v5.binding";
pub const DISCOVERY_BENCHMARK_V5_BOUNDARY: &str = "five deterministic generated sixteen-state tasks: four calibration tasks covering affine-hidden, reflection-symmetry, representation-recovery and catalog-diagonalized-negative cases, plus one synthetic held-out task selected under a distinct domain and excluded from calibration selection; labels and the held-out expected observer are not embedded, and this is not statistical, external or empirical validation";

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum DiscoveryBenchmarkIdV5 {
    HiddenAffine,
    ReflectionSymmetry,
    MisrepresentationRecovery,
    DiagonalNegativeControl,
    HeldOutAffine,
}

impl DiscoveryBenchmarkIdV5 {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::HiddenAffine => "hidden-affine-v5",
            Self::ReflectionSymmetry => "reflection-symmetry-v5",
            Self::MisrepresentationRecovery => "misrepresentation-recovery-v5",
            Self::DiagonalNegativeControl => "diagonal-negative-control-v5",
            Self::HeldOutAffine => "held-out-affine-v5",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum DiscoveryBenchmarkSplitV5 {
    Calibration,
    SyntheticHeldOut,
}

impl DiscoveryBenchmarkSplitV5 {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Calibration => "CALIBRATION",
            Self::SyntheticHeldOut => "SYNTHETIC_HELD_OUT",
        }
    }
}

pub const CALIBRATION_DISCOVERY_BENCHMARKS_V5: [DiscoveryBenchmarkIdV5; 4] = [
    DiscoveryBenchmarkIdV5::HiddenAffine,
    DiscoveryBenchmarkIdV5::ReflectionSymmetry,
    DiscoveryBenchmarkIdV5::MisrepresentationRecovery,
    DiscoveryBenchmarkIdV5::DiagonalNegativeControl,
];
pub const HELD_OUT_DISCOVERY_BENCHMARKS_V5: [DiscoveryBenchmarkIdV5; 1] =
    [DiscoveryBenchmarkIdV5::HeldOutAffine];
pub const ALL_DISCOVERY_BENCHMARKS_V5: [DiscoveryBenchmarkIdV5; 5] = [
    DiscoveryBenchmarkIdV5::HiddenAffine,
    DiscoveryBenchmarkIdV5::ReflectionSymmetry,
    DiscoveryBenchmarkIdV5::MisrepresentationRecovery,
    DiscoveryBenchmarkIdV5::DiagonalNegativeControl,
    DiscoveryBenchmarkIdV5::HeldOutAffine,
];

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DiscoveryBenchmarkV5 {
    pub schema: &'static str,
    pub id: DiscoveryBenchmarkIdV5,
    pub split: DiscoveryBenchmarkSplitV5,
    pub surface_states: [u8; 16],
    pub target_classes: [u8; 16],
    pub hidden_variable: bool,
    pub symmetry: bool,
    pub misrepresentation: bool,
    pub negative_control: bool,
    pub generator_digest: String,
    pub task_digest: String,
    pub boundary: &'static str,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DiscoveryBenchmarkFamilyV5 {
    pub schema: &'static str,
    pub tasks: Vec<DiscoveryBenchmarkV5>,
    pub family_digest: String,
    pub boundary: &'static str,
}

fn eligible(term: DiscoveryObserverTermV5, id: DiscoveryBenchmarkIdV5) -> bool {
    match (id, term) {
        (
            DiscoveryBenchmarkIdV5::HiddenAffine,
            DiscoveryObserverTermV5::AffineBitParity {
                multiplier,
                shift,
                mask,
            },
        ) => multiplier != 1 && shift != 0 && mask.count_ones() >= 2,
        (
            DiscoveryBenchmarkIdV5::ReflectionSymmetry,
            DiscoveryObserverTermV5::AffineReflectionOrbit { multiplier, shift },
        ) => multiplier != 1 && shift != 0,
        (
            DiscoveryBenchmarkIdV5::MisrepresentationRecovery,
            DiscoveryObserverTermV5::AffineBitParity {
                multiplier,
                shift,
                mask,
            },
        ) => multiplier > 7 && shift > 7 && mask.count_ones() >= 3,
        (
            DiscoveryBenchmarkIdV5::HeldOutAffine,
            DiscoveryObserverTermV5::AffineBitParity {
                multiplier,
                shift,
                mask,
            },
        ) => multiplier > 9 && shift > 9 && mask.count_ones() == 2,
        _ => false,
    }
}

fn generated_candidate<'a>(
    candidates: &'a [DiscoveryObserverCandidateV5],
    id: DiscoveryBenchmarkIdV5,
) -> Result<&'a DiscoveryObserverCandidateV5, SynthesisCoreError> {
    diagnostics::event(
        "BENCH_V5_GENERATOR_ENTER",
        "selecting generated witness term",
    );
    let mut eligible_rows: Vec<_> = candidates
        .iter()
        .filter(|row| eligible(row.term, id))
        .collect();
    if id == DiscoveryBenchmarkIdV5::HeldOutAffine {
        let mut calibration_partitions: Vec<_> = [
            DiscoveryBenchmarkIdV5::HiddenAffine,
            DiscoveryBenchmarkIdV5::ReflectionSymmetry,
            DiscoveryBenchmarkIdV5::MisrepresentationRecovery,
        ]
        .into_iter()
        .map(|calibration_id| {
            generated_candidate(candidates, calibration_id)
                .map(|row| partition_code(&row.responses()))
        })
        .collect::<Result<_, _>>()?;
        calibration_partitions.push(partition_code(&diagonal_negative(candidates)?));
        eligible_rows
            .retain(|row| !calibration_partitions.contains(&partition_code(&row.responses())));
    }
    eligible_rows.sort_by(|left, right| {
        let domain = if id == DiscoveryBenchmarkIdV5::HeldOutAffine {
            HELD_OUT_GENERATOR_DOMAIN
        } else {
            GENERATOR_DOMAIN
        };
        let left_score = domain_sha256_hex(domain, left.candidate_digest.as_bytes());
        let right_score = domain_sha256_hex(domain, right.candidate_digest.as_bytes());
        left_score.cmp(&right_score)
    });
    let result = eligible_rows
        .first()
        .copied()
        .ok_or(SynthesisCoreError("empty-discovery-benchmark-generator"));
    diagnostics::event(
        if result.is_ok() {
            "BENCH_V5_GENERATOR_EXIT"
        } else {
            "BENCH_V5_GENERATOR_REJECT"
        },
        "generated witness selection completed",
    );
    result
}

fn partition_code(values: &[u8; 16]) -> u64 {
    let mut canonical = [0u8; 16];
    let mut seen = [u8::MAX; 16];
    let mut next = 0u8;
    for (index, value) in values.iter().copied().enumerate() {
        let slot = &mut seen[value as usize];
        if *slot == u8::MAX {
            *slot = next;
            next += 1;
        }
        canonical[index] = *slot;
    }
    canonical
        .into_iter()
        .fold(0u64, |code, value| (code << 4) | value as u64)
}

fn diagonal_negative(
    candidates: &[DiscoveryObserverCandidateV5],
) -> Result<[u8; 16], SynthesisCoreError> {
    diagnostics::event(
        "BENCH_V5_DIAGONAL_ENTER",
        "constructing diagonal negative control",
    );
    let catalog_partitions: HashSet<_> = candidates
        .iter()
        .map(|candidate| partition_code(&candidate.responses()))
        .collect();
    for bits in 1u16..u16::MAX {
        if bits & 1 != 0 {
            continue;
        }
        let target = std::array::from_fn(|state| ((bits >> state) & 1) as u8);
        if !catalog_partitions.contains(&partition_code(&target)) {
            diagnostics::event("BENCH_V5_DIAGONAL_EXIT", "negative control constructed");
            return Ok(target);
        }
    }
    diagnostics::event("BENCH_V5_DIAGONAL_REJECT", "negative control unavailable");
    Err(SynthesisCoreError(
        "discovery-v5-negative-control-unavailable",
    ))
}

pub fn discovery_benchmark_v5(
    id: DiscoveryBenchmarkIdV5,
) -> Result<DiscoveryBenchmarkV5, SynthesisCoreError> {
    diagnostics::event("BENCH_V5_TASK_ENTER", "generating discovery benchmark");
    let catalog =
        enumerate_discovery_grammar_v5(DiscoveryGrammarProfileIdV5::AffineParityReflectionV5)?;
    let (targets, generator_key, hidden_variable, symmetry, misrepresentation, negative_control) =
        if id == DiscoveryBenchmarkIdV5::DiagonalNegativeControl {
            (
                diagonal_negative(&catalog.candidates)?,
                String::from("catalog-diagonal-first-absent-binary-partition"),
                false,
                false,
                false,
                true,
            )
        } else {
            let selected = generated_candidate(&catalog.candidates, id)?;
            (
                selected.responses(),
                selected.candidate_digest.clone(),
                id == DiscoveryBenchmarkIdV5::HiddenAffine,
                id == DiscoveryBenchmarkIdV5::ReflectionSymmetry,
                id == DiscoveryBenchmarkIdV5::MisrepresentationRecovery,
                false,
            )
        };
    let split = if id == DiscoveryBenchmarkIdV5::HeldOutAffine {
        DiscoveryBenchmarkSplitV5::SyntheticHeldOut
    } else {
        DiscoveryBenchmarkSplitV5::Calibration
    };
    let generator_body = format!("{}:{}:{generator_key}", split.as_str(), id.as_str());
    let generator_domain = if split == DiscoveryBenchmarkSplitV5::SyntheticHeldOut {
        HELD_OUT_GENERATOR_DOMAIN
    } else {
        GENERATOR_DOMAIN
    };
    let generator_digest = domain_sha256_hex(generator_domain, generator_body.as_bytes());
    let target_text = targets.map(|value| value.to_string()).join(",");
    let task_body = format!(
        "{}:{}:{target_text}:{hidden_variable}:{symmetry}:{misrepresentation}:{negative_control}:{generator_digest}",
        id.as_str(), split.as_str()
    );
    let result = DiscoveryBenchmarkV5 {
        schema: DISCOVERY_BENCHMARK_V5_SCHEMA,
        id,
        split,
        surface_states: std::array::from_fn(|state| state as u8),
        target_classes: targets,
        hidden_variable,
        symmetry,
        misrepresentation,
        negative_control,
        generator_digest,
        task_digest: domain_sha256_hex(TASK_DOMAIN, task_body.as_bytes()),
        boundary: DISCOVERY_BENCHMARK_V5_BOUNDARY,
    };
    diagnostics::event("BENCH_V5_TASK_EXIT", "discovery benchmark generated");
    Ok(result)
}

pub fn canonical_discovery_benchmark_v5_bytes(
    task: &DiscoveryBenchmarkV5,
) -> Result<Vec<u8>, SynthesisCoreError> {
    diagnostics::event(
        "BENCH_V5_CODEC_ENTER",
        "encoding canonical discovery benchmark",
    );
    if task.schema != DISCOVERY_BENCHMARK_V5_SCHEMA
        || task.surface_states != std::array::from_fn(|state| state as u8)
        || task.boundary != DISCOVERY_BENCHMARK_V5_BOUNDARY
        || task.target_classes.iter().any(|value| *value > 15)
        || ![&task.generator_digest, &task.task_digest]
            .into_iter()
            .all(|digest| {
                digest.len() == 64
                    && digest
                        .bytes()
                        .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
            })
    {
        diagnostics::event("BENCH_V5_CODEC_REJECT", "discovery benchmark rejected");
        return Err(SynthesisCoreError("invalid-discovery-benchmark-v5"));
    }
    let targets = task.target_classes.map(|value| value.to_string()).join(",");
    let bytes = format!(
        "{}\0{}\0{}\0{}\0{}\0{}\0{}\0{}\0{}\0{}\0{}",
        task.schema,
        task.id.as_str(),
        task.split.as_str(),
        targets,
        task.hidden_variable,
        task.symmetry,
        task.misrepresentation,
        task.negative_control,
        task.generator_digest,
        task.task_digest,
        task.boundary,
    )
    .into_bytes();
    diagnostics::event(
        "BENCH_V5_CODEC_EXIT",
        "canonical discovery benchmark encoded",
    );
    Ok(bytes)
}

pub fn discovery_benchmark_v5_root(
    task: &DiscoveryBenchmarkV5,
) -> Result<String, SynthesisCoreError> {
    diagnostics::event("BENCH_V5_ROOT_ENTER", "binding discovery benchmark root");
    let root = domain_sha256_hex(TASK_DOMAIN, &canonical_discovery_benchmark_v5_bytes(task)?);
    diagnostics::event("BENCH_V5_ROOT_EXIT", "discovery benchmark root bound");
    Ok(root)
}

pub fn discovery_benchmark_family_v5() -> Result<DiscoveryBenchmarkFamilyV5, SynthesisCoreError> {
    diagnostics::event(
        "BENCH_V5_FAMILY_ENTER",
        "generating discovery benchmark family",
    );
    let tasks: Vec<_> = ALL_DISCOVERY_BENCHMARKS_V5
        .into_iter()
        .map(discovery_benchmark_v5)
        .collect::<Result<_, _>>()?;
    let body = tasks
        .iter()
        .map(|task| task.task_digest.as_str())
        .collect::<Vec<_>>()
        .join(":");
    let result = DiscoveryBenchmarkFamilyV5 {
        schema: DISCOVERY_BENCHMARK_V5_SCHEMA,
        tasks,
        family_digest: domain_sha256_hex(FAMILY_DOMAIN, body.as_bytes()),
        boundary: DISCOVERY_BENCHMARK_V5_BOUNDARY,
    };
    if result.family_digest != DISCOVERY_BENCHMARK_V5_FAMILY_DIGEST {
        diagnostics::event("BENCH_V5_FAMILY_REJECT", "discovery family pin drifted");
        return Err(SynthesisCoreError("discovery-benchmark-v5-family-drift"));
    }
    diagnostics::event(
        "BENCH_V5_FAMILY_EXIT",
        "discovery benchmark family generated",
    );
    Ok(result)
}
