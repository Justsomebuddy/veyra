"""Captured PΩ2 source, exact Lean output, and bounded private compilation."""

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
from .padic_completion_common import exact_digest, exact_shape, reject, sha
from .padic_completion_digest import digest, texts
from .padic_completion_prime import _witness_bytes
from .padic_completion_types import (
    PadicCompletionTheoremSource, PadicExecutionFailureKind, PrimeSource,
)
from .stream_completion_formal_attestation import ToolchainContract, attest_toolchain
from .stream_completion_formal_process import FormalPhaseReceipt, capture_phase

from .paths import TMP_DIR

logger = logging.getLogger(__name__)
FORMAL_VERSION = "pomega2-formal-v1"
ARTIFACT_PATH = "proofs/lean/VeyraPadicCompletion.lean"
ARTIFACT_SHA256 = "28052d0260b1535e484ddd8e70f97fea945ca3ff9a23c358bb45d209a071a18f"
TOOLCHAIN_ID = "leanprover/lean4:v4.30.0-rc2"
LEAN_VERSION = (
    "Lean (version 4.30.0-rc2, x86_64-unknown-linux-gnu, "
    "commit 3dc1a088b6d2d8eafe25a7cd7ec7b58d731bd7cc, Release)\n"
)
ELAN_SHA256 = "19d38963260cfb376f1aab0f0fbcf4e80ec25c8bd0ba3b1797d95141d56ec55a"
LEAN_BINARY_SHA256 = "3e0d0d3d801675359f2d4cf9815bfdb417b20b92fdd9d48b3b14c95bbae28bbf"
REPRESENTATION_ID = "literal-dependent-subtype-of-compatible-prime-power-Fin-families-v2"
CANONICAL_OPS_ID = "veyraCanonicalStageRingLaws"
CONCRETE_INSTANCE_ID = "pomega2ConcreteCompletion"
CANONICAL_OPS_AXIOMS = ("propext",)
CONCRETE_INSTANCE_AXIOMS = ("Quot.sound", "propext")
THEOREM_IDS = tuple(
    f"THM_POMEGA2_{index:03d}_{suffix}" for index, suffix in enumerate((
        "prime_lower_bound", "stage_modulus_divisibility",
        "reduction_well_formed_congruence", "reduction_identity",
        "reduction_composition", "carrier_presentation_compatible",
        "universal_realization", "coordinate_agreement", "joint_separation",
        "relative_uniqueness", "zero_family_nonvacuity", "one_family_formation",
        "addition_closure", "negation_additive_inverse", "multiplication_closure",
        "full_commutative_ring", "ppcp_introduction",
    ), 1)
)
TCB_DIGEST = digest("veyra.pomega2.tcb.v1", (
    ("toolchain", TOOLCHAIN_ID.encode()), ("elan", ELAN_SHA256.encode()),
    ("lean", LEAN_BINARY_SHA256.encode()), ("version", LEAN_VERSION.encode()),
    ("process", b"shared-deadline-live-output-cap-process-group-kill"),
))
TOOLCHAIN_ATTESTATION_DIGEST = digest("veyra.pomega2.attestation.v1", (
    ("toolchain", TOOLCHAIN_ID.encode()), ("elan", ELAN_SHA256.encode()),
    ("lean", LEAN_BINARY_SHA256.encode()), ("version", LEAN_VERSION.encode()),
))
TheoremAxiomRows = tuple[tuple[str, tuple[str, ...]], ...]


@dataclass(frozen=True)
class PadicCompileOutcome:
    kind: PadicExecutionFailureKind | None
    output: bytes
    return_codes: tuple[int, ...]
    theorem_axiom_rows: TheoremAxiomRows = ()
    attestation_digest: str = TOOLCHAIN_ATTESTATION_DIGEST
    phase_receipts: tuple[FormalPhaseReceipt, ...] = ()


def padic_completion_theorem_source() -> PadicCompletionTheoremSource:
    """Construct the sole pinned generic 17-theorem source."""
    logger.debug("padic_completion_theorem_source entry")
    value = digest("veyra.pomega2.formal-source.v1", (
        ("version", FORMAL_VERSION.encode()), ("artifact", ARTIFACT_PATH.encode()),
        ("artifact-sha", ARTIFACT_SHA256.encode()), *texts("theorem", THEOREM_IDS),
        ("representation", REPRESENTATION_ID.encode()),
        ("canonical-ops", CANONICAL_OPS_ID.encode()),
        ("concrete-instance", CONCRETE_INSTANCE_ID.encode()),
        ("toolchain", TOOLCHAIN_ID.encode()), ("tcb", TCB_DIGEST.encode()),
    ))
    result = PadicCompletionTheoremSource(
        FORMAL_VERSION, ARTIFACT_PATH, ARTIFACT_SHA256, THEOREM_IDS,
        REPRESENTATION_ID, CANONICAL_OPS_ID, CONCRETE_INSTANCE_ID,
        TOOLCHAIN_ID, TCB_DIGEST, value,
    )
    logger.debug("padic_completion_theorem_source exit")
    return result


