//! Exhaustive finite shift/permutation representation family and transport.

use std::collections::HashSet;

use super::ast::SynthesisCoreError;
use super::cegis::ExpectedRelation;
use super::diagnostics;
use super::grammar::{enumerate_observer_grammar_profile, grammar_config_for_profile};
use super::grammar_profile::ObserverGrammarProfileId;
use super::hash::domain_sha256_hex;
use super::semantics::{echo, EchoOutcome, Recurrence};

pub const REPRESENTATION_FAMILY_SCHEMA: &str = "veyra.native-representation.shift-permutation-4.v1";
pub const REPRESENTATION_FAMILY_ID: &str = "unary-shifts-0-4-all-permutations-4-v1";
pub const REPRESENTATION_TRANSFORMS: usize = 120;
pub const REPRESENTATION_FAMILY_DIGEST: &str =
    "dbba66299481323f4621af7a896fb8486e14199a9ce0e2cd1f7cbf8acee62bad";
pub const FIRST_REPRESENTATION_TRANSFORM_DIGEST: &str =
    "f01b9eacf394f579539c3576ca021c841750c9114ab160e73300120ecdfa3e2b";
pub const LAST_REPRESENTATION_TRANSFORM_DIGEST: &str =
    "0de8ccbef96f174f72ae8b537af45276303a4c9b3e3ebf66b1911509295cea24";
pub const PARITY_XOR_SURVEY_DIGEST: &str =
    "f1b3d0a5313a82ae4fb5490ec56b8180a8c14e5374778d345449c96e3e3c148b";
pub const PARITY_XOR_SURVEY_CLASSES: usize = 3;
pub const PARITY_XOR_PRESERVING_TRANSFORMS: usize = 40;
const TRANSFORM_DOMAIN: &str = "veyra.native-representation.transform.v1.binding";
const FAMILY_DOMAIN: &str = "veyra.native-representation.family.v1.binding";
const TRANSPORT_DOMAIN: &str = "veyra.native-representation.transport-systematic.v1.binding";

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NativeRepresentationTransformV1 {
    ordinal: usize,
    shift: u8,
    permutation: [u8; 4],
    cost: usize,
    canonical: Vec<u8>,
    transform_digest: String,
}

impl NativeRepresentationTransformV1 {
    pub const fn ordinal(&self) -> usize {
        self.ordinal
    }

    pub const fn shift(&self) -> u8 {
        self.shift
    }

    pub const fn permutation(&self) -> [u8; 4] {
        self.permutation
    }

    pub const fn cost(&self) -> usize {
        self.cost
    }

    pub fn canonical(&self) -> &[u8] {
        &self.canonical
    }

