"""Q4 finite topological Veyra-qubit echo rows."""
from __future__ import annotations
from dataclasses import dataclass
import logging
from ..geometry.topology_echo import EchoShape, echo_shape, invariant_value, subdivide_corridor, deform_shape

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class VTopoQubit:
    """Finite topological Veyra-qubit shadow: state plus topology signature."""
    name: str
    logical: int
    shape: EchoShape
    raw_state: str
    boundary: str

@dataclass(frozen=True)
class QTopoEchoRow:
    """Local deformation row preserving a topology-indexed quantum echo."""
    name: str
    before: str
    after: str
    invariant: str
    before_value: int
    after_value: int
    status: str
    boundary: str

@dataclass(frozen=True)
class QTopoLogicalRow:
    """Logical loop row: topology echo can hold while logical shadow changes."""
    name: str
    loop: str
    before_logical: int
    after_logical: int
    topo_echo: bool
    logical_echo: bool
    status: str
    boundary: str

@dataclass(frozen=True)
class QTopoObstructionRow:
    """Topology-breaking deformation row for the finite topological qubit."""
    name: str
    deformation: str
    invariant: str
    before_value: int
    after_value: int
    status: str
    obstruction: str
    boundary: str

@dataclass(frozen=True)
class QBraidOrderRow:
    """Finite braid-order row: adjacent exchanges need not commute."""
    left_word: tuple[str, ...]
    right_word: tuple[str, ...]
    left_shadow: tuple[str, ...]
    right_shadow: tuple[str, ...]
    echo: bool
    status: str
    boundary: str

def topo_shape() -> EchoShape:
    """Return the finite cycle shape used as the protected topology shadow."""
    logger.debug("topo_shape entry")
    result = echo_shape("qtopo_shell", ("A", "B", "C"), (("A", "B"), ("B", "C"), ("C", "A")), "qtopo-shell")
    logger.debug("topo_shape exit result=%r", result)
    return result

def topo_deformed_shape() -> EchoShape:
    """Return a local deformation that preserves the cycle invariant."""
    logger.debug("topo_deformed_shape entry")
    result = subdivide_corridor(topo_shape(), ("A", "B"), "X", "qtopo_shell_subdivided")
    logger.debug("topo_deformed_shape exit result=%r", result)
    return result

def topo_broken_shape() -> EchoShape:
    """Return a topology-breaking deformation of the finite cycle."""
    logger.debug("topo_broken_shape entry")
    result = deform_shape(topo_shape(), {}, "qtopo_shell_torn", drop=(("A", "B"),))
    logger.debug("topo_broken_shape exit result=%r", result)
    return result

def topo_signature(shape: EchoShape) -> tuple[int, int, int]:
    """Return component, boundary, and cycle-rank signature."""
    logger.debug("topo_signature entry shape=%s", shape.name)
    result = (invariant_value(shape, "components"), invariant_value(shape, "boundary"), invariant_value(shape, "cycle-rank"))
    logger.debug("topo_signature exit result=%r", result)
    return result

def vtopo_qubit(logical: int, shape: EchoShape | None = None, name: str | None = None) -> VTopoQubit:
    """Create one finite topological Veyra-qubit shadow."""
    logger.debug("vtopo_qubit entry logical=%d name=%s", logical, name)
    base = topo_shape() if shape is None else shape
    result = VTopoQubit(name or f"vtq{logical}", logical, base, f"|{logical}>_topo", "finite topological echo-class shadow only")
    logger.debug("vtopo_qubit exit result=%r", result)
    return result

def qtopo_echo(left: VTopoQubit, right: VTopoQubit) -> bool:
    """Return topology-signature echo for two finite topological qubits."""
    logger.debug("qtopo_echo entry left=%s right=%s", left.name, right.name)
    result = topo_signature(left.shape) == topo_signature(right.shape)
    logger.debug("qtopo_echo exit result=%s", result)
    return result

def loop_action(qubit: VTopoQubit, loop: str) -> VTopoQubit:
    """Apply a contractible or non-contractible logical loop shadow."""
    logger.debug("loop_action entry qubit=%s loop=%s", qubit.name, loop)
    if loop == "contractible":
        logical = qubit.logical
    elif loop == "noncontractible":
        logical = 1 - qubit.logical
    else:
        logger.error("loop_action unknown loop=%s", loop)
        raise ValueError("unknown loop")
    result = vtopo_qubit(logical, qubit.shape, f"{qubit.name}:{loop}")
    logger.debug("loop_action exit result=%r", result)
    return result

