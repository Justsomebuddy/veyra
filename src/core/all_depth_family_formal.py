"""Captured Lean theorem source for the first P1-D3 periodic family."""

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

from .all_depth_family_common import exact_digest, exact_shape, reject
from .all_depth_family_digest import formal_digest
from .all_depth_family_ledger import FOUNDATION_ID, LEAN_TCB_DIGEST
from .all_depth_family_types import FormalFamilySource
from .formal_export_catalog import _strip_lean_comments

from .paths import TMP_DIR

logger = logging.getLogger(__name__)
FORMAL_VERSION = "p1-d3-formal-v1"
ARTIFACT_NAME = "proofs/lean/VeyraAllDepthFamily.lean"
ARTIFACT_SHA256 = "4766c63f1d398eff41d490218acbaa56a396ce61ec06a14fe85b1814cc64a70b"
LEAN_TOOLCHAIN_ID = "leanprover/lean4:v4.30.0-rc2"
LEAN_TCB_DESCRIPTOR = (
    r"veyra.p1d3.lean-runner-tcb.v1\0leanprover/lean4:v4.30.0-rc2\0lean"
    r"\0-DwarningAsError=true\0captured-private-source\0post-read-continuity"
)
THEOREM_IDS = (
    "THM_D3_LEAN_001_coordinate_total",
    "THM_D3_LEAN_002_coordinate_member",
    "THM_D3_LEAN_003_restriction_compatible",
    "THM_D3_LEAN_004_relation_reflexive",
    "THM_D3_LEAN_005_relation_symmetric",
    "THM_D3_LEAN_006_relation_transitive",
    "THM_D3_LEAN_007_restriction_identity",
    "THM_D3_LEAN_008_restriction_composition",
    "THM_D3_LEAN_009_restriction_congruence",
    "THM_D3_LEAN_010_family_equivalence",
    "THM_D3_LEAN_011_constructor_deterministic",
)
AXIOM_CLOSURE: tuple[str, ...] = ()
_AXIOM_ROWS = tuple(f"{name}' does not depend on any axioms" for name in THEOREM_IDS)


def periodic_family_formal_source() -> FormalFamilySource:
    """Build the sole exact formal source without compiling it yet."""
    logger.debug("periodic_family_formal_source entry")
    if sha256(LEAN_TCB_DESCRIPTOR.encode()).hexdigest() != LEAN_TCB_DIGEST:
        reject("formal-tcb-descriptor-drift")
    value = formal_digest(
        FORMAL_VERSION, FOUNDATION_ID, ARTIFACT_NAME, ARTIFACT_SHA256,
        THEOREM_IDS, AXIOM_CLOSURE, LEAN_TOOLCHAIN_ID, LEAN_TCB_DIGEST,
    )
    result = FormalFamilySource(
        FORMAL_VERSION, FOUNDATION_ID, ARTIFACT_NAME, ARTIFACT_SHA256,
        tuple(THEOREM_IDS), tuple(AXIOM_CLOSURE), LEAN_TOOLCHAIN_ID,
        LEAN_TCB_DIGEST, value,
    )
    logger.debug("periodic_family_formal_source exit")
    return result


def snapshot_formal_source(value: FormalFamilySource) -> FormalFamilySource:
    """Reject forged theorem names, axiom closure, source, foundation, or TCB."""
    logger.debug("snapshot_formal_source entry")
    exact_shape(value, FormalFamilySource, "formal-family-source")
    expected = periodic_family_formal_source()
    try:
        scalar_fields = (
            "version", "foundation_id", "artifact_name", "toolchain_id",
        )
        if any(type(getattr(value, name)) is not str for name in scalar_fields):
            reject("formal-source-scalar-must-be-exact-string")
        for name in ("artifact_sha256", "tcb_digest", "formal_source_digest"):
            exact_digest(getattr(value, name), name.replace("_", "-"))
        if type(value.theorem_ids) is not tuple or type(value.axiom_closure) is not tuple:
            reject("formal-source-tuples-must-be-exact")
        if any(type(item) is not str for item in (*value.theorem_ids, *value.axiom_closure)):
            reject("formal-source-row-must-be-exact-string")
    except AttributeError:
        reject("formal-family-source-missing-fields")
    if value != expected:
        reject("formal-family-source-drift")
    logger.debug("snapshot_formal_source exit")
    return expected


def check_formal_source(value: FormalFamilySource) -> FormalFamilySource:
    """Compile captured bytes and bind success to exact post-read continuity."""
    logger.debug("check_formal_source entry")
    source = snapshot_formal_source(value)
    path = Path(source.artifact_name)
    try:
        payload = path.read_bytes()
    except OSError as exc:
        logger.error("formal artifact unavailable error=%s", exc)
        reject("formal-artifact-unavailable")
    if not hmac.compare_digest(sha256(payload).hexdigest(), source.artifact_sha256):
        reject("formal-artifact-drift")
    _check_symbols(payload)
    if not _compile_captured(payload, source.artifact_sha256, source.toolchain_id, source.tcb_digest):
        reject("formal-lean-check-failed")
    try:
        after = path.read_bytes()
    except OSError:
        reject("formal-artifact-continuity-failed")
    if payload != after or sha256(after).hexdigest() != source.artifact_sha256:
        reject("formal-artifact-continuity-failed")
    logger.debug("check_formal_source exit")
    return periodic_family_formal_source()


def _check_symbols(payload: bytes) -> None:
    logger.debug("_check_symbols entry bytes=%d", len(payload))
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeError:
        reject("formal-artifact-invalid-utf8")
    symbols = tuple(re.findall(
        r"(?m)^[ \t]*(?:theorem|lemma)[ \t]+(THM_D3_[A-Za-z0-9_]+)(?=[ \t\r\n:(])",
        _strip_lean_comments(text),
    ))
    if symbols != THEOREM_IDS or "sorry" in text or "admit" in text:
        reject("formal-theorem-set-drift")
    logger.debug("_check_symbols exit count=%d", len(symbols))


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
        with tempfile.TemporaryDirectory(prefix="d3-lean-", dir=root) as directory:
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
    result = completed.returncode == 0 and all(row in output for row in _AXIOM_ROWS)
    logger.debug("_compile_captured exit rc=%d result=%s", completed.returncode, result)
    return result
