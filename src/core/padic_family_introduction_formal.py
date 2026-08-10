"""Captured-source continuity and bounded private Lean execution for P3-N1."""

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
from .padic_completion_formal import (
    ELAN_SHA256, LEAN_BINARY_SHA256, LEAN_VERSION,
)
from .padic_family_introduction_common import digest, reject, sha
from .padic_family_introduction_sources import (
    THEOREM_IDS, TOOLCHAIN_ID,
)
from .padic_family_introduction_types import N1ExecutionFailureKind, N1IntroductionPackage
from .stream_completion_formal_attestation import ToolchainContract, attest_toolchain
from .stream_completion_formal_process import FormalPhaseReceipt, capture_phase

from .paths import TMP_DIR

logger = logging.getLogger(__name__)
EXPECTED_AXIOM_ROWS = (
    (THEOREM_IDS[0], ()), (THEOREM_IDS[1], ("propext",)),
    (THEOREM_IDS[2], ("propext",)),
)
ATTESTATION_DIGEST = digest("veyra.p3n1.toolchain-attestation.v1", (
    ("toolchain", TOOLCHAIN_ID.encode()), ("elan", ELAN_SHA256.encode()),
    ("lean", LEAN_BINARY_SHA256.encode()), ("version", LEAN_VERSION.encode()),
))


@dataclass(frozen=True)
class N1CompileOutcome:
    kind: N1ExecutionFailureKind | None
    output: bytes
    return_codes: tuple[int, ...]
    theorem_axiom_rows: tuple[tuple[str, tuple[str, ...]], ...]
    attestation_digest: str
    phase_receipts: tuple[FormalPhaseReceipt, ...]


def _read(path: Path) -> bytes:
    """Read at most one byte beyond the per-file hard source cap."""
    logger.debug("_read entry file=%s", path.name)
    try:
        with path.open("rb") as handle:
            result = handle.read(2 * 1024 * 1024 + 1)
    except OSError:
        reject("n1-artifact-unavailable")
    if len(result) > 2 * 1024 * 1024:
        reject("n1-artifact-too-large")
    logger.debug("_read exit bytes=%d", len(result))
    return result


def _symbols(payload: bytes) -> None:
    """Require the exact ordered theorem set and no placeholder proofs."""
    logger.debug("_symbols entry")
    try:
        clean = _strip_lean_comments(payload.decode("utf-8", errors="strict"))
    except UnicodeError:
        reject("n1-artifact-invalid-utf8")
    found = tuple(re.findall(
        r"(?m)^\s*theorem\s+(THM_P3N1_[A-Za-z0-9_]+)(?=[\s:(])", clean,
    ))
    if found != THEOREM_IDS or re.search(r"\b(?:sorry|admit)\b", clean):
        reject("n1-artifact-symbol-set-drift")
    logger.debug("_symbols exit count=%d", len(found))


def _instance_bytes(package: N1IntroductionPackage) -> bytes:
    """Generate only exact p/z introduction use, never universal completion."""
    logger.debug("_instance_bytes entry p=%d bits=%d", package.prime.p, package.integer.z.bit_length())
    z = str(package.integer.z)
    result = f"""import VeyraPadicFamilyIntroduction

set_option autoImplicit false

def p3n1PrimeWitness : VeyraPrimeWitness {package.prime.p} := by
  constructor
  · decide
  · decide

def p3n1Integer : Int := ({z} : Int)

def p3n1Family : VeyraCompatibleFamily p3n1PrimeWitness :=
  veyraIntegerFamily p3n1PrimeWitness p3n1Integer

theorem p3n1ConcreteIntroduction :
    exists f : VeyraCompatibleFamily p3n1PrimeWitness,
      f = p3n1Family /\\ forall n, f.val n =
        veyraIntegerResidue p3n1PrimeWitness p3n1Integer n := by
  exact THM_P3N1_003_integer_family_introduction
    p3n1PrimeWitness p3n1Integer

#print axioms p3n1PrimeWitness
#print axioms p3n1Family
#print axioms p3n1ConcreteIntroduction
""".encode()
    logger.debug("_instance_bytes exit bytes=%d", len(result))
    return result


def capture_sources(package: N1IntroductionPackage) -> tuple[bytes, bytes, bytes]:
    """Capture exact PΩ2 dependency, N1 theorem, and generated p/z instance bytes."""
    logger.debug("capture_sources entry")
    base = _read(Path(package.theorem_source.pomega2_artifact_path_id))
    theorem = _read(Path(package.theorem_source.artifact_path_id))
    if sha(base) != package.theorem_source.pomega2_artifact_sha256:
        reject("n1-pomega2-source-drift")
    if sha(theorem) != package.theorem_source.artifact_sha256:
        reject("n1-theorem-source-drift")
    _symbols(theorem)
    instance = _instance_bytes(package)
    logger.debug("capture_sources exit bytes=%d", sum(map(len, (base, theorem, instance))))
    return base, theorem, instance


