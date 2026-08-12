//! Versioned systematic finite representation families and task-relative survey.

use super::ast::SynthesisCoreError;
use super::diagnostics;
use super::hash::domain_sha256_hex;
use super::joint_synthesis::NativePartitionTaskId;
use super::transport_dsl::{
    compile_transport, CompiledTransportV1, FiniteDomainV1, TransportOpV1, TransportTermV1,
};

pub const REPRESENTATION_SURVEY_V4_SCHEMA: &str =
    "veyra.systematic-finite-representation-survey.v4";
pub const SYSTEMATIC_REPRESENTATION_FAMILY_V4_DIGEST: &str =
    "b62774bdcbd7d882f03fe86ce5a4bfec55aad5abe36aa4130db3f8cd2ce1f9b2";
const FAMILY_DOMAIN: &str = "veyra.systematic-finite-representation-family.v4.binding";
const ROW_DOMAIN: &str = "veyra.systematic-finite-representation-row.v4.binding";
const SURVEY_DOMAIN: &str = "veyra.systematic-finite-representation-survey.v4.binding";
pub const REPRESENTATION_SURVEY_V4_BOUNDARY: &str = "exact only for the declared four-state families: all 24 permutations, eight modular cyclic-affine maps, all 14 proper canonical grouping/quotient maps, and six zero-anchored canonical encodings; task-relative classification is the exact equality/collision trichotomy on those four states, not invariance over arbitrary representations";

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum RepresentationFamilyKindV4 {
    Permutation,
    CyclicAffine,
    GroupingQuotient,
    CanonicalEncoding,
}

impl RepresentationFamilyKindV4 {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Permutation => "permutation",
            Self::CyclicAffine => "cyclic-affine",
            Self::GroupingQuotient => "grouping-quotient",
            Self::CanonicalEncoding => "canonical-encoding",
        }
    }

    pub const fn representation_cost(self) -> usize {
        match self {
            Self::Permutation => 1,
            Self::CyclicAffine => 2,
            Self::GroupingQuotient => 2,
            Self::CanonicalEncoding => 3,
        }
    }
}

pub const ALL_REPRESENTATION_FAMILIES_V4: [RepresentationFamilyKindV4; 4] = [
    RepresentationFamilyKindV4::Permutation,
    RepresentationFamilyKindV4::CyclicAffine,
    RepresentationFamilyKindV4::GroupingQuotient,
    RepresentationFamilyKindV4::CanonicalEncoding,
];

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RepresentationTaskClassV4 {
    /// Transport equality is exactly the task equivalence relation.
    RepresentationStable,
    /// No cross-class collision occurs, but equality alone does not expose the
    /// entire task partition; a further observer is required.
    RepresentationHidden,
    /// At least one transport collision merges distinct task classes, with the
    /// first such finite pair carried by the survey row.
    InformationDestroyed,
}

