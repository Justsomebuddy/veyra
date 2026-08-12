//! Fixed child entry for the physically bounded observer-pipeline lane.

use std::process;

use vam_native::observer_worker::{run_observer_pipeline_child_v3, WorkerV2Limits};

fn event(code: &'static str, detail: &'static str) {
    if std::env::var("VEYRA_NATIVE_DEBUG")
        .map(|value| matches!(value.as_str(), "1" | "true" | "TRUE" | "yes" | "YES"))
        .unwrap_or(false)
    {
        eprintln!("[veyra-native][observer-pipeline-worker] {code} {detail}");
    }
}

fn parse_limits(arguments: &[String]) -> Result<WorkerV2Limits, &'static str> {
    event("WORKER_V3_BIN_PARSE_ENTER", "parsing child limits");
    let [_, command, cpu, address_space] = arguments else {
        return Err("worker-v3-usage");
    };
    if command != "--child" {
        return Err("worker-v3-usage");
    }
    let cpu_seconds = cpu.parse::<u32>().map_err(|_| "worker-v3-usage")?;
    let address_space_bytes = address_space
        .parse::<u64>()
        .map_err(|_| "worker-v3-usage")?;
    event("WORKER_V3_BIN_PARSE_EXIT", "child limits parsed");
    Ok(WorkerV2Limits {
        cpu_seconds,
        address_space_bytes,
    })
}

fn main() {
    event("WORKER_V3_BIN_ENTER", "fixed child started");
    let arguments = std::env::args().collect::<Vec<_>>();
    let result = parse_limits(&arguments).and_then(|limits| {
        run_observer_pipeline_child_v3(std::io::stdin().lock(), std::io::stdout().lock(), limits)
            .map_err(|error| error.0)
    });
    if let Err(reason) = result {
        eprintln!("vam-observer-pipeline-worker blocked: {reason}");
        process::exit(1);
    }
    event("WORKER_V3_BIN_EXIT", "fixed child completed");
}
