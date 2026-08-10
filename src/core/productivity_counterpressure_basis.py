"""Exact Lean-backed foundation source for P1-D2 countermodels."""

from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
import hmac
import logging
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from .formal_export_catalog import _strip_lean_comments
from .productivity_counterpressure_common import exact_dataclass_shape, exact_digest, reject
from .productivity_counterpressure_digest import basis_digest as make_basis_digest
from .productivity_counterpressure_types import CounterpressureBasisSource, DerivationKind

from .paths import TMP_DIR

logger = logging.getLogger(__name__)
BASIS_VERSION = "p1-d2-basis-v1"
BASIS_ID = "p1-d2-nat-countermodels-v1"
FOUNDATION_ID = "lean4-nat-v4.30.0-rc2"
ARTIFACT_NAME = "proofs/lean/VeyraProductivityCounterpressure.lean"
ARTIFACT_SHA256 = "32ebbb960c6a3091402f3dcddf6753c5cf451a7c98357b68ff08fd13e390fcec"
LEAN_TOOLCHAIN_ID = "leanprover/lean4:v4.30.0-rc2"
LEAN_TCB_DESCRIPTOR = (
    r"veyra.p1d2.lean-runner-tcb.v1\0leanprover/lean4:v4.30.0-rc2\0lean"
    r"\0-DwarningAsError=true\0captured-private-source\0post-read-continuity"
)
LEAN_TCB_DIGEST = "8687516385b19c5799d2fe08f3c8721fee41c261aff9499205b9132dd968acff"
THEOREM_IDS = (
    "THM_D2_LEAN_001_finite_strict_descent",
    "THM_D2_LEAN_002_no_infinite_nat_descent",
    "THM_D2_LEAN_003a_self_mem",
    "THM_D2_LEAN_003b_succ_subset",
    "THM_D2_LEAN_003c_diagonal_absence",
)
_AXIOM_ROWS = (
    "THM_D2_LEAN_001_finite_strict_descent' depends on axioms: [propext, Quot.sound]",
    "THM_D2_LEAN_002_no_infinite_nat_descent' depends on axioms: [propext, Quot.sound]",
    "THM_D2_LEAN_003a_self_mem' does not depend on any axioms",
    "THM_D2_LEAN_003b_succ_subset' does not depend on any axioms",
    "THM_D2_LEAN_003c_diagonal_absence' does not depend on any axioms",
)


def counterpressure_basis_source() -> CounterpressureBasisSource:
    """Build the sole exact foundation source without compiling it yet."""
    logger.debug("counterpressure_basis_source entry")
    if sha256(LEAN_TCB_DESCRIPTOR.encode()).hexdigest() != LEAN_TCB_DIGEST:
        reject("lean-tcb-descriptor-drift")
    digest = make_basis_digest(
        BASIS_VERSION, BASIS_ID, DerivationKind.LEAN_CHECKED_THEOREM.value,
        FOUNDATION_ID, ARTIFACT_NAME, ARTIFACT_SHA256, THEOREM_IDS,
        LEAN_TOOLCHAIN_ID, LEAN_TCB_DIGEST,
    )
    result = CounterpressureBasisSource(
        BASIS_VERSION, BASIS_ID, DerivationKind.LEAN_CHECKED_THEOREM,
        FOUNDATION_ID, ARTIFACT_NAME, ARTIFACT_SHA256, tuple(list(THEOREM_IDS)),
        LEAN_TOOLCHAIN_ID, LEAN_TCB_DIGEST, digest,
    )
    logger.debug("counterpressure_basis_source exit digest=%s", digest)
    return result


