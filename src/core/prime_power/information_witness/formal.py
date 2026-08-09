"""Private N6-W replay layered on the repaired N6 capture/formal continuity."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import re
from typing import cast

from .sources import snapshot_theorem_source
from .types import N6WTheoremSourceV1
from ...prime_power_unbounded_capture import capture_fixed_source
from ...prime_power_unbounded_common import digest, reject, sha
from ...prime_power_unbounded_formal import (
    capture_e_sources,
    continuity_holds as e_continuity_holds,
)
from ...prime_power_unbounded_sources import theorem_source as n6_theorem_source
from ...prime_power_unbounded_types import N6FormalFailureKind, N6Lane
from ...construction.stream_completion.formal_process import FormalPhaseReceipt
from ...construction.stream_completion.types import FormalExecutionFailureKind

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class N6WCompileOutcomeV1:
    """Exact combined base-N6 and N6-W execution transcript."""

    kind: N6FormalFailureKind | None
    output: bytes
    return_codes: tuple[int, ...]
    theorem_axiom_rows: tuple[tuple[str, tuple[str, ...]], ...]
    attestation_digest: str
    phase_receipts: tuple[FormalPhaseReceipt, ...]
    base_formal_run_digest: str


def _symbols(payload: bytes) -> None:
    """Require the exact import, record, constructor, theorems and no placeholders."""
    logger.debug("_symbols entry bytes=%d", len(payload))
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeError:
        reject("n6w-formal-source-invalid-utf8")
    imports = tuple(re.findall(r"(?m)^import\s+(\S+)\s*$", text))
    theorems = tuple(re.findall(
        r"(?m)^theorem\s+(THM_P3N6W_[A-Za-z0-9_]+)(?=[\s:(])", text,
    ))
    records = tuple(re.findall(
        r"(?m)^structure\s+(VeyraPrimePowerLateWitness)(?=[\s{:(])", text,
    ))
    constructors = tuple(re.findall(
        r"(?m)^def\s+(veyraPrimePowerLateWitness)(?=[\s{:(])", text,
    ))
    theorem_ids = (
        "THM_P3N6W_001_exact_shape", "THM_P3N6W_002_prefix",
        "THM_P3N6W_003_later", "THM_P3N6W_004_uniform",
    )
    if (
        imports != ("VeyraPrimePowerUnbounded",)
        or theorems != theorem_ids
        or records != ("VeyraPrimePowerLateWitness",)
        or constructors != ("veyraPrimePowerLateWitness",)
        or re.search(r"\b(?:sorry|admit|axiom|unsafe)\b", text)
    ):
        reject("n6w-formal-symbol-or-import-drift")
    logger.debug("_symbols exit theorems=%d", len(theorems))


def capture_sources(source: N6WTheoremSourceV1) -> tuple[bytes, bytes, bytes, bytes]:
    """Use N6's repaired capture for its chain, then capture the isolated W leaf."""
    logger.debug("capture_sources entry")
    checked = snapshot_theorem_source(source)
    base_source = n6_theorem_source(N6Lane.E_POWER_INJECTION)
    logger.debug("capture_sources external-call=capture_e_sources state=begin")
    base = capture_e_sources(base_source)
    logger.debug("capture_sources external-call=capture_e_sources state=end")
    if checked.direct_import != (
        base_source.artifact_path_id, base_source.artifact_sha256,
    ):
        reject("n6w-formal-base-source-binding-drift")
    leaf = capture_fixed_source(checked.artifact_path_id, checked.artifact_sha256)
    _symbols(leaf)
    result = (base[0], base[1], base[2], leaf)
    logger.debug("capture_sources exit sources=4 bytes=%d", sum(map(len, result)))
    return result


