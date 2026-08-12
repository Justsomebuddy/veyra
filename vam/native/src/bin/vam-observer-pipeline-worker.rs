//! Fixed child entry for the physically bounded observer-pipeline lane.

use std::process;

use std::path::PathBuf;

use vam_native::observer_worker::{
    run_observer_pipeline_child_v3, run_observer_pipeline_child_v4, IsolationProfileV4,
    WorkerV2Limits,
};

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

fn parse_v4(
    arguments: &[String],
) -> Result<(IsolationProfileV4, WorkerV2Limits, Option<PathBuf>), &'static str> {
    event("WORKER_V4_BIN_PARSE_ENTER", "parsing v4 child controls");
    if !(arguments.len() == 5 || arguments.len() == 6) || arguments[1] != "--child-v4" {
        event("WORKER_V4_BIN_PARSE_REJECT", "invalid v4 child arguments");
        return Err("worker-v4-usage");
    }
    let profile = match arguments[2].as_str() {
        "1" => IsolationProfileV4::Isolated,
        "2" => IsolationProfileV4::Strict,
        _ => {
            event("WORKER_V4_BIN_PARSE_REJECT", "invalid v4 isolation profile");
            return Err("worker-v4-usage");
        }
    };
    let cpu_seconds = arguments[3].parse::<u32>().map_err(|_| "worker-v4-usage")?;
    let address_space_bytes = arguments[4].parse::<u64>().map_err(|_| "worker-v4-usage")?;
    let cgroup = arguments.get(5).map(PathBuf::from);
    if (profile == IsolationProfileV4::Strict) != cgroup.is_some() {
        event(
            "WORKER_V4_BIN_PARSE_REJECT",
            "cgroup/profile shape mismatch",
        );
        return Err("worker-v4-usage");
    }
    event("WORKER_V4_BIN_PARSE_EXIT", "v4 child controls parsed");
    Ok((
        profile,
        WorkerV2Limits {
            cpu_seconds,
            address_space_bytes,
        },
        cgroup,
    ))
}

fn main() {
    event("WORKER_V3_BIN_ENTER", "fixed child started");
    let arguments = std::env::args().collect::<Vec<_>>();
    let result = if arguments.get(1).map(String::as_str) == Some("--child-v4") {
        parse_v4(&arguments).and_then(|(profile, limits, cgroup)| {
            run_observer_pipeline_child_v4(
                std::io::stdin().lock(),
                std::io::stdout().lock(),
                profile,
                limits,
                cgroup.as_deref(),
            )
            .map_err(|error| error.0)
        })
    } else {
        parse_limits(&arguments).and_then(|limits| {
            run_observer_pipeline_child_v3(
                std::io::stdin().lock(),
                std::io::stdout().lock(),
                limits,
            )
            .map_err(|error| error.0)
        })
    };
    if let Err(reason) = result {
        eprintln!("vam-observer-pipeline-worker blocked: {reason}");
        process::exit(1);
    }
    event("WORKER_V3_BIN_EXIT", "fixed child completed");
}
