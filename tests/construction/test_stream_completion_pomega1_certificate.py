"""Direct PΩ1 certificate, captured sources, pinned Lean, and permanence checks."""

from hashlib import sha256
from pathlib import Path
import re
import sys
import time

from src.core.certify_stream_completion import certify_stream_completion_pomega1
from src.core.formal_export_catalog import _strip_lean_comments
from src.core.stream_completion import (
    ARTIFACT_PATH, ARTIFACT_SHA256, SCP_THEOREM_IDS, THEOREM_IDS,
)
from src.core.stream_completion_formal import (
    ELAN_SHA256, LEAN_BINARY_SHA256, LEAN_VERSION, TOOLCHAIN_ATTESTATION_DIGEST,
    TOOLCHAIN_ID, _parse_axiom_rows, capture_generic_source, compile_captured_sources,
    stream_completion_theorem_source,
)
from src.core.stream_completion_formal_attestation import (
    ToolchainContract, attest_toolchain,
)
from src.core.stream_completion_formal_process import (
    CapturedPhase, FormalPhaseReceipt, capture_command,
)
from src.core.stream_completion_types import FormalExecutionFailureKind
from stream_completion_fixture import exact_package
import pytest

pytestmark = pytest.mark.requires_lean


def test_direct_level_one_certificate_passes_exact_counts():
    certificate = certify_stream_completion_pomega1()
    assert certificate.passed is True and certificate.level == 1
    assert certificate.name == "stream_completion_pomega1"
    assert certificate.detail == (
        "theorems=15 obligations=11 positive=1 resource=1 shadows=2 physical=0 metaphysical=0"
    )


def test_captured_generic_digest_symbols_and_no_placeholders_are_exact():
    source = stream_completion_theorem_source()
    payload = capture_generic_source(source)
    assert sha256(payload).hexdigest() == ARTIFACT_SHA256 == source.artifact_sha256
    text = payload.decode("utf-8")
    clean = _strip_lean_comments(text)
    names = tuple(re.findall(
        r"(?m)^[ \t]*(?:theorem|lemma)[ \t]+(THM_POMEGA1_[A-Za-z0-9_]+)(?=[ \t\r\n:(])",
        clean,
    ))
    assert names == SCP_THEOREM_IDS and source.theorem_ids == THEOREM_IDS
    assert "sorry" not in clean and "admit" not in clean
    assert Path(ARTIFACT_PATH).read_bytes() == payload


def test_private_compile_checks_generic_and_exact_utf8_instance():
    package = exact_package(("零", "𐍈", "\n"))
    generic = capture_generic_source(package.theorem_source)
    outcome = compile_captured_sources(
        generic, package.alphabet_presentation.generated_instance_bytes, 120, 1024 * 1024,
    )
    assert outcome.kind is None and outcome.return_codes == (0, 0, 0, 0)
    assert tuple(row.phase for row in outcome.phase_receipts) == (
        "elan-which", "lean-version", "generic-compile", "instance-compile",
    )
    assert all(name.encode() in outcome.output for name in THEOREM_IDS)
    assert tuple(name for name, _ in outcome.theorem_axiom_rows) == THEOREM_IDS
    assert tuple(sorted({axiom for _, row in outcome.theorem_axiom_rows for axiom in row})) == (
        "Quot.sound",
    )


def test_no_old_olean_family_or_callable_is_packaged():
    package = exact_package()
    assert not hasattr(package, "family") and not hasattr(package, "generator")
    assert not hasattr(package, "oracle") and not hasattr(package, "callback")
    assert b".olean" not in package.alphabet_presentation.generated_instance_bytes


def test_axiom_parser_rejects_duplicate_missing_extra_and_includes_bridges():
    package = exact_package()
    generic = capture_generic_source(package.theorem_source)
    outcome = compile_captured_sources(
        generic, package.alphabet_presentation.generated_instance_bytes, 120, 1024 * 1024,
    )
    assert outcome.kind is None and len(outcome.theorem_axiom_rows) == 15
    lines = outcome.output.splitlines(keepends=True)
    theorem_lines = [line for line in lines if line.startswith(b"'THM_POMEGA1_")]
    assert _parse_axiom_rows(outcome.output + theorem_lines[0]) is None
    assert _parse_axiom_rows(outcome.output.replace(theorem_lines[0], b"", 1)) is None
    extra = b"'THM_POMEGA1_999_extra' does not depend on any axioms\n"
    assert _parse_axiom_rows(outcome.output + extra) is None


