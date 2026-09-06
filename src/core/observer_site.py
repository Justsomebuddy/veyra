"""Finite observer site: apartness, echo, silence and stage-relative equality (docs/190).

Executable twin of ``proofs/lean/VeyraObserverSite.lean``. A *stage* is a finite
family of admitted observers; an observer reads a presentation and answers a
hashable value or ``SILENT``. Distinction is the positive primitive and
persists when observers are added; echo is its defeasible negation and can be
retracted by a finer stage; internal equality relative to a site is "never
apart within the site". Every pair therefore carries a three-valued status at
every stage (echo / apart / silent).

Host-carried computation: readings are host values compared by host ``==``;
stages are host tuples; the general statements are the Lean cards
``THM_OS_001``–``019``, this module only replays them on bounded finite sites.
Nothing here forms observers, and no result concerns physical observers.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum
from itertools import product
import logging

logger = logging.getLogger(__name__)

Word = tuple[str, ...]
SILENT = None
SHADOW_LICENSED: tuple[str, ...] = ()
MAX_SITE_OBSERVERS = 6
MAX_PRESENTATIONS = 256
MAX_POWER_LENGTH = 12


class ObserverSiteError(ValueError):
    """Raised on a malformed site, stage or presentation family."""


@dataclass(frozen=True)
class Observer:
    """One partial observer: ``read`` answers a hashable value or ``SILENT``."""

    name: str
    read: Callable[[Word], object]
    length_respecting: bool = False


Stage = tuple[Observer, ...]


class PairStatus(str, Enum):
    """The three-valued judgment of one pair at one stage (``THM_OS_003``)."""

    ECHO = "echo"
    APART = "apart"
    SILENT = "silent"


def distinguishes(observer: Observer, x: Word, y: Word) -> bool:
    """One observer positively distinguishes: ready on both with different values."""
    left, right = observer.read(x), observer.read(y)
    return left is not SILENT and right is not SILENT and left != right


def echoes(observer: Observer, x: Word, y: Word) -> bool:
    """One observer echoes: ready on both with the same value."""
    left, right = observer.read(x), observer.read(y)
    return left is not SILENT and right is not SILENT and left == right


def apart(stage: Stage, x: Word, y: Word) -> bool:
    """Apartness at a stage: some admitted observer distinguishes."""
    return any(distinguishes(observer, x, y) for observer in stage)


def echo(stage: Stage, x: Word, y: Word) -> bool:
    """Echo at a stage: every admitted observer echoes."""
    return all(echoes(observer, x, y) for observer in stage)


def readable(stage: Stage, x: Word) -> bool:
    """Every admitted observer is ready on ``x`` (``THM_OS_017``: echo is reflexive exactly here)."""
    return all(observer.read(x) is not SILENT for observer in stage)


def pair_status(stage: Stage, x: Word, y: Word) -> PairStatus:
    """Exhaustive and exclusive status of one pair at one stage."""
    if echo(stage, x, y):
        return PairStatus.ECHO
    if apart(stage, x, y):
        return PairStatus.APART
    return PairStatus.SILENT


def refines(coarse: Stage, fine: Stage) -> bool:
    """``coarse`` is refined by ``fine``: every admitted observer stays admitted."""
    names = {observer.name for observer in fine}
    return all(observer.name in names for observer in coarse)


def internal_equal(site: Stage, x: Word, y: Word) -> bool:
    """Internal equality relative to a site: never apart within the site."""
    return not apart(site, x, y)


def forces_decided(site: Stage, stage: Stage, x: Word, y: Word) -> bool:
    """Kripke forcing of ``x = y ∨ x # y`` at ``stage`` of ``site`` (``THM_OS_009/010``)."""
    return internal_equal(site, x, y) or apart(stage, x, y)


