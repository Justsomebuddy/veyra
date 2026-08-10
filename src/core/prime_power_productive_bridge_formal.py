"""Exact continuity and fresh private Lean replay for P3-A1b."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import re
import shutil
import tempfile
import time

from .formal_export_catalog import _strip_lean_comments
from .padic_completion_formal import ELAN_SHA256, LEAN_BINARY_SHA256, LEAN_VERSION
from .prime_power_productive_bridge_common import (
    ProductiveBridgeValidationError, digest, reject, sha,
)
from .prime_power_productive_bridge_sources import AXIOM_ROWS, THEOREM_IDS, TOOLCHAIN_ID
from .prime_power_productive_bridge_pressure import (
    PRESSURE_ARTIFACT_SHA256, PRESSURE_AXIOM_ROWS, PRESSURE_THEOREM_IDS,
    snapshot_offset_program,
)
from .prime_power_productive_bridge_types import (
    FormalFailureKind, OffsetResidueProgramSource, ProductiveBridgePackage,
)
from .stream_completion_formal_attestation import ToolchainContract, attest_toolchain
from .stream_completion_formal_process import FormalPhaseReceipt, capture_phase

from .paths import TMP_DIR

logger = logging.getLogger(__name__)
ATTESTATION_DIGEST = digest("veyra.p3a1b.attestation.v1", (
    ("toolchain", TOOLCHAIN_ID.encode()), ("elan", ELAN_SHA256.encode()),
    ("lean", LEAN_BINARY_SHA256.encode()), ("version", LEAN_VERSION.encode()),
))


@dataclass(frozen=True)
class CompileOutcome:
    kind: FormalFailureKind | None
    output: bytes
    return_codes: tuple[int, ...]
    theorem_axiom_rows: tuple[tuple[str, tuple[str, ...]], ...]
    attestation_digest: str
    phase_receipts: tuple[FormalPhaseReceipt, ...]


def _read(path: Path) -> bytes:
    """Read no more than one byte beyond the per-file hard cap."""
    logger.debug("_read entry file=%s", path.name)
    try:
        with path.open("rb") as handle:
            result = handle.read(2 * 1024 * 1024 + 1)
    except OSError:
        reject("formal-artifact-unavailable")
    if len(result) > 2 * 1024 * 1024:
        reject("formal-artifact-too-large")
    logger.debug("_read exit bytes=%d", len(result))
    return result


def _symbols(payload: bytes) -> None:
    """Require exact ordered theorem names and no proof placeholders."""
    logger.debug("_symbols entry")
    try:
        clean = _strip_lean_comments(payload.decode("utf-8", errors="strict"))
    except UnicodeError:
        reject("bridge-artifact-invalid-utf8")
    found = tuple(re.findall(r"(?m)^\s*theorem\s+(THM_P3A1B_[A-Za-z0-9_]+)(?=[\s:(])", clean))
    if found != THEOREM_IDS or re.search(r"\b(?:sorry|admit)\b", clean):
        reject("bridge-artifact-symbol-set-drift")
    if "THM_P3N1_002_integer_residue_reduction" in clean:
        reject("process-coherence-circular-through-n1")
    logger.debug("_symbols exit count=%d", len(found))


def _instance(package: ProductiveBridgePackage) -> bytes:
    """Generate exact p/z theorem applications with no completion premise."""
    logger.debug("_instance entry p=%d", package.prime.p)
    result = f"""import VeyraPrimePowerProductiveBridge
