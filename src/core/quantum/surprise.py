"""Finite surprise-witness entanglement detection rows for Q-Veyra.

Limited-observer basis menus (Z-only, X-only, small basis subsets) detect the
hidden correlation of the finite Bell seed versus product states without full
tomography.  The surprise idiom: the surface observer is the pair of
single-qubit marginals, the hidden observer is the joint menu shadow, and the
witness gap is the joint shadow differing from the product of its marginals.
Blind mixed-basis menus are explicit obstruction rows, never exceptions.
"""
from __future__ import annotations
from dataclasses import dataclass
import logging
from .veyra import (
    QGate,
    QMode,
    Rad2,
    bell_state,
    is_product_factorable_2q,
    q_basis_state,
    q_gate_h,
    q_gate_i,
    tensor_gate,
)

logger = logging.getLogger(__name__)

BELL_PHI_PLUS = "bell-phi-plus"
PRODUCT_00 = "product-00"
PRODUCT_PLUS_PLUS = "product-++"
PRODUCT_PLUS_0 = "product-+0"
PRODUCT_0_PLUS = "product-0+"
PRODUCT_STATES = (PRODUCT_00, PRODUCT_PLUS_PLUS, PRODUCT_PLUS_0, PRODUCT_0_PLUS)
BASIS_SPECS = ("ZZ", "ZX", "XZ", "XX")

