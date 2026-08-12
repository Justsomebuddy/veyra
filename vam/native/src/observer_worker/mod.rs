//! Bounded isolated execution and authenticated replay for native observer receipts.

mod autonomous_replay_v4;
mod digest;
mod isolation_v4;
mod linux;
mod pipeline_replay_v3;
mod protocol;
mod replay;
mod replay_v2;
mod supervisor;
mod supervisor_v3;
mod supervisor_v4;
mod synthesis_v2;
mod worker_v2;

pub use autonomous_replay_v4::{
    build_autonomous_replay_package_from_worker_v4, build_autonomous_replay_package_v4,
    decode_autonomous_replay_package_v4, decode_autonomous_replay_package_v4_bytes,
    encode_autonomous_replay_package_v4, verify_autonomous_replay_package_v4,
    AutonomousReplayPackageV4, AutonomousReplayV4Error, ManifestEntryV4, ManifestKindV4,
    WorkerPolicyAndReceiptV4, WorkerPolicyManifestV4, WorkerProfileEvidenceV4,
    AUTONOMOUS_REPLAY_V4_BOUNDARY, AUTONOMOUS_REPLAY_V4_MAGIC, AUTONOMOUS_REPLAY_V4_SCHEMA,
    AUTONOMOUS_REPLAY_V4_VERSION, MAX_AUTONOMOUS_MANIFEST_ROWS_V4, MAX_AUTONOMOUS_REPLAY_V4_BYTES,
};
pub use pipeline_replay_v3::{
    build_ed25519_observer_pipeline_bundle_v3, build_hmac_observer_pipeline_bundle_v3,
    canonical_observer_pipeline_result_v3_bytes, decode_observer_pipeline_request_v3,
    encode_observer_pipeline_request_v3, MAX_PIPELINE_REQUEST_V3_BYTES,
    MAX_PIPELINE_RESULT_V3_BYTES,
};
pub use protocol::{
    decode_worker_receipt, encode_request_frame, encode_worker_receipt_frame, IsolationProfile,
    NativeWorkerReceiptV1, NativeWorkerRequestV1, NativeWorkerStatus, NATIVE_WORKER_BOUNDARY,
};
pub use replay::{
    build_portable_replay_package, decode_portable_replay_package, encode_portable_replay_package,
    replay_portable_package, validate_portable_replay_package, PortableReplayPackageV1,
    MAX_PORTABLE_REPLAY_BYTES, PORTABLE_REPLAY_BOUNDARY,
};
pub use replay_v2::{
    build_ed25519_replay_bundle_v2, build_hmac_replay_bundle_v2, decode_replay_bundle_v2,
    decode_replay_bundle_v2_bytes, decode_replay_bundle_v2_exact, ed25519_key_id,
    encode_replay_bundle_v2, verify_replay_bundle_v2, Ed25519ReplayTrustV2, HmacReplayTrustV2,
    ReplayAuthAlgorithmV2, ReplayBundleV2, ReplayPayloadKindV2, ReplayTrustPolicyV2,
    ReplayTrustResolverV2, ReplayV2Error, MAX_REPLAY_BUNDLE_V2_BYTES, MAX_REPLAY_V2_LABEL_BYTES,
    MAX_REPLAY_V2_RECEIPT_BYTES, MAX_REPLAY_V2_REQUEST_BYTES, REPLAY_V2_BOUNDARY, REPLAY_V2_MAGIC,
    REPLAY_V2_VERSION,
};
pub use supervisor::{run_child_entry, supervise_current_executable, NativeWorkerError};
pub use supervisor_v3::{
    run_observer_pipeline_child_v3, supervise_observer_pipeline_v3, ObserverWorkerControlsV3,
    ObserverWorkerLimitsV3, ObserverWorkerReceiptV3, ObserverWorkerStatusV3, ObserverWorkerV3Error,
    OBSERVER_WORKER_V3_BOUNDARY,
};
pub use supervisor_v4::{
    run_observer_pipeline_child_v4, supervise_observer_pipeline_v4, IsolationProfileV4,
    ObserverWorkerControlsV4, ObserverWorkerLaunchV4, ObserverWorkerLimitsV4,
    ObserverWorkerReceiptV4, ObserverWorkerV4Error, OBSERVER_WORKER_V4_BOUNDARY,
};
pub use synthesis_v2::{
    build_observer_synthesis_v2_receipt, replay_observer_synthesis_v2_receipt,
    ObserverSynthesisV2Receipt, OBSERVER_SYNTHESIS_V2_BOUNDARY,
    OBSERVER_SYNTHESIS_V2_RECEIPT_DIGEST_HEX, OBSERVER_SYNTHESIS_V2_SCHEMA,
};
pub use worker_v2::{
    apply_worker_v2_child_controls, inspect_worker_v2_capabilities, WorkerControlEvidenceV2,
    WorkerControlStateV2, WorkerV2Admission, WorkerV2CapabilityReport, WorkerV2Error,
    WorkerV2LaunchOptions, WorkerV2Limits, WorkerV2Policy,
};

pub(crate) fn event(code: &'static str, detail: &'static str) {
    if std::env::var("VEYRA_NATIVE_DEBUG")
        .map(|value| matches!(value.as_str(), "1" | "true" | "TRUE" | "yes" | "YES"))
        .unwrap_or(false)
    {
        eprintln!("[veyra-native][observer-worker] {code} {detail}");
    }
}
