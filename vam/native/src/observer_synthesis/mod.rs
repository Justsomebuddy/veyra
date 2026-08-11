//! Dependency-free Rust shadow of the closed R11/R14 observer-synthesis core.
//!
//! This module is finite calibration infrastructure.  It does not replace the
//! Python oracle, claim general synthesis, or alter the VAM execution profile.

mod ast;
mod budget;
mod canonical;
mod cegis;
mod diagnostics;
mod grammar;
mod hash;
mod semantics;

pub use ast::{infer_observer_kind, ObserverExpr, PrimitiveId, ResponseKind, SynthesisCoreError};
pub use budget::{
    BudgetCutoff, BudgetLedger, BudgetLimits, BudgetSnapshot, MAX_CANDIDATES, MAX_CANONICAL_BYTES,
    MAX_EVALUATIONS, MAX_OUTPUT_BYTES,
};
pub use canonical::{canonical_observer_bytes, observer_digest};
pub use cegis::{
    default_train_cases, fit_observer_cegis, CegisEvent, CegisTraceStep, ExpectedRelation,
    LockedObserverWinner, ObserverCase, SynthesisReport, SynthesisStatus, CEGIS_BOUNDARY,
};
pub use grammar::{
    enumerate_observer_grammar, GrammarConfig, GrammarEnumeration, GrammarStratum,
    ObserverCandidate, DEFAULT_CANDIDATES, DEFAULT_CANONICAL_BYTES, DEFAULT_CATALOG_DIGEST,
    DEFAULT_MAX_ROW_BYTES, DEFAULT_STRATA,
};
pub use semantics::{
    echo, observe, EchoOutcome, Mark, Observation, ObserverObstruction, ObstructionCode, PathStep,
    Recurrence, ResponseValue, MAX_RECURRENCE_PULSES,
};
