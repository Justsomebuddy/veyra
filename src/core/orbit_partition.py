"""Orbit-partition rule (DI-2): congruences licensed from partition structure.

DI-2 is the second candidate inference rule of the DI family. For a length
whose primality is witnessed natively — every candidate divisor length leaves
a residual under `structural_divide` — the rotation partition of the words at
that length is classified structurally: the cyclic period of a word is the
least shift `d` whose unary length divides the word length exactly under
`structural_divide` AND whose rotation echoes the word (`_native_period`;
no host `%`/`//` and no `primitive_root` on the decision path), and the
dichotomy "period is 1 or the full length" is licensed BY the divisor
witness. The congruence conclusion is a native reconstruction:
`weave(p̄, full_count)` must breath-equal the nonconstant tally. Boundary
(docs/06 §3 shadow license, stated rather than hidden): the tally is the
ENUMERATED orbit total — every rotation of every class is counted by the
cut-free `cycle_echo` orbit — so the woven equality is a cross-check between
the structural period classification and host enumeration, and word
enumeration/loop counters are host bookkeeping. Composed with DI-1 over the
alphabet depth (letters are minted from the intrinsic index; each step
classifies only the rotation-closed delta of words using the new letter),
this re-derives the N8 Fermat cells for the witnessed prime lengths it is
run on (lengths 3 and 5 in the certificate; N8's p=2,7 rows stay N8-only) as
one licensed family statement each. Statuses are `witnessed`/`blocked`/
`licensed`, never `proved`. See docs/181_orbit_partition_di2.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
import logging

from .doctrinal_induction import PropertyContract, mode_shape
from .intrinsic_arithmetic import one, stitch, successor, weave, zero
from .intrinsic_arithmetic_division import structural_divide
from .modes import Mode as WordMode
from .native_number import cycle_echo
from .native_runtime import Mode, NativeObstruction, Nod

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DivisorRow:
    """One candidate divisor length with its native division outcome."""

    candidate: int
    division_status: str
    residual_tacts: int


@dataclass(frozen=True)
class PrimeLengthWitness:
    """Native primality: every candidate divisor leaves a residual."""

    length: int
    rows: tuple[DivisorRow, ...]
    prime: bool
    status: str
    obstruction: str


@dataclass(frozen=True)
class Di2Evidence:
    """Partition ledger for one (length, alphabet-depth) cell."""

    depth: int
    fix_mode: Mode
    full_mode: Mode
    tally_mode: Mode
    congruent: bool
    status: str
    obstruction: str


def _intrinsic(anchor: Nod, count: int) -> Mode | NativeObstruction:
    logger.debug("di2._intrinsic entry count=%d", count)
    value: Mode | NativeObstruction = zero(anchor)
    for _ in range(count):
        value = successor(value)
        if isinstance(value, NativeObstruction):
            logger.error("di2._intrinsic blocked %r", value)
            return value
    logger.debug("di2._intrinsic exit")
    return value


def _letters(depth: int) -> tuple[str, ...]:
    logger.debug("di2._letters entry depth=%d", depth)
    result = tuple(f"t{index + 1}" for index in range(depth))
    logger.debug("di2._letters exit count=%d", len(result))
    return result


def prime_length_witness(anchor: Nod, length: int) -> PrimeLengthWitness:
    """Witness primality natively: each candidate divisor leaves a residual."""
    logger.debug("di2.prime_length_witness entry length=%d", length)
    if length < 2:
        result = PrimeLengthWitness(length, (), False, "blocked", "length-too-short")
        logger.error("di2.prime_length_witness blocked %r", result)
        return result
    p_mode = _intrinsic(anchor, length)
    if isinstance(p_mode, NativeObstruction):
        result = PrimeLengthWitness(length, (), False, "blocked", p_mode.reason)
        logger.error("di2.prime_length_witness blocked %r", result)
        return result
    rows: list[DivisorRow] = []
    for candidate in range(2, length):
        d_mode = _intrinsic(anchor, candidate)
        if isinstance(d_mode, NativeObstruction):
            result = PrimeLengthWitness(length, tuple(rows), False, "blocked", d_mode.reason)
            logger.error("di2.prime_length_witness blocked %r", result)
            return result
        proof = structural_divide(p_mode, d_mode)
        rows.append(DivisorRow(candidate, proof.status, len(proof.residual.breath.tacts)))
        if proof.status == "exact":
            result = PrimeLengthWitness(length, tuple(rows), False, "blocked", "composite-length")
            logger.error("di2.prime_length_witness composite divisor=%d", candidate)
            return result
        if proof.status != "residual":
            result = PrimeLengthWitness(length, tuple(rows), False, "blocked", proof.status)
            logger.error("di2.prime_length_witness blocked %r", result)
            return result
    result = PrimeLengthWitness(length, tuple(rows), True, "witnessed", "none")
    logger.debug("di2.prime_length_witness exit prime=%s rows=%d", result.prime, len(rows))
    return result


def _native_period(anchor: Nod, p_mode: Mode, word: tuple[str, ...]) -> Mode | NativeObstruction:
    """Return the cyclic period of `word` as a unary mode, decided structurally.

    The period is the least shift `d >= 1` such that (i) the unary length `d̄`
    divides `p̄` exactly under `structural_divide` and (ii) the rotation by `d`
    echoes the word. No host `%`/`//` and no `primitive_root` are consulted;
    the rotation echo is tuple equality under the docs/06 §3 shadow license.
    """
    logger.debug("di2._native_period entry length=%d", len(word))
    length = len(word)
    for shift in range(1, length):
        d_mode = _intrinsic(anchor, shift)
        if isinstance(d_mode, NativeObstruction):
            logger.error("di2._native_period blocked %r", d_mode)
            return d_mode
        if structural_divide(p_mode, d_mode).status != "exact":
            continue
        if word[shift:] + word[:shift] == word:
            logger.debug("di2._native_period exit period=%d", shift)
            return d_mode
    logger.debug("di2._native_period exit period=full")
    return p_mode


def _classify(
    anchor: Nod,
    p_mode: Mode,
    length: int,
    words: tuple[tuple[str, ...], ...],
) -> tuple[int, int, Mode, Mode] | NativeObstruction:
    """Classify words into constant and full orbits via the structural route."""
    logger.debug("di2._classify entry words=%d", len(words))
    classes: dict[object, tuple[str, ...]] = {}
    for word in words:
        echo = cycle_echo(WordMode(word))
        if echo not in classes:
            classes[echo] = word
    fix = 0
    full_count_mode: Mode | NativeObstruction = zero(anchor)
    tally: Mode | NativeObstruction = zero(anchor)
    unit = one(anchor)
    for echo, representative in classes.items():
        per_mode = _native_period(anchor, p_mode, representative)
        if isinstance(per_mode, NativeObstruction):
            logger.error("di2._classify blocked %r", per_mode)
            return per_mode
        if per_mode.breath == unit.breath:
            if len(set(representative)) != 1:
                result = NativeObstruction(
                    "di2-partition", "period-one-nonconstant", ("".join(representative),)
                )
                logger.error("di2._classify period-one nonconstant rep=%s", "".join(representative))
                return result
            fix += 1
            continue
        proof = structural_divide(p_mode, per_mode)
        if proof.status != "exact" or per_mode.breath != p_mode.breath:
            result = NativeObstruction(
                "di2-partition", "dichotomy-failure", ("".join(representative),)
            )
            logger.error("di2._classify dichotomy break rep=%s", "".join(representative))
            return result
        full_count_mode = successor(full_count_mode)
        if isinstance(full_count_mode, NativeObstruction):
            logger.error("di2._classify blocked %r", full_count_mode)
            return full_count_mode
        for _ in range(len(echo.orbit)):
            tally = successor(tally)
            if isinstance(tally, NativeObstruction):
                logger.error("di2._classify blocked %r", tally)
                return tally
    logger.debug("di2._classify exit classes=%d fix=%d", len(classes), fix)
    return (len(classes), fix, full_count_mode, tally)


def partition_evidence(anchor: Nod, length: int, depth: int) -> Di2Evidence:
    """Build the full partition ledger for one (length, depth) cell."""
    logger.debug("di2.partition_evidence entry length=%d depth=%d", length, depth)
    p_mode = _intrinsic(anchor, length)
    silent = zero(anchor)
    if isinstance(p_mode, NativeObstruction):
        result = Di2Evidence(depth, silent, silent, silent, False, "blocked", p_mode.reason)
        logger.error("di2.partition_evidence blocked %r", result)
        return result
    words = tuple(product(_letters(depth), repeat=length))
    classified = _classify(anchor, p_mode, length, words)
    if isinstance(classified, NativeObstruction):
        result = Di2Evidence(depth, silent, silent, silent, False, "blocked", classified.reason)
        logger.error("di2.partition_evidence blocked %r", result)
        return result
    _total_classes, fix, full_mode, tally = classified
    fix_mode = _intrinsic(anchor, fix)
    if isinstance(fix_mode, NativeObstruction):
        result = Di2Evidence(depth, silent, silent, silent, False, "blocked", fix_mode.reason)
        logger.error("di2.partition_evidence blocked %r", result)
        return result
    woven = weave(p_mode, full_mode)
    congruent = isinstance(woven, Mode) and woven.breath == tally.breath
    depth_mode = _intrinsic(anchor, depth)
    fix_matches_depth = (
        isinstance(depth_mode, Mode) and fix_mode.breath == depth_mode.breath
    )
    if not congruent or not fix_matches_depth:
        obstruction = "congruence-reconstruction-failed" if not congruent else "constant-count-mismatch"
        result = Di2Evidence(depth, fix_mode, full_mode, tally, congruent, "blocked", obstruction)
        logger.error("di2.partition_evidence blocked %r", obstruction)
        return result
    result = Di2Evidence(depth, fix_mode, full_mode, tally, True, "witnessed", "none")
    logger.debug("di2.partition_evidence exit witnessed depth=%d", depth)
    return result


def _evidence_shape(evidence: object, rename: dict[str, str]) -> str:
    logger.debug("di2._evidence_shape entry")
    if not isinstance(evidence, Di2Evidence):
        result = f"nondi2[{type(evidence).__name__}]"
        logger.debug("di2._evidence_shape exit result=%s", result)
        return result
    result = "di2[{};{};{};{};{};{}]".format(
        evidence.depth, evidence.status, evidence.congruent,
        mode_shape(evidence.fix_mode, rename), mode_shape(evidence.full_mode, rename),
        mode_shape(evidence.tally_mode, rename),
    )
    logger.debug("di2._evidence_shape exit")
    return result


def fermat_family_contract(length: int):
    """Contract factory: the Fermat partition family over alphabet depth."""
    logger.debug("di2.fermat_family_contract entry length=%d", length)

    def factory(anchor: Nod) -> PropertyContract | NativeObstruction:
        logger.debug("di2.fermat.factory entry")
        primality = prime_length_witness(anchor, length)
        if not primality.prime:
            result = NativeObstruction("di2-fermat", primality.obstruction, (str(length),))
            logger.error("di2.fermat.factory blocked %r", result)
            return result

        def subject_base(a: Nod) -> Mode | NativeObstruction:
            logger.debug("di2.fermat.subject_base entry")
            return one(a)

        def subject_step(previous: Mode) -> Mode | NativeObstruction:
            logger.debug("di2.fermat.subject_step entry")
            return successor(previous)

        def establish_base(a: Nod, subject: Mode) -> object:
            logger.debug("di2.fermat.establish_base entry")
            evidence = partition_evidence(a, length, 1)
            if evidence.status != "witnessed":
                return NativeObstruction("di2-fermat", evidence.obstruction, ())
            return evidence

        def transform_step(a: Nod, previous: Mode, current: Mode, prior: object) -> object:
            logger.debug("di2.fermat.transform_step entry")
            if not isinstance(prior, Di2Evidence) or prior.status != "witnessed":
                result = NativeObstruction("di2-fermat", "prior-evidence-not-witnessed", ())
                logger.error("di2.fermat.transform_step blocked %r", result)
                return result
            depth = prior.depth + 1
            letters = _letters(depth)
            fresh = letters[-1]
            delta = tuple(
                word for word in product(letters, repeat=length) if fresh in word
            )
            p_mode = _intrinsic(a, length)
            if isinstance(p_mode, NativeObstruction):
                return p_mode
            classified = _classify(a, p_mode, length, delta)
            if isinstance(classified, NativeObstruction):
                logger.error("di2.fermat.transform_step blocked %r", classified)
                return classified
            _classes, delta_fix, delta_full, delta_tally = classified
            if delta_fix != 1:
                result = NativeObstruction("di2-fermat", "delta-constant-count", (str(delta_fix),))
                logger.error("di2.fermat.transform_step blocked %r", result)
                return result
            fix_mode = successor(prior.fix_mode)
            full_mode = stitch(prior.full_mode, delta_full)
            tally = stitch(prior.tally_mode, delta_tally)
            for value in (fix_mode, full_mode, tally):
                if isinstance(value, NativeObstruction):
                    logger.error("di2.fermat.transform_step blocked %r", value)
                    return value
            woven = weave(p_mode, full_mode)
            congruent = isinstance(woven, Mode) and woven.breath == tally.breath
            result = Di2Evidence(
                depth, fix_mode, full_mode, tally, congruent,
                "witnessed" if congruent else "blocked",
                "none" if congruent else "congruence-reconstruction-failed",
            )
            logger.debug("di2.fermat.transform_step exit depth=%d", depth)
            return result

        def validate(a: Nod, subject: Mode, evidence: object) -> bool | NativeObstruction:
            logger.debug("di2.fermat.validate entry")
            if not isinstance(evidence, Di2Evidence) or evidence.status != "witnessed":
                logger.error("di2.fermat.validate wrong evidence")
                return False
            if not evidence.congruent:
                logger.error("di2.fermat.validate noncongruent")
                return False
            independent = partition_evidence(a, length, evidence.depth)
            result = (
                independent.status == "witnessed"
                and independent.fix_mode.breath == evidence.fix_mode.breath
                and independent.full_mode.breath == evidence.full_mode.breath
                and independent.tally_mode.breath == evidence.tally_mode.breath
                and subject.breath == evidence.fix_mode.breath
            )
            if not result:
                logger.error("di2.fermat.validate independent recheck failed")
            logger.debug("di2.fermat.validate exit result=%s", result)
            return result

        result = PropertyContract(
            "di2.fermat-partition.v1", subject_base, subject_step,
            establish_base, transform_step, validate, _evidence_shape,
        )
        logger.debug("di2.fermat.factory exit")
        return result

    logger.debug("di2.fermat_family_contract exit")
    return factory


def tally_bomb_contract(length: int, bomb_depth: int):
    """Adversarial control: drop one tally tact at one exact depth."""
    logger.debug("di2.tally_bomb_contract entry bomb=%d", bomb_depth)
    base_factory = fermat_family_contract(length)

    def factory(anchor: Nod) -> PropertyContract | NativeObstruction:
        logger.debug("di2.bomb.factory entry")
        inner = base_factory(anchor)
        if isinstance(inner, NativeObstruction):
            return inner

        def transform(a: Nod, previous: Mode, current: Mode, prior: object) -> object:
            logger.debug("di2.bomb.transform entry")
            evidence = inner.transform_step(a, previous, current, prior)
            if isinstance(evidence, Di2Evidence) and evidence.depth == bomb_depth:
                logger.error("di2.bomb.transform corrupting depth=%d", bomb_depth)
                truncated = Mode(
                    type(evidence.tally_mode.breath)(
                        evidence.tally_mode.breath.tacts[:-1]
                    ),
                    evidence.tally_mode.observer,
                )
                return Di2Evidence(
                    evidence.depth, evidence.fix_mode, evidence.full_mode,
                    truncated, evidence.congruent, evidence.status, evidence.obstruction,
                )
            return evidence

        result = PropertyContract(
            "di2.tally-bomb-control.v1", inner.subject_base, inner.subject_step,
            inner.establish_base, transform, inner.validate, inner.evidence_shape,
        )
        logger.debug("di2.bomb.factory exit")
        return result

    logger.debug("di2.tally_bomb_contract exit")
    return factory


def orbit_partition_checklist() -> tuple[str, ...]:
    """Return the DI-2 lane acceptance checklist."""
    logger.debug("di2.checklist entry")
    result = (
        "primality is witnessed natively: every candidate divisor leaves a structural residual",
        "the cyclic period is decided by structural division plus rotation echo; no host % or primitive_root on the decision path",
        "the congruence is a native reconstruction: weave(length, full-orbits) breath-equals the enumerated nonconstant tally (declared host bookkeeping)",
        "the family step classifies only the rotation-closed delta; the validator recomputes independently",
        "composed with DI-1 this re-derives the N8 Fermat cells at the witnessed lengths it is run on; statuses never say proved",
    )
    logger.debug("di2.checklist exit count=%d", len(result))
    return result