def continuity_holds(
    source: N6WTheoremSourceV1,
    captured: tuple[bytes, bytes, bytes, bytes],
) -> bool:
    """Reopen both the repaired N6 chain and isolated W source after execution."""
    logger.debug("continuity_holds entry")
    try:
        base = n6_theorem_source(N6Lane.E_POWER_INJECTION)
        snapshot_theorem_source(source)
        result = bool(
            e_continuity_holds(base, (captured[0], captured[1], captured[2]))
            and capture_fixed_source(
                source.artifact_path_id, source.artifact_sha256,
            ) == captured[3]
        )
    except Exception:
        logger.error("continuity_holds recapture failed")
        result = False
    logger.debug("continuity_holds exit result=%s", result)
    return result


def _failure(
    kind: N6FormalFailureKind,
    output: bytes,
    codes: list[int],
    receipts: list[FormalPhaseReceipt],
    attestation: str,
    base_run: str,
) -> N6WCompileOutcomeV1:
    """Build one typed operational failure without semantic reclassification."""
    logger.debug("_failure entry kind=%s", kind.value)
    result = N6WCompileOutcomeV1(
        kind, output, tuple(codes), (), attestation, tuple(receipts), base_run,
    )
    logger.debug("_failure exit kind=%s", kind.value)
    return result


def _kind(value: FormalExecutionFailureKind) -> N6FormalFailureKind:
    """Map only the shared runner's operational vocabulary."""
    logger.debug("_kind entry kind=%s", value.value)
    result = N6FormalFailureKind(value.value)
    logger.debug("_kind exit kind=%s", result.value)
    return result


def _axioms(output: bytes) -> tuple[tuple[str, tuple[str, ...]], ...] | None:
    """Parse the exact ordered four-row propext closure."""
    logger.debug("_axioms entry bytes=%d", len(output))
    pattern = re.compile(
        r"(?m)^'([^']+)' (does not depend on any axioms|depends on axioms: \[([^\]]*)\])$"
    )
    expected_source = snapshot_theorem_source_source()
    theorem_ids = expected_source.theorem_ids
    matches = tuple(
        (name, phrase, body)
        for name, phrase, body in pattern.findall(output.decode("utf-8", errors="replace"))
        if name in theorem_ids
    )
    if tuple(name for name, _, _ in matches) != theorem_ids:
        logger.error("_axioms missing, duplicate or reordered rows")
        return None
    rows = tuple(
        (name, () if phrase.startswith("does not") else tuple(sorted(body.split(", "))))
        for name, phrase, body in matches
    )
    expected = expected_source.theorem_axiom_rows
    result = rows if rows == expected else None
    if result is None:
        logger.error("_axioms exact closure drift")
    logger.debug("_axioms exit matched=%s", result is not None)
    return result


def snapshot_theorem_source_source() -> N6WTheoremSourceV1:
    """Return the exact source through its validator for local immutable use."""
    logger.debug("snapshot_theorem_source_source entry")
    from .sources import theorem_source

    result = snapshot_theorem_source(theorem_source())
    logger.debug("snapshot_theorem_source_source exit")
    return result


def formal_run_digest(outcome: N6WCompileOutcomeV1) -> str:
    """Bind both N6-E dependency replay and the exact W phase receipts."""
    logger.debug("formal_run_digest entry")
    if type(outcome) is not N6WCompileOutcomeV1:
        reject("n6w-formal-outcome-exact-type-required")
    rows: list[tuple[str, bytes]] = [
        ("base-run", outcome.base_formal_run_digest.encode()),
        ("kind", b"" if outcome.kind is None else outcome.kind.value.encode()),
        ("output", sha(outcome.output).encode()),
        ("attestation", outcome.attestation_digest.encode()),
    ]
    rows.extend(
        (f"return-{index}", value.to_bytes(8, "big", signed=True))
        for index, value in enumerate(outcome.return_codes)
    )
    rows.extend(
        (f"phase-{index}", (
            f"{value.phase}\0{value.return_code}\0{value.output_bytes}\0"
            f"{value.output_digest}\0"
            f"{'' if value.failure_kind is None else value.failure_kind.value}"
        ).encode())
        for index, value in enumerate(outcome.phase_receipts)
    )
    result = digest("veyra.p3n6w.formal-run.v1", tuple(rows))
    logger.debug("formal_run_digest exit phases=%d", len(outcome.phase_receipts))
    return cast(str, result)
