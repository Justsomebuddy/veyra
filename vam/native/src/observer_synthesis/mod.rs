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
mod grammar_profile;
mod hash;
mod joint_synthesis;
mod receipt;
mod representation_family;
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
    enumerate_observer_grammar, enumerate_observer_grammar_profile, grammar_config_for_profile,
    GrammarConfig, GrammarEnumeration, GrammarStratum, ObserverCandidate,
    ProfiledGrammarEnumeration, DEFAULT_CANDIDATES, DEFAULT_CANONICAL_BYTES,
    DEFAULT_CATALOG_DIGEST, DEFAULT_MAX_ROW_BYTES, DEFAULT_STRATA, PARITY_V2_CANDIDATES,
    PARITY_V2_CANONICAL_BYTES, PARITY_V2_CATALOG_DIGEST, PARITY_V2_CATALOG_DOMAIN,
    PARITY_V2_MAX_ROW_BYTES, PARITY_V2_STRATA,
};
pub use grammar_profile::{
    observer_grammar_profile, ObserverGrammarProfile, ObserverGrammarProfileId,
    GRAMMAR_PROFILE_SCHEMA, LEGACY_GRAMMAR_PROFILE_DIGEST, LEGACY_GRAMMAR_PROFILE_ID,
    PARITY_GRAMMAR_PROFILE_DIGEST, PARITY_GRAMMAR_PROFILE_ID,
};
pub use joint_synthesis::{
    synthesize_transform_and_observer, JointBudgetCutoff, JointSynthesisLedger,
    JointSynthesisLimits, JointSynthesisStatus, NativeJointSynthesisReportV1, NativeJointWinnerV1,
    NativePartitionTaskId, JOINT_SYNTHESIS_SCHEMA, MAX_JOINT_CANDIDATES,
    MAX_JOINT_RELATION_EVALUATIONS, MAX_JOINT_TRANSFORMS, PARITY_INPUT_DIGEST,
    PARITY_V2_JOINT_ORDER_DIGEST, PARITY_V2_XOR_TRACE_DIGEST, XOR_PARITY_TASK_DIGEST,
};
pub use receipt::{
    build_zero_positive_surprise_receipt, canonical_native_surprise_receipt_bytes,
    native_surprise_receipt_from_run, replay_native_surprise_receipt,
    NativeObserverSurpriseReceiptV1, NATIVE_SURPRISE_RECEIPT_SCHEMA,
};
pub use representation_family::{
    encoded_recurrences, enumerate_representation_family, evaluate_systematic_transport,
    survey_representation_family, NativeRepresentationFamilyV1, NativeRepresentationSurveyV1,
    NativeRepresentationTransformV1, NativeSystematicTransportV1,
    NativeTransportEquivalenceClassV1, FIRST_REPRESENTATION_TRANSFORM_DIGEST,
    LAST_REPRESENTATION_TRANSFORM_DIGEST, PARITY_XOR_PRESERVING_TRANSFORMS,
    PARITY_XOR_SURVEY_CLASSES, PARITY_XOR_SURVEY_DIGEST, REPRESENTATION_FAMILY_DIGEST,
    REPRESENTATION_FAMILY_ID, REPRESENTATION_FAMILY_SCHEMA, REPRESENTATION_TRANSFORMS,
};
pub use semantics::{
    echo, observe, EchoOutcome, Mark, Observation, ObserverObstruction, ObstructionCode, PathStep,
    Recurrence, ResponseValue, MAX_RECURRENCE_PULSES,
};