def validate_site(site: Stage) -> None:
    """Reject sites that are not small tuples of distinctly named observers."""
    if type(site) is not tuple or not site or len(site) > MAX_SITE_OBSERVERS:
        logger.error("validate_site size rejected")
        raise ObserverSiteError("site-size")
    if any(type(observer) is not Observer for observer in site):
        logger.error("validate_site member rejected")
        raise ObserverSiteError("site-member")
    if len({observer.name for observer in site}) != len(site):
        logger.error("validate_site duplicate name rejected")
        raise ObserverSiteError("site-duplicate-name")


def validate_presentations(presentations: Sequence[Word]) -> tuple[Word, ...]:
    """Return a bounded, duplicate-free tuple of word presentations."""
    words = tuple(presentations)
    if not words or len(words) > MAX_PRESENTATIONS or len(set(words)) != len(words):
        logger.error("validate_presentations rejected")
        raise ObserverSiteError("presentations")
    if any(type(word) is not tuple or any(type(letter) is not str for letter in word) for word in words):
        logger.error("validate_presentations letter rejected")
        raise ObserverSiteError("presentation-letters")
    return words


def substages(site: Stage) -> tuple[Stage, ...]:
    """All admitted subfamilies of the site, in binary order (the stage lattice)."""
    validate_site(site)
    rows: list[Stage] = []
    for mask in range(1 << len(site)):
        rows.append(tuple(observer for index, observer in enumerate(site) if mask >> index & 1))
    return tuple(rows)


def stage_name(stage: Stage) -> str:
    """Canonical display name of a stage."""
    return "{" + ",".join(observer.name for observer in stage) + "}"


@dataclass(frozen=True)
class SiteLawReport:
    """Executable replay of ``THM_OS_001``–``003`` over the whole stage lattice."""

    stages: int
    pairs: int
    persistence_violations: int
    retraction_violations: int
    trichotomy_violations: int
    silent_pairs: int

    @property
    def passed(self) -> bool:
        return not (self.persistence_violations or self.retraction_violations or self.trichotomy_violations)


def site_law_report(site: Stage, presentations: Sequence[Word]) -> SiteLawReport:
    """Check persistence, retraction and trichotomy on every stage pair of the lattice."""
    words = validate_presentations(presentations)
    stages = substages(site)
    statuses = {stage_name(stage): {(x, y): pair_status(stage, x, y) for x in words for y in words} for stage in stages}
    persistence = retraction = trichotomy = silent = 0
    for stage in stages:
        table = statuses[stage_name(stage)]
        silent += sum(1 for status in table.values() if status is PairStatus.SILENT)
        for x in words:
            for y in words:
                if echo(stage, x, y) and apart(stage, x, y):
                    trichotomy += 1
        for finer in stages:
            if not refines(stage, finer):
                continue
            finer_table = statuses[stage_name(finer)]
            for pair, status in table.items():
                if status is PairStatus.APART and finer_table[pair] is not PairStatus.APART:
                    persistence += 1
                if finer_table[pair] is PairStatus.ECHO and status is not PairStatus.ECHO:
                    retraction += 1
    report = SiteLawReport(len(stages), len(words) * len(words), persistence, retraction, trichotomy, silent)
    logger.debug("site_law_report exit passed=%s", report.passed)
    return report


@dataclass(frozen=True)
class UndecidedPair:
    """A pair not apart at the stage but apart in the site: neither disjunct of ``x = y ∨ x # y`` is forced."""

    stage: str
    left: Word
    right: Word
    status_at_stage: PairStatus
    splitting_observers: tuple[str, ...]


def undecided_pairs(site: Stage, stage: Stage, presentations: Sequence[Word]) -> tuple[UndecidedPair, ...]:
    """Witnesses of ``THM_OS_009`` on a finite family: retractable equalities at ``stage``."""
    validate_site(site)
    if not refines(stage, site):
        logger.error("undecided_pairs stage rejected")
        raise ObserverSiteError("stage-not-in-site")
    words = validate_presentations(presentations)
    rows: list[UndecidedPair] = []
    for index, left in enumerate(words):
        for right in words[index + 1 :]:
            if apart(stage, left, right) or not apart(site, left, right):
                continue
            splitting = tuple(observer.name for observer in site if distinguishes(observer, left, right))
            rows.append(UndecidedPair(stage_name(stage), left, right, pair_status(stage, left, right), splitting))
    return tuple(rows)


