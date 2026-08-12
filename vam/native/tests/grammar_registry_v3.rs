//! Public append-only grammar-registry compatibility checks.

use vam_native::observer_synthesis::{
    enumerate_observer_grammar, grammar_registry_v1, validate_registry_prefix, GrammarConfig,
    GrammarLifecycleV1, DEFAULT_CATALOG_DIGEST, GRAMMAR_REGISTRY_DIGEST, LEGACY_GRAMMAR_PROFILE_ID,
    LEGACY_REGISTRY_PREFIX_DIGEST, PARITY_GRAMMAR_PROFILE_ID,
};

#[test]
fn registry_chains_the_two_published_profiles_without_changing_legacy() {
    let registry = grammar_registry_v1().unwrap();
    assert_eq!(registry.registry_digest, GRAMMAR_REGISTRY_DIGEST);
    assert_eq!(
        registry.registry_digest,
        "f937c322be2fd20933a32993d5549009fbac6c23f80cae16964cdaaf653af8b5"
    );
    assert_eq!(
        LEGACY_REGISTRY_PREFIX_DIGEST,
        "6ea628f5924b82a2cb89b402beb08d762c4716ae2d4044ade3ceb21062bfdc0c"
    );
    assert_eq!(registry.entries.len(), 2);
    assert_eq!(registry.entries[0].profile_id(), LEGACY_GRAMMAR_PROFILE_ID);
    assert_eq!(registry.entries[1].profile_id(), PARITY_GRAMMAR_PROFILE_ID);
    assert_eq!(registry.entries[0].introduced_in(), "observer-synthesis-v1");
    assert_eq!(registry.entries[1].introduced_in(), "observer-synthesis-v2");
    assert_eq!(
        registry.entries[1].lifecycle(),
        GrammarLifecycleV1::ActiveImmutable
    );
    assert_eq!(registry.entries[0].catalog_digest(), DEFAULT_CATALOG_DIGEST);
    assert_eq!(
        enumerate_observer_grammar(GrammarConfig::default())
            .unwrap()
            .catalog_digest,
        DEFAULT_CATALOG_DIGEST
    );
    assert!(validate_registry_prefix(2, &registry.registry_digest));
    assert!(validate_registry_prefix(1, LEGACY_REGISTRY_PREFIX_DIGEST));
}
