//! Closed, versioned observer-grammar profiles.
//!
//! A profile is an immutable language/catalog contract, not a caller-defined
//! primitive list. This keeps legacy catalog and receipt identities stable.

use super::ast::PrimitiveId;
use super::diagnostics;
use super::hash::domain_sha256_hex;

pub const GRAMMAR_PROFILE_SCHEMA: &str = "veyra.native-observer-grammar-profile.v1";
const GRAMMAR_PROFILE_DOMAIN: &str = "veyra.native-observer-grammar-profile.v1.binding";

pub const LEGACY_GRAMMAR_PROFILE_ID: &str = "r14-tail-crest-pair-v1";
pub const PARITY_GRAMMAR_PROFILE_ID: &str = "r14-tail-crest-parity-pair-v2";
pub const LEGACY_GRAMMAR_PROFILE_DIGEST: &str =
    "c0c6b1706a73655c9438a7249d0bad2ea4ad9c6c39a8078d2d1f35b47209d63e";
pub const PARITY_GRAMMAR_PROFILE_DIGEST: &str =
    "9ffad357ca724932ffafee3b11e47c81f88dd73c3b7415e3fccebc1748eb089b";

const LEGACY_PRIMITIVES: [PrimitiveId; 2] = [PrimitiveId::Tail, PrimitiveId::Crest];
const PARITY_PRIMITIVES: [PrimitiveId; 3] =
    [PrimitiveId::Tail, PrimitiveId::Crest, PrimitiveId::Parity];

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ObserverGrammarProfileId {
    LegacyV1,
    ParityV2,
}

impl ObserverGrammarProfileId {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::LegacyV1 => LEGACY_GRAMMAR_PROFILE_ID,
            Self::ParityV2 => PARITY_GRAMMAR_PROFILE_ID,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObserverGrammarProfile {
    pub schema: &'static str,
    pub profile_id: ObserverGrammarProfileId,
    pub max_cost: usize,
    pub max_depth: usize,
    pub candidate_limit: usize,
    pub canonical_bytes_limit: usize,
    pub profile_digest: String,
    pub boundary: &'static str,
}

impl ObserverGrammarProfile {
    pub const fn primitives(&self) -> &'static [PrimitiveId] {
        match self.profile_id {
            ObserverGrammarProfileId::LegacyV1 => &LEGACY_PRIMITIVES,
            ObserverGrammarProfileId::ParityV2 => &PARITY_PRIMITIVES,
        }
    }
}

fn profile_body(profile: ObserverGrammarProfileId) -> String {
    diagnostics::event("GRAMMAR_PROFILE_JSON_ENTER", "encoding grammar profile");
    let (max_cost, primitives) = match profile {
        ObserverGrammarProfileId::LegacyV1 => (6, "[\"tail\",\"crest\"]"),
        ObserverGrammarProfileId::ParityV2 => (4, "[\"tail\",\"crest\",\"parity\"]"),
    };
    let result = format!(
        "{{\"candidate_limit\":2048,\"canonical_bytes_limit\":8388608,\"max_cost\":{max_cost},\"max_depth\":4,\"primitive_order\":{primitives},\"profile_id\":\"{}\",\"schema\":\"{GRAMMAR_PROFILE_SCHEMA}\"}}",
        profile.as_str(),
    );
    diagnostics::event("GRAMMAR_PROFILE_JSON_EXIT", "grammar profile encoded");
    result
}

pub fn observer_grammar_profile(profile_id: ObserverGrammarProfileId) -> ObserverGrammarProfile {
    diagnostics::event(
        "GRAMMAR_PROFILE_ENTER",
        "constructing closed grammar profile",
    );
    let max_cost = match profile_id {
        ObserverGrammarProfileId::LegacyV1 => 6,
        ObserverGrammarProfileId::ParityV2 => 4,
    };
    let body = profile_body(profile_id);
    let result = ObserverGrammarProfile {
        schema: GRAMMAR_PROFILE_SCHEMA,
        profile_id,
        max_cost,
        max_depth: 4,
        candidate_limit: 2_048,
        canonical_bytes_limit: 8 * 1024 * 1024,
        profile_digest: domain_sha256_hex(GRAMMAR_PROFILE_DOMAIN, body.as_bytes()),
        boundary: "closed finite observer syntax and exact enumeration order; profile identity does not establish semantic completeness, minimality, or theoremhood",
    };
    diagnostics::event("GRAMMAR_PROFILE_EXIT", "closed grammar profile constructed");
    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn legacy_and_parity_profiles_are_disjoint_and_closed() {
        let legacy = observer_grammar_profile(ObserverGrammarProfileId::LegacyV1);
        let parity = observer_grammar_profile(ObserverGrammarProfileId::ParityV2);
        assert_eq!(legacy.profile_id.as_str(), LEGACY_GRAMMAR_PROFILE_ID);
        assert_eq!(legacy.primitives(), &LEGACY_PRIMITIVES);
        assert_eq!(parity.primitives(), &PARITY_PRIMITIVES);
        assert_ne!(legacy.profile_digest, parity.profile_digest);
        assert_eq!(legacy.profile_digest, LEGACY_GRAMMAR_PROFILE_DIGEST);
        assert_eq!(parity.profile_digest, PARITY_GRAMMAR_PROFILE_DIGEST);
        assert_eq!(legacy.max_cost, 6);
        assert_eq!(parity.max_cost, 4);
    }
}
