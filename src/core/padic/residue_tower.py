"""Finite p-adic residue windows for the bounded I1 experiment.

One concept end to end: the immutable residue DTOs, the exact-type and resource
gates that admit them, and the window logic — construction, projection,
compatibility, and componentwise arithmetic — built on top. Compatibility is
reported only across the supplied finite stages; nothing here claims a
completed limit.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Callable

logger = logging.getLogger(__name__)

MAX_PADIC_DEPTH = 128
MAX_PADIC_PRIME = 257
MAX_PADIC_SOURCE_BITS = 4096


@dataclass(frozen=True)
class PrimeBase:
    """One exact bounded prime used by a residue window."""

    prime: int


@dataclass(frozen=True)
class PadicResidueStage:
    """A canonical residue modulo ``p^(level + 1)``."""

    level: int
    modulus: int
    residue: int


@dataclass(frozen=True)
class PadicResidueWindow:
    """A finite candidate inverse-system window over one prime."""

    prime: PrimeBase
    stages: tuple[PadicResidueStage, ...]


@dataclass(frozen=True)
class PadicCompatibilityObstruction:
    """The first residue that fails to restrict to its predecessor."""

    lower_index: int
    upper_index: int
    expected_residue: int
    projected_residue: int


@dataclass(frozen=True)
class PadicCoherenceReport:
    """Finite compatibility status; it makes no completed-limit claim."""

    prime: int
    depth: int
    checked_links: int
    coherent: bool
    first_obstruction: PadicCompatibilityObstruction | None
    scope: str = "finite-prime-power-window"


class PadicResidueValidationError(ValueError):
    """A finite p-adic DTO failed exact structural validation."""


def is_bounded_prime(value: int) -> bool:
    """Decide primality inside the deliberately tiny I1 resource bound."""
    logger.debug("is_bounded_prime entry")
    if type(value) is not int or not 2 <= value <= MAX_PADIC_PRIME:
        logger.debug("is_bounded_prime exit result=False")
        return False
    divisor = 2
    while divisor * divisor <= value:
        if value % divisor == 0:
            result = value == divisor
            logger.debug("is_bounded_prime exit result=%s", result)
            return result
        divisor += 1
    logger.debug("is_bounded_prime exit result=True")
    return True


def snapshot_prime_base(value: PrimeBase) -> PrimeBase:
    """Capture one exact bounded prime base."""
    logger.debug("snapshot_prime_base entry")
    if type(value) is not PrimeBase:
        logger.error("snapshot_prime_base invalid container type")
        raise PadicResidueValidationError("base must be an exact PrimeBase")
    try:
        prime = value.prime
    except AttributeError as exc:
        logger.error("snapshot_prime_base missing field")
        raise PadicResidueValidationError("prime is missing required fields") from exc
    if not is_bounded_prime(prime):
        logger.error("snapshot_prime_base invalid prime")
        raise PadicResidueValidationError("prime must be an exact bounded prime integer")
    result = PrimeBase(prime)
    logger.debug("snapshot_prime_base exit prime=%d", result.prime)
    return result


def snapshot_padic_stage(
    value: PadicResidueStage, prime: PrimeBase, expected_level: int
) -> PadicResidueStage:
    """Capture one canonical stage without checking predecessor agreement."""
    logger.debug("snapshot_padic_stage entry")
    prime = snapshot_prime_base(prime)
    if type(expected_level) is not int or not 0 <= expected_level < MAX_PADIC_DEPTH:
        logger.error("snapshot_padic_stage invalid expected level")
        raise PadicResidueValidationError("expected level must be a bounded exact integer")
    if type(value) is not PadicResidueStage:
        logger.error("snapshot_padic_stage invalid container type")
        raise PadicResidueValidationError("stage must be an exact PadicResidueStage")
    try:
        level, modulus, residue = value.level, value.modulus, value.residue
    except AttributeError as exc:
        logger.error("snapshot_padic_stage missing field")
        raise PadicResidueValidationError("stage is missing required fields") from exc
    if any(type(item) is not int for item in (level, modulus, residue)):
        logger.error("snapshot_padic_stage nonexact integer field")
        raise PadicResidueValidationError("stage fields must be exact integers")
    expected_modulus = prime.prime ** (expected_level + 1)
    if level != expected_level or modulus != expected_modulus:
        logger.error("snapshot_padic_stage level/modulus mismatch level=%r", level)
        raise PadicResidueValidationError("stage level or prime-power modulus is not canonical")
    if not 0 <= residue < modulus:
        logger.error("snapshot_padic_stage noncanonical residue level=%d", level)
        raise PadicResidueValidationError("stage residue must be canonical")
    result = PadicResidueStage(level, modulus, residue)
    logger.debug("snapshot_padic_stage exit level=%d", result.level)
    return result


def snapshot_padic_window(value: PadicResidueWindow) -> PadicResidueWindow:
    """Deep-capture a structural candidate while preserving incompatibility."""
    logger.debug("snapshot_padic_window entry")
    if type(value) is not PadicResidueWindow:
        logger.error("snapshot_padic_window invalid container type")
        raise PadicResidueValidationError("window must be an exact PadicResidueWindow")
    try:
        source_prime, source_stages = value.prime, value.stages
    except AttributeError as exc:
        logger.error("snapshot_padic_window missing field")
        raise PadicResidueValidationError("window is missing required fields") from exc
    prime = snapshot_prime_base(source_prime)
    if type(source_stages) is not tuple or not 1 <= len(source_stages) <= MAX_PADIC_DEPTH:
        logger.error("snapshot_padic_window invalid stages container")
        raise PadicResidueValidationError("stages must be a bounded nonempty exact tuple")
    stages = tuple(
        snapshot_padic_stage(stage, prime, level)
        for level, stage in enumerate(source_stages)
    )
    result = PadicResidueWindow(prime, stages)
    logger.debug("snapshot_padic_window exit levels=%d", len(stages))
    return result


def validate_padic_source_integer(value: int) -> int:
    """Reject bool/subclasses and integers beyond the constructor budget."""
    logger.debug("validate_padic_source_integer entry")
    if type(value) is not int or value.bit_length() > MAX_PADIC_SOURCE_BITS:
        logger.error("validate_padic_source_integer invalid source")
        raise PadicResidueValidationError("source must be a bounded exact integer")
    logger.debug("validate_padic_source_integer exit bits=%d", value.bit_length())
    return value


def prime_base(prime: int) -> PrimeBase:
    """Build one exact bounded prime base."""
    logger.debug("prime_base entry")
    result = snapshot_prime_base(PrimeBase(prime))
    logger.debug("prime_base exit prime=%d", result.prime)
    return result


def padic_residue_window(
    prime: PrimeBase, residues: tuple[int, ...]
) -> PadicResidueWindow:
    """Build a structural candidate, preserving canonical incompatibilities."""
    logger.debug("padic_residue_window entry")
    prime = snapshot_prime_base(prime)
    if type(residues) is not tuple or not 1 <= len(residues) <= MAX_PADIC_DEPTH:
        logger.error("padic_residue_window invalid residues container")
        raise PadicResidueValidationError("residues must be a bounded nonempty exact tuple")
    stages: list[PadicResidueStage] = []
    for level, residue in enumerate(residues):
        if type(residue) is not int:
            logger.error("padic_residue_window nonexact residue level=%d", level)
            raise PadicResidueValidationError("residues must be exact integers")
        modulus = prime.prime ** (level + 1)
        stages.append(PadicResidueStage(level, modulus, residue))
    result = snapshot_padic_window(PadicResidueWindow(prime, tuple(stages)))
    logger.debug("padic_residue_window exit levels=%d", len(result.stages))
    return result


def padic_residue_stage(
    prime: PrimeBase, index: int, residue: int
) -> PadicResidueStage:
    """Build one canonical residue stage at an explicit prime-power level."""
    logger.debug("padic_residue_stage entry")
    prime = snapshot_prime_base(prime)
    if type(index) is not int or not 0 <= index < MAX_PADIC_DEPTH:
        logger.error("padic_residue_stage invalid index")
        raise PadicResidueValidationError("index must be a bounded exact integer")
    if type(residue) is not int:
        logger.error("padic_residue_stage invalid residue type")
        raise PadicResidueValidationError("residue must be an exact integer")
    result = snapshot_padic_stage(
        PadicResidueStage(index, prime.prime ** (index + 1), residue), prime, index
    )
    logger.debug("padic_residue_stage exit level=%d", result.level)
    return result


def project_padic_stage(
    prime: PrimeBase, stage: PadicResidueStage, target_index: int
) -> PadicResidueStage:
    """Project a canonical residue stage to a lower prime-power observer."""
    logger.debug("project_padic_stage entry")
    prime = snapshot_prime_base(prime)
    if type(stage) is not PadicResidueStage:
        logger.error("project_padic_stage invalid stage type")
        raise PadicResidueValidationError("stage must be an exact PadicResidueStage")
    try:
        source_level = stage.level
    except AttributeError as exc:
        logger.error("project_padic_stage missing stage field")
        raise PadicResidueValidationError("stage is missing required fields") from exc
    if type(source_level) is not int:
        logger.error("project_padic_stage invalid source level")
        raise PadicResidueValidationError("stage level must be an exact integer")
    stage = snapshot_padic_stage(stage, prime, source_level)
    if type(target_index) is not int or not 0 <= target_index <= stage.level:
        logger.error("project_padic_stage invalid target index")
        raise PadicResidueValidationError("projection level must be an exact in-range integer")
    modulus = prime.prime ** (target_index + 1)
    result = padic_residue_stage(prime, target_index, stage.residue % modulus)
    logger.debug("project_padic_stage exit level=%d", result.level)
    return result


def integer_padic_window(
    prime: PrimeBase, source: int, depth: int
) -> PadicResidueWindow:
    """Return the finite classical residue shadows of one integer."""
    logger.debug("integer_padic_window entry")
    prime = snapshot_prime_base(prime)
    source = validate_padic_source_integer(source)
    if type(depth) is not int or not 1 <= depth <= MAX_PADIC_DEPTH:
        logger.error("integer_padic_window invalid depth")
        raise PadicResidueValidationError("depth must be a bounded positive exact integer")
    residues = tuple(source % (prime.prime ** (level + 1)) for level in range(depth))
    result = padic_residue_window(prime, residues)
    logger.debug("integer_padic_window exit levels=%d", len(result.stages))
    return result


def first_padic_obstruction(
    window: PadicResidueWindow,
) -> PadicCompatibilityObstruction | None:
    """Return the first failed adjacent residue restriction."""
    logger.debug("first_padic_obstruction entry")
    window = snapshot_padic_window(window)
    for upper_level in range(1, len(window.stages)):
        lower = window.stages[upper_level - 1]
        upper = window.stages[upper_level]
        actual = upper.residue % lower.modulus
        if actual != lower.residue:
            result = PadicCompatibilityObstruction(
                lower.level, upper.level, lower.residue, actual
            )
            logger.debug("first_padic_obstruction exit result=%r", result)
            return result
    logger.debug("first_padic_obstruction exit result=None")
    return None


def padic_coherence_report(window: PadicResidueWindow) -> PadicCoherenceReport:
    """Report compatibility only across the supplied finite residue stages."""
    logger.debug("padic_coherence_report entry")
    window = snapshot_padic_window(window)
    obstruction = first_padic_obstruction(window)
    depth = len(window.stages)
    checked_links = depth - 1 if obstruction is None else obstruction.upper_index
    result = PadicCoherenceReport(
        window.prime.prime, depth, checked_links, obstruction is None, obstruction
    )
    logger.debug("padic_coherence_report exit coherent=%s", result.coherent)
    return result


def add_padic_windows(
    left: PadicResidueWindow, right: PadicResidueWindow
) -> PadicResidueWindow:
    """Add equal coherent finite p-adic windows componentwise."""
    logger.debug("add_padic_windows entry")
    result = _combine_padic_windows(left, right, lambda a, b: a + b, "addition")
    logger.debug("add_padic_windows exit levels=%d", len(result.stages))
    return result


def multiply_padic_windows(
    left: PadicResidueWindow, right: PadicResidueWindow
) -> PadicResidueWindow:
    """Multiply equal coherent finite p-adic windows componentwise."""
    logger.debug("multiply_padic_windows entry")
    result = _combine_padic_windows(left, right, lambda a, b: a * b, "multiplication")
    logger.debug("multiply_padic_windows exit levels=%d", len(result.stages))
    return result


def _combine_padic_windows(
    left: PadicResidueWindow,
    right: PadicResidueWindow,
    operation: Callable[[int, int], int],
    name: str,
) -> PadicResidueWindow:
    logger.debug("_combine_padic_windows entry operation=%s", name)
    left = snapshot_padic_window(left)
    right = snapshot_padic_window(right)
    if left.prime != right.prime or len(left.stages) != len(right.stages):
        logger.error("_combine_padic_windows incompatible shape operation=%s", name)
        raise PadicResidueValidationError("p-adic operations require equal prime and depth")
    if first_padic_obstruction(left) is not None or first_padic_obstruction(right) is not None:
        logger.error("_combine_padic_windows incoherent input operation=%s", name)
        raise PadicResidueValidationError("p-adic operations require coherent input windows")
    residues = tuple(
        operation(a.residue, b.residue) % a.modulus
        for a, b in zip(left.stages, right.stages, strict=True)
    )
    result = padic_residue_window(left.prime, residues)
    if first_padic_obstruction(result) is not None:
        logger.error("_combine_padic_windows internal coherence failure operation=%s", name)
        raise RuntimeError("componentwise p-adic operation broke compatibility")
    logger.debug("_combine_padic_windows exit operation=%s levels=%d", name, len(result.stages))
    return result