set_option autoImplicit false
def p3a1bPrime : VeyraPrimeWitness {package.prime.p} := by constructor <;> decide
def p3a1bInteger : Int := ({package.integer.z} : Int)
def p3a1bTotal := THM_P3A1B_001_total p3a1bPrime p3a1bInteger
def p3a1bDeterministic := THM_P3A1B_002_deterministic p3a1bPrime p3a1bInteger
def p3a1bCoherent := THM_P3A1B_003_process_coherent p3a1bPrime p3a1bInteger
def p3a1bCommutes := THM_P3A1B_004_commutes p3a1bPrime p3a1bInteger
#print axioms p3a1bTotal
#print axioms p3a1bDeterministic
#print axioms p3a1bCoherent
#print axioms p3a1bCommutes
""".encode()
    logger.debug("_instance exit bytes=%d", len(result))
    return result
def capture_sources(package: ProductiveBridgePackage) -> tuple[bytes, bytes, bytes, bytes]:
    """Capture exact PΩ2, direct N1, bridge, and generated application bytes."""
    logger.debug("capture_sources entry")
    p2 = _read(Path(package.theorem.pomega2_artifact_path_id))
    n1 = _read(Path(package.theorem.n1_artifact_path_id))
    bridge = _read(Path(package.theorem.artifact_path_id))
    expected = (package.theorem.pomega2_artifact_sha256,
                package.theorem.n1_artifact_sha256, package.theorem.artifact_sha256)
    if tuple(map(sha, (p2, n1, bridge))) != expected:
        reject("captured-source-continuity-drift")
    _symbols(bridge)
    result = (p2, n1, bridge, _instance(package))
    logger.debug("capture_sources exit bytes=%d", sum(map(len, result)))
    return result
def _pressure_instance(package: ProductiveBridgePackage,
                       source: OffsetResidueProgramSource) -> bytes:
    """Generate exact concrete applications of both pressure proofs."""
    logger.debug("_pressure_instance entry")
    result = f"""import VeyraPrimePowerProductiveBridgePressure
set_option autoImplicit false
def p3a1bPressurePrime : VeyraPrimeWitness {package.prime.p} := by constructor <;> decide
def p3a1bPressureInteger : Int := ({package.integer.z} : Int)
def p3a1bPressureOffset : Int := ({source.offset} : Int)
def p3a1bPressureTotal := THM_P3A1B_PRESSURE_001_total p3a1bPressurePrime
  p3a1bPressureInteger p3a1bPressureOffset
def p3a1bPressureCoherent := THM_P3A1B_PRESSURE_002_coherent p3a1bPressurePrime
  p3a1bPressureInteger p3a1bPressureOffset
