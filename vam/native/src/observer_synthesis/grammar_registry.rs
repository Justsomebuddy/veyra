//! Append-only registry for immutable observer-grammar profiles.

use super::ast::SynthesisCoreError;
use super::diagnostics;
use super::grammar::{
    enumerate_observer_grammar_profile, grammar_config_for_profile, ProfiledGrammarEnumeration,
};
use super::grammar_profile::{
    ObserverGrammarProfileId, LEGACY_GRAMMAR_PROFILE_ID, PARITY_GRAMMAR_PROFILE_ID,
};
use super::hash::domain_sha256_hex;

pub const GRAMMAR_REGISTRY_SCHEMA: &str = "veyra.native-observer-grammar-registry.v1";
pub const LEGACY_REGISTRY_PREFIX_DIGEST: &str =
    "6ea628f5924b82a2cb89b402beb08d762c4716ae2d4044ade3ceb21062bfdc0c";
pub const GRAMMAR_REGISTRY_DIGEST: &str =
    "f937c322be2fd20933a32993d5549009fbac6c23f80cae16964cdaaf653af8b5";
const ENTRY_DOMAIN: &str = "veyra.native-observer-grammar-registry.entry.v1.binding";
const REGISTRY_DOMAIN: &str = "veyra.native-observer-grammar-registry.v1.binding";

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum GrammarLifecycleV1 {
    ActiveImmutable,
}

