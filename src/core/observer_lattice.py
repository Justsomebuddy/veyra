"""Observer lattice (TR-1): arithmetic observables across commutation doctrines.

A commutation doctrine declares which unordered letter pairs may swap when
adjacent. Doctrines form a refinement lattice between the ordered word
observer (no pairs) and the bag observer (all pairs). TR-1 makes the lattice
executable and instruments the first arithmetic transfer questions on it:

- node identity is the FULL trace class — the swap-reachability echo object —
  never a canonical representative; the Cartier–Foata layer form is computed
  as a display/receipt (intra-layer print order is a docs/06 §3 shadow; the
  layer SETS are canonical);
- node primitivity: a word is imprimitive at a doctrine iff its trace class
  contains a literal power, detected through the cut-free `primitive_root`
  of members; the edge obstruction Ω is the concrete exhibit `v = u^k` that
  lives in the coarse class and is absent from the fine one;
- transfer monotonicity (coarse-primitive implies fine-primitive) has its
  formal spine in `proofs/lean/VeyraObserverLattice.lean` (`Reaches`
  closure monotonicity); here every edge row carries executable witnesses;
- the fragility spectrum of a word along a doctrine chain records per-node
  status and the exact first-break edge with its Ω exhibit.

Class enumeration is exact and bounded: exceeding the declared cap yields a
typed `class-size-refusal`, never a silent truncation. Loop counters and
set/frozenset grouping are docs/06 §3 shadow bookkeeping in the same sense
as `native_number.CycleEcho`; classical trace theory (Cartier–Foata,
Mazurkiewicz) is credited in doc 182 — the registered novelty is the
transfer/obstruction instrumentation, not trace monoids. Statuses are
`witnessed`/`blocked`/`refused`, never `proved`. TR-2 (licensed transfer
laws) is OPEN. See docs/182_observer_lattice_tr1.md.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .modes import Mode as WordMode, primitive_root

logger = logging.getLogger(__name__)

DEFAULT_CLASS_CAP = 1500


@dataclass(frozen=True)
class CommutationDoctrine:
    """One lattice node: alphabet plus unordered independent letter pairs."""

    doctrine_id: str
    alphabet: tuple[str, ...]
    independent_pairs: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class TraceEcho:
    """Whole swap-reachability class at a doctrine — the node echo object."""

    doctrine_id: str
    words: frozenset[tuple[str, ...]]

    @property
    def size(self) -> int:
        """Return exact class size (shadow bookkeeping)."""
        logger.debug("TraceEcho.size entry")
        result = len(self.words)
        logger.debug("TraceEcho.size exit result=%d", result)
        return result

    def contains(self, word: tuple[str, ...]) -> bool:
        """Return native membership of a presentation in this class."""
        logger.debug("TraceEcho.contains entry word=%s", "".join(word))
        result = word in self.words
        logger.debug("TraceEcho.contains exit result=%s", result)
        return result


@dataclass(frozen=True)
class RefinementRow:
    """Edge check: fine must declare a subset of the coarse pairs."""

    fine_id: str
    coarse_id: str
    extra_pairs: tuple[tuple[str, str], ...]
    status: str
    obstruction: str


@dataclass(frozen=True)
class PrimitivityRow:
    """Node observable: primitivity with an explicit power exhibit."""

    doctrine_id: str
    word: str
    class_size: int
    primitive: bool
    power_word: str
    power_root: str
    power_exponent: int
    status: str
    obstruction: str


@dataclass(frozen=True)
class TransferRow:
    """One lattice edge for one word: stability or the Ω break exhibit."""

    word: str
    fine_id: str
    coarse_id: str
    fine_primitive: bool
    coarse_primitive: bool
    omega_word: str
    omega_root: str
    omega_exponent: int
    omega_outside_fine: bool
    status: str
    obstruction: str


@dataclass(frozen=True)
class SpectrumReport:
    """Fragility spectrum of one word along a doctrine chain."""

    word: str
    nodes: tuple[PrimitivityRow, ...]
    edges: tuple[TransferRow, ...]
    first_break_edge: str
    status: str
    obstruction: str


def _normalize_pairs(pairs: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    logger.debug("lattice._normalize_pairs entry count=%d", len(pairs))
    seen = []
    for left, right in pairs:
        item = (left, right) if left <= right else (right, left)
        if item not in seen:
            seen.append(item)
    result = tuple(sorted(seen))
    logger.debug("lattice._normalize_pairs exit count=%d", len(result))
    return result


def doctrine(doctrine_id: str, alphabet: tuple[str, ...], pairs: tuple[tuple[str, str], ...]) -> CommutationDoctrine | RefinementRow:
    """Build a validated doctrine; reject reflexive or foreign pairs."""
    logger.debug("lattice.doctrine entry id=%s", doctrine_id)
    normalized = _normalize_pairs(pairs)
    for left, right in normalized:
        if left == right or left not in alphabet or right not in alphabet:
            result = RefinementRow(doctrine_id, doctrine_id, ((left, right),), "blocked", "invalid-pair")
            logger.error("lattice.doctrine blocked pair=(%s,%s)", left, right)
            return result
    result = CommutationDoctrine(doctrine_id, tuple(alphabet), normalized)
    logger.debug("lattice.doctrine exit pairs=%d", len(normalized))
    return result


def _independent(node: CommutationDoctrine, left: str, right: str) -> bool:
    logger.debug("lattice._independent entry %s,%s", left, right)
    item = (left, right) if left <= right else (right, left)
    result = item in node.independent_pairs
    logger.debug("lattice._independent exit result=%s", result)
    return result


def trace_class(node: CommutationDoctrine, word: tuple[str, ...], cap: int = DEFAULT_CLASS_CAP) -> TraceEcho | tuple[str, int]:
    """Enumerate the full swap-reachability class, or refuse at the cap."""
    logger.debug("lattice.trace_class entry node=%s word=%s", node.doctrine_id, "".join(word))
    frontier = [tuple(word)]
    seen: set[tuple[str, ...]] = {tuple(word)}
    while frontier:
        current = frontier.pop()
        for index in range(len(current) - 1):
            left, right = current[index], current[index + 1]
            if left != right and _independent(node, left, right):
                swapped = current[:index] + (right, left) + current[index + 2:]
                if swapped not in seen:
                    if len(seen) >= cap:
                        logger.error("lattice.trace_class refusal cap=%d", cap)
                        return ("class-size-refusal", cap)
                    seen.add(swapped)
                    frontier.append(swapped)
    result = TraceEcho(node.doctrine_id, frozenset(seen))
    logger.debug("lattice.trace_class exit size=%d", result.size)
    return result


def verify_class_closure(node: CommutationDoctrine, echo: TraceEcho) -> bool:
    """Re-check independently that a claimed class is swap-closed."""
    logger.debug("lattice.verify_class_closure entry size=%d", echo.size)
    for member in echo.words:
        for index in range(len(member) - 1):
            left, right = member[index], member[index + 1]
            if left != right and _independent(node, left, right):
                swapped = member[:index] + (right, left) + member[index + 2:]
                if swapped not in echo.words:
                    logger.error("lattice.verify_class_closure open at %s", "".join(member))
                    return False
    logger.debug("lattice.verify_class_closure exit closed=True")
    return True


def foata_layers(node: CommutationDoctrine, word: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    """Return Cartier–Foata layers as a display receipt (layer sets canonical)."""
    logger.debug("lattice.foata_layers entry word=%s", "".join(word))
    remaining = list(range(len(word)))
    depends: dict[int, set[int]] = {index: set() for index in remaining}
    for later in remaining:
        for earlier in range(later):
            if word[earlier] == word[later] or not _independent(node, word[earlier], word[later]):
                depends[later].add(earlier)
    layers: list[tuple[str, ...]] = []
    placed: set[int] = set()
    while len(placed) < len(word):
        ready = tuple(
            index for index in remaining
            if index not in placed and depends[index] <= placed
        )
        if not ready:
            logger.error("lattice.foata_layers stalled placed=%d", len(placed))
            break
        layers.append(tuple(sorted(word[index] for index in ready)))
        placed.update(ready)
    result = tuple(layers)
    logger.debug("lattice.foata_layers exit layers=%d", len(result))
    return result


def refinement_row(fine: CommutationDoctrine, coarse: CommutationDoctrine) -> RefinementRow:
    """Check that `fine` refines `coarse` (declares no extra independence)."""
    logger.debug("lattice.refinement_row entry %s->%s", fine.doctrine_id, coarse.doctrine_id)
    extra = tuple(pair for pair in fine.independent_pairs if pair not in coarse.independent_pairs)
    if fine.alphabet != coarse.alphabet:
        result = RefinementRow(fine.doctrine_id, coarse.doctrine_id, extra, "blocked", "alphabet-mismatch")
        logger.error("lattice.refinement_row blocked alphabet")
        return result
    if extra:
        result = RefinementRow(fine.doctrine_id, coarse.doctrine_id, extra, "blocked", "not-a-refinement")
        logger.error("lattice.refinement_row blocked extra=%d", len(extra))
        return result
    result = RefinementRow(fine.doctrine_id, coarse.doctrine_id, (), "witnessed", "none")
    logger.debug("lattice.refinement_row exit witnessed")
    return result


def _power_exhibit(echo: TraceEcho) -> tuple[str, str, int] | None:
    logger.debug("lattice._power_exhibit entry size=%d", echo.size)
    for member in sorted(echo.words):
        root, exponent = primitive_root(WordMode(member))
        if exponent >= 2:
            logger.debug("lattice._power_exhibit exit member=%s k=%d", "".join(member), exponent)
            return ("".join(member), root.word, exponent)
    logger.debug("lattice._power_exhibit exit none")
    return None


def primitivity_row(node: CommutationDoctrine, word: tuple[str, ...], cap: int = DEFAULT_CLASS_CAP) -> PrimitivityRow:
    """Decide node primitivity through the whole class; exhibit any power."""
    logger.debug("lattice.primitivity_row entry node=%s word=%s", node.doctrine_id, "".join(word))
    echo = trace_class(node, word, cap)
    text = "".join(word)
    if isinstance(echo, tuple):
        result = PrimitivityRow(node.doctrine_id, text, 0, False, "", "", 0, "refused", echo[0])
        logger.error("lattice.primitivity_row refused %s", echo[0])
        return result
    exhibit = _power_exhibit(echo)
    if exhibit is None:
        result = PrimitivityRow(node.doctrine_id, text, echo.size, True, "", "", 0, "witnessed", "none")
    else:
        result = PrimitivityRow(node.doctrine_id, text, echo.size, False, exhibit[0], exhibit[1], exhibit[2], "witnessed", "none")
    logger.debug("lattice.primitivity_row exit primitive=%s", result.primitive)
    return result


def transfer_row(fine: CommutationDoctrine, coarse: CommutationDoctrine, word: tuple[str, ...], cap: int = DEFAULT_CLASS_CAP) -> TransferRow:
    """One edge for one word: stability, or the Ω exhibit outside the fine class."""
    logger.debug("lattice.transfer_row entry %s->%s word=%s", fine.doctrine_id, coarse.doctrine_id, "".join(word))
    text = "".join(word)
    edge = refinement_row(fine, coarse)
    if edge.status != "witnessed":
        result = TransferRow(text, fine.doctrine_id, coarse.doctrine_id, False, False, "", "", 0, False, "blocked", edge.obstruction)
        logger.error("lattice.transfer_row blocked %s", edge.obstruction)
        return result
    fine_echo = trace_class(fine, word, cap)
    coarse_echo = trace_class(coarse, word, cap)
    for echo in (fine_echo, coarse_echo):
        if isinstance(echo, tuple):
            result = TransferRow(text, fine.doctrine_id, coarse.doctrine_id, False, False, "", "", 0, False, "refused", echo[0])
            logger.error("lattice.transfer_row refused %s", echo[0])
            return result
    if not fine_echo.words <= coarse_echo.words:
        result = TransferRow(text, fine.doctrine_id, coarse.doctrine_id, False, False, "", "", 0, False, "blocked", "class-containment-violated")
        logger.error("lattice.transfer_row containment violated")
        return result
    fine_exhibit = _power_exhibit(fine_echo)
    coarse_exhibit = _power_exhibit(coarse_echo)
    fine_primitive = fine_exhibit is None
    coarse_primitive = coarse_exhibit is None
    if fine_primitive and coarse_primitive:
        result = TransferRow(text, fine.doctrine_id, coarse.doctrine_id, True, True, "", "", 0, False, "witnessed", "none")
    elif not fine_primitive:
        result = TransferRow(
            text, fine.doctrine_id, coarse.doctrine_id, False, False,
            fine_exhibit[0], fine_exhibit[1], fine_exhibit[2], False, "witnessed", "none",
        )
    else:
        outside = not fine_echo.contains(tuple(coarse_exhibit[0]))
        result = TransferRow(
            text, fine.doctrine_id, coarse.doctrine_id, True, False,
            coarse_exhibit[0], coarse_exhibit[1], coarse_exhibit[2], outside,
            "witnessed" if outside else "blocked",
            "none" if outside else "omega-not-outside-fine",
        )
    logger.debug("lattice.transfer_row exit status=%s", result.status)
    return result


def fragility_spectrum(chain: tuple[CommutationDoctrine, ...], word: tuple[str, ...], cap: int = DEFAULT_CLASS_CAP) -> SpectrumReport:
    """Per-node primitivity plus per-edge transfer along a refinement chain."""
    logger.debug("lattice.fragility_spectrum entry chain=%d word=%s", len(chain), "".join(word))
    text = "".join(word)
    if len(chain) < 2:
        result = SpectrumReport(text, (), (), "", "blocked", "chain-too-short")
        logger.error("lattice.fragility_spectrum blocked chain-too-short")
        return result
    nodes = tuple(primitivity_row(node, word, cap) for node in chain)
    for row in nodes:
        if row.status != "witnessed":
            result = SpectrumReport(text, nodes, (), "", row.status, row.obstruction)
            logger.error("lattice.fragility_spectrum %s %s", row.status, row.obstruction)
            return result
    edges = []
    first_break = ""
    for fine, coarse in zip(chain, chain[1:]):
        row = transfer_row(fine, coarse, word, cap)
        edges.append(row)
        if row.status != "witnessed":
            result = SpectrumReport(text, nodes, tuple(edges), "", row.status, row.obstruction)
            logger.error("lattice.fragility_spectrum edge %s", row.obstruction)
            return result
        if not first_break and row.fine_primitive and not row.coarse_primitive:
            first_break = "%s->%s" % (row.fine_id, row.coarse_id)
    result = SpectrumReport(text, nodes, tuple(edges), first_break, "witnessed", "none")
    logger.debug("lattice.fragility_spectrum exit first_break=%s", first_break or "-")
    return result


def observer_lattice_checklist() -> tuple[str, ...]:
    """Return the TR-1 lane acceptance checklist."""
    logger.debug("lattice.checklist entry")
    result = (
        "node identity is the whole trace-class echo; Cartier-Foata layers are display receipts only",
        "primitivity is decided through class members via the cut-free primitive root",
        "every break carries a concrete omega exhibit verified to live outside the fine class",
        "refinement edges are checked with extra-pair witnesses; class caps refuse, never truncate",
        "monotonicity has a formal Lean spine; TR-2 transfer laws stay OPEN; nothing here is proved",
    )
    logger.debug("lattice.checklist exit count=%d", len(result))
    return result