def snapshot_theorem_source(value: PadicCompletionTheoremSource) -> PadicCompletionTheoremSource:
    """Reject theorem order, source, representation, toolchain, or TCB drift."""
    logger.debug("snapshot_theorem_source entry")
    exact_shape(value, PadicCompletionTheoremSource, "padic-theorem-source")
    try:
        if type(value.theorem_ids) is not tuple or len(value.theorem_ids) != 17:
            reject("padic-theorem-count-invalid")
        if any(type(item) is not str for item in value.theorem_ids):
            reject("padic-theorem-id-type-invalid")
        for name in (
            "version", "artifact_path_id", "representation_id", "canonical_ops_id",
            "concrete_instance_id", "toolchain_id",
        ):
            if type(getattr(value, name)) is not str:
                reject("padic-theorem-source-scalar-invalid")
        for name in ("artifact_sha256", "tcb_digest", "source_digest"):
            exact_digest(getattr(value, name), name)
    except AttributeError:
        reject("padic-theorem-source-missing-fields")
    expected = padic_completion_theorem_source()
    if value != expected:
        reject("padic-theorem-source-drift")
    logger.debug("snapshot_theorem_source exit")
    return expected


def _read_bounded(path: Path) -> bytes | None:
    """Read at most one byte beyond the formal hard cap."""
    logger.debug("_read_bounded entry file=%s", path.name)
    try:
        with path.open("rb") as handle:
            result = handle.read(2 * 1024 * 1024 + 1)
    except OSError as exc:
        logger.error("_read_bounded failed error=%s", exc)
        return None
    logger.debug("_read_bounded exit bytes=%d", len(result))
    return result


def capture_generic_source(source: PadicCompletionTheoremSource) -> bytes:
    """Read once, authenticate, and exact-symbol-check generic Lean bytes."""
    logger.debug("capture_generic_source entry")
    source = snapshot_theorem_source(source)
    payload = _read_bounded(Path(source.artifact_path_id))
    if payload is None or len(payload) > 2 * 1024 * 1024:
        reject("padic-artifact-unavailable-or-too-large")
    if sha(payload) != source.artifact_sha256:
        reject("padic-artifact-drift")
    _check_symbols(payload)
    logger.debug("capture_generic_source exit bytes=%d", len(payload))
    return payload


def _check_symbols(payload: bytes) -> None:
    """Require exactly the ordered 17 declarations and no placeholders."""
    logger.debug("_check_symbols entry")
    try:
        clean = _strip_lean_comments(payload.decode("utf-8", errors="strict"))
    except UnicodeError:
        reject("padic-formal-invalid-utf8")
    found = tuple(re.findall(
        r"(?m)^[ \t]*(?:theorem|lemma)[ \t]+(THM_POMEGA2_[A-Za-z0-9_]+)(?=[ \t\r\n:(])",
        clean,
    ))
    if found != THEOREM_IDS or re.search(r"\b(?:sorry|admit)\b", clean):
        reject("padic-formal-symbol-set-drift")
    logger.debug("_check_symbols exit count=%d", len(found))


def validate_captured_sources(generic: bytes, prime: PrimeSource) -> None:
    """Validate both captured byte identities before policy or execution."""
    logger.debug("validate_captured_sources entry")
    if type(generic) is not bytes or len(generic) > 2 * 1024 * 1024 or sha(generic) != ARTIFACT_SHA256:
        reject("captured-padic-source-invalid")
    witness = prime.generated_witness_bytes
    if type(witness) is not bytes or len(witness) > 2 * 1024 * 1024:
        reject("captured-prime-witness-invalid")
    if sha(witness) != prime.generated_witness_sha256 or witness != _witness_bytes(prime.p):
        reject("captured-prime-witness-drift")
    logger.debug("validate_captured_sources exit")


