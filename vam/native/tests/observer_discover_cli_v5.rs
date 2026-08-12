//! Product-boundary tests for the deterministic discovery-v5 CLI.

use std::io::Write;
use std::process::{Command, Stdio};

use vam_native::observer_synthesis::{
    canonical_discovery_request_v5_bytes, DiscoveryBenchmarkIdV5, DiscoverySearchRequestV5,
};

fn binary() -> &'static str {
    env!("CARGO_BIN_EXE_vam-observer-discover-v5")
}

#[test]
fn exact_benchmark_mode_is_deterministic_and_exposes_product_roots() {
    let run = || {
        Command::new(binary())
            .args(["--benchmark", "held-out-affine-v5"])
            .output()
            .unwrap()
    };
    let first = run();
    let second = run();
    assert!(first.status.success());
    assert_eq!(first.stdout, second.stdout);
    assert!(first.stderr.is_empty());
    let summary = String::from_utf8(first.stdout).unwrap();
    for required in [
        "\"ok\":true",
        "\"benchmark_split\":\"SYNTHETIC_HELD_OUT\"",
        "\"status\":\"FOUND\"",
        "\"representation_root\"",
        "\"observer_root\"",
        "\"explanation_root\"",
        "\"observer_gap\"",
        "\"alternatives_at_same_cost\"",
        "\"prune_proof_root\"",
        "\"package_mode\":false",
    ] {
        assert!(summary.contains(required), "missing {required}");
    }
}

#[test]
fn canonical_request_stdin_matches_exact_id_and_rejects_noncanonical_bytes() {
    let request = DiscoverySearchRequestV5::systematic(DiscoveryBenchmarkIdV5::HiddenAffine);
    let bytes = canonical_discovery_request_v5_bytes(&request).unwrap();
    let mut child = Command::new(binary())
        .arg("--request-stdin")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .unwrap();
    child.stdin.take().unwrap().write_all(&bytes).unwrap();
    let stdin_run = child.wait_with_output().unwrap();
    let id_run = Command::new(binary())
        .args(["--benchmark", "hidden-affine-v5"])
        .output()
        .unwrap();
    assert!(stdin_run.status.success());
    assert_eq!(stdin_run.stdout, id_run.stdout);

    let mut rejected = Command::new(binary())
        .arg("--request-stdin")
        .stdin(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    rejected
        .stdin
        .take()
        .unwrap()
        .write_all(b"not-canonical")
        .unwrap();
    let rejected = rejected.wait_with_output().unwrap();
    assert_eq!(rejected.status.code(), Some(2));
    assert!(String::from_utf8(rejected.stderr)
        .unwrap()
        .contains("invalid-canonical-request"));
}