impl RepresentationTaskClassV4 {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::RepresentationStable => "REPRESENTATION_STABLE",
            Self::RepresentationHidden => "REPRESENTATION_HIDDEN",
            Self::InformationDestroyed => "INFORMATION_DESTROYED",
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RepresentationCandidateV4 {
    pub ordinal: usize,
    pub family: RepresentationFamilyKindV4,
    pub family_ordinal: usize,
    pub representation_cost: usize,
    pub term: TransportTermV1,
    pub transport_digest: String,
    pub transport_cost: usize,
    pub image: [u16; 4],
    pub row_digest: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RepresentationFamilyV4 {
    pub schema: &'static str,
    pub selected_families: Vec<RepresentationFamilyKindV4>,
    pub candidates: Vec<RepresentationCandidateV4>,
    pub family_digest: String,
    pub boundary: &'static str,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RepresentationSurveyRowV4 {
    pub ordinal: usize,
    pub family: RepresentationFamilyKindV4,
    pub transport_digest: String,
    pub classification: RepresentationTaskClassV4,
    pub first_destroyed_pair: Option<(u16, u16, u16)>,
    pub row_digest: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RepresentationSurveyV4 {
    pub schema: &'static str,
    pub task_id: NativePartitionTaskId,
    pub family_digest: String,
    pub rows: Vec<RepresentationSurveyRowV4>,
    pub stable_count: usize,
    pub hidden_count: usize,
    pub destroyed_count: usize,
    pub survey_digest: String,
    pub boundary: &'static str,
}

fn validate_selection(selected: &[RepresentationFamilyKindV4]) -> Result<(), SynthesisCoreError> {
    diagnostics::event(
        "REP_V4_SELECTION_ENTER",
        "validating representation families",
    );
    if selected.is_empty()
        || selected.len() > ALL_REPRESENTATION_FAMILIES_V4.len()
        || selected.windows(2).any(|pair| pair[0] >= pair[1])
    {
        diagnostics::event(
            "REP_V4_SELECTION_REJECT",
            "representation families rejected",
        );
        return Err(SynthesisCoreError(
            "invalid-v4-representation-family-selection",
        ));
    }
    diagnostics::event("REP_V4_SELECTION_EXIT", "representation families validated");
    Ok(())
}

fn permutations() -> Vec<[u16; 4]> {
    diagnostics::event("REP_V4_PERM_ENTER", "enumerating permutations");
    let mut rows = Vec::with_capacity(24);
    for a in 0..4 {
        for b in 0..4 {
            for c in 0..4 {
                for d in 0..4 {
                    let row = [a, b, c, d];
                    if row
                        .iter()
                        .all(|value| row.iter().filter(|other| *other == value).count() == 1)
                    {
                        rows.push(row);
                    }
                }
            }
        }
    }
    diagnostics::event("REP_V4_PERM_EXIT", "permutations enumerated");
    rows
}

fn cyclic_affine() -> Vec<[u16; 4]> {
    diagnostics::event("REP_V4_AFFINE_ENTER", "enumerating cyclic-affine maps");
    let mut rows = Vec::with_capacity(8);
    for multiplier in [1u16, 3] {
        for shift in 0..4u16 {
            rows.push(std::array::from_fn(|value| {
                (multiplier * value as u16 + shift) % 4
            }));
        }
    }
    diagnostics::event("REP_V4_AFFINE_EXIT", "cyclic-affine maps enumerated");
    rows
}

fn grouping_quotients() -> Vec<[u16; 4]> {
    diagnostics::event("REP_V4_GROUP_ENTER", "enumerating canonical quotients");
    let mut rows = Vec::with_capacity(14);
    for second in 0..=1 {
        let max_second = second;
        for third in 0..=max_second + 1 {
            let max_third = max_second.max(third);
            for fourth in 0..=max_third + 1 {
                let row = [0, second, third, fourth];
                if row != [0, 1, 2, 3] {
                    rows.push(row);
                }
            }
        }
    }
    diagnostics::event("REP_V4_GROUP_EXIT", "canonical quotients enumerated");
    rows
}

fn canonical_encodings() -> Vec<[u16; 4]> {
    diagnostics::event("REP_V4_CANON_ENTER", "enumerating canonical encodings");
    let rows = permutations()
        .into_iter()
        .filter(|row| row[0] == 0)
        .map(|row| std::array::from_fn(|index| row[index] * 2))
        .collect();
    diagnostics::event("REP_V4_CANON_EXIT", "canonical encodings enumerated");
    rows
}

fn rows_for(kind: RepresentationFamilyKindV4) -> Vec<[u16; 4]> {
    diagnostics::event(
        "REP_V4_ROWS_ENTER",
        "selecting representation row generator",
    );
    let result = match kind {
        RepresentationFamilyKindV4::Permutation => permutations(),
        RepresentationFamilyKindV4::CyclicAffine => cyclic_affine(),
        RepresentationFamilyKindV4::GroupingQuotient => grouping_quotients(),
        RepresentationFamilyKindV4::CanonicalEncoding => canonical_encodings(),
    };
    diagnostics::event("REP_V4_ROWS_EXIT", "representation rows selected");
    result
}

fn term_for(
    kind: RepresentationFamilyKindV4,
    family_ordinal: usize,
    image: [u16; 4],
) -> Result<TransportTermV1, SynthesisCoreError> {
    diagnostics::event(
        "REP_V4_TERM_ENTER",
        "constructing typed representation transport",
    );
    let source = FiniteDomainV1::new("v4-abstract-four-state-domain", 4)?;
    let target_cardinality = image.iter().copied().max().unwrap_or(0) + 1;
    let target = FiniteDomainV1::new(
        &format!("v4-{}-{family_ordinal}-target", kind.as_str()),
        target_cardinality,
    )?;
    let op = match kind {
        RepresentationFamilyKindV4::Permutation | RepresentationFamilyKindV4::CyclicAffine => {
            TransportOpV1::Relabel(image.to_vec())
        }
        RepresentationFamilyKindV4::GroupingQuotient => TransportOpV1::Group(image.to_vec()),
        RepresentationFamilyKindV4::CanonicalEncoding => {
            TransportOpV1::CanonicalEncode(image.to_vec())
        }
    };
    let result = TransportTermV1 { source, target, op };
    diagnostics::event(
        "REP_V4_TERM_EXIT",
        "typed representation transport constructed",
    );
    Ok(result)
}

fn candidate(
    ordinal: usize,
    family: RepresentationFamilyKindV4,
    family_ordinal: usize,
    image: [u16; 4],
) -> Result<RepresentationCandidateV4, SynthesisCoreError> {
    diagnostics::event("REP_V4_ROW_ENTER", "binding representation candidate");
    let term = term_for(family, family_ordinal, image)?;
    let compiled = compile_transport(&term)?;
    let image_text = image.map(|value| value.to_string()).join(",");
    let body = format!(
        "{ordinal}:{}:{family_ordinal}:{}:{}:{image_text}",
        family.as_str(),
        family.representation_cost(),
        compiled.digest()
    );
    let result = RepresentationCandidateV4 {
        ordinal,
        family,
        family_ordinal,
        representation_cost: family.representation_cost(),
        term,
        transport_digest: compiled.digest().to_owned(),
        transport_cost: compiled.cost() as usize,
        image,
        row_digest: domain_sha256_hex(ROW_DOMAIN, body.as_bytes()),
    };
    diagnostics::event("REP_V4_ROW_EXIT", "representation candidate bound");
    Ok(result)
}

pub fn enumerate_representation_family_v4(
    selected: &[RepresentationFamilyKindV4],
) -> Result<RepresentationFamilyV4, SynthesisCoreError> {
    diagnostics::event(
        "REP_V4_FAMILY_ENTER",
        "enumerating representation family v4",
    );
    validate_selection(selected)?;
    let mut candidates = Vec::new();
    for family in selected {
        for (family_ordinal, image) in rows_for(*family).into_iter().enumerate() {
            candidates.push(candidate(candidates.len(), *family, family_ordinal, image)?);
        }
    }
    let body = format!(
        "{}:{}",
        selected
            .iter()
            .map(|kind| kind.as_str())
            .collect::<Vec<_>>()
            .join(","),
        candidates
            .iter()
            .map(|row| row.row_digest.as_str())
            .collect::<Vec<_>>()
            .join(":")
    );
    let result = RepresentationFamilyV4 {
        schema: REPRESENTATION_SURVEY_V4_SCHEMA,
        selected_families: selected.to_vec(),
        candidates,
        family_digest: domain_sha256_hex(FAMILY_DOMAIN, body.as_bytes()),
        boundary: REPRESENTATION_SURVEY_V4_BOUNDARY,
    };
    if selected == ALL_REPRESENTATION_FAMILIES_V4
        && result.family_digest != SYSTEMATIC_REPRESENTATION_FAMILY_V4_DIGEST
    {
        diagnostics::event("REP_V4_FAMILY_REJECT", "systematic family digest drifted");
        return Err(SynthesisCoreError(
            "systematic-v4-representation-family-drift",
        ));
    }
    diagnostics::event("REP_V4_FAMILY_EXIT", "representation family v4 enumerated");
    Ok(result)
}

fn classify(
    compiled: &CompiledTransportV1,
    targets: [u8; 4],
) -> (RepresentationTaskClassV4, Option<(u16, u16, u16)>) {
    diagnostics::event(
        "REP_V4_CLASS_ENTER",
        "classifying task-relative representation",
    );
    let image = compiled.image();
    let mut first_destroyed = None;
    let mut equality_matches = true;
    for left in 0..4 {
        for right in left + 1..4 {
            let same_image = image[left] == image[right];
            let same_target = targets[left] == targets[right];
            equality_matches &= same_image == same_target;
            if same_image && !same_target && first_destroyed.is_none() {
                first_destroyed = Some((left as u16, right as u16, image[left]));
            }
        }
    }
    let class = if first_destroyed.is_some() {
        RepresentationTaskClassV4::InformationDestroyed
    } else if equality_matches {
        RepresentationTaskClassV4::RepresentationStable
    } else {
        RepresentationTaskClassV4::RepresentationHidden
    };
    diagnostics::event(
        "REP_V4_CLASS_EXIT",
        "task-relative representation classified",
    );
    (class, first_destroyed)
}

pub fn survey_representation_family_v4(
    task_id: NativePartitionTaskId,
    selected: &[RepresentationFamilyKindV4],
) -> Result<RepresentationSurveyV4, SynthesisCoreError> {
    diagnostics::event("REP_V4_SURVEY_ENTER", "starting representation survey v4");
    let family = enumerate_representation_family_v4(selected)?;
    let targets = task_id.target_classes();
    let mut rows = Vec::with_capacity(family.candidates.len());
    for candidate in &family.candidates {
        let compiled = compile_transport(&candidate.term)?;
        let (classification, first_destroyed_pair) = classify(&compiled, targets);
        let body = format!(
            "{}:{}:{}:{}",
            candidate.ordinal,
            candidate.transport_digest,
            classification.as_str(),
            first_destroyed_pair.map_or_else(
                || "none".to_owned(),
                |(left, right, image)| format!("{left},{right},{image}")
            )
        );
        rows.push(RepresentationSurveyRowV4 {
            ordinal: candidate.ordinal,
            family: candidate.family,
            transport_digest: candidate.transport_digest.clone(),
            classification,
            first_destroyed_pair,
            row_digest: domain_sha256_hex(SURVEY_DOMAIN, body.as_bytes()),
        });
    }
    let stable_count = rows
        .iter()
        .filter(|row| row.classification == RepresentationTaskClassV4::RepresentationStable)
        .count();
    let hidden_count = rows
        .iter()
        .filter(|row| row.classification == RepresentationTaskClassV4::RepresentationHidden)
        .count();
    let destroyed_count = rows.len() - stable_count - hidden_count;
    let body = format!(
        "{}:{}:{}:{}:{}:{}",
        task_id.as_str(),
        family.family_digest,
        stable_count,
        hidden_count,
        destroyed_count,
        rows.iter()
            .map(|row| row.row_digest.as_str())
            .collect::<Vec<_>>()
            .join(":")
    );
    let result = RepresentationSurveyV4 {
        schema: REPRESENTATION_SURVEY_V4_SCHEMA,
        task_id,
        family_digest: family.family_digest,
        rows,
        stable_count,
        hidden_count,
        destroyed_count,
        survey_digest: domain_sha256_hex(SURVEY_DOMAIN, body.as_bytes()),
        boundary: REPRESENTATION_SURVEY_V4_BOUNDARY,
    };
    diagnostics::event("REP_V4_SURVEY_EXIT", "representation survey v4 completed");
    Ok(result)
}
