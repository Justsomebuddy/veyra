//! Append-only v5 discovery grammar over a finite sixteen-state domain.

use super::ast::SynthesisCoreError;
use super::diagnostics;
use super::grammar_registry::GRAMMAR_REGISTRY_DIGEST;
use super::hash::domain_sha256_hex;

pub const DISCOVERY_GRAMMAR_V5_SCHEMA: &str = "veyra.discovery-observer-grammar.v5";
pub const DISCOVERY_GRAMMAR_V5_PROFILE_ID: &str = "affine-parity-reflection-v5";
pub const DISCOVERY_GRAMMAR_V5_PROFILE_DIGEST: &str =
    "787b4f3b9538f6861a0490ca5d3c89177f4579fc001c35de2d3c358fee1611ba";
pub const DISCOVERY_GRAMMAR_V5_CATALOG_DIGEST: &str =
    "cb691d7892fa3235984538c3becd746109d112a597f1a6be52a364011543b7a7";
pub const DISCOVERY_GRAMMAR_V5_EXTENSION_DIGEST: &str =
    "b70613a0ac46aa6ae328792f484486bab2749953672e6255eb36cd9b4053274e";
const PROFILE_DOMAIN: &str = "veyra.discovery-observer-grammar.profile.v5.binding";
const CANDIDATE_DOMAIN: &str = "veyra.discovery-observer-grammar.candidate.v5.binding";
const CATALOG_DOMAIN: &str = "veyra.discovery-observer-grammar.catalog.v5.binding";
const EXTENSION_DOMAIN: &str = "veyra.discovery-observer-grammar.extension.v5.binding";
pub const DISCOVERY_GRAMMAR_V5_BOUNDARY: &str = "append-only finite extension after the frozen v1 registry: 1,920 affine bit-parity terms followed by 128 affine reflection-orbit terms on exactly sixteen states; costs, order and lower bounds are catalog-relative and do not claim semantic completeness";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum DiscoveryGrammarProfileIdV5 {
    AffineParityReflectionV5,
}

impl DiscoveryGrammarProfileIdV5 {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::AffineParityReflectionV5 => DISCOVERY_GRAMMAR_V5_PROFILE_ID,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum DiscoveryObserverTermV5 {
    AffineBitParity { multiplier: u8, shift: u8, mask: u8 },
    AffineReflectionOrbit { multiplier: u8, shift: u8 },
}

impl DiscoveryObserverTermV5 {
    pub const fn tag(self) -> &'static str {
        match self {
            Self::AffineBitParity { .. } => "affine-bit-parity",
            Self::AffineReflectionOrbit { .. } => "affine-reflection-orbit",
        }
    }

    pub const fn cost(self) -> usize {
        match self {
            Self::AffineBitParity {
                multiplier,
                shift,
                mask,
            } => {
                1 + (multiplier != 1) as usize + (shift != 0) as usize + mask.count_ones() as usize
            }
            Self::AffineReflectionOrbit { multiplier, shift } => {
                4 + (multiplier != 1) as usize + (shift != 0) as usize
            }
        }
    }

    pub const fn response(self, surface_state: u8) -> u8 {
        let (multiplier, shift) = match self {
            Self::AffineBitParity {
                multiplier, shift, ..
            }
            | Self::AffineReflectionOrbit { multiplier, shift } => (multiplier, shift),
        };
        let latent = multiplier.wrapping_mul(surface_state).wrapping_add(shift) & 15;
        match self {
            Self::AffineBitParity { mask, .. } => (latent & mask).count_ones() as u8 & 1,
            Self::AffineReflectionOrbit { .. } => {
                let reflected = 16u8.wrapping_sub(latent) & 15;
                if latent < reflected {
                    latent
                } else {
                    reflected
                }
            }
        }
    }

