//! Dependency-free isolated execution and portable replay for native observer receipts.

mod digest;
mod linux;
mod protocol;
mod replay;
mod supervisor;
mod synthesis_v2;

pub use protocol::{
    decode_worker_receipt, encode_request_frame, encode_worker_receipt_frame, IsolationProfile,
    NativeWorkerReceiptV1, NativeWorkerRequestV1, NativeWorkerStatus, NATIVE_WORKER_BOUNDARY,
};
pub use replay::{
    build_portable_replay_package, decode_portable_replay_package, encode_portable_replay_package,
    replay_portable_package, validate_portable_replay_package, PortableReplayPackageV1,
    MAX_PORTABLE_REPLAY_BYTES, PORTABLE_REPLAY_BOUNDARY,
};
pub use supervisor::{run_child_entry, supervise_current_executable, NativeWorkerError};
pub use synthesis_v2::{
    build_observer_synthesis_v2_receipt, replay_observer_synthesis_v2_receipt,
    ObserverSynthesisV2Receipt, OBSERVER_SYNTHESIS_V2_BOUNDARY,
    OBSERVER_SYNTHESIS_V2_RECEIPT_DIGEST_HEX, OBSERVER_SYNTHESIS_V2_SCHEMA,
};

pub(crate) fn event(code: &'static str, detail: &'static str) {
    if std::env::var("VEYRA_NATIVE_DEBUG")
        .map(|value| matches!(value.as_str(), "1" | "true" | "TRUE" | "yes" | "YES"))
        .unwrap_or(false)
    {
        eprintln!("[veyra-native][observer-worker] {code} {detail}");
    }
}
