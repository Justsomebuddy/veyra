"""Finite science-domain certificates for Veyra applicability."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import logging

from ..geometry.theorems import TheoremCard
from .ratio import RatioMode, add_ratios, ratio_from_fraction, ratio_from_ints, ratio_shadow, subtract_ratios

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConservationRow:
    """Finite before/after conserved-total certificate."""

    label: str
    before: tuple[RatioMode, ...]
    after: tuple[RatioMode, ...]
    before_total: RatioMode
    after_total: RatioMode
    status: str
    obstruction: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready conservation row."""
        logger.debug("ConservationRow.as_dict entry label=%s", self.label)
        result = {"label": self.label, "before_total": str(ratio_shadow(self.before_total)), "after_total": str(ratio_shadow(self.after_total)), "status": self.status, "obstruction": self.obstruction}
        logger.debug("ConservationRow.as_dict exit result=%r", result)
        return result


@dataclass(frozen=True)
class FlowEdge:
    """One directed finite flow edge with nonnegative exact amount."""

    source: str
    target: str
    amount: RatioMode

    def __post_init__(self) -> None:
        """Validate edge endpoints and nonnegative flow."""
        logger.debug("FlowEdge.__post_init__ entry source=%s target=%s", self.source, self.target)
        if not self.source or not self.target or ratio_shadow(self.amount) < 0:
            logger.error("FlowEdge invalid source=%r target=%r amount=%s", self.source, self.target, ratio_shadow(self.amount))
            raise ValueError("flow edge needs endpoints and nonnegative amount")
        logger.debug("FlowEdge.__post_init__ exit amount=%s", self.amount.word)


@dataclass(frozen=True)
class FlowBalanceRow:
    """Finite network flow balance certificate."""

    label: str
    balances: tuple[tuple[str, RatioMode], ...]
    status: str
    obstruction: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready flow balance row."""
        logger.debug("FlowBalanceRow.as_dict entry label=%s", self.label)
        result = {"label": self.label, "balances": tuple((name, str(ratio_shadow(value))) for name, value in self.balances), "status": self.status, "obstruction": self.obstruction}
        logger.debug("FlowBalanceRow.as_dict exit result=%r", result)
        return result


@dataclass(frozen=True)
class DiffusionRow:
    """Finite smoothing/anti-smoothing certificate."""

    label: str
    before_variation: RatioMode
    after_variation: RatioMode
    status: str
    obstruction: str

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready diffusion row."""
        logger.debug("DiffusionRow.as_dict entry label=%s", self.label)
        result = {"label": self.label, "before_variation": str(ratio_shadow(self.before_variation)), "after_variation": str(ratio_shadow(self.after_variation)), "status": self.status, "obstruction": self.obstruction}
        logger.debug("DiffusionRow.as_dict exit result=%r", result)
        return result


def ratio_total(values: tuple[RatioMode, ...]) -> RatioMode:
    """Return exact total of finite ratio observations."""
    logger.debug("ratio_total entry count=%d", len(values))
    total = ratio_from_ints(0)
    for value in values:
        total = add_ratios(total, value)
    logger.debug("ratio_total exit result=%s", total.word)
    return total


def ratio_variation(values: tuple[RatioMode, ...]) -> RatioMode:
    """Return max-minus-min variation for finite observations."""
    logger.debug("ratio_variation entry count=%d", len(values))
    if not values:
        logger.error("ratio_variation empty values")
        raise ValueError("variation needs at least one value")
    shadows = [ratio_shadow(value) for value in values]
    result = ratio_from_fraction(max(shadows) - min(shadows))
    logger.debug("ratio_variation exit result=%s", result.word)
    return result


def finite_conservation_row(label: str, before: tuple[RatioMode, ...], after: tuple[RatioMode, ...]) -> ConservationRow:
    """Check exact finite conserved total between two observation states."""
    logger.debug("finite_conservation_row entry label=%s", label)
    before_total = ratio_total(before)
    after_total = ratio_total(after)
    ok = ratio_shadow(before_total) == ratio_shadow(after_total)
    result = ConservationRow(label, before, after, before_total, after_total, "conserved" if ok else "blocked", "none" if ok else "total-drift")
    logger.debug("finite_conservation_row exit result=%r", result.as_dict())
    return result


def finite_flow_balance_row(label: str, edges: tuple[FlowEdge, ...], boundary: frozenset[str]) -> FlowBalanceRow:
    """Check finite network flow has only declared boundary imbalance."""
    logger.debug("finite_flow_balance_row entry label=%s edges=%d", label, len(edges))
    nodes = sorted({node for edge in edges for node in (edge.source, edge.target)})
    balances: list[tuple[str, RatioMode]] = []
    for node in nodes:
        incoming = ratio_total(tuple(edge.amount for edge in edges if edge.target == node))
        outgoing = ratio_total(tuple(edge.amount for edge in edges if edge.source == node))
        balances.append((node, subtract_ratios(incoming, outgoing)))
    internal_ok = all(ratio_shadow(value) == 0 for node, value in balances if node not in boundary)
    total_ok = ratio_shadow(ratio_total(tuple(value for _, value in balances))) == 0
    ok = internal_ok and total_ok
    result = FlowBalanceRow(label, tuple(balances), "boundary-balanced" if ok else "blocked", "none" if ok else "flow-leak")
    logger.debug("finite_flow_balance_row exit result=%r", result.as_dict())
    return result


def finite_diffusion_row(label: str, before: tuple[RatioMode, ...], after: tuple[RatioMode, ...]) -> DiffusionRow:
    """Check whether a finite update does not increase variation."""
    logger.debug("finite_diffusion_row entry label=%s", label)
    before_variation = ratio_variation(before)
    after_variation = ratio_variation(after)
    ok = ratio_shadow(after_variation) <= ratio_shadow(before_variation)
    result = DiffusionRow(label, before_variation, after_variation, "smoothed" if ok else "blocked", "none" if ok else "variation-growth")
    logger.debug("finite_diffusion_row exit result=%r", result.as_dict())
    return result


def anti_diffusion_obstruction_card() -> TheoremCard:
    """Return counterexample card for variation-increasing update."""
    logger.debug("anti_diffusion_obstruction_card entry")
    row = finite_diffusion_row("anti-diffusion", (ratio_from_ints(1, 2), ratio_from_ints(1, 2)), (ratio_from_ints(0), ratio_from_ints(1)))
    result = TheoremCard("science-anti-diffusion-obstruction", "finite", "blocked" if row.status == "blocked" else "unexpected", row.obstruction, (("before_var", str(ratio_shadow(row.before_variation))), ("after_var", str(ratio_shadow(row.after_variation)))))
    logger.debug("anti_diffusion_obstruction_card exit relation=%s", result.relation)
    return result


def science_certificate_checklist() -> tuple[str, ...]:
    """Return finite science-domain certificate checklist."""
    logger.debug("science_certificate_checklist entry")
    result = ("finite conserved total", "network flow boundary balance", "diffusion variation contraction", "anti-diffusion obstruction")
    logger.debug("science_certificate_checklist exit count=%d", len(result))
    return result