    fn canonical_body(self) -> String {
        match self {
            Self::AffineBitParity {
                multiplier,
                shift,
                mask,
            } => format!("affine-bit-parity:{multiplier}:{shift}:{mask}"),
            Self::AffineReflectionOrbit { multiplier, shift } => {
                format!("affine-reflection-orbit:{multiplier}:{shift}")
            }
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DiscoveryObserverCandidateV5 {
    pub ordinal: usize,
    pub term: DiscoveryObserverTermV5,
    pub cost: usize,
    pub response_digest: String,
    pub candidate_digest: String,
}

impl DiscoveryObserverCandidateV5 {
    pub fn responses(&self) -> [u8; 16] {
        std::array::from_fn(|state| self.term.response(state as u8))
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DiscoveryGrammarProfileV5 {
    pub schema: &'static str,
    pub profile_id: DiscoveryGrammarProfileIdV5,
    pub parent_registry_digest: &'static str,
    pub candidate_limit: usize,
    pub profile_digest: String,
    pub boundary: &'static str,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DiscoveryGrammarCatalogV5 {
    pub profile: DiscoveryGrammarProfileV5,
    pub candidates: Vec<DiscoveryObserverCandidateV5>,
    pub catalog_digest: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DiscoveryGrammarExtensionV5 {
    pub frozen_registry_digest: &'static str,
    pub extension_ordinal: u16,
    pub profile_digest: String,
    pub catalog_digest: String,
    pub extension_digest: String,
    pub boundary: &'static str,
}

fn profile() -> DiscoveryGrammarProfileV5 {
    diagnostics::event("GRAMMAR_V5_PROFILE_ENTER", "constructing discovery profile");
    let body = format!(
        "{DISCOVERY_GRAMMAR_V5_SCHEMA}:{DISCOVERY_GRAMMAR_V5_PROFILE_ID}:{GRAMMAR_REGISTRY_DIGEST}:2048:16"
    );
    let result = DiscoveryGrammarProfileV5 {
        schema: DISCOVERY_GRAMMAR_V5_SCHEMA,
        profile_id: DiscoveryGrammarProfileIdV5::AffineParityReflectionV5,
        parent_registry_digest: GRAMMAR_REGISTRY_DIGEST,
        candidate_limit: 2_048,
        profile_digest: domain_sha256_hex(PROFILE_DOMAIN, body.as_bytes()),
        boundary: DISCOVERY_GRAMMAR_V5_BOUNDARY,
    };
    diagnostics::event("GRAMMAR_V5_PROFILE_EXIT", "discovery profile constructed");
    result
}

fn response_digest(term: DiscoveryObserverTermV5) -> String {
    let responses: [u8; 16] = std::array::from_fn(|state| term.response(state as u8));
    domain_sha256_hex(CANDIDATE_DOMAIN, &responses)
}

fn raw_terms() -> Vec<DiscoveryObserverTermV5> {
    diagnostics::event("GRAMMAR_V5_TERMS_ENTER", "enumerating discovery terms");
    let mut terms = Vec::with_capacity(2_048);
    for multiplier in (1..16).step_by(2) {
        for shift in 0..16 {
            for mask in 1..16 {
                terms.push(DiscoveryObserverTermV5::AffineBitParity {
                    multiplier,
                    shift,
                    mask,
                });
            }
        }
    }
    for multiplier in (1..16).step_by(2) {
        for shift in 0..16 {
            terms.push(DiscoveryObserverTermV5::AffineReflectionOrbit { multiplier, shift });
        }
    }
    diagnostics::event("GRAMMAR_V5_TERMS_EXIT", "discovery terms enumerated");
    terms
}

pub fn enumerate_discovery_grammar_v5(
    profile_id: DiscoveryGrammarProfileIdV5,
) -> Result<DiscoveryGrammarCatalogV5, SynthesisCoreError> {
    diagnostics::event("GRAMMAR_V5_ENUM_ENTER", "enumerating discovery catalog");
    if profile_id != DiscoveryGrammarProfileIdV5::AffineParityReflectionV5 {
        diagnostics::event("GRAMMAR_V5_ENUM_REJECT", "unknown discovery profile");
        return Err(SynthesisCoreError("unknown-discovery-grammar-profile-v5"));
    }
    let profile = profile();
    let mut rows: Vec<_> = raw_terms()
        .into_iter()
        .map(|term| {
            let response_digest = response_digest(term);
            let body = format!(
                "{}:{}:{response_digest}",
                term.cost(),
                term.canonical_body()
            );
            (term.cost(), body, term, response_digest)
        })
        .collect();
    rows.sort_by(|left, right| (left.0, &left.1).cmp(&(right.0, &right.1)));
    if rows.len() != profile.candidate_limit {
        diagnostics::event("GRAMMAR_V5_ENUM_REJECT", "discovery catalog size drifted");
        return Err(SynthesisCoreError("discovery-grammar-v5-size-drift"));
    }
    let candidates: Vec<_> = rows
        .into_iter()
        .enumerate()
        .map(
            |(ordinal, (cost, body, term, response_digest))| DiscoveryObserverCandidateV5 {
                ordinal,
                term,
                cost,
                response_digest,
                candidate_digest: domain_sha256_hex(CANDIDATE_DOMAIN, body.as_bytes()),
            },
        )
        .collect();
    let body = candidates
        .iter()
        .map(|row| row.candidate_digest.as_str())
        .collect::<Vec<_>>()
        .join(":");
    let result = DiscoveryGrammarCatalogV5 {
        profile,
        catalog_digest: domain_sha256_hex(CATALOG_DOMAIN, body.as_bytes()),
        candidates,
    };
    if result.profile.profile_digest != DISCOVERY_GRAMMAR_V5_PROFILE_DIGEST
        || result.catalog_digest != DISCOVERY_GRAMMAR_V5_CATALOG_DIGEST
    {
        diagnostics::event("GRAMMAR_V5_ENUM_REJECT", "discovery catalog pins drifted");
        return Err(SynthesisCoreError("discovery-grammar-v5-pin-drift"));
    }
    diagnostics::event("GRAMMAR_V5_ENUM_EXIT", "discovery catalog enumerated");
    Ok(result)
}

pub fn discovery_grammar_extension_v5() -> Result<DiscoveryGrammarExtensionV5, SynthesisCoreError> {
    diagnostics::event("GRAMMAR_V5_EXTENSION_ENTER", "binding grammar extension");
    let catalog =
        enumerate_discovery_grammar_v5(DiscoveryGrammarProfileIdV5::AffineParityReflectionV5)?;
    let body = format!(
        "{GRAMMAR_REGISTRY_DIGEST}:2:{}:{}",
        catalog.profile.profile_digest, catalog.catalog_digest
    );
    let result = DiscoveryGrammarExtensionV5 {
        frozen_registry_digest: GRAMMAR_REGISTRY_DIGEST,
        extension_ordinal: 2,
        profile_digest: catalog.profile.profile_digest,
        catalog_digest: catalog.catalog_digest,
        extension_digest: domain_sha256_hex(EXTENSION_DOMAIN, body.as_bytes()),
        boundary: DISCOVERY_GRAMMAR_V5_BOUNDARY,
    };
    if result.extension_digest != DISCOVERY_GRAMMAR_V5_EXTENSION_DIGEST {
        diagnostics::event(
            "GRAMMAR_V5_EXTENSION_REJECT",
            "grammar extension pin drifted",
        );
        return Err(SynthesisCoreError("discovery-grammar-v5-extension-drift"));
    }
    diagnostics::event("GRAMMAR_V5_EXTENSION_EXIT", "grammar extension bound");
    Ok(result)
}