impl GrammarLifecycleV1 {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::ActiveImmutable => "ACTIVE_IMMUTABLE",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GrammarRegistryEntryV1 {
    ordinal: u16,
    profile_id: &'static str,
    parent_profile_id: Option<&'static str>,
    introduced_in: &'static str,
    lifecycle: GrammarLifecycleV1,
    profile_digest: String,
    catalog_digest: String,
    candidate_count: u32,
    canonical_bytes: u64,
    previous_entry_digest: Option<String>,
    entry_digest: String,
}

impl GrammarRegistryEntryV1 {
    pub const fn ordinal(&self) -> u16 {
        self.ordinal
    }
    pub const fn profile_id(&self) -> &'static str {
        self.profile_id
    }
    pub const fn parent_profile_id(&self) -> Option<&'static str> {
        self.parent_profile_id
    }
    pub const fn introduced_in(&self) -> &'static str {
        self.introduced_in
    }
    pub const fn lifecycle(&self) -> GrammarLifecycleV1 {
        self.lifecycle
    }
    pub fn profile_digest(&self) -> &str {
        &self.profile_digest
    }
    pub fn catalog_digest(&self) -> &str {
        &self.catalog_digest
    }
    pub const fn candidate_count(&self) -> u32 {
        self.candidate_count
    }
    pub const fn canonical_bytes(&self) -> u64 {
        self.canonical_bytes
    }
    pub fn previous_entry_digest(&self) -> Option<&str> {
        self.previous_entry_digest.as_deref()
    }
    pub fn entry_digest(&self) -> &str {
        &self.entry_digest
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GrammarRegistryReceiptV1 {
    pub schema: &'static str,
    pub entries: Vec<GrammarRegistryEntryV1>,
    pub registry_digest: String,
    pub boundary: &'static str,
}

fn profile_id(value: &str) -> Result<ObserverGrammarProfileId, SynthesisCoreError> {
    match value {
        LEGACY_GRAMMAR_PROFILE_ID => Ok(ObserverGrammarProfileId::LegacyV1),
        PARITY_GRAMMAR_PROFILE_ID => Ok(ObserverGrammarProfileId::ParityV2),
        _ => Err(SynthesisCoreError("unknown-grammar-profile")),
    }
}

fn entry_body(entry: &GrammarRegistryEntryV1) -> Vec<u8> {
    format!(
        "{{\"canonical_bytes\":{},\"candidate_count\":{},\"catalog_digest\":\"{}\",\"introduced_in\":\"{}\",\"lifecycle\":\"{}\",\"ordinal\":{},\"parent_profile_id\":{},\"previous_entry_digest\":{},\"profile_digest\":\"{}\",\"profile_id\":\"{}\",\"schema\":\"{GRAMMAR_REGISTRY_SCHEMA}\"}}",
        entry.canonical_bytes,
        entry.candidate_count,
        entry.catalog_digest,
        entry.introduced_in,
        entry.lifecycle.as_str(),
        entry.ordinal,
        entry.parent_profile_id.map_or_else(|| "null".to_owned(), |value| format!("\"{value}\"")),
        entry.previous_entry_digest.as_ref().map_or_else(|| "null".to_owned(), |value| format!("\"{value}\"")),
        entry.profile_digest,
        entry.profile_id,
    ).into_bytes()
}

pub fn enumerate_registered_grammar(
    profile_key: &str,
) -> Result<ProfiledGrammarEnumeration, SynthesisCoreError> {
    diagnostics::event(
        "GRAMMAR_REGISTRY_ENUM_ENTER",
        "enumerating registered profile",
    );
    let id = profile_id(profile_key).inspect_err(|_| {
        diagnostics::event("GRAMMAR_REGISTRY_ENUM_REJECT", "profile is not registered")
    })?;
    let result = enumerate_observer_grammar_profile(id, grammar_config_for_profile(id));
    diagnostics::event(
        if result.is_ok() {
            "GRAMMAR_REGISTRY_ENUM_EXIT"
        } else {
            "GRAMMAR_REGISTRY_ENUM_REJECT"
        },
        "registered profile enumeration completed",
    );
    result
}

pub fn grammar_registry_v1() -> Result<GrammarRegistryReceiptV1, SynthesisCoreError> {
    diagnostics::event(
        "GRAMMAR_REGISTRY_ENTER",
        "building append-only grammar registry",
    );
    let specs = [
        (LEGACY_GRAMMAR_PROFILE_ID, None, "observer-synthesis-v1"),
        (
            PARITY_GRAMMAR_PROFILE_ID,
            Some(LEGACY_GRAMMAR_PROFILE_ID),
            "observer-synthesis-v2",
        ),
    ];
    let mut entries = Vec::with_capacity(specs.len());
    for (ordinal, (key, parent, introduced_in)) in specs.into_iter().enumerate() {
        let enumeration = enumerate_registered_grammar(key)?;
        let mut entry = GrammarRegistryEntryV1 {
            ordinal: ordinal as u16,
            profile_id: key,
            parent_profile_id: parent,
            introduced_in,
            lifecycle: GrammarLifecycleV1::ActiveImmutable,
            profile_digest: enumeration.profile.profile_digest,
            catalog_digest: enumeration.enumeration.catalog_digest,
            candidate_count: enumeration.enumeration.candidates.len() as u32,
            canonical_bytes: enumeration.enumeration.canonical_bytes as u64,
            previous_entry_digest: entries
                .last()
                .map(|row: &GrammarRegistryEntryV1| row.entry_digest.clone()),
            entry_digest: String::new(),
        };
        entry.entry_digest = domain_sha256_hex(ENTRY_DOMAIN, &entry_body(&entry));
        entries.push(entry);
    }
    let last = entries
        .last()
        .ok_or(SynthesisCoreError("empty-grammar-registry"))?;
    let body = format!(
        "{{\"count\":{},\"last_entry_digest\":\"{}\",\"schema\":\"{GRAMMAR_REGISTRY_SCHEMA}\"}}",
        entries.len(),
        last.entry_digest,
    );
    let result = GrammarRegistryReceiptV1 {
        schema: GRAMMAR_REGISTRY_SCHEMA,
        entries,
        registry_digest: domain_sha256_hex(REGISTRY_DOMAIN, body.as_bytes()),
        boundary: "append-only registry of two already-published closed profiles; registry inclusion does not prove completeness, deprecation safety, or scientific adequacy",
    };
    diagnostics::event(
        "GRAMMAR_REGISTRY_EXIT",
        "append-only grammar registry built",
    );
    Ok(result)
}

pub fn validate_registry_prefix(count: u16, expected_digest: &str) -> bool {
    diagnostics::event(
        "GRAMMAR_REGISTRY_PREFIX_ENTER",
        "validating registry prefix",
    );
    let result = grammar_registry_v1().ok().and_then(|registry| {
        let prefix = registry.entries.get(count.checked_sub(1)? as usize)?;
        let body = format!(
            "{{\"count\":{count},\"last_entry_digest\":\"{}\",\"schema\":\"{GRAMMAR_REGISTRY_SCHEMA}\"}}",
            prefix.entry_digest,
        );
        Some(domain_sha256_hex(REGISTRY_DOMAIN, body.as_bytes()) == expected_digest)
    }).unwrap_or(false);
    diagnostics::event(
        if result {
            "GRAMMAR_REGISTRY_PREFIX_EXIT"
        } else {
            "GRAMMAR_REGISTRY_PREFIX_REJECT"
        },
        "registry prefix validated",
    );
    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn registry_is_ordered_chained_and_unknown_profiles_fail() {
        let registry = grammar_registry_v1().unwrap();
        assert_eq!(registry.registry_digest, GRAMMAR_REGISTRY_DIGEST);
        assert_eq!(registry.entries.len(), 2);
        assert_eq!(registry.entries[0].profile_id(), LEGACY_GRAMMAR_PROFILE_ID);
        assert_eq!(
            registry.entries[1].parent_profile_id(),
            Some(LEGACY_GRAMMAR_PROFILE_ID)
        );
        assert_eq!(
            registry.entries[1].previous_entry_digest(),
            Some(registry.entries[0].entry_digest())
        );
        assert!(enumerate_registered_grammar("not-registered").is_err());
        assert!(validate_registry_prefix(2, &registry.registry_digest));
        assert!(validate_registry_prefix(1, LEGACY_REGISTRY_PREFIX_DIGEST));
        assert!(!validate_registry_prefix(0, &registry.registry_digest));
    }
}