    pub fn transform_digest(&self) -> &str {
        &self.transform_digest
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NativeRepresentationFamilyV1 {
    pub schema: &'static str,
    pub family_id: &'static str,
    pub transforms: Vec<NativeRepresentationTransformV1>,
    pub family_digest: String,
    pub boundary: &'static str,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NativeSystematicTransportV1 {
    pub schema: &'static str,
    pub grammar_profile_id: ObserverGrammarProfileId,
    pub grammar_profile_digest: String,
    pub catalog_digest: String,
    pub observer_ordinal: usize,
    pub observer_digest: String,
    pub source_transform_ordinal: usize,
    pub source_transform_digest: String,
    pub target_transform_ordinal: usize,
    pub target_transform_digest: String,
    pub target_classes: [u8; 4],
    pub source_case_results: [bool; 6],
    pub target_case_results: [bool; 6],
    pub source_preserved: bool,
    pub target_preserved: bool,
    pub transport_preserved: bool,
    pub transport_digest: String,
    pub boundary: &'static str,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NativeTransportEquivalenceClassV1 {
    pub class_ordinal: usize,
    pub obligation_results: [bool; 6],
    pub preserving: bool,
    pub transform_ordinals: Vec<usize>,
    pub class_digest: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NativeRepresentationSurveyV1 {
    pub schema: &'static str,
    pub grammar_profile_id: ObserverGrammarProfileId,
    pub grammar_profile_digest: String,
    pub catalog_digest: String,
    pub family_digest: String,
    pub observer_ordinal: usize,
    pub observer_digest: String,
    pub target_classes: [u8; 4],
    pub equivalence_classes: Vec<NativeTransportEquivalenceClassV1>,
    pub preserving_transform_ordinals: Vec<usize>,
    pub preserving_transform_count: usize,
    pub transform_count: usize,
    pub survey_digest: String,
    pub boundary: &'static str,
}

fn inversion_count(permutation: [u8; 4]) -> usize {
    diagnostics::event(
        "REPRESENTATION_COST_ENTER",
        "counting permutation inversions",
    );
    let mut count = 0;
    for left in 0..4 {
        for right in (left + 1)..4 {
            count += usize::from(permutation[left] > permutation[right]);
        }
    }
    diagnostics::event("REPRESENTATION_COST_EXIT", "permutation inversions counted");
    count
}

fn transform_body(ordinal: usize, shift: u8, permutation: [u8; 4], cost: usize) -> String {
    diagnostics::event("REPRESENTATION_JSON_ENTER", "encoding finite transform");
    let result = format!(
        "{{\"cost\":{cost},\"family_id\":\"{REPRESENTATION_FAMILY_ID}\",\"ordinal\":{ordinal},\"permutation\":[{},{},{},{}],\"schema\":\"{REPRESENTATION_FAMILY_SCHEMA}\",\"shift\":{shift}}}",
        permutation[0], permutation[1], permutation[2], permutation[3],
    );
    diagnostics::event("REPRESENTATION_JSON_EXIT", "finite transform encoded");
    result
}

fn permutations() -> Vec<[u8; 4]> {
    diagnostics::event("PERMUTATIONS_ENTER", "enumerating four-state permutations");
    let mut result = Vec::with_capacity(24);
    for a in 0..4u8 {
        for b in 0..4u8 {
            for c in 0..4u8 {
                for d in 0..4u8 {
                    if [a, b, c, d].iter().collect::<HashSet<_>>().len() == 4 {
                        result.push([a, b, c, d]);
                    }
                }
            }
        }
    }
    diagnostics::event("PERMUTATIONS_EXIT", "four-state permutations enumerated");
    result
}

pub fn enumerate_representation_family() -> Result<NativeRepresentationFamilyV1, SynthesisCoreError>
{
    diagnostics::event(
        "REPRESENTATION_FAMILY_ENTER",
        "enumerating closed shift-permutation family",
    );
    let permutations = permutations();
    if permutations.len() != 24 {
        diagnostics::event(
            "REPRESENTATION_FAMILY_REJECT",
            "permutation cardinality drifted",
        );
        return Err(SynthesisCoreError("representation-permutation-drift"));
    }
    let mut transforms = Vec::with_capacity(REPRESENTATION_TRANSFORMS);
    for shift in 0..=4u8 {
        for permutation in &permutations {
            let ordinal = transforms.len();
            let cost = shift as usize + inversion_count(*permutation);
            let canonical = transform_body(ordinal, shift, *permutation, cost).into_bytes();
            transforms.push(NativeRepresentationTransformV1 {
                ordinal,
                shift,
                permutation: *permutation,
                cost,
                transform_digest: domain_sha256_hex(TRANSFORM_DOMAIN, &canonical),
                canonical,
            });
        }
    }
    if transforms.len() != REPRESENTATION_TRANSFORMS
        || transforms
            .iter()
            .enumerate()
            .any(|(ordinal, row)| row.ordinal != ordinal)
    {
        diagnostics::event(
            "REPRESENTATION_FAMILY_REJECT",
            "transform cardinality/order drifted",
        );
        return Err(SynthesisCoreError("representation-family-order-drift"));
    }
    let mut framed = REPRESENTATION_FAMILY_SCHEMA.as_bytes().to_vec();
    framed.push(0);
    for transform in &transforms {
        framed.extend_from_slice(&(transform.canonical.len() as u64).to_be_bytes());
        framed.extend_from_slice(&transform.canonical);
    }
    let result = NativeRepresentationFamilyV1 {
        schema: REPRESENTATION_FAMILY_SCHEMA,
        family_id: REPRESENTATION_FAMILY_ID,
        transforms,
        family_digest: domain_sha256_hex(FAMILY_DOMAIN, &framed),
        boundary: "exact shifts 0..4 crossed with all 24 lexicographic permutations; cost is shift count plus permutation inversion count, not physical or statistical distance",
    };
    diagnostics::event(
        "REPRESENTATION_FAMILY_EXIT",
        "closed shift-permutation family enumerated",
    );
    Ok(result)
}

pub fn encoded_recurrences(
    transform: &NativeRepresentationTransformV1,
) -> Result<[Recurrence; 4], SynthesisCoreError> {
    diagnostics::event("REPRESENTATION_APPLY_ENTER", "applying finite transform");
    let result = [
        Recurrence::new(transform.shift as u16 + transform.permutation[0] as u16),
        Recurrence::new(transform.shift as u16 + transform.permutation[1] as u16),
        Recurrence::new(transform.shift as u16 + transform.permutation[2] as u16),
        Recurrence::new(transform.shift as u16 + transform.permutation[3] as u16),
    ];
    if let [Ok(a), Ok(b), Ok(c), Ok(d)] = result {
        diagnostics::event("REPRESENTATION_APPLY_EXIT", "finite transform applied");
        Ok([a, b, c, d])
    } else {
        diagnostics::event("REPRESENTATION_APPLY_REJECT", "encoded recurrence rejected");
        Err(SynthesisCoreError("representation-encoding-rejected"))
    }
}

fn relation_table(
    observer: &super::ast::ObserverExpr,
    encoded: [Recurrence; 4],
    targets: [u8; 4],
) -> Result<[bool; 6], SynthesisCoreError> {
    diagnostics::event("TRANSPORT_TABLE_ENTER", "evaluating six quotient relations");
    let mut result = [false; 6];
    let mut row = 0;
    for left in 0..4 {
        for right in (left + 1)..4 {
            let expected = if targets[left] == targets[right] {
                ExpectedRelation::Echo
            } else {
                ExpectedRelation::Separate
            };
            let actual = match echo(observer, encoded[left], encoded[right]).inspect_err(|_| {
                diagnostics::event("TRANSPORT_TABLE_REJECT", "observer evaluation rejected")
            })? {
                EchoOutcome::Echo(_) => ExpectedRelation::Echo,
                EchoOutcome::Mismatch { .. } => ExpectedRelation::Separate,
                EchoOutcome::DomainBlocked { .. } => ExpectedRelation::DomainBlocked,
            };
            result[row] = actual == expected;
            row += 1;
        }
    }
    diagnostics::event("TRANSPORT_TABLE_EXIT", "six quotient relations evaluated");
    Ok(result)
}

fn bool_array(values: [bool; 6]) -> String {
    diagnostics::event("TRANSPORT_BOOL_ENTER", "encoding fixed truth table");
    let result = values
        .iter()
        .map(bool::to_string)
        .collect::<Vec<_>>()
        .join(",");
    diagnostics::event("TRANSPORT_BOOL_EXIT", "fixed truth table encoded");
    result
}

fn target_array(values: [u8; 4]) -> String {
    diagnostics::event("TRANSPORT_TARGET_ENTER", "encoding binary target");
    let result = format!("[{},{},{},{}]", values[0], values[1], values[2], values[3]);
    diagnostics::event("TRANSPORT_TARGET_EXIT", "binary target encoded");
    result
}

fn validate_target(target_classes: [u8; 4]) -> Result<(), SynthesisCoreError> {
    diagnostics::event(
        "TRANSPORT_TARGET_VALIDATE_ENTER",
        "validating binary target",
    );
    if target_classes.iter().any(|value| *value > 1)
        || target_classes
            .iter()
            .all(|value| *value == target_classes[0])
    {
        diagnostics::event(
            "TRANSPORT_TARGET_VALIDATE_REJECT",
            "binary target is invalid",
        );
        return Err(SynthesisCoreError("invalid-systematic-transport-target"));
    }
    diagnostics::event("TRANSPORT_TARGET_VALIDATE_EXIT", "binary target validated");
    Ok(())
}

fn class_body(
    class_ordinal: usize,
    obligation_results: [bool; 6],
    transform_ordinals: &[usize],
) -> String {
    diagnostics::event("TRANSPORT_CLASS_JSON_ENTER", "encoding transport class");
    let members = transform_ordinals
        .iter()
        .map(usize::to_string)
        .collect::<Vec<_>>()
        .join(",");
    let result = format!(
        "{{\"class_ordinal\":{class_ordinal},\"obligation_results\":[{}],\"preserving\":{},\"transform_ordinals\":[{members}]}}",
        bool_array(obligation_results),
        obligation_results.iter().all(|value| *value),
    );
    diagnostics::event("TRANSPORT_CLASS_JSON_EXIT", "transport class encoded");
    result
}

pub fn evaluate_systematic_transport(
    profile_id: ObserverGrammarProfileId,
    observer_ordinal: usize,
    source_transform_ordinal: usize,
    target_transform_ordinal: usize,
    target_classes: [u8; 4],
) -> Result<NativeSystematicTransportV1, SynthesisCoreError> {
    diagnostics::event(
        "SYSTEMATIC_TRANSPORT_ENTER",
        "evaluating closed transport row",
    );
    validate_target(target_classes)
        .inspect_err(|_| diagnostics::event("SYSTEMATIC_TRANSPORT_REJECT", "target rejected"))?;
    let family = enumerate_representation_family().inspect_err(|_| {
        diagnostics::event("SYSTEMATIC_TRANSPORT_REJECT", "family enumeration rejected")
    })?;
    let source = family
        .transforms
        .get(source_transform_ordinal)
        .ok_or(SynthesisCoreError("invalid-source-transform-ordinal"))
        .inspect_err(|_| {
            diagnostics::event("SYSTEMATIC_TRANSPORT_REJECT", "source ordinal rejected")
        })?;
    let target = family
        .transforms
        .get(target_transform_ordinal)
        .ok_or(SynthesisCoreError("invalid-target-transform-ordinal"))
        .inspect_err(|_| {
            diagnostics::event("SYSTEMATIC_TRANSPORT_REJECT", "target ordinal rejected")
        })?;
    let profiled =
        enumerate_observer_grammar_profile(profile_id, grammar_config_for_profile(profile_id))
            .inspect_err(|_| {
                diagnostics::event("SYSTEMATIC_TRANSPORT_REJECT", "profile rejected")
            })?;
    let candidate = profiled
        .enumeration
        .candidates
        .get(observer_ordinal)
        .ok_or(SynthesisCoreError("invalid-transport-observer-ordinal"))
        .inspect_err(|_| {
            diagnostics::event("SYSTEMATIC_TRANSPORT_REJECT", "observer ordinal rejected")
        })?;
    let source_case_results = relation_table(
        &candidate.observer,
        encoded_recurrences(source).inspect_err(|_| {
            diagnostics::event("SYSTEMATIC_TRANSPORT_REJECT", "source encoding rejected")
        })?,
        target_classes,
    )
    .inspect_err(|_| diagnostics::event("SYSTEMATIC_TRANSPORT_REJECT", "source table rejected"))?;
    let target_case_results = relation_table(
        &candidate.observer,
        encoded_recurrences(target).inspect_err(|_| {
            diagnostics::event("SYSTEMATIC_TRANSPORT_REJECT", "target encoding rejected")
        })?,
        target_classes,
    )
    .inspect_err(|_| diagnostics::event("SYSTEMATIC_TRANSPORT_REJECT", "target table rejected"))?;
    let source_preserved = source_case_results.iter().all(|value| *value);
    let target_preserved = target_case_results.iter().all(|value| *value);
    let mut row = NativeSystematicTransportV1 {
        schema: "veyra.native-representation.transport-systematic.v1",
        grammar_profile_id: profile_id,
        grammar_profile_digest: profiled.profile.profile_digest,
        catalog_digest: profiled.enumeration.catalog_digest,
        observer_ordinal,
        observer_digest: candidate.digest.clone(),
        source_transform_ordinal,
        source_transform_digest: source.transform_digest.clone(),
        target_transform_ordinal,
        target_transform_digest: target.transform_digest.clone(),
        target_classes,
        source_case_results,
        target_case_results,
        source_preserved,
        target_preserved,
        transport_preserved: source_preserved && target_preserved,
        transport_digest: String::new(),
        boundary: "same exact catalog observer evaluated across two members of the closed representation family; no invariance theorem or physical transport claim",
    };
    let body = format!(
        "{{\"catalog_digest\":\"{}\",\"observer_digest\":\"{}\",\"observer_ordinal\":{},\"profile_digest\":\"{}\",\"source_digest\":\"{}\",\"source_results\":[{}],\"target_classes\":[{},{},{},{}],\"target_digest\":\"{}\",\"target_results\":[{}]}}",
        row.catalog_digest,
        row.observer_digest,
        row.observer_ordinal,
        row.grammar_profile_digest,
        row.source_transform_digest,
        bool_array(row.source_case_results),
        row.target_classes[0], row.target_classes[1], row.target_classes[2], row.target_classes[3],
        row.target_transform_digest,
        bool_array(row.target_case_results),
    );
    row.transport_digest = domain_sha256_hex(TRANSPORT_DOMAIN, body.as_bytes());
    diagnostics::event(
        "SYSTEMATIC_TRANSPORT_EXIT",
        "closed transport row evaluated",
    );
    Ok(row)
}

/// Evaluate one exact observer over every declared representation and quotient
/// the 120 transforms by six obligation-satisfaction results.
pub fn survey_representation_family(
    profile_id: ObserverGrammarProfileId,
    observer_ordinal: usize,
    target_classes: [u8; 4],
) -> Result<NativeRepresentationSurveyV1, SynthesisCoreError> {
    diagnostics::event(
        "REPRESENTATION_SURVEY_ENTER",
        "surveying complete representation family",
    );
    validate_target(target_classes)
        .inspect_err(|_| diagnostics::event("REPRESENTATION_SURVEY_REJECT", "target rejected"))?;
    let family = enumerate_representation_family().inspect_err(|_| {
        diagnostics::event(
            "REPRESENTATION_SURVEY_REJECT",
            "family enumeration rejected",
        )
    })?;
    let profiled =
        enumerate_observer_grammar_profile(profile_id, grammar_config_for_profile(profile_id))
            .inspect_err(|_| {
                diagnostics::event("REPRESENTATION_SURVEY_REJECT", "profile rejected")
            })?;
    let candidate = profiled
        .enumeration
        .candidates
        .get(observer_ordinal)
        .ok_or(SynthesisCoreError("invalid-survey-observer-ordinal"))
        .inspect_err(|_| {
            diagnostics::event("REPRESENTATION_SURVEY_REJECT", "observer ordinal rejected")
        })?;
    let mut grouped: Vec<([bool; 6], Vec<usize>)> = Vec::new();
    for transform in &family.transforms {
        let table = relation_table(
            &candidate.observer,
            encoded_recurrences(transform).inspect_err(|_| {
                diagnostics::event("REPRESENTATION_SURVEY_REJECT", "encoding rejected")
            })?,
            target_classes,
        )
        .inspect_err(|_| {
            diagnostics::event(
                "REPRESENTATION_SURVEY_REJECT",
                "obligation results rejected",
            )
        })?;
        match grouped.iter_mut().find(|(existing, _)| *existing == table) {
            Some((_, members)) => members.push(transform.ordinal),
            None => grouped.push((table, vec![transform.ordinal])),
        }
    }
    grouped.sort_by_key(|(_, members)| members[0]);
    let mut equivalence_classes = Vec::with_capacity(grouped.len());
    for (class_ordinal, (obligation_results, transform_ordinals)) in grouped.into_iter().enumerate()
    {
        let body = class_body(class_ordinal, obligation_results, &transform_ordinals);
        equivalence_classes.push(NativeTransportEquivalenceClassV1 {
            class_ordinal,
            obligation_results,
            preserving: obligation_results.iter().all(|value| *value),
            transform_ordinals,
            class_digest: domain_sha256_hex(
                "veyra.native-representation.transport-class.v1.binding",
                body.as_bytes(),
            ),
        });
    }
    let preserving_transform_ordinals = equivalence_classes
        .iter()
        .filter(|row| row.preserving)
        .flat_map(|row| row.transform_ordinals.iter().copied())
        .collect::<Vec<_>>();
    let classes_body = equivalence_classes
        .iter()
        .map(|row| {
            format!(
                "{{\"class_digest\":\"{}\",\"class_ordinal\":{}}}",
                row.class_digest, row.class_ordinal
            )
        })
        .collect::<Vec<_>>()
        .join(",");
    let body = format!(
        "{{\"catalog_digest\":\"{}\",\"classes\":[{classes_body}],\"family_digest\":\"{}\",\"observer_digest\":\"{}\",\"observer_ordinal\":{observer_ordinal},\"profile_digest\":\"{}\",\"target_classes\":{},\"transform_count\":{}}}",
        profiled.enumeration.catalog_digest,
        family.family_digest,
        candidate.digest,
        profiled.profile.profile_digest,
        target_array(target_classes),
        family.transforms.len(),
    );
    let result = NativeRepresentationSurveyV1 {
        schema: "veyra.native-representation.transport-survey.v1",
        grammar_profile_id: profile_id,
        grammar_profile_digest: profiled.profile.profile_digest,
        catalog_digest: profiled.enumeration.catalog_digest,
        family_digest: family.family_digest,
        observer_ordinal,
        observer_digest: candidate.digest.clone(),
        target_classes,
        preserving_transform_count: preserving_transform_ordinals.len(),
        preserving_transform_ordinals,
        transform_count: family.transforms.len(),
        equivalence_classes,
        survey_digest: domain_sha256_hex(
            "veyra.native-representation.transport-survey.v1.binding",
            body.as_bytes(),
        ),
        boundary: "complete truth-table quotient only for one exact observer, binary target, and the declared 120-row family; not a representation invariance theorem",
    };
    diagnostics::event(
        "REPRESENTATION_SURVEY_EXIT",
        "complete representation family surveyed",
    );
    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn family_is_exact_complete_and_deterministic() {
        let first = enumerate_representation_family().unwrap();
        let second = enumerate_representation_family().unwrap();
        assert_eq!(first.family_digest, REPRESENTATION_FAMILY_DIGEST);
        assert_eq!(
            first.transforms[0].transform_digest,
            FIRST_REPRESENTATION_TRANSFORM_DIGEST
        );
        assert_eq!(
            first.transforms[119].transform_digest,
            LAST_REPRESENTATION_TRANSFORM_DIGEST
        );
        assert_eq!(first, second);
        assert_eq!(first.transforms.len(), REPRESENTATION_TRANSFORMS);
        assert_eq!(first.transforms[0].shift, 0);
        assert_eq!(first.transforms[0].permutation, [0, 1, 2, 3]);
        assert_eq!(first.transforms[119].shift, 4);
        assert_eq!(first.transforms[119].permutation, [3, 2, 1, 0]);
        assert_eq!(first.transforms[0].cost, 0);
        assert_eq!(first.transforms[119].cost, 10);
        assert_eq!(
            first
                .transforms
                .iter()
                .map(|row| row.transform_digest.as_str())
                .collect::<HashSet<_>>()
                .len(),
            REPRESENTATION_TRANSFORMS
        );
    }

    #[test]
    fn parity_xor_survey_partitions_all_transforms_deterministically() {
        let first =
            survey_representation_family(ObserverGrammarProfileId::ParityV2, 2, [0, 1, 1, 0])
                .unwrap();
        let second =
            survey_representation_family(ObserverGrammarProfileId::ParityV2, 2, [0, 1, 1, 0])
                .unwrap();
        assert_eq!(first, second);
        assert_eq!(first.transform_count, REPRESENTATION_TRANSFORMS);
        assert_eq!(
            first
                .equivalence_classes
                .iter()
                .map(|row| row.transform_ordinals.len())
                .sum::<usize>(),
            REPRESENTATION_TRANSFORMS
        );
        assert_eq!(
            first
                .equivalence_classes
                .iter()
                .flat_map(|row| row.transform_ordinals.iter().copied())
                .collect::<HashSet<_>>()
                .len(),
            REPRESENTATION_TRANSFORMS
        );
        assert_eq!(first.survey_digest, PARITY_XOR_SURVEY_DIGEST);
        assert_eq!(first.equivalence_classes.len(), PARITY_XOR_SURVEY_CLASSES);
        assert_eq!(
            first.preserving_transform_count,
            PARITY_XOR_PRESERVING_TRANSFORMS
        );
        assert_eq!(
            first.preserving_transform_count,
            first.preserving_transform_ordinals.len()
        );
    }
}
