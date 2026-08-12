//! Focused child-local worker-v2 control probe.

use std::process;

use vam_native::observer_worker::{
    apply_worker_v2_child_controls, inspect_worker_v2_capabilities, WorkerV2LaunchOptions,
    WorkerV2Limits, WorkerV2Policy,
};

fn main() {
    let arguments = std::env::args().collect::<Vec<_>>();
    let options = WorkerV2LaunchOptions::default();
    let result = match arguments.as_slice() {
        [_, command] if command == "--baseline-child-probe" => apply_worker_v2_child_controls(
            WorkerV2Policy::Baseline,
            WorkerV2Limits::default(),
            &options,
        ),
        [_, command] if command == "--strict-preflight" => Ok(inspect_worker_v2_capabilities(
            WorkerV2Policy::Strict,
            &options,
        )),
        _ => Err(vam_native::observer_worker::WorkerV2Error(
            "worker-v2-probe-usage",
        )),
    };
    match result {
        Ok(report) => print!("{}", report.canonical_text()),
        Err(error) => {
            eprintln!("vam-observer-worker-v2 blocked: {error}");
            process::exit(1);
        }
    }
}
