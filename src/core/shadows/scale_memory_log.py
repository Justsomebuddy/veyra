"""Scale-memory logarithm recovery certificates for Veyra."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .power import ratio_power
from .ratio import RatioMode, ratio_from_fraction, ratio_from_ints, ratio_shadow

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TransitionDepthRow:
    """One finite candidate for multiplicative transition-depth recovery."""

    label: str
    depth: int
    value: RatioMode
    target: RatioMode
    residual: RatioMode

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready transition-depth row."""
        logger.debug("TransitionDepthRow.as_dict entry label=%s depth=%d", self.label, self.depth)
        result = {
            "label": self.label,
            "depth": self.depth,
            "value": str(ratio_shadow(self.value)),
            "target": str(ratio_shadow(self.target)),
            "residual": str(ratio_shadow(self.residual)),
        }
        logger.debug("TransitionDepthRow.as_dict exit result=%r", result)
        return result


@dataclass(frozen=True)
class ScaleMemoryLogCertificate:
    """Recovered process-depth certificate for a ratio transition."""

    label: str
    candidate: TransitionDepthRow
    tolerance: RatioMode
    status: str
    obstruction: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready scale-memory certificate."""
        logger.debug("ScaleMemoryLogCertificate.as_dict entry label=%s", self.label)
        result = {
            "label": self.label,
            "candidate": self.candidate.as_dict(),
            "tolerance": str(ratio_shadow(self.tolerance)),
            "status": self.status,
            "obstruction": self.obstruction,
        }
        logger.debug("ScaleMemoryLogCertificate.as_dict exit result=%r", result)
        return result


@dataclass(frozen=True)
class CyclicDepthCertificate:
    """Recovered depth certificate for a finite cyclic shadow."""

    label: str
    modulus: int
    generator: int
    target: int
    candidate_depth: int | None
    candidate_value: int | None
    cycle_length: int | None
    status: str
    obstruction: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready cyclic depth certificate."""
        logger.debug("CyclicDepthCertificate.as_dict entry label=%s", self.label)
        result = {
            "label": self.label,
            "modulus": self.modulus,
            "generator": self.generator,
            "target": self.target,
            "candidate_depth": self.candidate_depth,
            "candidate_value": self.candidate_value,
            "cycle_length": self.cycle_length,
            "status": self.status,
            "obstruction": self.obstruction,
        }
        logger.debug("CyclicDepthCertificate.as_dict exit result=%r", result)
        return result


def residual_ratio(value: RatioMode, target: RatioMode) -> RatioMode:
    """Return absolute exact rational residual between two ratio shadows."""
    logger.debug("residual_ratio entry value=%s target=%s", value.word, target.word)
    diff = ratio_shadow(value) - ratio_shadow(target)
    result = ratio_from_fraction(abs(diff))
    logger.debug("residual_ratio exit result=%s", result.word)
    return result


def transition_depth_rows(label: str, base: RatioMode, target: RatioMode, max_depth: int) -> tuple[TransitionDepthRow, ...]:
    """Enumerate finite process-depth rows for base^n against target."""
    logger.debug("transition_depth_rows entry label=%s max_depth=%d", label, max_depth)
    if not label:
        logger.error("transition_depth_rows empty label")
        raise ValueError("label must be nonempty")
    if max_depth < 0:
        logger.error("transition_depth_rows invalid max_depth=%d", max_depth)
        raise ValueError("max_depth must be nonnegative")
    rows = tuple(
        TransitionDepthRow(label, depth, ratio_power(base, depth), target, residual_ratio(ratio_power(base, depth), target))
        for depth in range(max_depth + 1)
    )
    logger.debug("transition_depth_rows exit count=%d", len(rows))
    return rows


def recover_transition_depth(label: str, base: RatioMode, target: RatioMode, max_depth: int, tolerance: RatioMode | None = None) -> ScaleMemoryLogCertificate:
    """Recover best finite transition depth with residual obstruction status."""
    logger.debug("recover_transition_depth entry label=%s max_depth=%d", label, max_depth)
    tol = tolerance if tolerance is not None else ratio_from_ints(0)
    rows = transition_depth_rows(label, base, target, max_depth)
    best = min(rows, key=lambda row: (ratio_shadow(row.residual), row.depth))
    residual = ratio_shadow(best.residual)
    if residual == 0:
        status, obstruction = "exact", "none"
    elif residual <= ratio_shadow(tol):
        status, obstruction = "approximate", "none"
    else:
        status, obstruction = "blocked", "residual-gap"
    result = ScaleMemoryLogCertificate(label, best, tol, status, obstruction)
    logger.debug("recover_transition_depth exit status=%s depth=%d residual=%s", status, best.depth, residual)
    return result


def recover_cyclic_depth(label: str, generator: int, target: int, modulus: int, max_depth: int) -> CyclicDepthCertificate:
    """Recover finite cyclic depth or report cycle/search obstruction."""
    logger.debug("recover_cyclic_depth entry label=%s generator=%d target=%d modulus=%d max_depth=%d", label, generator, target, modulus, max_depth)
    if not label:
        logger.error("recover_cyclic_depth empty label")
        raise ValueError("label must be nonempty")
    if modulus <= 1 or max_depth < 0:
        logger.error("recover_cyclic_depth invalid modulus=%d max_depth=%d", modulus, max_depth)
        raise ValueError("modulus must exceed one and max_depth must be nonnegative")
    current = 1 % modulus
    seen: dict[int, int] = {}
    for depth in range(max_depth + 1):
        if current == target % modulus:
            result = CyclicDepthCertificate(label, modulus, generator % modulus, target % modulus, depth, current, None, "exact", "none")
            logger.debug("recover_cyclic_depth exit exact depth=%d", depth)
            return result
        if current in seen:
            cycle = depth - seen[current]
            result = CyclicDepthCertificate(label, modulus, generator % modulus, target % modulus, None, current, cycle, "blocked", "cycle-collapse")
            logger.debug("recover_cyclic_depth exit cycle=%d", cycle)
            return result
        seen[current] = depth
        current = (current * generator) % modulus
    result = CyclicDepthCertificate(label, modulus, generator % modulus, target % modulus, None, current, None, "blocked", "outside-search-window")
    logger.debug("recover_cyclic_depth exit obstruction=%s", result.obstruction)
    return result


def finite_field_log_fixture() -> CyclicDepthCertificate:
    """Return stable finite-field cyclic unwrap fixture."""
    logger.debug("finite_field_log_fixture entry")
    result = recover_cyclic_depth("finite-field-log", 5, 83, 97, 32)
    logger.debug("finite_field_log_fixture exit result=%r", result.as_dict())
    return result


def scale_memory_obstruction_card() -> CyclicDepthCertificate:
    """Return stable cyclic-collapse obstruction fixture."""
    logger.debug("scale_memory_obstruction_card entry")
    result = recover_cyclic_depth("collapsed-generator", 1, 2, 97, 8)
    logger.debug("scale_memory_obstruction_card exit result=%r", result.as_dict())
    return result


def scale_memory_log_checklist() -> tuple[str, ...]:
    """Return checklist for the scale-memory logarithm layer."""
    logger.debug("scale_memory_log_checklist entry")
    result = (
        "exact transition-depth recovery is separated from approximate recovery",
        "residual gaps are explicit obstructions rather than silent failures",
        "cyclic shadows use unwrap certificates with branch/cycle status",
        "finite cyclic readings remain bounded unless independently generalized",
    )
    logger.debug("scale_memory_log_checklist exit count=%d", len(result))
    return result