def test_toolchain_binary_drift_and_live_combined_cap_are_fail_closed(monkeypatch):
    package = exact_package()
    generic = capture_generic_source(package.theorem_source)
    instance = package.alphabet_presentation.generated_instance_bytes
    monkeypatch.setattr("src.core.stream_completion_formal_attestation.file_sha", lambda path: "0" * 64)
    drift = compile_captured_sources(generic, instance, 120, 1024 * 1024)
    assert drift.kind.value == "compile-error" and drift.return_codes == ()
    monkeypatch.undo()
    full = compile_captured_sources(generic, instance, 120, 1024 * 1024)
    before_instance = sum(row.output_bytes for row in full.phase_receipts[:3])
    combined = compile_captured_sources(generic, instance, 120, before_instance + 1)
    assert combined.kind.value == "output-limit"
    assert tuple(row.phase for row in combined.phase_receipts) == (
        "elan-which", "lean-version", "generic-compile", "instance-compile",
    )
    assert combined.phase_receipts[-1].failure_kind is FormalExecutionFailureKind.OUTPUT_LIMIT
    assert len(combined.output) == before_instance + 1
    assert sum(row.output_bytes for row in combined.phase_receipts) == len(combined.output)
    assert len(combined.output) <= before_instance + 1


def test_scp_ledger_has_exact_formal_dependencies_and_real_sources():
    package = exact_package()
    rows = {row.row_id: row for row in package.ledger.rows}
    scp = rows["THM_POMEGA1_011_scp_introduction"]
    assert scp.direct_dependencies[:4] == (
        "THM_POMEGA1_006_universal_realization",
        "THM_POMEGA1_008_joint_separation",
        "THM_POMEGA1_009_relative_uniqueness",
        "THM_POMEGA1_010_nonvacuity_inhabitance",
    )
    assert all(rows[name].source_digest != rows["natural-numbers"].source_digest for name in THEOREM_IDS)
    assert rows[THEOREM_IDS[0]].axiom_closure == ("Quot.sound",)
    assert rows[THEOREM_IDS[2]].axiom_closure == ()


def test_live_capture_kills_process_group_at_cap_and_deadline():
    started = time.monotonic()
    kind, code, output = capture_command(
        [sys.executable, "-c", "import sys,time;sys.stdout.write('x'*1000000);sys.stdout.flush();time.sleep(30)"],
        None, time.monotonic() + 5, 128,
    )
    assert kind is FormalExecutionFailureKind.OUTPUT_LIMIT and code == -1
    assert output == b"x" * 128 and time.monotonic() - started < 2
    started = time.monotonic()
    kind, code, output = capture_command(
        [sys.executable, "-c", "import time;time.sleep(30)"],
        None, time.monotonic() + 0.1, 128,
    )
    assert kind is FormalExecutionFailureKind.TIMEOUT and code == -1
    assert output == b"" and time.monotonic() - started < 2


def test_live_overflow_receipts_bind_exact_prefix_under_tiny_caps():
    from hashlib import sha256
    from src.core.stream_completion_formal_process import capture_phase

    for cap in (1, 2, 8):
        phase = capture_phase(
            "tiny-overflow", [sys.executable, "-c", "import sys;sys.stdout.write('abcdefghijk')"],
            None, time.monotonic() + 5, cap,
        )
        assert phase.kind is FormalExecutionFailureKind.OUTPUT_LIMIT
        assert phase.output == b"abcdefgh"[:cap]
        assert phase.receipt.output_bytes == cap
        assert phase.receipt.output_digest == sha256(phase.output).hexdigest()

    package = exact_package()
    generic = capture_generic_source(package.theorem_source)
    for cap in (1, 2, 8):
        outcome = compile_captured_sources(
            generic, package.alphabet_presentation.generated_instance_bytes, 120, cap,
        )
        assert outcome.kind is FormalExecutionFailureKind.OUTPUT_LIMIT
        assert len(outcome.output) == cap
        assert sum(row.output_bytes for row in outcome.phase_receipts) == cap
        assert outcome.phase_receipts[-1].output_digest == sha256(outcome.output).hexdigest()


def test_attestation_timeout_and_overflow_propagate_for_both_commands(monkeypatch):
    contract = ToolchainContract(
        TOOLCHAIN_ID, ELAN_SHA256, LEAN_BINARY_SHA256, LEAN_VERSION.encode(),
        TOOLCHAIN_ATTESTATION_DIGEST,
    )
    monkeypatch.setattr(
        "src.core.stream_completion_formal_attestation.file_sha",
        lambda path: ELAN_SHA256 if str(path) == "/elan" else LEAN_BINARY_SHA256,
    )

    def receipt(phase, kind, output):
        from hashlib import sha256

        code = -1 if kind is not None else 0
        row = FormalPhaseReceipt(phase, code, len(output), sha256(output).hexdigest(), kind)
        return CapturedPhase(kind, code, output, row)

    for target in ("elan-which", "lean-version"):
        for kind in (FormalExecutionFailureKind.TIMEOUT, FormalExecutionFailureKind.OUTPUT_LIMIT):
            def fake(phase, *args, target=target, kind=kind, **kwargs):
                if phase == target:
                    return receipt(phase, kind, b"phase-failure")
                output = b"/lean\n" if phase == "elan-which" else LEAN_VERSION.encode()
                return receipt(phase, None, output)

            monkeypatch.setattr("src.core.stream_completion_formal_attestation.capture_phase", fake)
            outcome = attest_toolchain("/elan", time.monotonic() + 5, 4096, contract)
            assert outcome.kind is kind
            assert outcome.phase_receipts[-1].phase == target
            assert outcome.phase_receipts[-1].failure_kind is kind
