"""Finite phase-equation normal forms for rational trigonometry shadows."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from ..geometry.theorems import TheoremCard
from ..shadows.ratio import RatioMode, ratio_shadow
from ..shadows.trigonometry_identities import TrigIdentityVector, conjugate_phase, trig_vector_from_ints, unit_identity_gap

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PhaseCoordinateRow:
    """Normal-form row for one rational cosine or sine equation."""

    target: str
    value: RatioMode
    matches: tuple[str, ...]
    relation: str
    obstruction: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready coordinate equation row."""
        logger.debug("PhaseCoordinateRow.as_dict entry target=%s", self.target)
        result = {"target": self.target, "value": str(ratio_shadow(self.value)), "matches": list(self.matches), "relation": self.relation, "obstruction": self.obstruction}
        logger.debug("PhaseCoordinateRow.as_dict exit result=%r", result)
        return result


@dataclass(frozen=True)
class PhasePairRow:
    """Normal-form row for a rational `(cos, sin)` phase equation."""

    cos: RatioMode
    sin: RatioMode
    matches: tuple[str, ...]
    relation: str
    obstruction: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready phase-pair equation row."""
        logger.debug("PhasePairRow.as_dict entry relation=%s", self.relation)
        result = {"cos": str(ratio_shadow(self.cos)), "sin": str(ratio_shadow(self.sin)), "matches": list(self.matches), "relation": self.relation, "obstruction": self.obstruction}
        logger.debug("PhasePairRow.as_dict exit result=%r", result)
        return result


def default_phase_basis() -> tuple[TrigIdentityVector, ...]:
    """Return the bounded rational phase dictionary used by D5."""
    logger.debug("default_phase_basis entry")
    a = trig_vector_from_ints(3, 4, 5, "a")
    b = trig_vector_from_ints(5, 12, 13, "b")
    result = (trig_vector_from_ints(1, 0, 1, "id"), a, conjugate_phase(a), b, conjugate_phase(b), trig_vector_from_ints(-1, 0, 1, "neg"))
    logger.debug("default_phase_basis exit count=%d", len(result))
    return result


def phase_coordinate_row(target: str, value: RatioMode, basis: tuple[TrigIdentityVector, ...] | None = None) -> PhaseCoordinateRow:
    """Resolve `cos θ = value` or `sin θ = value` against a finite rational basis."""
    logger.debug("phase_coordinate_row entry target=%s value=%s", target, value.word)
    rows = default_phase_basis() if basis is None else basis
    if target not in {"cos", "sin"}:
        logger.error("phase_coordinate_row invalid target=%s", target)
        raise ValueError("target must be 'cos' or 'sin'")
    value_shadow = ratio_shadow(value)
    matches = tuple(item.label for item in rows if ratio_shadow(item.cos if target == "cos" else item.sin) == value_shadow)
    relation = "resolved" if matches else "blocked"
    obstruction = "none" if matches else "no-rational-phase-coordinate"
    result = PhaseCoordinateRow(target, value, matches, relation, obstruction)
    logger.debug("phase_coordinate_row exit matches=%r relation=%s", matches, relation)
    return result


def phase_pair_row(cos: RatioMode, sin: RatioMode, basis: tuple[TrigIdentityVector, ...] | None = None) -> PhasePairRow:
    """Resolve a full rational phase equation against a finite basis."""
    logger.debug("phase_pair_row entry cos=%s sin=%s", cos.word, sin.word)
    rows = default_phase_basis() if basis is None else basis
    query = TrigIdentityVector(cos, sin, "query")
    if ratio_shadow(unit_identity_gap(query)) != 0:
        result = PhasePairRow(cos, sin, (), "blocked", "unit-gap")
    else:
        matches = tuple(item.label for item in rows if ratio_shadow(item.cos) == ratio_shadow(cos) and ratio_shadow(item.sin) == ratio_shadow(sin))
        result = PhasePairRow(cos, sin, matches, "resolved" if matches else "blocked", "none" if matches else "basis-gap")
    logger.debug("phase_pair_row exit matches=%r relation=%s obstruction=%s", result.matches, result.relation, result.obstruction)
    return result


def phase_equation_normal_form_card(cos: RatioMode, sin: RatioMode, basis: tuple[TrigIdentityVector, ...] | None = None) -> TheoremCard:
    """Card for finite phase-equation normal-form resolution."""
    logger.debug("phase_equation_normal_form_card entry cos=%s sin=%s", cos.word, sin.word)
    row = phase_pair_row(cos, sin, basis)
    result = TheoremCard("phase-equation-normal-form", "finite", row.relation, row.obstruction, (("cos", str(ratio_shadow(cos))), ("sin", str(ratio_shadow(sin))), ("matches", ",".join(row.matches))))
    logger.debug("phase_equation_normal_form_card exit relation=%s obstruction=%s", result.relation, result.obstruction)
    return result


def inverse_phase_obstruction_card(cos: RatioMode, sin: RatioMode, basis: tuple[TrigIdentityVector, ...] | None = None) -> TheoremCard:
    """Card that names why a rational inverse-phase request is unresolved."""
    logger.debug("inverse_phase_obstruction_card entry cos=%s sin=%s", cos.word, sin.word)
    row = phase_pair_row(cos, sin, basis)
    relation = "available" if row.relation == "resolved" else "blocked"
    result = TheoremCard("inverse-phase-obstruction", "finite", relation, row.obstruction, (("cos", str(ratio_shadow(cos))), ("sin", str(ratio_shadow(sin))), ("matches", ",".join(row.matches))))
    logger.debug("inverse_phase_obstruction_card exit relation=%s obstruction=%s", result.relation, result.obstruction)
    return result


def phase_equation_checklist() -> tuple[str, ...]:
    """Return D5 phase-equation acceptance checklist."""
    logger.debug("phase_equation_checklist entry")
    result = ("finite rational phase basis", "coordinate equation rows", "phase-pair normal forms", "inverse-phase obstruction cards")
    logger.debug("phase_equation_checklist exit count=%d", len(result))
    return result