def _parse_axiom_rows(payload: bytes) -> TheoremAxiomRows | None:
    """Parse exactly 17 ordered duplicate-free Lean axiom reports."""
    logger.debug("_parse_axiom_rows entry bytes=%d", len(payload))
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeError:
        logger.error("_parse_axiom_rows invalid utf8")
        return None
    pattern = re.compile(
        r"(?m)^'(THM_POMEGA2_[A-Za-z0-9_]+)' (does not depend on any axioms|depends on axioms: \[([^\]]*)\])$"
    )
    matches = tuple(pattern.findall(text))
    if tuple(row[0] for row in matches) != THEOREM_IDS or len(matches) != 17:
        logger.error("_parse_axiom_rows theorem set mismatch")
        return None
    auxiliary = tuple(re.findall(
        r"(?m)^'(veyraCanonicalStageRingLaws|pomega2PrimeWitness|pomega2ConcreteCompletion)' "
        r"(does not depend on any axioms|depends on axioms: \[([^\]]*)\])$", text,
    ))
    expected_auxiliary = (
        (CANONICAL_OPS_ID, CANONICAL_OPS_AXIOMS), ("pomega2PrimeWitness", ()),
        (CONCRETE_INSTANCE_ID, CONCRETE_INSTANCE_AXIOMS),
    )
    parsed_auxiliary = tuple(
        (name, () if phrase.startswith("does not") else tuple(sorted(body.split(", "))))
        for name, phrase, body in auxiliary
    )
    if parsed_auxiliary != expected_auxiliary:
        logger.error("_parse_axiom_rows auxiliary witness rows mismatch")
        return None
    rows = tuple((name, () if phrase.startswith("does not") else tuple(sorted(body.split(", "))))
                 for name, phrase, body in matches)
    if any(re.fullmatch(r"[A-Za-z0-9_.]+", item) is None for _, closure in rows for item in closure):
        logger.error("_parse_axiom_rows invalid axiom id")
        return None
    logger.debug("_parse_axiom_rows exit rows=%d", len(rows))
    return rows


def _kind(value: object) -> PadicExecutionFailureKind | None:
    """Translate the shared bounded-process enum into the PΩ2 result vocabulary."""
    logger.debug("_kind entry value=%r", value)
    result = None if value is None else PadicExecutionFailureKind(value.value)
    logger.debug("_kind exit result=%r", result)
    return result


def compile_captured_sources(
    generic: bytes, witness: bytes, timeout: int, max_output: int,
) -> PadicCompileOutcome:
    """Attest and compile two captured sources under one deadline/live cap."""
    logger.debug("compile_captured_sources entry")
    elan = shutil.which("elan")
    deadline = time.monotonic() + timeout
    if elan is None:
        logger.error("compile_captured_sources elan unavailable")
        return PadicCompileOutcome(PadicExecutionFailureKind.COMPILE_ERROR, b"", ())
    contract = ToolchainContract(
        TOOLCHAIN_ID, ELAN_SHA256, LEAN_BINARY_SHA256, LEAN_VERSION.encode(),
        TOOLCHAIN_ATTESTATION_DIGEST,
    )
    attested = attest_toolchain(elan, deadline, max_output, contract)
    if attested.kind is not None:
        return PadicCompileOutcome(
            _kind(attested.kind), attested.output, attested.return_codes, (),
            attested.attestation_digest, attested.phase_receipts,
        )
    combined = bytearray(attested.output)
    codes = list(attested.return_codes)
    receipts = list(attested.phase_receipts)
    try:
        root = TMP_DIR
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="pomega2-", dir=root) as directory:
            private = Path(directory)
            paths = (
                private / "VeyraPadicCompletion.lean", private / "PadicPrimeInstance.lean",
            )
            for path, payload in zip(paths, (generic, witness), strict=True):
                path.write_bytes(payload)
                path.chmod(0o400)
            commands = (
                [elan, "run", TOOLCHAIN_ID, "lean", "-DwarningAsError=true",
                 "-o", "VeyraPadicCompletion.olean", paths[0].name],
                [elan, "run", TOOLCHAIN_ID, "lean", "-DwarningAsError=true", paths[1].name],
            )
            environment = dict(os.environ, LEAN_PATH=str(private.resolve()))
            for phase, command in zip(("generic-compile", "prime-compile"), commands, strict=True):
                captured = capture_phase(
                    phase, command, private, deadline, max_output - len(combined), environment,
                )
                codes.append(captured.return_code)
                receipts.append(captured.receipt)
                combined.extend(captured.output)
                if captured.kind is not None:
                    return PadicCompileOutcome(
                        _kind(captured.kind), bytes(combined), tuple(codes), (),
                        attested.attestation_digest, tuple(receipts),
                    )
    except OSError as exc:
        logger.error("compile_captured_sources filesystem error=%s", exc)
        return PadicCompileOutcome(
            PadicExecutionFailureKind.COMPILE_ERROR, bytes(combined), tuple(codes), (),
            attested.attestation_digest, tuple(receipts),
        )
    rows = _parse_axiom_rows(bytes(combined))
    kind = None if rows is not None else PadicExecutionFailureKind.COMPILE_ERROR
    logger.debug("compile_captured_sources exit kind=%r", kind)
    return PadicCompileOutcome(
        kind, bytes(combined), tuple(codes), () if rows is None else rows,
        attested.attestation_digest, tuple(receipts),
    )


def continuity_holds(generic: bytes, prime: PrimeSource) -> bool:
    """Re-read the artifact and regenerate the witness after compilation."""
    logger.debug("continuity_holds entry")
    current = _read_bounded(Path(ARTIFACT_PATH))
    result = current == generic and sha(generic) == ARTIFACT_SHA256 and _witness_bytes(prime.p) == prime.generated_witness_bytes
    logger.debug("continuity_holds exit result=%s", result)
    return result