@dataclass(frozen=True)
class QSurpriseWitnessRow:
    """One finite limited-menu correlation-gap witness row."""
    row_id: str
    state_name: str
    menu: tuple[str, ...]
    gap_specs: tuple[str, ...]
    blind_specs: tuple[str, ...]
    detects_hidden_correlation: bool
    status: str
    boundary: str

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready witness row."""
        logger.debug("QSurpriseWitnessRow.as_dict entry row_id=%s", self.row_id)
        result = {
            "row_id": self.row_id,
            "state_name": self.state_name,
            "menu": self.menu,
            "gap_specs": self.gap_specs,
            "blind_specs": self.blind_specs,
            "detects_hidden_correlation": self.detects_hidden_correlation,
            "status": self.status,
            "boundary": self.boundary,
        }
        logger.debug("QSurpriseWitnessRow.as_dict exit result=%r", result)
        return result

@dataclass(frozen=True)
class QSurpriseObstructionRow:
    """Expected-failure row: a blind menu cannot distinguish the two states."""
    row_id: str
    left_state: str
    right_state: str
    menu: tuple[str, ...]
    menu_echo: bool
    gaps_detected: bool
    status: str
    boundary: str

@dataclass(frozen=True)
class QSurpriseBaselineRow:
    """One Q3-style baseline-comparison row for the surprise witness rows."""
    result_id: str
    veyra_artifact: str
    baseline_family: str
    baseline_method: str
    verdict: str
    stronger_claim: bool
    status: str
    boundary: str

def named_two_qubit_state(name: str) -> QMode:
    """Return one finite two-qubit seed state by name."""
    logger.debug("named_two_qubit_state entry name=%s", name)
    hadamard, identity = q_gate_h(), q_gate_i()
    builders = {
        BELL_PHI_PLUS: bell_state,
        PRODUCT_00: lambda: q_basis_state("00"),
        PRODUCT_PLUS_PLUS: lambda: tensor_gate(hadamard, hadamard).apply(q_basis_state("00")),
        PRODUCT_PLUS_0: lambda: tensor_gate(hadamard, identity).apply(q_basis_state("00")),
        PRODUCT_0_PLUS: lambda: tensor_gate(identity, hadamard).apply(q_basis_state("00")),
    }
    if name not in builders:
        logger.error("named_two_qubit_state unknown name=%s", name)
        raise ValueError(f"unknown two-qubit seed state: {name}")
    result = builders[name]()
    logger.debug("named_two_qubit_state exit name=%s norm=%r", name, result.norm2())
    return result

def basis_rotation(spec: str) -> QGate:
    """Return the two-qubit gate rotating into a basis spec such as ``ZX``."""
    logger.debug("basis_rotation entry spec=%s", spec)
    if len(spec) != 2 or any(char not in "ZX" for char in spec):
        logger.error("basis_rotation invalid spec=%s", spec)
        raise ValueError("basis spec must be two characters over {Z, X}")
    gates = {"Z": q_gate_i(), "X": q_gate_h()}
    result = tensor_gate(gates[spec[0]], gates[spec[1]])
    logger.debug("basis_rotation exit gate=%s", result.name)
    return result

def basis_shadow(mode: QMode, spec: str) -> tuple[tuple[str, Rad2], ...]:
    """Return the exact measurement distribution under one two-qubit basis spec."""
    logger.debug("basis_shadow entry spec=%s basis=%r", spec, mode.basis)
    result = basis_rotation(spec).apply(mode).distribution()
    logger.debug("basis_shadow exit spec=%s result=%r", spec, result)
    return result

def marginal_distribution(distribution: tuple[tuple[str, Rad2], ...], qubit: int) -> tuple[tuple[str, Rad2], ...]:
    """Return the single-qubit marginal of a two-qubit distribution."""
    logger.debug("marginal_distribution entry qubit=%d", qubit)
    if qubit not in (0, 1):
        logger.error("marginal_distribution invalid qubit=%d", qubit)
        raise ValueError("qubit index must be 0 or 1")
    zero, one = Rad2(), Rad2()
    for label, prob in distribution:
        if label[qubit] == "0":
            zero = zero + prob
        else:
            one = one + prob
    result = (("0", zero), ("1", one))
    logger.debug("marginal_distribution exit result=%r", result)
    return result

def product_of_marginals(distribution: tuple[tuple[str, Rad2], ...]) -> tuple[tuple[str, Rad2], ...]:
    """Return the independent coupling with the same marginals (surface observer)."""
    logger.debug("product_of_marginals entry")
    left = marginal_distribution(distribution, 0)
    right = marginal_distribution(distribution, 1)
    result = tuple((first + second, p_first * p_second) for first, p_first in left for second, p_second in right)
    logger.debug("product_of_marginals exit result=%r", result)
    return result

def correlation_gap_labels(distribution: tuple[tuple[str, Rad2], ...]) -> tuple[str, ...]:
    """Return labels where the joint shadow differs from the product of its marginals."""
    logger.debug("correlation_gap_labels entry")
    surface = dict(product_of_marginals(distribution))
    result = tuple(label for label, prob in distribution if prob != surface[label])
    logger.debug("correlation_gap_labels exit result=%r", result)
    return result

def menu_shadow(mode: QMode, menu: tuple[str, ...]) -> tuple[tuple[str, tuple[tuple[str, Rad2], ...]], ...]:
    """Return per-spec measurement shadows for a limited basis menu."""
    logger.debug("menu_shadow entry menu=%r", menu)
    if not menu:
        logger.error("menu_shadow empty menu")
        raise ValueError("menu must contain at least one basis spec")
    result = tuple((spec, basis_shadow(mode, spec)) for spec in menu)
    logger.debug("menu_shadow exit menu=%r count=%d", menu, len(result))
    return result

def menu_detects_gap(mode: QMode, menu: tuple[str, ...]) -> bool:
    """Return whether any spec in the menu sees a correlation gap."""
    logger.debug("menu_detects_gap entry menu=%r", menu)
    result = any(correlation_gap_labels(distribution) for _, distribution in menu_shadow(mode, menu))
    logger.debug("menu_detects_gap exit result=%s", result)
    return result

def surprise_witness_row(row_id: str, state_name: str, menu: tuple[str, ...]) -> QSurpriseWitnessRow:
    """Return one finite limited-menu surprise witness row."""
    logger.debug("surprise_witness_row entry row_id=%s state=%s menu=%r", row_id, state_name, menu)
    shadow = menu_shadow(named_two_qubit_state(state_name), menu)
    gaps = tuple((spec, correlation_gap_labels(distribution)) for spec, distribution in shadow)
    gap_specs = tuple(spec for spec, labels in gaps if labels)
    blind_specs = tuple(spec for spec, labels in gaps if not labels)
    result = QSurpriseWitnessRow(
        row_id,
        state_name,
        menu,
        gap_specs,
        blind_specs,
        bool(gap_specs),
        "ready",
        "finite two-qubit pure-state limited-menu witness only; gap is joint-vs-marginal surprise, not a nonclassicality or tomography-replacement claim",
    )
    logger.debug("surprise_witness_row exit result=%r", result)
    return result

def surprise_witness_rows() -> tuple[QSurpriseWitnessRow, ...]:
    """Return canonical witness rows: Bell detected, products not flagged."""
    logger.debug("surprise_witness_rows entry")
    result = (
        surprise_witness_row("QS-ZZ-BELL", BELL_PHI_PLUS, ("ZZ",)),
        surprise_witness_row("QS-XX-BELL", BELL_PHI_PLUS, ("XX",)),
        surprise_witness_row("QS-ZZXX-BELL", BELL_PHI_PLUS, ("ZZ", "XX")),
        surprise_witness_row("QS-ZZ-PRODUCT-00", PRODUCT_00, ("ZZ",)),
        surprise_witness_row("QS-ZZ-PRODUCT-PP", PRODUCT_PLUS_PLUS, ("ZZ",)),
        surprise_witness_row("QS-XX-PRODUCT-PP", PRODUCT_PLUS_PLUS, ("XX",)),
    )
    logger.debug("surprise_witness_rows exit count=%d", len(result))
    return result

def blind_menu_obstruction_row(row_id: str, left_state: str, right_state: str, menu: tuple[str, ...]) -> QSurpriseObstructionRow:
    """Return one blind-menu obstruction row (expected failure as data)."""
    logger.debug("blind_menu_obstruction_row entry row_id=%s menu=%r", row_id, menu)
    left, right = named_two_qubit_state(left_state), named_two_qubit_state(right_state)
    left_shadow, right_shadow = menu_shadow(left, menu), menu_shadow(right, menu)
    echo = all(l_dist == r_dist for (_, l_dist), (_, r_dist) in zip(left_shadow, right_shadow, strict=True))
    gaps = menu_detects_gap(left, menu) or menu_detects_gap(right, menu)
    result = QSurpriseObstructionRow(
        row_id,
        left_state,
        right_state,
        menu,
        echo,
        gaps,
        "ready" if echo and not gaps else "blocked",
        "finite blind-menu obstruction only; a wider menu or full tomography may separate the pair",
    )
    logger.debug("blind_menu_obstruction_row exit result=%r", result)
    return result

def blind_menu_obstruction_rows() -> tuple[QSurpriseObstructionRow, ...]:
    """Return canonical blind mixed-basis menu obstruction rows."""
    logger.debug("blind_menu_obstruction_rows entry")
    result = (
        blind_menu_obstruction_row("QS-BLIND-ZX", BELL_PHI_PLUS, PRODUCT_PLUS_0, ("ZX",)),
        blind_menu_obstruction_row("QS-BLIND-XZ", BELL_PHI_PLUS, PRODUCT_0_PLUS, ("XZ",)),
    )
    logger.debug("blind_menu_obstruction_rows exit count=%d", len(result))
    return result

def _baseline_row(result_id: str, artifact: str, family: str, method: str, verdict: str, boundary: str) -> QSurpriseBaselineRow:
    """Return one benchmarked baseline row with no stronger claim."""
    logger.debug("_baseline_row entry result_id=%s family=%s", result_id, family)
    result = QSurpriseBaselineRow(result_id, artifact, family, method, verdict, False, "benchmarked", boundary)
    logger.debug("_baseline_row exit result=%r", result)
    return result

def quantum_surprise_baseline_rows() -> tuple[QSurpriseBaselineRow, ...]:
    """Return the self-contained Q3-style baseline ledger for the witness rows."""
    logger.debug("quantum_surprise_baseline_rows entry")
    bell = bell_state()
    ok = (
        not is_product_factorable_2q(bell)
        and all(is_product_factorable_2q(named_two_qubit_state(name)) for name in PRODUCT_STATES)
        and bool(correlation_gap_labels(basis_shadow(bell, "ZZ")))
        and bool(correlation_gap_labels(basis_shadow(bell, "XX")))
        and not menu_detects_gap(bell, ("ZX",))
        and not menu_detects_gap(bell, ("XZ",))
    )
    if not ok:
        logger.error("quantum_surprise_baseline_rows blocked: executable witness facts failed")
        return ()
    result = (
        _baseline_row("QS-BASE-PRODUCT-FACTOR", "quantum_veyra.is_product_factorable_2q", "tensor-product", "rank-one determinant test on the four exact amplitudes with full amplitude access", "baseline-known", "finite comparison only; the menu witness uses strictly less access (chosen-basis shadows)"),
        _baseline_row("QS-BASE-TOMOGRAPHY", "quantum_surprise.surprise_witness_rows", "full-tomography", "reconstruct all four amplitudes from a complete basis set, then test factorization exactly", "baseline-stronger-reference", "finite declared stronger reference class; limited menus do not replace tomography"),
        _baseline_row("QS-BASE-CLASSICAL-CORR", "quantum_surprise.surprise_witness_rows", "classical-correlation", "a classically correlated 50/50 source reproduces the Bell ZZ support shadow", "baseline-matches-witness", "finite honesty row: the menu gap detects correlation, not nonclassicality; no Bell-inequality claim"),
    )
    logger.debug("quantum_surprise_baseline_rows exit count=%d", len(result))
    return result

def quantum_surprise_summary() -> dict[str, int | bool]:
    """Return compact counters for the surprise-witness rows."""
    logger.debug("quantum_surprise_summary entry")
    rows, obstructions, baselines = surprise_witness_rows(), blind_menu_obstruction_rows(), quantum_surprise_baseline_rows()
    result: dict[str, int | bool] = {
        "witness_rows": len(rows),
        "bell_detected": sum(row.detects_hidden_correlation and row.state_name == BELL_PHI_PLUS for row in rows),
        "products_flagged": sum(row.detects_hidden_correlation for row in rows if row.state_name != BELL_PHI_PLUS),
        "obstruction_rows": len(obstructions),
        "ready_obstructions": sum(row.status == "ready" for row in obstructions),
        "baseline_rows": len(baselines),
        "stronger_claims": sum(row.stronger_claim for row in baselines),
        "overclaims": sum("finite" not in row.boundary for row in (*rows, *obstructions, *baselines)),
    }
    logger.debug("quantum_surprise_summary exit result=%r", result)
    return result

def quantum_surprise_checklist() -> tuple[str, ...]:
    """Return the surprise-witness acceptance checklist."""
    logger.debug("quantum_surprise_checklist entry")
    result = (
        "limited basis menus (Z-only / X-only / small subsets) as measurement access",
        "correlation gap: joint menu shadow differs from product of its marginals",
        "Bell seed detected by ZZ/XX menus without full tomography",
        "product states correctly not flagged by any menu",
        "blind mixed-basis ZX/XZ menus are explicit obstruction rows",
        "named baselines: product-factor test, full-tomography stronger reference, classical-correlation honesty row",
        "no quantum-advantage, nonclassicality, or tomography-replacement claim",
    )
    logger.debug("quantum_surprise_checklist exit count=%d", len(result))
    return result
