//! Dependency-free Rust shadow of the closed R11/R14 observer-synthesis core.
//!
//! This module is finite calibration infrastructure.  It does not replace the
//! Python oracle, claim general synthesis, or alter the VAM execution profile.

mod ast;
mod benchmark;
mod benchmark_marginals;
mod benchmark_suite;
mod benchmark_suite_receipt;
mod benchmark_transport;
mod budget;
mod canonical;
mod cegis;
mod diagnostics;
mod grammar;
mod hash;
mod receipt;
mod semantics;

pub use ast::{infer_observer_kind, ObserverExpr, PrimitiveId, ResponseKind, SynthesisCoreError};
pub use benchmark::{
    synthesize_zero_positive_surprise, zero_positive_surprise_benchmark, NativeSurpriseBenchmark,
    NativeSurpriseRun, NativeSurpriseScore, NativeSurpriseWitness, NATIVE_SURPRISE_BOUNDARY,
    ZERO_POSITIVE_BENCHMARK_ID,
};
pub use benchmark_marginals::NativeBitMarginalBalanceV1;
pub use benchmark_suite::{
    native_observer_benchmarks, run_native_benchmark_suite, NativeBenchmarkExpectation,
    NativeBenchmarkExperimentRun, NativeBenchmarkRowReceiptV1, NativeBenchmarkScore,
    NativeBenchmarkSuiteReceiptV1, NativeBenchmarkSuiteRun, NativeBenchmarkWinnerReceiptV1,
    NativeEncodedState, NativeObserverBenchmark, MIXTURE_BENCHMARK_ID,
    NATIVE_BENCHMARK_SUITE_BOUNDARY, NATIVE_BENCHMARK_SUITE_SCHEMA,
    PERMUTED_TRANSPORT_BENCHMARK_ID, SHIFT_TRANSPORT_BENCHMARK_ID, XOR_PARITY_BENCHMARK_ID,
};
pub use benchmark_suite_receipt::{
    build_native_benchmark_suite_receipt, canonical_native_benchmark_suite_receipt_bytes,
    replay_native_benchmark_suite_receipt,
};
pub use benchmark_transport::NativeRepresentationTransportReceiptV1;
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
pub use receipt::{
    build_zero_positive_surprise_receipt, canonical_native_surprise_receipt_bytes,
    native_surprise_receipt_from_run, replay_native_surprise_receipt,
    NativeObserverSurpriseReceiptV1, NATIVE_SURPRISE_RECEIPT_SCHEMA,
};
pub use semantics::{
    echo, observe, EchoOutcome, Mark, Observation, ObserverObstruction, ObstructionCode, PathStep,
    Recurrence, ResponseValue, MAX_RECURRENCE_PULSES,
};
