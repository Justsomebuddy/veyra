"""Finite Q-Veyra seed: observer-indexed quantum circuit theorem cards."""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
import logging

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class Rad2:
    """Exact element `a + b√2` used for finite symbolic amplitudes."""
    a: Fraction = Fraction(0)
    b: Fraction = Fraction(0)

    def __add__(self, other: Rad2) -> Rad2:
        logger.debug("Rad2.__add__ entry self=%r other=%r", self, other)
        result = Rad2(self.a + other.a, self.b + other.b)
        logger.debug("Rad2.__add__ exit result=%r", result)
        return result

    def __sub__(self, other: Rad2) -> Rad2:
        logger.debug("Rad2.__sub__ entry self=%r other=%r", self, other)
        result = Rad2(self.a - other.a, self.b - other.b)
        logger.debug("Rad2.__sub__ exit result=%r", result)
        return result

    def __neg__(self) -> Rad2:
        logger.debug("Rad2.__neg__ entry self=%r", self)
        result = Rad2(-self.a, -self.b)
        logger.debug("Rad2.__neg__ exit result=%r", result)
        return result

    def __mul__(self, other: Rad2) -> Rad2:
        logger.debug("Rad2.__mul__ entry self=%r other=%r", self, other)
        result = Rad2(self.a * other.a + 2 * self.b * other.b, self.a * other.b + self.b * other.a)
        logger.debug("Rad2.__mul__ exit result=%r", result)
        return result

    def is_zero(self) -> bool:
        logger.debug("Rad2.is_zero entry self=%r", self)
        result = self.a == 0 and self.b == 0
        logger.debug("Rad2.is_zero exit result=%s", result)
        return result

@dataclass(frozen=True)
class QAmp:
    """Exact complex amplitude with real/imaginary parts in `Q(√2)`."""
    re: Rad2 = Rad2()
    im: Rad2 = Rad2()

    def __add__(self, other: QAmp) -> QAmp:
        logger.debug("QAmp.__add__ entry self=%r other=%r", self, other)
        result = QAmp(self.re + other.re, self.im + other.im)
        logger.debug("QAmp.__add__ exit result=%r", result)
        return result

    def __sub__(self, other: QAmp) -> QAmp:
        logger.debug("QAmp.__sub__ entry self=%r other=%r", self, other)
        result = QAmp(self.re - other.re, self.im - other.im)
        logger.debug("QAmp.__sub__ exit result=%r", result)
        return result

    def __mul__(self, other: QAmp) -> QAmp:
        logger.debug("QAmp.__mul__ entry self=%r other=%r", self, other)
        result = QAmp(self.re * other.re - self.im * other.im, self.re * other.im + self.im * other.re)
        logger.debug("QAmp.__mul__ exit result=%r", result)
        return result

    def norm2(self) -> Rad2:
        logger.debug("QAmp.norm2 entry self=%r", self)
        result = self.re * self.re + self.im * self.im
        logger.debug("QAmp.norm2 exit result=%r", result)
        return result

    def is_zero(self) -> bool:
        logger.debug("QAmp.is_zero entry self=%r", self)
        result = self.re.is_zero() and self.im.is_zero()
        logger.debug("QAmp.is_zero exit result=%s", result)
        return result

@dataclass(frozen=True)
class QMode:
    """Finite symbolic quantum state with basis labels and exact amplitudes."""
    basis: tuple[str, ...]
    amplitudes: tuple[QAmp, ...]

    def norm2(self) -> Rad2:
        logger.debug("QMode.norm2 entry basis=%r", self.basis)
        total = R0
        for amp in self.amplitudes:
            total = total + amp.norm2()
        logger.debug("QMode.norm2 exit result=%r", total)
        return total

    def distribution(self) -> tuple[tuple[str, Rad2], ...]:
        logger.debug("QMode.distribution entry basis=%r", self.basis)
        result = tuple((label, amp.norm2()) for label, amp in zip(self.basis, self.amplitudes, strict=True))
        logger.debug("QMode.distribution exit result=%r", result)
        return result

@dataclass(frozen=True)
class QGate:
    """Finite gate matrix over exact symbolic amplitudes."""
    name: str
    matrix: tuple[tuple[QAmp, ...], ...]

    def apply(self, mode: QMode) -> QMode:
        logger.debug("QGate.apply entry gate=%s basis=%r", self.name, mode.basis)
        amps = []
        for row in self.matrix:
            total = A0
            for coeff, amp in zip(row, mode.amplitudes, strict=True):
                total = total + coeff * amp
            amps.append(total)
        result = QMode(mode.basis, tuple(amps))
        logger.debug("QGate.apply exit norm=%r", result.norm2())
        return result

@dataclass(frozen=True)
class QuantumTheoremCard:
    """One finite Q-Veyra theorem/obstruction card with explicit boundary."""
    theorem_id: str
    claim: str
    relation: str
    status: str
    evidence: str
    boundary: str