#print axioms p3a1bPressureTotal
#print axioms p3a1bPressureCoherent
""".encode()
    logger.debug("_pressure_instance exit bytes=%d", len(result))
    return result
def capture_pressure_sources(package: ProductiveBridgePackage,
                             raw_source: OffsetResidueProgramSource) -> tuple[bytes, ...]:
    """Capture bridge dependencies plus exact pressure proof and application."""
    logger.debug("capture_pressure_sources entry")
    source = snapshot_offset_program(raw_source)
    if (source.prime_digest != package.prime.source_digest
            or source.integer_digest != package.integer.source_digest):
        reject("pressure-program-p-or-z-binding-mismatch")
    base = capture_sources(package)[:3]
    pressure = _read(Path(source.artifact_path_id))
    if sha(pressure) != PRESSURE_ARTIFACT_SHA256:
        reject("pressure-artifact-continuity-drift")
    try:
        clean = _strip_lean_comments(pressure.decode("utf-8", errors="strict"))
    except UnicodeError:
        reject("pressure-artifact-invalid-utf8")
    found = tuple(re.findall(r"(?m)^\s*theorem\s+(THM_P3A1B_PRESSURE_[A-Za-z0-9_]+)(?=[\s:(])", clean))
    if found != PRESSURE_THEOREM_IDS or re.search(r"\b(?:sorry|admit)\b", clean):
        reject("pressure-artifact-symbol-set-drift")
    result = (*base, pressure, _pressure_instance(package, source))
    logger.debug("capture_pressure_sources exit bytes=%d", sum(map(len, result)))
    return result
def continuity_holds(package: ProductiveBridgePackage, captured: tuple[bytes, ...]) -> bool:
    """Re-read all theorem bytes and regenerate the application after replay."""
    logger.debug("continuity_holds entry")
    try:
        current = capture_sources(package)
    except ProductiveBridgeValidationError:
        logger.error("continuity_holds failed")
        return False
    result = current == captured
    logger.debug("continuity_holds exit result=%s", result)
    return result
def _map_kind(value) -> FormalFailureKind | None:
    """Map shared execution failures without reclassification."""
    logger.debug("_map_kind entry")
    result = None if value is None else FormalFailureKind(value.value)
    logger.debug("_map_kind exit result=%s", None if result is None else result.value)
    return result
def _parse(payload: bytes):
    """Parse exact generic and concrete theorem axiom closures."""
    logger.debug("_parse entry bytes=%d", len(payload))
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeError:
        return None
    pattern = r"(?m)^'([^']+)' (does not depend on any axioms|depends on axioms: \[([^\]]*)\])$"
    rows = tuple((name, () if phrase.startswith("does not") else tuple(sorted(body.split(", "))))
                 for name, phrase, body in re.findall(pattern, text))
    generic = tuple(row for row in rows if row[0].startswith("THM_P3A1B_"))
    concrete = tuple(row for row in rows if row[0].startswith("p3a1b"))
    expected_concrete = tuple((f"p3a1b{x}", axioms) for x, (_, axioms) in zip(
        ("Total", "Deterministic", "Coherent", "Commutes"), AXIOM_ROWS, strict=True))
    result = generic if generic == AXIOM_ROWS and concrete == expected_concrete else None
    logger.debug("_parse exit valid=%s", result is not None)
    return result


def _parse_pressure(payload: bytes):
    """Parse exact generic and concrete pressure theorem closures."""
    logger.debug("_parse_pressure entry bytes=%d", len(payload))
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeError:
        return None
    pattern = r"(?m)^'([^']+)' (does not depend on any axioms|depends on axioms: \[([^\]]*)\])$"
    rows = tuple((name, () if phrase.startswith("does not") else tuple(sorted(body.split(", "))))
                 for name, phrase, body in re.findall(pattern, text))
    generic = tuple(row for row in rows if row[0] in PRESSURE_THEOREM_IDS)
    concrete = tuple(row for row in rows if row[0].startswith("p3a1bPressure"))
    expected = (("p3a1bPressureTotal", ()), ("p3a1bPressureCoherent", ("propext",)))
    result = generic if generic == PRESSURE_AXIOM_ROWS and concrete == expected else None
    logger.debug("_parse_pressure exit valid=%s", result is not None)
    return result


def compile_sources(captured: tuple[bytes, ...], timeout: int, max_output: int) -> CompileOutcome:
    """Attest then compile four immutable phases under one deadline/live cap."""
    logger.debug("compile_sources entry timeout=%d cap=%d", timeout, max_output)
    elan = shutil.which("elan")
    if elan is None:
        return CompileOutcome(FormalFailureKind.COMPILE_ERROR, b"", (), (), ATTESTATION_DIGEST, ())
    deadline = time.monotonic() + timeout
    contract = ToolchainContract(TOOLCHAIN_ID, ELAN_SHA256, LEAN_BINARY_SHA256,
                                 LEAN_VERSION.encode(), ATTESTATION_DIGEST)
    attested = attest_toolchain(elan, deadline, max_output, contract)
    output = bytearray(attested.output)
    codes = list(attested.return_codes)
    receipts = list(attested.phase_receipts)
    if attested.kind is not None:
        return CompileOutcome(_map_kind(attested.kind), bytes(output), tuple(codes), (),
                              attested.attestation_digest, tuple(receipts))
    root = TMP_DIR
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="p3a1b-", dir=root) as directory:
        private = Path(directory)
        names = ("VeyraPadicCompletion.lean", "VeyraPadicFamilyIntroduction.lean",
                 "VeyraPrimePowerProductiveBridge.lean", "P3A1BInstance.lean")
        for name, payload in zip(names, captured, strict=True):
            path = private / name
            path.write_bytes(payload)
            path.chmod(0o400)
        commands = tuple(
            [elan, "run", TOOLCHAIN_ID, "lean", "-DwarningAsError=true", *(
                [] if i == 3 else ["-o", name.replace(".lean", ".olean")]), name]
            for i, name in enumerate(names)
        )
        env = dict(os.environ, LEAN_PATH=str(private.resolve()))
        for name, command in zip(names, commands, strict=True):
            part = capture_phase(name, command, private, deadline, max_output - len(output), env)
            output.extend(part.output)
            codes.append(part.return_code)
            receipts.append(part.receipt)
            if part.kind is not None:
                return CompileOutcome(_map_kind(part.kind), bytes(output), tuple(codes), (),
                                      attested.attestation_digest, tuple(receipts))
    rows = _parse(bytes(output))
    kind = None if rows is not None else FormalFailureKind.COMPILE_ERROR
    result = CompileOutcome(kind, bytes(output), tuple(codes), () if rows is None else rows,
                            attested.attestation_digest, tuple(receipts))
    logger.debug("compile_sources exit kind=%s", None if kind is None else kind.value)
    return result


def compile_pressure_sources(captured: tuple[bytes, ...], timeout: int,
                             max_output: int) -> CompileOutcome:
    """Attest and compile the five immutable pressure phases with live caps."""
    logger.debug("compile_pressure_sources entry timeout=%d cap=%d", timeout, max_output)
    elan = shutil.which("elan")
    if elan is None:
        return CompileOutcome(FormalFailureKind.COMPILE_ERROR, b"", (), (), ATTESTATION_DIGEST, ())
    deadline = time.monotonic() + timeout
    contract = ToolchainContract(TOOLCHAIN_ID, ELAN_SHA256, LEAN_BINARY_SHA256,
                                 LEAN_VERSION.encode(), ATTESTATION_DIGEST)
    attested = attest_toolchain(elan, deadline, max_output, contract)
    output = bytearray(attested.output)
    codes = list(attested.return_codes)
    receipts = list(attested.phase_receipts)
    if attested.kind is not None:
        return CompileOutcome(_map_kind(attested.kind), bytes(output), tuple(codes), (),
                              attested.attestation_digest, tuple(receipts))
    root = TMP_DIR
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="p3a1b-pressure-", dir=root) as directory:
        private = Path(directory)
        names = ("VeyraPadicCompletion.lean", "VeyraPadicFamilyIntroduction.lean",
                 "VeyraPrimePowerProductiveBridge.lean",
                 "VeyraPrimePowerProductiveBridgePressure.lean", "P3A1BPressureInstance.lean")
        for name, payload in zip(names, captured, strict=True):
            path = private / name
            path.write_bytes(payload)
            path.chmod(0o400)
        env = dict(os.environ, LEAN_PATH=str(private.resolve()))
        for i, name in enumerate(names):
            command = [elan, "run", TOOLCHAIN_ID, "lean", "-DwarningAsError=true"]
            if i != len(names) - 1:
                command += ["-o", name.replace(".lean", ".olean")]
            command.append(name)
            part = capture_phase(name, tuple(command), private, deadline, max_output - len(output), env)
            output.extend(part.output)
            codes.append(part.return_code)
            receipts.append(part.receipt)
            if part.kind is not None:
                return CompileOutcome(_map_kind(part.kind), bytes(output), tuple(codes), (),
                                      attested.attestation_digest, tuple(receipts))
    rows = _parse_pressure(bytes(output))
    kind = None if rows is not None else FormalFailureKind.COMPILE_ERROR
    result = CompileOutcome(kind, bytes(output), tuple(codes), () if rows is None else rows,
                            attested.attestation_digest, tuple(receipts))
    logger.debug("compile_pressure_sources exit kind=%s", None if kind is None else kind.value)
    return result