def continuity_holds(package: N1IntroductionPackage, captured: tuple[bytes, bytes, bytes]) -> bool:
    """Re-read both artifacts and regenerate the instance after compilation."""
    logger.debug("continuity_holds entry")
    try:
        current = (_read(Path(package.theorem_source.pomega2_artifact_path_id)),
                   _read(Path(package.theorem_source.artifact_path_id)), _instance_bytes(package))
    except Exception:
        logger.error("continuity_holds failed")
        return False
    result = current == captured
    logger.debug("continuity_holds exit result=%s", result)
    return result


def _kind(value: object) -> N1ExecutionFailureKind | None:
    """Map shared process failures without reclassification."""
    logger.debug("_kind entry")
    result = None if value is None else N1ExecutionFailureKind(value.value)
    logger.debug("_kind exit result=%s", None if result is None else result.value)
    return result


def _parse_axioms(payload: bytes):
    """Parse exact generic and instance axiom output."""
    logger.debug("_parse_axioms entry bytes=%d", len(payload))
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeError:
        return None
    matches = re.findall(
        r"(?m)^'(THM_P3N1_[A-Za-z0-9_]+)' (does not depend on any axioms|depends on axioms: \[([^\]]*)\])$",
        text,
    )
    rows = tuple((name, () if phrase.startswith("does not") else tuple(sorted(body.split(", "))))
                 for name, phrase, body in matches)
    aux = re.findall(
        r"(?m)^'(p3n1PrimeWitness|p3n1Family|p3n1ConcreteIntroduction)' "
        r"(does not depend on any axioms|depends on axioms: \[([^\]]*)\])$", text,
    )
    aux_rows = tuple((name, () if phrase.startswith("does not") else tuple(sorted(body.split(", "))))
                     for name, phrase, body in aux)
    expected_aux = (("p3n1PrimeWitness", ()), ("p3n1Family", ("propext",)),
                    ("p3n1ConcreteIntroduction", ("propext",)))
    result = rows if rows == EXPECTED_AXIOM_ROWS and aux_rows == expected_aux else None
    logger.debug("_parse_axioms exit valid=%s", result is not None)
    return result


def compile_sources(captured: tuple[bytes, bytes, bytes], timeout: int, max_output: int) -> N1CompileOutcome:
    """Attest and compile all three sources under one deadline and live byte cap."""
    logger.debug("compile_sources entry timeout=%d cap=%d", timeout, max_output)
    elan = shutil.which("elan")
    if elan is None:
        return N1CompileOutcome(N1ExecutionFailureKind.COMPILE_ERROR, b"", (), (),
                                ATTESTATION_DIGEST, ())
    deadline = time.monotonic() + timeout
    contract = ToolchainContract(TOOLCHAIN_ID, ELAN_SHA256, LEAN_BINARY_SHA256,
                                 LEAN_VERSION.encode(), ATTESTATION_DIGEST)
    attested = attest_toolchain(elan, deadline, max_output, contract)
    combined = bytearray(attested.output)
    codes = list(attested.return_codes)
    receipts = list(attested.phase_receipts)
    if attested.kind is not None:
        return N1CompileOutcome(_kind(attested.kind), bytes(combined), tuple(codes), (),
                                attested.attestation_digest, tuple(receipts))
    try:
        root = TMP_DIR
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="p3n1-", dir=root) as directory:
            private = Path(directory)
            names = ("VeyraPadicCompletion.lean", "VeyraPadicFamilyIntroduction.lean",
                     "P3N1ConcreteInstance.lean")
            paths = tuple(private / name for name in names)
            for path, payload in zip(paths, captured, strict=True):
                path.write_bytes(payload)
                path.chmod(0o400)
            commands = (
                [elan, "run", TOOLCHAIN_ID, "lean", "-DwarningAsError=true", "-o",
                 "VeyraPadicCompletion.olean", names[0]],
                [elan, "run", TOOLCHAIN_ID, "lean", "-DwarningAsError=true", "-o",
                 "VeyraPadicFamilyIntroduction.olean", names[1]],
                [elan, "run", TOOLCHAIN_ID, "lean", "-DwarningAsError=true", names[2]],
            )
            env = dict(os.environ, LEAN_PATH=str(private.resolve()))
            phases = ("pomega2-dependency-compile", "n1-theorem-compile", "n1-instance-compile")
            for phase, command in zip(phases, commands, strict=True):
                part = capture_phase(phase, command, private, deadline,
                                     max_output - len(combined), env)
                combined.extend(part.output)
                codes.append(part.return_code)
                receipts.append(part.receipt)
                if part.kind is not None:
                    return N1CompileOutcome(_kind(part.kind), bytes(combined), tuple(codes), (),
                                            attested.attestation_digest, tuple(receipts))
    except OSError as exc:
        logger.error("compile_sources filesystem error=%s", exc)
        return N1CompileOutcome(N1ExecutionFailureKind.COMPILE_ERROR, bytes(combined),
                                tuple(codes), (), attested.attestation_digest, tuple(receipts))
    rows = _parse_axioms(bytes(combined))
    kind = None if rows is not None else N1ExecutionFailureKind.COMPILE_ERROR
    result = N1CompileOutcome(kind, bytes(combined), tuple(codes), () if rows is None else rows,
                              attested.attestation_digest, tuple(receipts))
    logger.debug("compile_sources exit kind=%s", None if kind is None else kind.value)
    return result
