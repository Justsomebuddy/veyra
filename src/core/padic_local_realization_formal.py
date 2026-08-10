"""Captured private Lean replay for isolated P3-N3/N4."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import re
import shutil
import tempfile
import time

from .padic_completion_formal import (
    ELAN_SHA256, LEAN_BINARY_SHA256, LEAN_VERSION, TOOLCHAIN_ATTESTATION_DIGEST,
    TOOLCHAIN_ID,
)
from .padic_local_realization_common import reject, sha
from .padic_local_realization_sources import (
    ARTIFACT_PATH, ARTIFACT_SHA256, N1_PATH, N1_SHA, P2_PATH, P2_SHA,
    PREMISE_PATH, PREMISE_SHA256, PREMISE_THEOREMS, THEOREM_IDS,
)
from .padic_local_realization_types import FormalFailureKind, N3Request, N4Request
from .stream_completion_formal_attestation import ToolchainContract, attest_toolchain
from .stream_completion_formal_process import FormalPhaseReceipt, capture_phase

from .paths import TMP_DIR

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class N34CompileOutcome:
    kind: FormalFailureKind | None
    output: bytes
    return_codes: tuple[int, ...]
    axiom_rows: tuple[tuple[str, tuple[str, ...]], ...]
    attestation_digest: str
    phase_receipts: tuple[FormalPhaseReceipt, ...]


def _read(path: str, expected_sha: str) -> bytes:
    """Read one bounded exact source once."""
    logger.debug("_read entry path=%s", Path(path).name)
    cap = 2 * 1024 * 1024
    try:
        source = Path(path)
        if source.stat().st_size > cap:
            reject("formal-source-drift-or-too-large")
        with source.open("rb") as stream:
            payload = stream.read(cap + 1)
            if len(payload) > cap or stream.read(1):
                reject("formal-source-drift-or-too-large")
    except OSError:
        reject("formal-source-unavailable")
    if sha(payload) != expected_sha:
        reject("formal-source-drift-or-too-large")
    logger.debug("_read exit bytes=%d", len(payload))
    return payload


def _symbols(payload: bytes, expected: tuple[str, ...], prefix: str) -> None:
    """Require exact ordered theorem declarations and no placeholders."""
    logger.debug("_symbols entry expected=%d", len(expected))
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeError:
        reject("formal-source-invalid-utf8")
    found = tuple(re.findall(
        rf"(?m)^\s*theorem\s+({re.escape(prefix)}[A-Za-z0-9_]+)(?=[\s:(])", text))
    if found != expected or re.search(r"\b(?:sorry|admit)\b", text):
        reject("formal-symbol-set-drift")
    logger.debug("_symbols exit")


def _instance(request: N3Request | N4Request) -> bytes:
    """Generate the exact p/z-bound N3 or N4 replay instance."""
    logger.debug("_instance entry type=%s", type(request).__name__)
    n1 = request.n1 if type(request) is N3Request else request.left_n1
    z = n1.integer.z
    integer = f"({z} : Int)" if z >= 0 else f"(-{abs(z)} : Int)"
    if type(request) is N3Request:
        body = f"""import VeyraPadicLocalRealization
import PadicPrimeInstance
set_option autoImplicit false
theorem p3n3Concrete : exists x : ZpVeyra pomega2PrimeWitness,
    forall n, veyraRho n x = (veyraIntegerFamily pomega2PrimeWitness {integer}).val n :=
  THM_P3N3_002_realized_integer_family_coordinate pomega2PrimeWitness {integer}
#print axioms p3n3Concrete
"""
    else:
        body = f"""import VeyraPadicAllDepthEquality
import PadicPrimeInstance
set_option autoImplicit false
theorem p3n4Concrete : exists x y : ZpVeyra pomega2PrimeWitness, x = y := by
  obtain ⟨x, hx⟩ := THM_P3N3_002_realized_integer_family_coordinate pomega2PrimeWitness {integer}
  obtain ⟨y, hy⟩ := THM_P3N3_002_realized_integer_family_coordinate pomega2PrimeWitness {integer}
  have hxy := THM_P3N4_PREMISE_001_same_integer_coordinates hx hy
  exact ⟨x, y, THM_P3N4_001_scoped_joint_separation x y hxy⟩
