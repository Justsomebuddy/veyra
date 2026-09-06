"""Arithmetic as a variable object over the observer site (docs/191).

Executable twin of ``proofs/lean/VeyraVariableArithmetic.lean``. Stitch
(concatenation, docs/02 §2) and weave (every tact of the first word replaced by
a copy of the second, docs/02 §3) act on the fibre of the presheaf of modes at a
stage exactly when echo at that stage is a congruence for them; then they
commute with restriction. The laws of arithmetic (commutativity, left
distributivity, associativity of cut-stitching on closed modes) are checked as
properties of stages on bounded word families.

Host-carried computation: words are host tuples, host ``==`` compares
readings, the general statements are the Lean cards ``THM_VA_001``–``014``.
The only host-arithmetic shadow is ``parikh_shadow_primitive`` (a ``gcd``
cross-check of the native bag-stage decision), declared in ``SHADOW_LICENSED``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import logging
from math import gcd

from .observer_site import (
    BAG,
    CYCLE,
    LENGTH,
    WORD,
    ObserverSiteError,
    Stage,
    Word,
    echo,
    echo_classes,
    primitive_at,
    refines,
    restriction,
    stage_name,
    validate_presentations,
)

logger = logging.getLogger(__name__)

SHADOW_LICENSED = ("parikh_shadow_primitive",)
MAX_CUT_TRIPLE_LENGTH = 4


def stitch(x: Word, y: Word) -> Word:
    """Stitch of open breaths: concatenation."""
    return x + y


def weave(x: Word, y: Word) -> Word:
    """Weave: every tact of ``x`` replaced by a full copy of ``y``."""
    return y * len(x)


OPERATIONS = {"stitch": stitch, "weave": weave}


@dataclass(frozen=True)
class DescentReport:
    """Whether echo at a stage is a congruence for an operation on a word family (``THM_VA_002/004/005``)."""

    stage: str
    operation: str
    checked: int
    violations: tuple[tuple[Word, Word, Word, Word], ...]

    @property
    def passed(self) -> bool:
        return not self.violations


def descends(stage: Stage, operation: str, presentations: Sequence[Word]) -> DescentReport:
    """Check ``x ≈ x'`` and ``y ≈ y'`` imply ``op(x, y) ≈ op(x', y')`` on all echo pairs of the family."""
    op = OPERATIONS[operation]
    words = validate_presentations(presentations)
    classes = echo_classes(stage, words).classes
    checked = 0
    violations: list[tuple[Word, Word, Word, Word]] = []
    for left_class in classes:
        for right_class in classes:
            for x in left_class:
                for x_prime in left_class:
                    for y in right_class:
                        for y_prime in right_class:
                            checked += 1
                            if not echo(stage, op(x, y), op(x_prime, y_prime)):
                                violations.append((x, x_prime, y, y_prime))
    report = DescentReport(stage_name(stage), operation, checked, tuple(violations))
    logger.debug("descends exit stage=%s op=%s passed=%s", report.stage, operation, report.passed)
    return report


def fibre_action(stage: Stage, operation: str, presentations: Sequence[Word]) -> tuple[tuple[int, int, int], ...]:
    """The operation on echo classes as index triples ``(i, j, k)``; refuses when it does not descend."""
    report = descends(stage, operation, presentations)
    if not report.passed:
        logger.error("fibre_action operation does not descend stage=%s op=%s", report.stage, operation)
        raise ObserverSiteError("operation-does-not-descend")
    op = OPERATIONS[operation]
    words = validate_presentations(presentations)
    classes = echo_classes(stage, words).classes
    rows: list[tuple[int, int, int]] = []
    for i, left_class in enumerate(classes):
        for j, right_class in enumerate(classes):
            result = op(left_class[0], right_class[0])
            targets = [k for k, group in enumerate(classes) if echo(stage, result, group[0])]
            rows.append((i, j, targets[0] if targets else -1))
    return tuple(rows)


def restriction_commutes(coarse: Stage, fine: Stage, operation: str, presentations: Sequence[Word]) -> bool:
    """``THM_VA_001`` on a family: acting at the fine stage then coarsening equals coarsening then acting."""
    if not refines(coarse, fine):
        logger.error("restriction_commutes stages rejected")
        raise ObserverSiteError("restriction-not-refinement")
    words = validate_presentations(presentations)
    fine_action = dict(((i, j), k) for i, j, k in fibre_action(fine, operation, words))
    coarse_action = dict(((i, j), k) for i, j, k in fibre_action(coarse, operation, words))
    coarsen = restriction(coarse, fine, words)
    return all(
        fine_action[(i, j)] == -1 or coarsen[fine_action[(i, j)]] == coarse_action[(coarsen[i], coarsen[j])]
        for i in range(len(coarsen))
        for j in range(len(coarsen))
    )


@dataclass(frozen=True)
class NatShadowReport:
    """The length fibre as the natural numbers (``THM_VA_003``)."""

    classes: int
    lengths: tuple[int, ...]
    stitch_is_addition: bool
    weave_is_multiplication: bool


def nat_shadow(presentations: Sequence[Word]) -> NatShadowReport:
    """Check that at the length stage classes are lengths, stitch adds and weave multiplies them."""
    words = validate_presentations(presentations)
    classes = echo_classes((LENGTH,), words).classes
    lengths = tuple(len(group[0]) for group in classes)
    addition = all(
        len(stitch(x, y)) == len(x) + len(y) and echo((LENGTH,), stitch(x, y), stitch(y, x))
        for x in words
        for y in words
    )
    multiplication = all(len(weave(x, y)) == len(x) * len(y) for x in words for y in words)
    return NatShadowReport(len(classes), lengths, addition, multiplication)


def bag_vector(word: Word, alphabet: Sequence[str]) -> tuple[int, ...]:
    """The Parikh vector of a word over an ordered alphabet."""
    return tuple(sum(1 for letter in word if letter == symbol) for symbol in alphabet)


def parikh_shadow_primitive(word: Word, alphabet: Sequence[str]) -> bool:
    """Host-``gcd`` shadow of bag-stage primitivity: coprime letter counts (``THM_VA_012``)."""
    counts = bag_vector(word, alphabet)
    value = 0
    for count in counts:
        value = gcd(value, count)
    return bool(word) and value == 1


def bag_primitivity_agreement(presentations: Sequence[Word], alphabet: Sequence[str]) -> tuple[int, int]:
    """Compare the native bag-stage decision with its Parikh shadow: (checked, disagreements)."""
    words = [word for word in validate_presentations(presentations) if word]
    disagreements = sum(
        1 for word in words if primitive_at((BAG,), word, alphabet) != parikh_shadow_primitive(word, alphabet)
    )
    return len(words), disagreements


def cyclic_echo(x: Word, y: Word) -> bool:
    """``y`` is a rotation of ``x`` (the cycle stage as a relation)."""
    if len(x) != len(y):
        return False
    return any(x[index:] + x[:index] == y for index in range(len(x))) if x else y == ()


def canonical_cut(word: Word) -> Word:
    """The lexicographically least rotation: one single-valued choice of cut."""
    return min(word[index:] + word[:index] for index in range(len(word))) if word else word


def cut_stitch(x: Word, y: Word) -> Word:
    """Stitch closed modes through their canonical cuts."""
    return canonical_cut(x) + canonical_cut(y)


def canonical_cut_associativity_failures(presentations: Sequence[Word]) -> tuple[tuple[Word, Word, Word], ...]:
    """Triples where ``(x ⊙ y) ⊙ z`` and ``x ⊙ (y ⊙ z)`` are not cyclically echoed (``THM_VA_011``)."""
    words = [word for word in validate_presentations(presentations) if word and len(word) <= MAX_CUT_TRIPLE_LENGTH]
    rows = []
    for x in words:
        for y in words:
            for z in words:
                if not cyclic_echo(cut_stitch(cut_stitch(x, y), z), cut_stitch(x, cut_stitch(y, z))):
                    rows.append((x, y, z))
    return tuple(rows)


def weave_respects_cycle_violations(presentations: Sequence[Word], exponent: int) -> int:
    """Count cyclically echoed pairs whose ``exponent``-th powers are not cyclically echoed (``THM_VA_006``)."""
    words = validate_presentations(presentations)
    return sum(1 for x in words for y in words if cyclic_echo(x, y) and not cyclic_echo(x * exponent, y * exponent))


@dataclass(frozen=True)
class LawRow:
    """The laws of arithmetic at one stage on a bounded family (``THM_VA_007``–``010``)."""

    stage: str
    stitch_descends: bool
    weave_descends: bool
    stitch_commutative: bool
    weave_commutative: bool
    left_distributive: bool
    witnesses: tuple[str, ...]


def law_table(stages: Sequence[Stage], presentations: Sequence[Word]) -> tuple[LawRow, ...]:
    """Which laws hold at which stage; right distributivity and associativity are literal identities."""
    words = validate_presentations(presentations)
    rows: list[LawRow] = []
    for stage in stages:
        stitch_report = descends(stage, "stitch", words)
        weave_report = descends(stage, "weave", words)
        witnesses: list[str] = []
        stitch_comm = True
        weave_comm = True
        left_dist = True
        for x in words:
            for y in words:
                if stitch_comm and not echo(stage, stitch(x, y), stitch(y, x)):
                    stitch_comm = False
                    witnesses.append(f"stitch-comm:{''.join(x) or 'ε'},{''.join(y) or 'ε'}")
                if weave_comm and not echo(stage, weave(x, y), weave(y, x)):
                    weave_comm = False
                    witnesses.append(f"weave-comm:{''.join(x) or 'ε'},{''.join(y) or 'ε'}")
                for y_prime in words:
                    if left_dist and not echo(
                        stage, weave(x, stitch(y, y_prime)), stitch(weave(x, y), weave(x, y_prime))
                    ):
                        left_dist = False
                        witnesses.append(f"left-dist:{''.join(x) or 'ε'},{''.join(y) or 'ε'},{''.join(y_prime) or 'ε'}")
        if not stitch_report.passed:
            x, x_prime, y, _ = stitch_report.violations[0]
            witnesses.append(f"stitch-descent:{''.join(x)}~{''.join(x_prime)},{''.join(y)}")
        rows.append(
            LawRow(
                stage_name(stage),
                stitch_report.passed,
                weave_report.passed,
                stitch_comm,
                weave_comm,
                left_dist,
                tuple(witnesses),
            )
        )
    return tuple(rows)


def literal_laws_hold(presentations: Sequence[Word]) -> bool:
    """Associativity of stitch and weave and right distributivity as literal word identities (``THM_VA_009/010``)."""
    words = validate_presentations(presentations)
    return all(
        stitch(stitch(x, y), z) == stitch(x, stitch(y, z))
        and weave(weave(x, y), z) == weave(x, weave(y, z))
        and weave(stitch(x, y), z) == stitch(weave(x, z), weave(y, z))
        for x in words
        for y in words
        for z in words
    )


def resonates_at(stage: Stage, factor: Word, carrier: Word) -> bool:
    """``factor`` resonates inside ``carrier`` at the stage: the carrier is echoed to a power of the factor (``THM_VA_013/014``)."""
    if not factor:
        return echo(stage, carrier, ())
    return any(echo(stage, carrier, factor * exponent) for exponent in range(len(carrier) + 1))


def length_divides(factor: Word, carrier: Word) -> bool:
    """Divisibility of lengths without host ``%``: some multiple of the factor length is the carrier length."""
    return any(len(factor) * exponent == len(carrier) for exponent in range(len(carrier) + 1))


def standard_stages() -> tuple[Stage, ...]:
    """The four single-observer stages of docs/06 in refinement order."""
    return ((LENGTH,), (BAG,), (CYCLE,), (WORD,))


def observer_arithmetic_checklist() -> tuple[tuple[str, str], ...]:
    """Lean cards of ``VeyraVariableArithmetic.lean`` and their executable replay here."""
    return (
        ("THM_VA_001_restriction_homomorphism", "restriction_commutes on every refinement where both stages descend"),
        ("THM_VA_002_descends_length_word", "descends at {length} and {word} for stitch and weave"),
        ("THM_VA_003_nat_is_length_fibre", "nat_shadow: classes are lengths, stitch adds, weave multiplies"),
        ("THM_VA_004_descends_bag", "descends at {bag} for stitch and weave"),
        ("THM_VA_005_stitch_breaks_cyclic", "descends at {cycle} fails for stitch with witness ab~ba"),
        ("THM_VA_006_weave_respects_cyclic", "weave_respects_cycle_violations == 0"),
        ("THM_VA_007_stitch_comm_stage", "law_table: stitch commutative at {bag}, not at {word}"),
        ("THM_VA_008_weave_comm_stage", "law_table: weave commutative at {length}, not at {bag}"),
        ("THM_VA_009_distributivity_stage", "law_table: left distributive at {bag}, not at {word}; right literal"),
        ("THM_VA_010_open_associativity", "literal_laws_hold"),
        ("THM_VA_011_canonical_cut_not_associative", "canonical_cut_associativity_failures contains (a, b, ab)"),
        ("THM_VA_012_bag_prime_iff_coprime", "bag_primitivity_agreement disagreements == 0"),
        ("THM_VA_013_resonance_retracts", "resonates_at at a finer stage implies resonates_at at a coarser stage"),
        ("THM_VA_014_length_resonance_is_divisibility", "resonates_at({length}) iff length_divides"),
    )
