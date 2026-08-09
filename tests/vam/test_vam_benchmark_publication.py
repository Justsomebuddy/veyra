"""Publication regressions for VAM benchmark runner labels."""

from __future__ import annotations

import argparse
import logging

from vam.benchmarks import battle_benchmark, semantic_parity

logger = logging.getLogger(__name__)


def test_battle_runner_labels_never_publish_host_paths() -> None:
    """Stored benchmark details expose a basename or repository-relative label."""
    logger.debug("test_battle_runner_labels_never_publish_host_paths entry")
    assert battle_benchmark.public_runner_label(("/private/location/custom-runner",)) == (
        "custom-runner"
    )
    assert battle_benchmark.public_runner_label(
        (str(battle_benchmark.DEFAULT_NATIVE_BIN),)
    ) == "vam/native/target/debug/vam0-inspect"
    assert battle_benchmark.public_runner_label(
        ("/private/location/cargo", "run", "--quiet")
    ) == "cargo run"
    logger.debug("test_battle_runner_labels_never_publish_host_paths exit")


def test_semantic_parity_explicit_runner_label_uses_only_basename(
    tmp_path,
) -> None:
    """The diagnostic header never repeats an explicit host-local runner path."""
    logger.debug("test_semantic_parity_explicit_runner_label_uses_only_basename entry")
    runner = tmp_path / "custom-runner"
    runner.write_bytes(b"")
    result = semantic_parity.resolve_runner(
        argparse.Namespace(native_bin=str(runner), cargo=False)
    )
    assert result.label == "bin:custom-runner"
    assert str(tmp_path) not in result.label
    logger.debug("test_semantic_parity_explicit_runner_label_uses_only_basename exit")