#print axioms p3n4Concrete
"""
    result = body.encode()
    logger.debug("_instance exit bytes=%d", len(result))
    return result


def capture_sources(request: N3Request | N4Request) -> tuple[bytes, ...]:
    """Capture exact imports, owned theorem/premise, witness, and instance bytes."""
    logger.debug("capture_sources entry type=%s", type(request).__name__)
    if type(request) not in (N3Request, N4Request):
        reject("request-exact-type-required")
    p2, n1 = _read(P2_PATH, P2_SHA), _read(N1_PATH, N1_SHA)
    own = _read(ARTIFACT_PATH, ARTIFACT_SHA256)
    _symbols(own, THEOREM_IDS, "THM_P3N")
    prime = request.pomega2.prime.generated_witness_bytes
    if sha(prime) != request.pomega2.prime.generated_witness_sha256:
        reject("prime-witness-capture-drift")
    items: tuple[bytes, ...] = (p2, n1, own)
    if type(request) is N4Request:
        premise = _read(PREMISE_PATH, PREMISE_SHA256)
        _symbols(premise, PREMISE_THEOREMS, "THM_P3N4_PREMISE_")
        items = (*items, premise)
    result = (*items, prime, _instance(request))
    logger.debug("capture_sources exit count=%d bytes=%d", len(result), sum(map(len, result)))
    return result


def continuity_holds(request: N3Request | N4Request, captured: tuple[bytes, ...]) -> bool:
    """Reread all disk sources and regenerate exact derived bytes."""
    logger.debug("continuity_holds entry")
    try:
        result = capture_sources(request) == captured
    except Exception:
        logger.error("continuity_holds failed")
        return False
    logger.debug("continuity_holds exit result=%s", result)
    return result


def _kind(value: object) -> FormalFailureKind | None:
    """Map the shared bounded-process failure vocabulary exactly."""
    logger.debug("_kind entry")
    result = None if value is None else FormalFailureKind(value.value)
    logger.debug("_kind exit result=%s", None if result is None else result.value)
    return result


def _axioms(output: bytes, n4: bool) -> tuple[tuple[str, tuple[str, ...]], ...] | None:
    """Parse exact owned theorem and concrete-instance axiom rows."""
    logger.debug("_axioms entry bytes=%d", len(output))
    names = (*THEOREM_IDS, *(PREMISE_THEOREMS if n4 else ()),
             "p3n4Concrete" if n4 else "p3n3Concrete")
    pattern = re.compile(
        r"(?m)^'([^']+)' (does not depend on any axioms|depends on axioms: \[([^\]]*)\])$")
    found = {name: (() if phrase.startswith("does not") else tuple(sorted(body.split(", "))))
             for name, phrase, body in pattern.findall(output.decode("utf-8", errors="replace"))}
    if any(name not in found for name in names):
        logger.error("_axioms missing rows")
        return None
    result = tuple((name, found[name]) for name in names)
    logger.debug("_axioms exit rows=%d", len(result))
    return result


def compile_sources(request: N3Request | N4Request, captured: tuple[bytes, ...]) -> N34CompileOutcome:
    """Attest and compile exact private sources under one deadline/live cap."""
    logger.debug("compile_sources entry")
    elan = shutil.which("elan")
    if elan is None:
        return N34CompileOutcome(FormalFailureKind.COMPILE_ERROR, b"", (), (), "", ())
    deadline = time.monotonic() + request.policy.timeout_seconds
    contract = ToolchainContract(TOOLCHAIN_ID, ELAN_SHA256, LEAN_BINARY_SHA256,
        LEAN_VERSION.encode(), TOOLCHAIN_ATTESTATION_DIGEST)
    attested = attest_toolchain(elan, deadline, request.policy.max_output_bytes, contract)
    output, codes, receipts = bytearray(attested.output), list(attested.return_codes), list(attested.phase_receipts)
    if attested.kind is not None:
        return N34CompileOutcome(_kind(attested.kind), bytes(output), tuple(codes), (),
                                 attested.attestation_digest, tuple(receipts))
    names = ["VeyraPadicCompletion.lean", "VeyraPadicFamilyIntroduction.lean",
             "VeyraPadicLocalRealization.lean"]
    if type(request) is N4Request:
        names.append("VeyraPadicAllDepthEquality.lean")
    names += ["PadicPrimeInstance.lean", "P3N34ConcreteInstance.lean"]
    try:
        root = TMP_DIR
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="p3n34-", dir=root) as directory:
            private = Path(directory)
            for name, payload in zip(names, captured, strict=True):
                path = private / name
                path.write_bytes(payload)
                path.chmod(0o400)
            env = dict(os.environ, LEAN_PATH=str(private.resolve()))
            for index, name in enumerate(names):
                command = [elan, "run", TOOLCHAIN_ID, "lean", "-DwarningAsError=true"]
                if index < len(names) - 1:
                    command += ["-o", name.replace(".lean", ".olean")]
                command.append(name)
                phase = capture_phase(f"p3n34-compile-{index}", command, private, deadline,
                                      request.policy.max_output_bytes - len(output), env)
                output.extend(phase.output)
                codes.append(phase.return_code)
                receipts.append(phase.receipt)
                if phase.kind is not None:
                    return N34CompileOutcome(_kind(phase.kind), bytes(output), tuple(codes), (),
                        attested.attestation_digest, tuple(receipts))
    except OSError:
        logger.error("compile_sources filesystem failure")
        return N34CompileOutcome(FormalFailureKind.COMPILE_ERROR, bytes(output), tuple(codes), (),
                                 attested.attestation_digest, tuple(receipts))
    rows = _axioms(bytes(output), type(request) is N4Request)
    kind = None if rows is not None else FormalFailureKind.COMPILE_ERROR
    result = N34CompileOutcome(kind, bytes(output), tuple(codes), () if rows is None else rows,
                               attested.attestation_digest, tuple(receipts))
    logger.debug("compile_sources exit kind=%s", None if kind is None else kind.value)
    return result