def snapshot_basis_source(value: CounterpressureBasisSource) -> CounterpressureBasisSource:
    """Reject basis subclasses, field drift, and theorem-name lookalikes."""
    logger.debug("snapshot_basis_source entry")
    exact_dataclass_shape(value, CounterpressureBasisSource, "basis-source")
    expected = counterpressure_basis_source()
    try:
        exact_digest(value.artifact_sha256, "artifact-sha256")
        exact_digest(value.tcb_digest, "tcb-digest")
        exact_digest(value.basis_digest, "basis-digest")
        if type(value.theorem_ids) is not tuple:
            reject("basis-theorem-ids-must-be-exact-tuple")
        scalar_rows = (
            (value.version, expected.version), (value.basis_id, expected.basis_id),
            (value.foundation_id, expected.foundation_id),
            (value.artifact_name, expected.artifact_name),
            (value.artifact_sha256, expected.artifact_sha256),
            (value.toolchain_id, expected.toolchain_id),
            (value.tcb_digest, expected.tcb_digest),
            (value.basis_digest, expected.basis_digest),
        )
        if any(type(actual) is not str or actual != wanted for actual, wanted in scalar_rows):
            reject("basis-source-drift")
        if (
            type(value.derivation_kind) is not DerivationKind
            or value.derivation_kind is not expected.derivation_kind
            or len(value.theorem_ids) != len(expected.theorem_ids)
            or any(
                type(actual) is not str or actual != wanted
                for actual, wanted in zip(value.theorem_ids, expected.theorem_ids, strict=True)
            )
        ):
            reject("basis-source-drift")
        supplied = CounterpressureBasisSource(
            value.version, value.basis_id, value.derivation_kind, value.foundation_id,
            value.artifact_name, value.artifact_sha256, tuple(value.theorem_ids),
            value.toolchain_id, value.tcb_digest, value.basis_digest,
        )
    except AttributeError:
        reject("basis-source-missing-fields")
    if supplied != expected:
        reject("basis-source-drift")
    logger.debug("snapshot_basis_source exit")
    return expected


def check_basis_source(value: CounterpressureBasisSource) -> CounterpressureBasisSource:
    """Compile captured exact bytes and rebind cached success to live continuity."""
    logger.debug("check_basis_source entry")
    source = snapshot_basis_source(value)
    path = Path(source.artifact_name)
    try:
        payload = path.read_bytes()
    except OSError as exc:
        logger.error("check_basis_source read failed error=%s", exc)
        reject("basis-artifact-unavailable")
    actual = sha256(payload).hexdigest()
    if not hmac.compare_digest(actual, source.artifact_sha256):
        reject("basis-artifact-drift")
    _check_exact_symbols(payload, source.theorem_ids)
    if not _compile_captured(payload, source.artifact_sha256, source.toolchain_id, source.tcb_digest):
        reject("basis-lean-check-failed")
    try:
        after = path.read_bytes()
    except OSError as exc:
        logger.error("check_basis_source reread failed error=%s", exc)
        reject("basis-artifact-continuity-failed")
    if payload != after or sha256(after).hexdigest() != source.artifact_sha256:
        reject("basis-artifact-continuity-failed")
    logger.debug("check_basis_source exit")
    return counterpressure_basis_source()


def _check_exact_symbols(payload: bytes, expected: tuple[str, ...]) -> None:
    logger.debug("_check_exact_symbols entry bytes=%d", len(payload))
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeError:
        reject("basis-artifact-invalid-utf8")
    symbols = tuple(re.findall(
        r"(?m)^[ \t]*(?:theorem|lemma)[ \t]+(THM_D2_[A-Za-z0-9_]+)(?=[ \t:(])",
        _strip_lean_comments(text),
    ))
    if symbols != expected:
        reject("basis-theorem-set-drift")
    logger.debug("_check_exact_symbols exit count=%d", len(symbols))


@lru_cache(maxsize=1)
def _compile_captured(payload: bytes, artifact_digest: str, toolchain: str, tcb: str) -> bool:
    logger.debug("_compile_captured entry bytes=%d", len(payload))
    if (
        sha256(payload).hexdigest() != artifact_digest or toolchain != LEAN_TOOLCHAIN_ID
        or tcb != LEAN_TCB_DIGEST
        or sha256(LEAN_TCB_DESCRIPTOR.encode()).hexdigest() != LEAN_TCB_DIGEST
    ):
        logger.error("_compile_captured identity precheck failed")
        return False
    elan = shutil.which("elan")
    if elan is None:
        logger.error("_compile_captured elan unavailable")
        return False
    root = TMP_DIR
    try:
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="d2-lean-", dir=root) as directory:
            capture = Path(directory) / f"{artifact_digest}.lean"
            capture.write_bytes(payload)
            capture.chmod(0o600)
            completed = subprocess.run(
                [elan, "run", toolchain, "lean", "-DwarningAsError=true", capture.name],
                cwd=capture.parent, capture_output=True, text=True, timeout=120, check=False,
            )
    except (OSError, subprocess.SubprocessError) as exc:
        logger.error("_compile_captured failed error=%s", exc)
        return False
    output = completed.stdout + completed.stderr
    axioms_exact = all(row in output for row in _AXIOM_ROWS)
    result = completed.returncode == 0 and axioms_exact
    logger.debug("_compile_captured exit rc=%d axioms=%s", completed.returncode, axioms_exact)
    return result