def qtopo_echo_rows() -> tuple[QTopoEchoRow, ...]:
    """Return finite deformation-invariant quantum echo rows."""
    logger.debug("qtopo_echo_rows entry")
    before = vtopo_qubit(0); after = vtopo_qubit(0, topo_deformed_shape(), "vtq0_subdivided")
    rows = []
    for inv in ("components", "boundary", "cycle-rank"):
        left = invariant_value(before.shape, inv); right = invariant_value(after.shape, inv)
        rows.append(QTopoEchoRow(f"qtopo-{inv}", before.name, after.name, inv, left, right, "ready" if left == right else "blocked", "finite local deformation echo only"))
    result = tuple(rows)
    logger.debug("qtopo_echo_rows exit count=%d", len(result))
    return result

def qtopo_logical_rows() -> tuple[QTopoLogicalRow, ...]:
    """Return contractible/non-contractible logical loop rows."""
    logger.debug("qtopo_logical_rows entry")
    start = vtopo_qubit(0)
    rows = []
    for loop in ("contractible", "noncontractible"):
        after = loop_action(start, loop); topo = qtopo_echo(start, after); logical = start.logical == after.logical
        ok = topo and (logical if loop == "contractible" else not logical)
        rows.append(QTopoLogicalRow(f"qtopo-loop-{loop}", loop, start.logical, after.logical, topo, logical, "ready" if ok else "blocked", "finite logical-loop observer row only"))
    result = tuple(rows)
    logger.debug("qtopo_logical_rows exit count=%d", len(result))
    return result

def qtopo_obstruction_rows() -> tuple[QTopoObstructionRow, ...]:
    """Return topology-break obstruction rows."""
    logger.debug("qtopo_obstruction_rows entry")
    before = topo_shape(); after = topo_broken_shape(); inv = "cycle-rank"
    left = invariant_value(before, inv); right = invariant_value(after, inv)
    result = (QTopoObstructionRow("qtopo-tear", "drop A-B", inv, left, right, "ready" if left != right else "blocked", "topology-echo-break", "finite topology-break obstruction only"),)
    logger.debug("qtopo_obstruction_rows exit count=%d", len(result))
    return result

def braid_shadow(word: tuple[str, ...], labels: tuple[str, ...] = ("a", "b", "c")) -> tuple[str, ...]:
    """Return finite braid shadow as adjacent label exchanges."""
    logger.debug("braid_shadow entry word=%r labels=%r", word, labels)
    arr = list(labels)
    for gate in word:
        if gate == "s1": arr[0], arr[1] = arr[1], arr[0]
        elif gate == "s2": arr[1], arr[2] = arr[2], arr[1]
        else:
            logger.error("braid_shadow unknown gate=%s", gate)
            raise ValueError("unknown braid generator")
    result = tuple(arr)
    logger.debug("braid_shadow exit result=%r", result)
    return result

def qbraid_order_rows() -> tuple[QBraidOrderRow, ...]:
    """Return finite non-commuting braid-order rows."""
    logger.debug("qbraid_order_rows entry")
    left, right = ("s1", "s2"), ("s2", "s1")
    ls, rs = braid_shadow(left), braid_shadow(right)
    result = (QBraidOrderRow(left, right, ls, rs, ls == rs, "ready" if ls != rs else "blocked", "finite braid-shadow noncommutation only"),)
    logger.debug("qbraid_order_rows exit count=%d", len(result))
    return result

def quantum_topology_summary() -> dict[str, int]:
    """Return compact Q4 topological-qubit counters."""
    logger.debug("quantum_topology_summary entry")
    e = qtopo_echo_rows(); logical = qtopo_logical_rows(); o = qtopo_obstruction_rows(); b = qbraid_order_rows()
    all_rows = (*e, *logical, *o, *b)
    result = {"topo_qubits": 2, "deformation_echoes": sum(r.status == "ready" for r in e), "logical_rows": sum(r.status == "ready" for r in logical), "obstructions": sum(r.status == "ready" for r in o), "braid_rows": sum(r.status == "ready" for r in b), "overclaims": sum("finite" not in r.boundary for r in all_rows)}
    logger.debug("quantum_topology_summary exit result=%r", result)
    return result

def quantum_topology_checklist() -> tuple[str, ...]:
    """Return Q4 topological-qubit acceptance checklist."""
    logger.debug("quantum_topology_checklist entry")
    result = ("finite VTopoQubit echo class", "local deformation preserves topology signature", "contractible loop is logical-trivial", "noncontractible loop changes logical observer", "topology break creates obstruction", "braid order has finite witness")
    logger.debug("quantum_topology_checklist exit count=%d", len(result))
    return result