def cotransitivity_failures(stage: Stage, presentations: Sequence[Word]) -> tuple[tuple[Word, Word, Word], ...]:
    """Triples with ``x # z`` but neither ``x # y`` nor ``y # z`` (``THM_OS_006/007``)."""
    words = validate_presentations(presentations)
    rows = []
    for x in words:
        for z in words:
            if not apart(stage, x, z):
                continue
            for y in words:
                if not apart(stage, x, y) and not apart(stage, y, z):
                    rows.append((x, y, z))
    return tuple(rows)


@dataclass(frozen=True)
class EchoClasses:
    """The presheaf fibre at one stage: echo classes of readable presentations (``THM_OS_017``)."""

    stage: str
    classes: tuple[tuple[Word, ...], ...]
    unreadable: tuple[Word, ...]


def echo_classes(stage: Stage, presentations: Sequence[Word]) -> EchoClasses:
    """Partition the readable presentations by echo; the others are silent at this stage."""
    words = validate_presentations(presentations)
    groups: dict[tuple[object, ...], list[Word]] = {}
    unreadable: list[Word] = []
    for word in words:
        if not readable(stage, word):
            unreadable.append(word)
            continue
        groups.setdefault(tuple(observer.read(word) for observer in stage), []).append(word)
    return EchoClasses(stage_name(stage), tuple(tuple(group) for group in groups.values()), tuple(unreadable))


def restriction(coarse: Stage, fine: Stage, presentations: Sequence[Word]) -> tuple[int, ...]:
    """Map every fine echo class to the coarse class containing it (``THM_OS_002`` makes it total)."""
    if not refines(coarse, fine):
        logger.error("restriction stages rejected")
        raise ObserverSiteError("restriction-not-refinement")
    coarse_classes = echo_classes(coarse, presentations).classes
    position = {word: index for index, group in enumerate(coarse_classes) for word in group}
    rows: list[int] = []
    for group in echo_classes(fine, presentations).classes:
        targets = {position[word] for word in group}
        if len(targets) != 1:
            logger.error("restriction class split")
            raise ObserverSiteError("restriction-not-well-defined")
        rows.append(targets.pop())
    return tuple(rows)


def power_at(stage: Stage, word: Word, alphabet: Sequence[str]) -> tuple[Word, int] | None:
    """A literal power ``u^k`` (``k ≥ 2``, ``u`` nonempty) echoed with ``word`` at the stage, if any.

    The bounded search assumes every admitted observer respects length (its echo
    implies equal length), which the standard observers declare; other observers
    are refused rather than searched unsoundly.
    """
    if any(not observer.length_respecting for observer in stage):
        logger.error("power_at observer refused")
        raise ObserverSiteError("stage-observer-not-length-respecting")
    if not word or len(word) > MAX_POWER_LENGTH:
        logger.error("power_at word rejected")
        raise ObserverSiteError("power-word-length")
    letters = tuple(alphabet)
    for root_length in range(1, len(word)):
        exponent = 2
        while exponent * root_length < len(word):
            exponent += 1
        if exponent * root_length != len(word):
            continue
        for root in product(letters, repeat=root_length):
            if echo(stage, word, root * exponent):
                return root, exponent
    return None


def primitive_at(stage: Stage, word: Word, alphabet: Sequence[str]) -> bool:
    """``word`` is primitive at the stage: nonempty and not echoed to a proper power (``THM_OS_011``–``016``)."""
    return bool(word) and power_at(stage, word, alphabet) is None


def prime_table(site: Stage, words: Sequence[Word], alphabet: Sequence[str]) -> dict[str, tuple[Word, ...]]:
    """Primitive words at every stage of the lattice, keyed by stage name."""
    return {
        stage_name(stage): tuple(word for word in words if primitive_at(stage, word, alphabet))
        for stage in substages(site)
    }


