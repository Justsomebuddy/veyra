"""Finite weighted echo measure seed for Veyra coverage."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import logging

from ..geometry.theorems import TheoremCard
from .ratio import RatioMode, add_ratios, ratio_from_fraction, ratio_from_ints, ratio_shadow, subtract_ratios

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WeightedEchoAtom:
    """One finite echo atom with an exact nonnegative weight."""

    name: str
    tact: str
    weight: RatioMode

    def __post_init__(self) -> None:
        """Validate atom labels and nonnegative weight."""
        logger.debug("WeightedEchoAtom.__post_init__ entry name=%s tact=%s", self.name, self.tact)
        if not self.name or not self.tact:
            logger.error("WeightedEchoAtom empty label name=%r tact=%r", self.name, self.tact)
            raise ValueError("atom name and tact must be nonempty")
        if ratio_shadow(self.weight) < 0:
            logger.error("WeightedEchoAtom negative weight=%s", ratio_shadow(self.weight))
            raise ValueError("atom weight must be nonnegative")
        logger.debug("WeightedEchoAtom.__post_init__ exit weight=%s", self.weight.word)


@dataclass(frozen=True)
class WeightedEchoMeasure:
    """Finite measure over weighted echo atoms."""

    atoms: tuple[WeightedEchoAtom, ...]

    def __post_init__(self) -> None:
        """Validate finite nonempty measure with positive total mass."""
        logger.debug("WeightedEchoMeasure.__post_init__ entry count=%d", len(self.atoms))
        names = [atom.name for atom in self.atoms]
        if not self.atoms or len(set(names)) != len(names) or self.total_weight <= 0:
            logger.error("WeightedEchoMeasure invalid atoms count=%d names=%r", len(self.atoms), names)
            raise ValueError("measure needs unique atoms and positive total weight")
        logger.debug("WeightedEchoMeasure.__post_init__ exit total=%s", self.total_weight)

    @property
    def total_weight(self) -> Fraction:
        """Return exact total weight shadow."""
        logger.debug("WeightedEchoMeasure.total_weight entry")
        result = sum((ratio_shadow(atom.weight) for atom in self.atoms), Fraction(0))
        logger.debug("WeightedEchoMeasure.total_weight exit result=%s", result)
        return result

    @property
    def atom_names(self) -> frozenset[str]:
        """Return known atom names."""
        logger.debug("WeightedEchoMeasure.atom_names entry")
        result = frozenset(atom.name for atom in self.atoms)
        logger.debug("WeightedEchoMeasure.atom_names exit count=%d", len(result))
        return result


@dataclass(frozen=True)
class CoverageRow:
    """Finite event/complement coverage row."""

    label: str
    names: frozenset[str]
    mass: RatioMode
    complement: RatioMode
    status: str
    obstruction: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready coverage row."""
        logger.debug("CoverageRow.as_dict entry label=%s", self.label)
        result = {"label": self.label, "names": tuple(sorted(self.names)), "mass": str(ratio_shadow(self.mass)), "complement": str(ratio_shadow(self.complement)), "status": self.status, "obstruction": self.obstruction}
        logger.debug("CoverageRow.as_dict exit result=%r", result)
        return result


@dataclass(frozen=True)
class AdditivityRow:
    """Finite additivity row for two events."""

    label: str
    left_mass: RatioMode
    right_mass: RatioMode
    intersection_mass: RatioMode
    union_mass: RatioMode
    naive_sum: RatioMode
    relation: str
    obstruction: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready additivity row."""
        logger.debug("AdditivityRow.as_dict entry label=%s", self.label)
        result = {"label": self.label, "left": str(ratio_shadow(self.left_mass)), "right": str(ratio_shadow(self.right_mass)), "intersection": str(ratio_shadow(self.intersection_mass)), "union": str(ratio_shadow(self.union_mass)), "naive_sum": str(ratio_shadow(self.naive_sum)), "relation": self.relation, "obstruction": self.obstruction}
        logger.debug("AdditivityRow.as_dict exit result=%r", result)
        return result


@dataclass(frozen=True)
class PushForwardRow:
    """Mass-preserving row after folding atoms by tact."""

    target: str
    source_names: tuple[str, ...]
    source_mass: RatioMode
    target_mass: RatioMode
    status: str
    obstruction: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready pushforward row."""
        logger.debug("PushForwardRow.as_dict entry target=%s", self.target)
        result = {"target": self.target, "source_names": self.source_names, "source_mass": str(ratio_shadow(self.source_mass)), "target_mass": str(ratio_shadow(self.target_mass)), "status": self.status, "obstruction": self.obstruction}
        logger.debug("PushForwardRow.as_dict exit result=%r", result)
        return result


def weighted_echo_measure() -> WeightedEchoMeasure:
    """Return the canonical finite weighted-echo fixture."""
    logger.debug("weighted_echo_measure entry")
    atoms = (WeightedEchoAtom("alpha", "warm", ratio_from_ints(1)), WeightedEchoAtom("beta", "cool", ratio_from_ints(2)), WeightedEchoAtom("gamma", "cool", ratio_from_ints(3)))
    result = WeightedEchoMeasure(atoms)
    logger.debug("weighted_echo_measure exit total=%s", result.total_weight)
    return result