R0, R1, RM1, RH = Rad2(), Rad2(Fraction(1)), Rad2(Fraction(-1)), Rad2(Fraction(0), Fraction(1, 2))
A0, A1, AM1, AH, AMH = QAmp(R0), QAmp(R1), QAmp(RM1), QAmp(RH), QAmp(-RH)

def q_basis_state(bits: str) -> QMode:
    """Return a computational basis state for one or two qubits."""
    logger.debug("q_basis_state entry bits=%s", bits)
    basis = _basis_for(len(bits)); amps = tuple(A1 if label == bits else A0 for label in basis)
    result = QMode(basis, amps)
    logger.debug("q_basis_state exit norm=%r", result.norm2())
    return result

def q_gate_x() -> QGate:
    """Return the one-qubit Pauli-X gate."""
    logger.debug("q_gate_x entry")
    result = QGate("X", ((A0, A1), (A1, A0)))
    logger.debug("q_gate_x exit result=%r", result)
    return result

def q_gate_h() -> QGate:
    """Return the one-qubit Hadamard gate over `Q(√2)`."""
    logger.debug("q_gate_h entry")
    result = QGate("H", ((AH, AH), (AH, AMH)))
    logger.debug("q_gate_h exit result=%r", result)
    return result

def q_gate_cnot() -> QGate:
    """Return two-qubit CNOT with first qubit as control."""
    logger.debug("q_gate_cnot entry")
    result = QGate("CNOT", ((A1, A0, A0, A0), (A0, A1, A0, A0), (A0, A0, A0, A1), (A0, A0, A1, A0)))
    logger.debug("q_gate_cnot exit result=%r", result)
    return result

def q_gate_i() -> QGate:
    """Return the one-qubit identity gate."""
    logger.debug("q_gate_i entry")
    result = QGate("I", ((A1, A0), (A0, A1)))
    logger.debug("q_gate_i exit result=%r", result)
    return result

def tensor_gate(left: QGate, right: QGate) -> QGate:
    """Return the tensor product of two one-qubit gates."""
    logger.debug("tensor_gate entry left=%s right=%s", left.name, right.name)
    rows = []
    for lrow in left.matrix:
        for rrow in right.matrix:
            rows.append(tuple(left_amp * right_amp for left_amp in lrow for right_amp in rrow))
    result = QGate(f"{left.name}⊗{right.name}", tuple(rows))
    logger.debug("tensor_gate exit gate=%s", result.name)
    return result

def compose_gate(left: QGate, right: QGate) -> QGate:
    """Return matrix composition `left ∘ right`."""
    logger.debug("compose_gate entry left=%s right=%s", left.name, right.name)
    cols = tuple(zip(*right.matrix, strict=True)); rows = []
    for lrow in left.matrix:
        rows.append(tuple(sum_amp(tuple(a * b for a, b in zip(lrow, col, strict=True))) for col in cols))
    result = QGate(f"{left.name}∘{right.name}", tuple(rows))
    logger.debug("compose_gate exit gate=%s", result.name)
    return result

def sum_amp(items: tuple[QAmp, ...]) -> QAmp:
    """Sum exact amplitudes."""
    logger.debug("sum_amp entry count=%d", len(items))
    total = A0
    for item in items:
        total = total + item
    logger.debug("sum_amp exit result=%r", total)
    return total

def observer_distribution(mode: QMode, observer: str) -> tuple[tuple[str, Rad2], ...]:
    """Return measurement distribution for `Z` or one-qubit `X` observer."""
    logger.debug("observer_distribution entry observer=%s", observer)
    if observer == "Z":
        result = mode.distribution()
    elif observer == "X" and len(mode.basis) == 2:
        result = q_gate_h().apply(mode).distribution()
    else:
        result = (("unknown", R0),)
    logger.debug("observer_distribution exit result=%r", result)
    return result

def qecho(left: QMode, right: QMode, observer: str) -> bool:
    """Return observer-indexed distribution equality."""
    logger.debug("qecho entry observer=%s", observer)
    result = observer_distribution(left, observer) == observer_distribution(right, observer)
    logger.debug("qecho exit result=%s", result)
    return result

def bell_state() -> QMode:
    """Return `(CNOT)(H⊗I)|00>` as the finite Bell seed."""
    logger.debug("bell_state entry")
    result = q_gate_cnot().apply(tensor_gate(q_gate_h(), q_gate_i()).apply(q_basis_state("00")))
    logger.debug("bell_state exit distribution=%r", result.distribution())
    return result

def is_product_factorable_2q(mode: QMode) -> bool:
    """Check two-qubit pure-state rank-one factorability by determinant obstruction."""
    logger.debug("is_product_factorable_2q entry basis=%r", mode.basis)
    a00, a01, a10, a11 = mode.amplitudes
    result = a00 * a11 == a01 * a10
    logger.debug("is_product_factorable_2q exit result=%s", result)
    return result

