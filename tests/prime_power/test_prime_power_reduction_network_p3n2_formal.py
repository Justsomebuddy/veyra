"""Exact-byte and fresh-private-Lean checks for P3-N2."""

from src.core.prime_power_reduction_network_formal import (
    capture_sources, compile_sources, continuity_holds,
)
from src.core.prime_power_reduction_network_sources import AXIOM_ROWS
from prime_power_reduction_network_fixture import exact_n2_package
import pytest

pytestmark = pytest.mark.requires_lean


def test_exact_sources_compile_privately_with_exact_axiom_rows():
    package = exact_n2_package()
    captured = capture_sources(package)
    outcome = compile_sources(captured, package.policy.timeout_seconds,
                              package.policy.max_output_bytes)
    assert outcome.kind is None
    assert outcome.axiom_rows == AXIOM_ROWS
    assert outcome.return_codes and all(code == 0 for code in outcome.return_codes)
    assert continuity_holds(package, captured)


def test_n2_artifact_excludes_completed_bundle_and_c2_import():
    payload = capture_sources(exact_n2_package())[2]
    assert b"VeyraPPCPBundle" not in payload
    assert b"THM_POMEGA2_017" not in payload
    assert b"VeyraTransportCoherence" not in payload
    assert b"THM_P3N2_003_reduction_witness_independent" in payload
    assert b"THM_P3N2_004_path_equality" in payload
