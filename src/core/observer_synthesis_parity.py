"""Exact parity corpus for observer synthesis and scoped strength."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
from pathlib import Path
import logging
import shutil
import subprocess

from .paths import repository_path

from .observer_synthesis import fit_observer, score_observer, synthesize_observer
from .observer_synthesis_types import (
    NamedBaseline, ObserverCase, ObserverGrammar, ObserverPrimitive,
    ObserverSynthesisResult, ObserverTerm, SynthesisConfig,
)

logger = logging.getLogger(__name__)
BitTable = tuple[str, ...]
BASELINE_CLASS = "observers factoring through all proper-subset marginals"
BOUNDARY = "strictly stronger only in the declared observer class; global parity is classical, not global Veyra superiority"
EXPECTED_WINNER = "histogram(xor-rows(input))"


@dataclass(frozen=True)
class ObserverClassSpec:
    """A coordinate-generated observer class used by the scoped R6 claim."""
    name: str
    coordinates: frozenset[str]


@dataclass(frozen=True)
class StrictObserverClassCertificate:
    theorem_ids: tuple[str, ...]
    baseline_class: str
    extended_class: str
    class_inclusion: bool
    winner_text: str
    winner_in_extended: bool
    winner_outside_baseline: bool
    baseline_equal_train: bool
    baseline_equal_holdout: bool
    all_named_baselines_blind: bool
    winner_separates_train: bool
    winner_separates_holdout: bool
    lean_status: str
    strictly_stronger: bool
    boundary: str


def parity_table(width: int, parity: int | None = None, duplicate: bool = False) -> BitTable:
    """Return a full cube or one optionally duplicated parity coset."""
    logger.debug("parity_table entry width=%d parity=%r duplicate=%s", width, parity, duplicate)
    if width < 2 or parity not in (None, 0, 1):
        logger.error("parity_table invalid width=%d parity=%r", width, parity)
        raise ValueError("invalid-parity-table")
    words = tuple(format(value, f"0{width}b") for value in range(1 << width))
    selected = words if parity is None else tuple(word for word in words if (_row_xor(word) == parity))
    result = tuple(word for word in selected for _ in range(2 if duplicate else 1))
    logger.debug("parity_table exit rows=%d", len(result)); return result


def proper_marginal_signature(table: BitTable) -> tuple[object, ...]:
    """Return all nonempty proper-subset marginal counts."""
    logger.debug("proper_marginal_signature entry rows=%d", len(table))
    width = _table_width(table); rows: list[object] = []
    for size in range(1, width):
        for axes in combinations(range(width), size):
            assignments = tuple(sorted((bits, sum(1 for word in table if "".join(word[index] for index in axes) == bits)) for bits in _bit_words(size)))
            rows.append((axes, assignments))
    result = tuple(rows)
    logger.debug("proper_marginal_signature exit cells=%d", len(result)); return result


def xor_rows(table: BitTable) -> tuple[int, ...]:
    """Return the global XOR bit of every row."""
    logger.debug("xor_rows entry rows=%d", len(table))
    _table_width(table); result = tuple(_row_xor(word) for word in table)
    logger.debug("xor_rows exit rows=%d", len(result)); return result


def histogram(values: tuple[int, ...]) -> tuple[tuple[int, int], ...]:
    """Return a deterministic finite histogram."""
    logger.debug("histogram entry values=%d", len(values))
    if not values or any(not isinstance(value, int) for value in values):
        logger.error("histogram invalid values"); raise ValueError("invalid-sequence")
    result = tuple((value, sum(item == value for item in values)) for value in sorted(set(values)))
    logger.debug("histogram exit bins=%d", len(result)); return result


def parity_observer_grammar() -> ObserverGrammar:
    """Return the locked typed grammar used by the R5 experiment."""
    logger.debug("parity_observer_grammar entry")
    primitives = (
        ObserverPrimitive("row-count", "bit-table", "scalar", 1, lambda table: sum(1 for _ in table), "row-count-v1"),
        ObserverPrimitive("proper-marginals", "bit-table", "signature", 1, proper_marginal_signature, "proper-marginals-v1"),
        ObserverPrimitive("xor-rows", "bit-table", "sequence", 1, xor_rows, "xor-rows-v1"),
        ObserverPrimitive("histogram", "sequence", "signature", 1, histogram, "histogram-v1"),
    )
    result = ObserverGrammar("parity-r5-v1", "bit-table", ("signature",), primitives, 2, 3)
    logger.debug("parity_observer_grammar exit primitives=%d", len(primitives)); return result


def parity_baselines() -> tuple[NamedBaseline, ...]:
    """Return named finite baselines fixed before fitting."""
    logger.debug("parity_baselines entry")
    source = ObserverTerm("input", "bit-table")
    result = (
        NamedBaseline("row-count", "cardinality", ObserverTerm("apply", "scalar", "row-count", (source,)), "row count only"),
        NamedBaseline("proper-marginals", BASELINE_CLASS, ObserverTerm("apply", "signature", "proper-marginals", (source,)), "all nonempty proper subsets"),
    )
    logger.debug("parity_baselines exit count=%d", len(result)); return result


def parity_train_cases() -> tuple[ObserverCase, ...]:
    """Return the locked width-four training split."""
    logger.debug("parity_train_cases entry")
    result = (ObserverCase("parity-train-n4", "train-even-4", parity_table(4, 0, True), parity_table(4), "separate"),)
    logger.debug("parity_train_cases exit count=%d", len(result)); return result


def parity_holdout_cases() -> tuple[ObserverCase, ...]:
    """Return untouched width-five odd-coset holdout."""
    logger.debug("parity_holdout_cases entry")
    structured = tuple(word[::-1] for word in parity_table(5, 1, True))
    control = tuple(word[::-1] for word in parity_table(5))
    result = (ObserverCase("parity-holdout-n5", "holdout-odd-5", structured, control, "separate"),)
    logger.debug("parity_holdout_cases exit count=%d", len(result)); return result


@lru_cache(maxsize=1)
def parity_observer_synthesis() -> ObserverSynthesisResult:
    """Synthesize on n=4 and validate the unchanged winner on n=5."""
    logger.debug("parity_observer_synthesis entry")
    result = synthesize_observer(parity_observer_grammar(), parity_train_cases(), parity_holdout_cases(), parity_baselines(), SynthesisConfig())
    logger.debug("parity_observer_synthesis exit status=%s", result.status); return result


def observer_term_text(term: ObserverTerm) -> str:
    """Return compact human-readable observer syntax."""
    logger.debug("observer_term_text entry op=%s", term.op)
    if term.op == "input": result = "input"
    elif term.op == "apply": result = f"{term.primitive}({observer_term_text(term.children[0])})"
    elif term.op == "pair": result = f"pair({observer_term_text(term.children[0])},{observer_term_text(term.children[1])})"
    else: result = "invalid"
    logger.debug("observer_term_text exit result=%s", result); return result


def observer_class_includes(superclass: ObserverClassSpec, subclass: ObserverClassSpec) -> bool:
    """Derive proper class inclusion from coordinate generators."""
    logger.debug("observer_class_includes entry super=%s sub=%s", superclass.name, subclass.name)
    result = subclass.coordinates < superclass.coordinates
    logger.debug("observer_class_includes exit result=%s", result); return result


def observer_class_membership(term: ObserverTerm, observer_class: ObserverClassSpec) -> bool:
    """Check membership for the locked, explicitly represented coordinate terms."""
    logger.debug("observer_class_membership entry class=%s", observer_class.name)
    coordinate = {
        "proper-marginals(input)": "proper-marginals",
        EXPECTED_WINNER: "global-parity",
    }.get(observer_term_text(term))
    result = coordinate is not None and coordinate in observer_class.coordinates
    logger.debug("observer_class_membership exit coordinate=%s result=%s", coordinate, result); return result


def observer_classes() -> tuple[ObserverClassSpec, ObserverClassSpec]:
    """Return the executable baseline and its declared one-coordinate extension."""
    logger.debug("observer_classes entry")
    baseline = ObserverClassSpec(BASELINE_CLASS, frozenset({"proper-marginals"}))
    extended = ObserverClassSpec(f"{BASELINE_CLASS} plus global parity", frozenset({"proper-marginals", "global-parity"}))
    logger.debug("observer_classes exit baseline=%s extended=%s", baseline.name, extended.name)
    return baseline, extended


@lru_cache(maxsize=1)
def strict_observer_class_certificate() -> StrictObserverClassCertificate:
    """Certify one scoped strict extension of a declared observer class."""
    logger.debug("strict_observer_class_certificate entry")
    train, holdout = parity_train_cases()[0], parity_holdout_cases()[0]
    synthesis = parity_observer_synthesis(); fitted = synthesis.fitted; report = synthesis.holdout
    baseline_class, extended_class = observer_classes()
    baseline_train = proper_marginal_signature(train.left) == proper_marginal_signature(train.right)
    baseline_holdout = proper_marginal_signature(holdout.left) == proper_marginal_signature(holdout.right)
    grammar = parity_observer_grammar(); config = SynthesisConfig()
    named_blind = all(score_observer(item.term, (train, holdout), grammar, config).fit == 0.0 for item in parity_baselines())
    train_hit = fitted.winner is not None and fitted.winner.fit == 1.0
    holdout_hit = report.winner_evaluation is not None and report.winner_evaluation.fit == 1.0
    winner_text = observer_term_text(fitted.winner.term) if fitted.winner else ""
    inclusion = observer_class_includes(extended_class, baseline_class)
    winner_in = fitted.winner is not None and observer_class_membership(fitted.winner.term, extended_class)
    winner_out = fitted.winner is not None and not observer_class_membership(fitted.winner.term, baseline_class)
    lean = _check_lean(repository_path("proofs/lean/VeyraObserverSynthesis.lean"))
    fields = (inclusion, winner_text == EXPECTED_WINNER, winner_in, winner_out, baseline_train,
              baseline_holdout, named_blind, train_hit, holdout_hit, lean == "checked", synthesis.status == "validated")
    result = StrictObserverClassCertificate(
        ("THM-R6-001", "THM-R6-002"), baseline_class.name, extended_class.name,
        inclusion, winner_text, winner_in, winner_out, baseline_train, baseline_holdout,
        named_blind, train_hit, holdout_hit, lean, all(fields), BOUNDARY,
    )
    logger.debug("strict_observer_class_certificate exit stronger=%s", result.strictly_stronger); return result


def observer_synthesis_summary() -> dict[str, object]:
    """Return concise R5/R6 readiness evidence."""
    logger.debug("observer_synthesis_summary entry")
    result = parity_observer_synthesis(); cert = strict_observer_class_certificate()
    winner = result.fitted.winner
    summary: dict[str, object] = {"status": result.status, "winner": observer_term_text(winner.term) if winner else "", "train_fit": winner.fit if winner else 0.0, "holdout_fit": result.holdout.winner_evaluation.fit if result.holdout.winner_evaluation else 0.0, "strictly_stronger": cert.strictly_stronger, "lean": cert.lean_status}
    logger.debug("observer_synthesis_summary exit result=%r", summary); return summary


def _row_xor(word: str) -> int:
    logger.debug("_row_xor entry width=%d", len(word))
    if not word or set(word) - {"0", "1"}: logger.error("_row_xor invalid"); raise ValueError("invalid-bit-row")
    result = sum(char == "1" for char in word) & 1
    logger.debug("_row_xor exit result=%d", result); return result


def _table_width(table: BitTable) -> int:
    logger.debug("_table_width entry rows=%d", len(table))
    if not table or not table[0] or any(len(word) != len(table[0]) or set(word) - {"0", "1"} for word in table):
        logger.error("_table_width invalid"); raise ValueError("invalid-bit-table")
    result = len(table[0]); logger.debug("_table_width exit result=%d", result); return result


def _bit_words(width: int) -> tuple[str, ...]:
    logger.debug("_bit_words entry width=%d", width)
    result = tuple(format(value, f"0{width}b") for value in range(1 << width))
    logger.debug("_bit_words exit count=%d", len(result)); return result


def _check_lean(path: Path) -> str:
    logger.debug("_check_lean entry path=%s", path)
    symbols = ("THM_R6_001", "THM_R6_002")
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.error("_check_lean blocked read_error=%s", exc); return "blocked"
    missing = tuple(symbol for symbol in symbols if f"theorem {symbol}" not in source)
    if missing:
        logger.error("_check_lean blocked missing=%r", missing); return "blocked"
    elan = shutil.which("elan"); lean = shutil.which("lean")
    command = [elan, "run", "leanprover/lean4:v4.30.0-rc2", "lean"] if elan else ([lean] if lean else [])
    if not command: logger.error("_check_lean blocked no lean"); return "blocked"
    proc = subprocess.run(command + [str(path)], capture_output=True, text=True, check=False)
    result = "checked" if proc.returncode == 0 else "blocked"
    if result == "blocked": logger.error("_check_lean blocked stderr=%s", proc.stderr[-240:])
    logger.debug("_check_lean exit status=%s", result); return result