def quantum_theorem_cards() -> tuple[QuantumTheoremCard, ...]:
    """Return minimal Q1 finite theorem/obstruction cards."""
    logger.debug("quantum_theorem_cards entry")
    result = (
        _involution_card("Q-HH", "H ∘ H = I", q_gate_h()),
        _involution_card("Q-XX", "X ∘ X = I", q_gate_x()),
        _cnot_norm_card(), _bell_nonfactor_card(), _zx_shadow_card(), _no_cloning_card(),
    )
    logger.debug("quantum_theorem_cards exit count=%d", len(result))
    return result

def quantum_veyra_summary() -> dict[str, int | bool]:
    """Return compact Q1 counters."""
    logger.debug("quantum_veyra_summary entry")
    cards = quantum_theorem_cards()
    result: dict[str, int | bool] = {"cards": len(cards), "ready": sum(c.status == "ready" for c in cards), "obstructions": sum(c.relation == "obstruction" for c in cards), "overclaims": sum("finite" not in c.boundary for c in cards), "has_born_shadow": True, "has_tensor_seed": True}
    logger.debug("quantum_veyra_summary exit result=%r", result)
    return result

def quantum_veyra_checklist() -> tuple[str, ...]:
    """Return Q1 acceptance checklist."""
    logger.debug("quantum_veyra_checklist entry")
    result = ("exact Q(√2) complex amplitudes", "finite gates H/X/CNOT", "observer distributions as Born shadows", "echo/obstruction rows", "entanglement non-factorization row", "anti-overclaim boundaries")
    logger.debug("quantum_veyra_checklist exit count=%d", len(result))
    return result

def _involution_card(card_id: str, claim: str, gate: QGate) -> QuantumTheoremCard:
    logger.debug("_involution_card entry card=%s", card_id)
    ok = compose_gate(gate, gate).matrix == q_gate_i().matrix
    result = QuantumTheoremCard(card_id, claim, "identity", "ready" if ok else "blocked", gate.name, "finite one-qubit matrix theorem card only")
    logger.debug("_involution_card exit result=%r", result)
    return result

def _cnot_norm_card() -> QuantumTheoremCard:
    logger.debug("_cnot_norm_card entry")
    states = tuple(q_basis_state(bits) for bits in ("00", "01", "10", "11")) + (bell_state(),)
    ok = all(q_gate_cnot().apply(state).norm2() == state.norm2() == R1 for state in states)
    result = QuantumTheoremCard("Q-CNOT-NORM", "CNOT preserves norm on finite seed states", "norm-preserved", "ready" if ok else "blocked", f"states={len(states)}", "finite seed-state norm card, not full unitarity calculus")
    logger.debug("_cnot_norm_card exit result=%r", result)
    return result

def _bell_nonfactor_card() -> QuantumTheoremCard:
    logger.debug("_bell_nonfactor_card entry")
    ok = not is_product_factorable_2q(bell_state())
    result = QuantumTheoremCard("Q-BELL-NONFACT", "Bell seed is not product-factorable", "obstruction", "ready" if ok else "blocked", "a00*a11 != a01*a10", "finite two-qubit factorization obstruction only")
    logger.debug("_bell_nonfactor_card exit result=%r", result)
    return result

def _zx_shadow_card() -> QuantumTheoremCard:
    logger.debug("_zx_shadow_card entry")
    state = q_basis_state("0")
    ok = observer_distribution(state, "Z") != observer_distribution(state, "X")
    result = QuantumTheoremCard("Q-ZX-SHADOW", "Z and X measurement observers differ on |0>", "distinguishable", "ready" if ok else "blocked", "Z=(1,0), X=(1/2,1/2)", "finite observer-shadow distinction only")
    logger.debug("_zx_shadow_card exit result=%r", result)
    return result

def _no_cloning_card() -> QuantumTheoremCard:
    logger.debug("_no_cloning_card entry")
    linear = QMode(_basis_for(2), (AH, A0, A0, AH)); desired = QMode(_basis_for(2), (QAmp(Rad2(Fraction(1, 2))),) * 4)
    ok = observer_distribution(linear, "Z") != observer_distribution(desired, "Z")
    result = QuantumTheoremCard("Q-NO-CLONE", "finite no-cloning obstruction for |+>", "obstruction", "ready" if ok else "blocked", "linear basis cloner shadow differs from desired clone", "finite linearity obstruction, not full no-cloning theorem")
    logger.debug("_no_cloning_card exit result=%r", result)
    return result

def _basis_for(qubits: int) -> tuple[str, ...]:
    logger.debug("_basis_for entry qubits=%d", qubits)
    result = tuple(format(i, f"0{qubits}b") for i in range(2 ** qubits))
    logger.debug("_basis_for exit result=%r", result)
    return result
