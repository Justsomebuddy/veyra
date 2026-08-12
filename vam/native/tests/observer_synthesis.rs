//! Public-crate boundary checks for the bounded observer-synthesis slice.

use vam_native::observer_synthesis::{
    default_train_cases, enumerate_observer_grammar, fit_observer_cegis, observer_digest,
    BudgetLimits, GrammarConfig, ObserverExpr, PrimitiveId, SynthesisStatus,
    DEFAULT_CATALOG_DIGEST,
};

#[test]
fn public_api_replays_the_pinned_default_calibration() {
    let catalog = enumerate_observer_grammar(GrammarConfig::default()).unwrap();
    assert_eq!(catalog.catalog_digest, DEFAULT_CATALOG_DIGEST);

    let report = fit_observer_cegis(&catalog, &default_train_cases(), BudgetLimits::default());
    assert_eq!(report.status, SynthesisStatus::Found);
    let winner = report.winner.expect("default calibration has a winner");
    assert_eq!(winner.ordinal, 1);
    assert_eq!(
        winner.digest,
        observer_digest(&ObserverExpr::apply(
            PrimitiveId::Crest,
            ObserverExpr::Input,
        ))
        .unwrap()
    );
}

#[test]
fn public_api_preserves_cutoff_as_incomplete() {
    let catalog = enumerate_observer_grammar(GrammarConfig::default()).unwrap();
    let limits = BudgetLimits {
        evaluation_limit: 1,
        ..BudgetLimits::default()
    };
    let report = fit_observer_cegis(&catalog, &default_train_cases(), limits);
    assert_eq!(report.status, SynthesisStatus::Incomplete);
    assert_eq!(report.detail, "evaluation-limit");
    assert!(report.winner.is_none());
}