def prime_monotonicity_violations(site: Stage, words: Sequence[Word], alphabet: Sequence[str]) -> int:
    """Count stage pairs and words breaking ``THM_OS_011`` (must be zero)."""
    table = prime_table(site, words, alphabet)
    stages = substages(site)
    count = 0
    for coarse in stages:
        for fine in stages:
            if refines(coarse, fine):
                count += sum(1 for word in table[stage_name(coarse)] if word not in table[stage_name(fine)])
    return count


def _cycle_value(word: Word) -> Word:
    return min(word[index:] + word[:index] for index in range(len(word))) if word else word


LENGTH = Observer("length", len, True)
BAG = Observer("bag", lambda word: tuple(sorted(word)), True)
CYCLE = Observer("cycle", _cycle_value, True)
WORD = Observer("word", lambda word: word, True)


def bounded_reader(limit: int) -> Observer:
    """The word observer with a resource bound: silent on words longer than ``limit``."""
    if type(limit) is not int or limit < 0:
        raise ObserverSiteError("reader-limit")
    return Observer(f"reader<={limit}", lambda word: word if len(word) <= limit else SILENT, True)


def standard_site() -> Stage:
    """The docs/06 observers in refinement order: length ⊂ bag ⊂ cycle ⊂ word."""
    return (LENGTH, BAG, CYCLE, WORD)


def words_up_to(alphabet: Sequence[str], max_length: int, include_empty: bool = True) -> tuple[Word, ...]:
    """All words over the alphabet up to a length, shortest first."""
    if type(max_length) is not int or not 0 <= max_length <= MAX_POWER_LENGTH:
        raise ObserverSiteError("words-length")
    rows: list[Word] = [()] if include_empty else []
    for length in range(1, max_length + 1):
        rows.extend(product(tuple(alphabet), repeat=length))
    return tuple(rows)


def observer_site_checklist() -> tuple[tuple[str, str], ...]:
    """Lean cards of ``VeyraObserverSite.lean`` and their executable replay here."""
    return (
        ("THM_OS_001_apart_persists", "site_law_report.persistence_violations == 0"),
        ("THM_OS_002_echo_retracts", "site_law_report.retraction_violations == 0; restriction total"),
        ("THM_OS_003_status_trichotomy", "pair_status; site_law_report.trichotomy_violations == 0"),
        ("THM_OS_004_total_no_silence", "site_law_report.silent_pairs == 0 on the standard site"),
        ("THM_OS_005_apart_irrefl_symm", "apart(stage, x, x) is False; apart symmetric"),
        ("THM_OS_006_cotransitive_of_total", "cotransitivity_failures == () on the standard site"),
        ("THM_OS_007_silence_breaks_cotransitivity", "cotransitivity_failures with bounded_reader(1)"),
        ("THM_OS_008_intEq_stable", "internal_equal implies not apart at every substage"),
        ("THM_OS_009_excluded_middle_fails", "undecided_pairs: ab/ba at {length} split by word"),
        ("THM_OS_010_complete_stage_decides", "forces_decided(site, site, x, y) always True"),
        ("THM_OS_011_prime_monotone", "prime_monotonicity_violations == 0"),
        ("THM_OS_012_prime_depends_on_stage", "aba composite at {length}, primitive at {word}"),
        ("THM_OS_013_apart_sieve_upclosed", "apart stages of a pair are up-closed"),
        ("THM_OS_014_echo_not_kripke", "echo stages of ab/ba are not up-closed"),
        ("THM_OS_015_word_stage_prime_iff_primitive", "primitive_at({word}) == literal primitivity"),
        ("THM_OS_016_length_stage_prime_iff_unit", "primitive_at({length}) only for one-letter words"),
        ("THM_OS_017_echo_is_per", "echo_classes partition the readable presentations"),
        ("THM_OS_018_silence_breaks_intEq_trans", "internal_equal not transitive with bounded_reader(1)"),
        ("THM_OS_019_intEq_equivalence_of_total", "internal_equal is an equivalence on the standard site"),
    )