def mass_of(measure: WeightedEchoMeasure, names: frozenset[str]) -> RatioMode:
    """Return normalized exact mass of an event."""
    logger.debug("mass_of entry names=%r", sorted(names))
    unknown = names - measure.atom_names
    if unknown:
        logger.error("mass_of unknown names=%r", sorted(unknown))
        raise ValueError("unknown atom name")
    numerator = sum((ratio_shadow(atom.weight) for atom in measure.atoms if atom.name in names), Fraction(0))
    result = ratio_from_fraction(numerator / measure.total_weight)
    logger.debug("mass_of exit result=%s", result.word)
    return result


def coverage_row(measure: WeightedEchoMeasure, label: str, names: frozenset[str]) -> CoverageRow:
    """Return event/complement coverage row."""
    logger.debug("coverage_row entry label=%s names=%r", label, sorted(names))
    event = mass_of(measure, names)
    complement = mass_of(measure, measure.atom_names - names)
    total = add_ratios(event, complement)
    ok = ratio_shadow(total) == 1
    result = CoverageRow(label, names, event, complement, "covered" if ok else "blocked", "none" if ok else "mass-gap")
    logger.debug("coverage_row exit result=%r", result.as_dict())
    return result


def finite_additivity_row(measure: WeightedEchoMeasure, label: str, left: frozenset[str], right: frozenset[str]) -> AdditivityRow:
    """Return finite additivity or overlap-correction row."""
    logger.debug("finite_additivity_row entry label=%s left=%r right=%r", label, sorted(left), sorted(right))
    left_mass = mass_of(measure, left)
    right_mass = mass_of(measure, right)
    intersection_mass = mass_of(measure, left & right)
    union_mass = mass_of(measure, left | right)
    naive_sum = add_ratios(left_mass, right_mass)
    corrected = subtract_ratios(naive_sum, intersection_mass)
    relation = "additive" if ratio_shadow(intersection_mass) == 0 and ratio_shadow(naive_sum) == ratio_shadow(union_mass) else "overlap-corrected"
    ok = ratio_shadow(corrected) == ratio_shadow(union_mass)
    obstruction = "none" if relation == "additive" and ok else "overlap-mass" if ok else "additivity-gap"
    result = AdditivityRow(label, left_mass, right_mass, intersection_mass, union_mass, naive_sum, relation if ok else "blocked", obstruction)
    logger.debug("finite_additivity_row exit result=%r", result.as_dict())
    return result


def pushforward_by_tact(measure: WeightedEchoMeasure) -> tuple[PushForwardRow, ...]:
    """Fold atom masses by tact labels and preserve total mass."""
    logger.debug("pushforward_by_tact entry count=%d", len(measure.atoms))
    groups = {tact: tuple(atom.name for atom in measure.atoms if atom.tact == tact) for tact in sorted({atom.tact for atom in measure.atoms})}
    rows = []
    for tact, names in groups.items():
        source = mass_of(measure, frozenset(names))
        target = ratio_from_fraction(sum((ratio_shadow(atom.weight) for atom in measure.atoms if atom.tact == tact), Fraction(0)) / measure.total_weight)
        ok = ratio_shadow(source) == ratio_shadow(target)
        rows.append(PushForwardRow(tact, names, source, target, "preserved" if ok else "blocked", "none" if ok else "pushforward-gap"))
    result = tuple(rows)
    logger.debug("pushforward_by_tact exit count=%d", len(result))
    return result


def overlap_gap_card(measure: WeightedEchoMeasure) -> TheoremCard:
    """Record why overlapping events cannot use naive additivity."""
    logger.debug("overlap_gap_card entry")
    row = finite_additivity_row(measure, "overlap-gap", frozenset({"alpha", "beta"}), frozenset({"beta", "gamma"}))
    relation = "blocked-naive" if row.obstruction == "overlap-mass" and ratio_shadow(row.intersection_mass) > 0 else "unexpected"
    result = TheoremCard("weighted-measure-overlap-gap", "finite", relation, "overlap-mass" if relation == "blocked-naive" else "missing-overlap", (("intersection", str(ratio_shadow(row.intersection_mass))), ("union", str(ratio_shadow(row.union_mass))), ("naive_sum", str(ratio_shadow(row.naive_sum)))))
    logger.debug("overlap_gap_card exit relation=%s", result.relation)
    return result


def weighted_measure_checklist() -> tuple[str, ...]:
    """Return finite weighted-measure checklist."""
    logger.debug("weighted_measure_checklist entry")
    result = ("finite weighted atoms", "event/complement coverage", "finite additivity with overlap obstruction", "tact pushforward mass preservation")
    logger.debug("weighted_measure_checklist exit count=%d", len(result))
    return result
