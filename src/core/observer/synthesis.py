"""Bounded observer synthesis, protocol identities, and parity evidence."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from functools import lru_cache, partial
from hashlib import sha256
from itertools import combinations
import json
import logging
import operator
from pathlib import Path
import shutil
import subprocess
from types import BuiltinFunctionType, CodeType
from typing import Callable

from ..paths import LEAN_DIR

logger = logging.getLogger(__name__)


# Protocol data

Canonical = str | int | float | bool | None | tuple["Canonical", ...]

@dataclass(frozen=True)
class ObserverPrimitive:
    name: str
    input_kind: str
    output_kind: str
    cost: int
    evaluator: Callable[[object], object]
    semantic_id: str = ""

@dataclass(frozen=True)
class ObserverTerm:
    op: str
    output_kind: str
    primitive: str = ""
    children: tuple["ObserverTerm", ...] = ()

@dataclass(frozen=True)
class ObserverGrammar:
    grammar_id: str
    input_kind: str
    accepted_output_kinds: tuple[str, ...]
    primitives: tuple[ObserverPrimitive, ...]
    max_depth: int
    max_cost: int

@dataclass(frozen=True)
class ObserverResponse:
    status: str
    value: Canonical = None
    obstruction: str = ""
    trace: tuple[str, ...] = ()

@dataclass(frozen=True)
class ObserverCase:
    case_id: str
    group_id: str
    left: object
    right: object
    expected: str
    expected_obstruction: str = ""
    payload_key: str = ""

@dataclass(frozen=True)
class SynthesisConfig:
    min_train_fit: float = 1.0
    min_holdout_fit: float = 1.0
    complexity_penalty: float = 0.01
    determinism_checks: int = 2

@dataclass(frozen=True)
class ObserverCaseEvidence:
    case_id: str
    passed: bool
    left_status: str
    right_status: str
    left_value: Canonical
    right_value: Canonical
    reason: str

@dataclass(frozen=True)
class CandidateEvaluation:
    term: ObserverTerm
    fingerprint: str
    passed: int
    total: int
    fit: float
    obstruction_rate: float
    complexity: int
    objective: float
    evidence: tuple[ObserverCaseEvidence, ...]

@dataclass(frozen=True)
class NamedBaseline:
    name: str
    observer_class: str
    term: ObserverTerm
    boundary: str

@dataclass(frozen=True)
class SynthesisObstruction:
    reason: str
    detail: str

@dataclass(frozen=True)
class FittedObserver:
    grammar_id: str
    protocol_digest: str
    evaluation_digest: str
    runtime_evaluator_ids: tuple[int, ...]
    train_payload_digests: tuple[str, ...]
    winner: CandidateEvaluation | None
    alternatives: tuple[CandidateEvaluation, ...]
    status: str
    train_case_ids: tuple[str, ...]
    train_group_ids: tuple[str, ...]
    obstructions: tuple[SynthesisObstruction, ...] = ()

@dataclass(frozen=True)
class HoldoutReport:
    fit_digest: str
    holdout_digest: str
    winner_evaluation: CandidateEvaluation | None
    baseline_evaluations: tuple[CandidateEvaluation, ...]
    status: str
    witnesses: tuple[ObserverCaseEvidence, ...]
    obstructions: tuple[SynthesisObstruction, ...] = ()

@dataclass(frozen=True)
class ObserverSynthesisResult:
    fitted: FittedObserver
    holdout: HoldoutReport
    status: str
    boundary: str


# Identity and leakage guards

logger = logging.getLogger(__name__)

_REDUCIBLE_CALLABLES = (type(operator.itemgetter(0)), type(operator.attrgetter("x")), type(operator.methodcaller("x")))

def callable_identity(function: object, semantic_id: str = "") -> str:
    """Bind a primitive name to declared identity and executable implementation."""
    logger.debug("callable_identity entry type=%s semantic_id=%s", type(function).__name__, semantic_id)
    if not semantic_id:
        logger.error("callable_identity unbound missing semantic id")
        raise ValueError("unbound-semantics:missing-semantic-id")
    if isinstance(function, partial):
        body = ("partial", callable_identity(function.func, semantic_id), _freeze(function.args), _freeze(function.keywords))
        result = digest_value((semantic_id, body)); logger.debug("callable_identity exit partial=%s", result[:12]); return result
    if isinstance(function, _REDUCIBLE_CALLABLES):
        body = (type(function).__module__, type(function).__qualname__, _freeze(function.__reduce__()[1]))
        result = digest_value((semantic_id, body)); logger.debug("callable_identity exit reducible=%s", result[:12]); return result
    code = getattr(function, "__code__", None)
    if code is None and not isinstance(function, BuiltinFunctionType):
        logger.error("callable_identity unbound callable type=%s", type(function).__name__)
        raise ValueError("unbound-semantics:callable")
    closure = getattr(function, "__closure__", None) or ()
    body = (
        semantic_id,
        getattr(function, "__module__", type(function).__module__),
        getattr(function, "__qualname__", type(function).__qualname__),
        _freeze(code),
        _freeze(getattr(function, "__defaults__", None)),
        _freeze(getattr(function, "__kwdefaults__", None)),
        tuple(_freeze(cell.cell_contents) for cell in closure),
        _freeze(getattr(function, "__dict__", None)),
        _dependency_shape(function),
    )
    result = digest_value(body)
    logger.debug("callable_identity exit digest=%s", result[:12])
    return result

def evaluation_digest(
    grammar: ObserverGrammar,
    baselines: tuple[NamedBaseline, ...],
    config: SynthesisConfig,
) -> str:
    """Hash all semantics allowed to affect fit or holdout evaluation."""
    logger.debug("evaluation_digest entry grammar=%s baselines=%d", grammar.grammar_id, len(baselines))
    primitives = tuple(
        (item.name, item.input_kind, item.output_kind, item.cost,
         callable_identity(item.evaluator, item.semantic_id))
        for item in grammar.primitives
    )
    baseline_rows = tuple(
        (item.name, item.observer_class, _term_shape(item.term), item.boundary)
        for item in baselines
    )
    shape = (
        grammar.grammar_id, grammar.input_kind, grammar.accepted_output_kinds,
        primitives, grammar.max_depth, grammar.max_cost, baseline_rows,
        _freeze(config),
    )
    result = digest_value(shape)
    logger.debug("evaluation_digest exit digest=%s", result[:12])
    return result

def case_payload_digest(case: ObserverCase) -> str:
    """Hash case content independently of case/group IDs and pair order."""
    logger.debug("case_payload_digest entry id=%s", case.case_id)
    if case.payload_key:
        result = digest_value(("trusted-payload-key", case.payload_key))
        logger.debug("case_payload_digest exit keyed=%s", result[:12]); return result
    pair = tuple(sorted((_freeze(case.left), _freeze(case.right)), key=repr))
    result = digest_value(pair)
    logger.debug("case_payload_digest exit digest=%s", result[:12])
    return result

def case_payload_digests(cases: tuple[ObserverCase, ...]) -> tuple[str, ...]:
    """Return stable payload identities for a declared split."""
    logger.debug("case_payload_digests entry count=%d", len(cases))
    result = tuple(case_payload_digest(case) for case in cases)
    logger.debug("case_payload_digests exit count=%d", len(result))
    return result

def digest_value(value: object) -> str:
    """Hash a deterministic frozen representation."""
    logger.debug("digest_value entry type=%s", type(value).__name__)
    result = sha256(repr(_freeze(value)).encode()).hexdigest()
    logger.debug("digest_value exit digest=%s", result[:12])
    return result

def _term_shape(term: ObserverTerm) -> tuple[object, ...]:
    logger.debug("_term_shape entry op=%s", term.op)
    result = (term.op, term.output_kind, term.primitive, tuple(_term_shape(child) for child in term.children))
    logger.debug("_term_shape exit op=%s", term.op)
    return result

def _dependency_shape(function: object) -> tuple[object, ...]:
    logger.debug("_dependency_shape entry type=%s", type(function).__name__)
    code = getattr(function, "__code__", None); namespace = getattr(function, "__globals__", {})
    rows = []
    for name in (() if code is None else code.co_names):
        value = namespace.get(name)
        if callable(value): rows.append((name, _callable_core(value)))
        elif value is None or isinstance(value, (str, int, float, bool, bytes, tuple, frozenset)):
            rows.append((name, _freeze(value)))
    result = tuple(rows)
    logger.debug("_dependency_shape exit count=%d", len(result)); return result

def _callable_core(function: object) -> tuple[object, ...]:
    logger.debug("_callable_core entry type=%s", type(function).__name__)
    code = getattr(function, "__code__", None)
    if code is None and not isinstance(function, BuiltinFunctionType):
        result = (type(function).__module__, type(function).__qualname__)
    else:
        result = (getattr(function, "__module__", ""), getattr(function, "__qualname__", ""),
                  _freeze(code), _freeze(getattr(function, "__defaults__", None)),
                  _freeze(getattr(function, "__kwdefaults__", None)))
    logger.debug("_callable_core exit type=%s", type(function).__name__); return result

def _freeze(value: object) -> object:
    logger.debug("_freeze entry type=%s", type(value).__name__)
    if value is None:
        result: object = ("none",)
    elif isinstance(value, bool):
        result = ("bool", value)
    elif isinstance(value, int):
        result = ("int", value)
    elif isinstance(value, float):
        result = ("float", value.hex())
    elif isinstance(value, complex):
        result = ("complex", value.real.hex(), value.imag.hex())
    elif isinstance(value, str):
        result = ("str", value)
    elif isinstance(value, bytes):
        result = ("bytes", value.hex())
    elif value is Ellipsis:
        result = ("ellipsis",)
    elif isinstance(value, CodeType):
        result = ("code", value.co_code.hex(), tuple(_freeze(item) for item in value.co_consts),
                  value.co_names, value.co_varnames, value.co_argcount,
                  value.co_posonlyargcount, value.co_kwonlyargcount, value.co_flags,
                  value.co_freevars, value.co_cellvars)
    elif isinstance(value, tuple):
        result = ("tuple", tuple(_freeze(item) for item in value))
    elif isinstance(value, list):
        result = ("list", tuple(_freeze(item) for item in value))
    elif isinstance(value, dict):
        rows = tuple((_freeze(key), _freeze(item)) for key, item in value.items())
        result = ("dict", tuple(sorted(rows, key=repr)))
    elif isinstance(value, set):
        result = ("set", tuple(sorted((_freeze(item) for item in value), key=repr)))
    elif isinstance(value, frozenset):
        result = ("frozenset", tuple(sorted((_freeze(item) for item in value), key=repr)))
    elif is_dataclass(value) and not isinstance(value, type):
        result = (type(value).__module__, type(value).__qualname__,
                  tuple((item.name, _freeze(getattr(value, item.name))) for item in fields(value)))
    elif callable(value):
        logger.error("_freeze unbound callable type=%s", type(value).__name__)
        raise ValueError("unbound-semantics:callable-value")
    else:
        logger.error("_freeze unbound value type=%s", type(value).__name__)
        raise ValueError("unbound-semantics:payload")
    logger.debug("_freeze exit type=%s", type(value).__name__)
    return result


# Synthesis engine

logger = logging.getLogger(__name__)

def canonical_term(term: ObserverTerm) -> str:
    """Return deterministic JSON for an observer AST."""
    logger.debug("canonical_term entry op=%s", term.op)
    node = {"children": [json.loads(canonical_term(child)) for child in term.children],
            "kind": term.output_kind, "op": term.op, "primitive": term.primitive}
    result = json.dumps(node, sort_keys=True, separators=(",", ":"))
    logger.debug("canonical_term exit bytes=%d", len(result))
    return result

def observer_fingerprint(term: ObserverTerm) -> str:
    """Hash the canonical observer AST."""
    logger.debug("observer_fingerprint entry op=%s", term.op)
    result = sha256(canonical_term(term).encode()).hexdigest()
    logger.debug("observer_fingerprint exit digest=%s", result[:12])
    return result

def observer_term_cost(term: ObserverTerm, registry: dict[str, ObserverPrimitive]) -> int:
    """Return audited grammar cost, rejecting invalid terms."""
    logger.debug("observer_term_cost entry op=%s", term.op)
    if term.op == "input":
        result = 0
    elif term.op == "apply" and len(term.children) == 1 and term.primitive in registry:
        primitive = registry[term.primitive]
        if primitive.cost <= 0 or term.children[0].output_kind != primitive.input_kind or term.output_kind != primitive.output_kind:
            raise ValueError("invalid-composition")
        result = primitive.cost + observer_term_cost(term.children[0], registry)
    elif term.op == "pair" and len(term.children) == 2 and term.output_kind == "pair":
        result = 1 + sum(observer_term_cost(child, registry) for child in term.children)
    else:
        raise ValueError("invalid-composition")
    logger.debug("observer_term_cost exit result=%d", result)
    return result

def enumerate_observer_terms(grammar: ObserverGrammar) -> tuple[ObserverTerm, ...]:
    """Enumerate the finite typed grammar in deterministic cost order."""
    logger.debug("enumerate_observer_terms entry grammar=%s", grammar.grammar_id)
    registry = _registry(grammar)
    seed = ObserverTerm("input", grammar.input_kind)
    known = {canonical_term(seed): seed}
    changed = True
    while changed:
        changed = False
        current = tuple(known.values())
        proposals: list[ObserverTerm] = []
        for child in current:
            proposals.extend(ObserverTerm("apply", p.output_kind, p.name, (child,)) for p in registry.values() if p.input_kind == child.output_kind)
        for left in current:
            for right in current:
                if canonical_term(left) <= canonical_term(right):
                    proposals.append(ObserverTerm("pair", "pair", children=(left, right)))
        for term in proposals:
            try:
                cost = observer_term_cost(term, registry)
            except ValueError:
                continue
            if cost > grammar.max_cost or _term_depth(term) > grammar.max_depth:
                continue
            key = canonical_term(term)
            if key not in known:
                known[key] = term; changed = True
    result = tuple(sorted((term for term in known.values() if term.output_kind in grammar.accepted_output_kinds), key=lambda t: (observer_term_cost(t, registry), _term_depth(t), canonical_term(t))))
    logger.debug("enumerate_observer_terms exit count=%d", len(result))
    return result

def evaluate_observer(term: ObserverTerm, value: object, registry: dict[str, ObserverPrimitive]) -> ObserverResponse:
    """Evaluate one observer without treating failure as separation."""
    logger.debug("evaluate_observer entry fingerprint=%s", observer_fingerprint(term)[:12])
    try:
        raw, trace = _evaluate(term, value, registry)
        canonical = _canonical_value(raw)
        result = ObserverResponse("ready", canonical, trace=trace)
    except Exception as exc:  # Evaluators are extension points; all failures become data.
        logger.error("evaluate_observer blocked error=%s", type(exc).__name__)
        result = ObserverResponse("blocked", obstruction=f"evaluation-error:{type(exc).__name__}")
    logger.debug("evaluate_observer exit status=%s", result.status)
    return result

def score_observer(term: ObserverTerm, cases: tuple[ObserverCase, ...], grammar: ObserverGrammar, config: SynthesisConfig) -> CandidateEvaluation:
    """Score a candidate on one declared split."""
    logger.debug("score_observer entry cases=%d", len(cases))
    registry = _registry(grammar); evidence = tuple(_case_evidence(term, case, registry, config) for case in cases)
    passed = sum(row.passed for row in evidence); total = len(evidence); fit = passed / total if total else 0.0
    obstructed = sum(row.left_status == "blocked" or row.right_status == "blocked" for row in evidence)
    complexity = observer_term_cost(term, registry)
    result = CandidateEvaluation(term, observer_fingerprint(term), passed, total, fit, obstructed / total if total else 0.0, complexity, fit - config.complexity_penalty * complexity / grammar.max_cost, evidence)
    logger.debug("score_observer exit fit=%.3f cost=%d", fit, complexity)
    return result

def fit_observer(grammar: ObserverGrammar, train_cases: tuple[ObserverCase, ...], baselines: tuple[NamedBaseline, ...] = (), config: SynthesisConfig = SynthesisConfig()) -> FittedObserver:
    """Fit on train only; the API deliberately cannot inspect holdout."""
    logger.debug("fit_observer entry grammar=%s cases=%d", grammar.grammar_id, len(train_cases))
    runtime_ids = tuple(id(item.evaluator) for item in grammar.primitives)
    try:
        evaluation = evaluation_digest(grammar, baselines, config)
        payloads = case_payload_digests(train_cases)
        protocol = digest_value((evaluation, _split_digest(train_cases, payloads)))
        duplicate = _duplicate_split(train_cases, payloads)
    except (TypeError, ValueError) as exc:
        detail = str(exc) if "unbound-semantics" in str(exc) else f"unbound-semantics:{type(exc).__name__}"
        result = FittedObserver(grammar.grammar_id, digest_value((grammar.grammar_id, detail)), "", runtime_ids, (), None, (), "blocked", _case_ids(train_cases), _group_ids(train_cases), (SynthesisObstruction("unbound-semantics", detail),))
        logger.error("fit_observer blocked detail=%s", detail); return result
    if duplicate:
        result = FittedObserver(grammar.grammar_id, protocol, evaluation, runtime_ids, payloads, None, (), "blocked", _case_ids(train_cases), _group_ids(train_cases), (SynthesisObstruction("split-leakage", duplicate),))
        logger.error("fit_observer blocked detail=%s", duplicate); return result
    scores = tuple(score_observer(term, train_cases, grammar, config) for term in enumerate_observer_terms(grammar))
    eligible = tuple(row for row in scores if row.fit >= config.min_train_fit)
    ranked = tuple(sorted(eligible, key=lambda row: (-row.objective, -row.fit, row.obstruction_rate, row.complexity, row.fingerprint)))
    winner = ranked[0] if ranked else None
    status = "ready" if winner else "blocked"
    obs = () if winner else (SynthesisObstruction("not-found", "no observer within declared grammar/budget met train threshold"),)
    result = FittedObserver(grammar.grammar_id, protocol, evaluation, runtime_ids, payloads, winner, ranked[1:], status, _case_ids(train_cases), _group_ids(train_cases), obs)
    logger.debug("fit_observer exit status=%s eligible=%d", status, len(ranked)); return result

def validate_observer(fitted: FittedObserver, grammar: ObserverGrammar, holdout_cases: tuple[ObserverCase, ...], baselines: tuple[NamedBaseline, ...] = (), config: SynthesisConfig = SynthesisConfig()) -> HoldoutReport:
    """Validate the fixed train winner without holdout reranking."""
    logger.debug("validate_observer entry holdout=%d", len(holdout_cases))
    runtime_ids = tuple(id(item.evaluator) for item in grammar.primitives)
    try:
        evaluation = evaluation_digest(grammar, baselines, config)
        holdout_payloads = case_payload_digests(holdout_cases)
        holdout_digest = _split_digest(holdout_cases, holdout_payloads)
    except (TypeError, ValueError) as exc:
        detail = str(exc) if "unbound-semantics" in str(exc) else f"unbound-semantics:{type(exc).__name__}"
        result = HoldoutReport(fitted.protocol_digest, digest_value((_case_ids(holdout_cases), detail)), None, (), "blocked", (), (SynthesisObstruction("unbound-semantics", detail),))
        logger.error("validate_observer blocked detail=%s", detail); return result
    if fitted.grammar_id != grammar.grammar_id or fitted.evaluation_digest != evaluation or fitted.runtime_evaluator_ids != runtime_ids:
        detail = "fit/holdout grammar, primitive semantics, baseline, or config changed"
        result = HoldoutReport(fitted.protocol_digest, holdout_digest, None, (), "blocked", (), (SynthesisObstruction("protocol-mismatch", detail),))
        logger.error("validate_observer blocked detail=%s", detail); return result
    payload_overlap = set(fitted.train_payload_digests) & set(holdout_payloads)
    overlap = set(fitted.train_case_ids) & set(_case_ids(holdout_cases)) or set(fitted.train_group_ids) & set(_group_ids(holdout_cases)) or payload_overlap
    duplicate = _duplicate_split(holdout_cases, holdout_payloads)
    if overlap or duplicate or fitted.winner is None:
        detail = duplicate or (f"overlap={sorted(overlap)}" if overlap else "no fitted winner")
        obs = (SynthesisObstruction("split-leakage" if overlap or duplicate else "not-fitted", detail),)
        result = HoldoutReport(fitted.protocol_digest, holdout_digest, None, (), "blocked", (), obs)
        logger.error("validate_observer blocked detail=%s", detail); return result
    winner = score_observer(fitted.winner.term, holdout_cases, grammar, config)
    baseline_rows = tuple(score_observer(item.term, holdout_cases, grammar, config) for item in baselines)
    status = "validated" if winner.fit >= config.min_holdout_fit else "blocked"
    obs = () if status == "validated" else (SynthesisObstruction("holdout-failure", f"fit={winner.fit}"),)
    result = HoldoutReport(fitted.protocol_digest, holdout_digest, winner, baseline_rows, status, winner.evidence, obs)
    logger.debug("validate_observer exit status=%s fit=%.3f", status, winner.fit); return result

def synthesize_observer(grammar: ObserverGrammar, train_cases: tuple[ObserverCase, ...], holdout_cases: tuple[ObserverCase, ...], baselines: tuple[NamedBaseline, ...] = (), config: SynthesisConfig = SynthesisConfig()) -> ObserverSynthesisResult:
    """Fit then validate, preserving the pre-holdout winner."""
    logger.debug("synthesize_observer entry grammar=%s", grammar.grammar_id)
    fitted = fit_observer(grammar, train_cases, baselines, config)
    holdout = validate_observer(fitted, grammar, holdout_cases, baselines, config)
    status = "validated" if fitted.status == "ready" and holdout.status == "validated" else "blocked"
    boundary = "bounded declared grammar and locked train/holdout only; absence is not impossibility"
    result = ObserverSynthesisResult(fitted, holdout, status, boundary)
    logger.debug("synthesize_observer exit status=%s", status); return result

def _registry(grammar: ObserverGrammar) -> dict[str, ObserverPrimitive]:
    logger.debug("_registry entry primitives=%d", len(grammar.primitives))
    result = {item.name: item for item in grammar.primitives}
    if len(result) != len(grammar.primitives) or any(item.cost <= 0 or not item.semantic_id for item in grammar.primitives):
        logger.error("_registry invalid grammar=%s", grammar.grammar_id); raise ValueError("invalid-grammar")
    logger.debug("_registry exit count=%d", len(result)); return result

def _evaluate(term: ObserverTerm, value: object, registry: dict[str, ObserverPrimitive]) -> tuple[object, tuple[str, ...]]:
    logger.debug("_evaluate entry op=%s", term.op)
    if term.op == "input": result = (value, ("input",))
    elif term.op == "apply":
        child, trace = _evaluate(term.children[0], value, registry); primitive = registry[term.primitive]
        if term.children[0].output_kind != primitive.input_kind: raise ValueError("invalid-composition")
        result = (primitive.evaluator(child), trace + (primitive.name,))
    elif term.op == "pair":
        left, lt = _evaluate(term.children[0], value, registry); right, rt = _evaluate(term.children[1], value, registry)
        result = ((left, right), lt + rt + ("pair",))
    else: raise ValueError("invalid-composition")
    logger.debug("_evaluate exit op=%s", term.op); return result

def _case_evidence(term: ObserverTerm, case: ObserverCase, registry: dict[str, ObserverPrimitive], config: SynthesisConfig) -> ObserverCaseEvidence:
    logger.debug("_case_evidence entry id=%s", case.case_id)
    lefts = tuple(evaluate_observer(term, case.left, registry) for _ in range(max(2, config.determinism_checks)))
    rights = tuple(evaluate_observer(term, case.right, registry) for _ in range(max(2, config.determinism_checks)))
    if len(set(lefts)) != 1 or len(set(rights)) != 1:
        result = ObserverCaseEvidence(case.case_id, False, "blocked", "blocked", None, None, "nondeterministic-evaluator")
        logger.error("_case_evidence nondeterministic id=%s", case.case_id); return result
    left, right = lefts[0], rights[0]
    if case.expected == "echo": passed = left.status == right.status == "ready" and left.value == right.value
    elif case.expected == "separate": passed = left.status == right.status == "ready" and left.value != right.value
    elif case.expected == "blocked-left": passed = left.status == "blocked" and (not case.expected_obstruction or case.expected_obstruction in left.obstruction)
    elif case.expected == "blocked-right": passed = right.status == "blocked" and (not case.expected_obstruction or case.expected_obstruction in right.obstruction)
    else: passed = False
    reason = "matched" if passed else ("unexpected-obstruction" if left.status == "blocked" or right.status == "blocked" else "blind-collision")
    result = ObserverCaseEvidence(case.case_id, passed, left.status, right.status, left.value, right.value, reason)
    logger.debug("_case_evidence exit passed=%s", passed); return result

def _canonical_value(value: object) -> Canonical:
    logger.debug("_canonical_value entry type=%s", type(value).__name__)
    if value is None or isinstance(value, (str, int, float, bool)): result: Canonical = value
    elif isinstance(value, tuple): result = tuple(_canonical_value(item) for item in value)
    else: raise TypeError("noncanonical-result")
    logger.debug("_canonical_value exit"); return result

def _term_depth(term: ObserverTerm) -> int:
    logger.debug("_term_depth entry op=%s", term.op)
    result = 0 if not term.children else 1 + max(_term_depth(child) for child in term.children)
    logger.debug("_term_depth exit result=%d", result); return result

def _case_ids(cases: tuple[ObserverCase, ...]) -> tuple[str, ...]:
    logger.debug("_case_ids entry count=%d", len(cases)); result = tuple(item.case_id for item in cases); logger.debug("_case_ids exit"); return result

def _group_ids(cases: tuple[ObserverCase, ...]) -> tuple[str, ...]:
    logger.debug("_group_ids entry count=%d", len(cases)); result = tuple(item.group_id for item in cases); logger.debug("_group_ids exit"); return result

def _split_digest(cases: tuple[ObserverCase, ...], payloads: tuple[str, ...]) -> str:
    logger.debug("_split_digest entry count=%d", len(cases))
    metadata = tuple((item.case_id, item.group_id, item.expected, item.expected_obstruction) for item in cases)
    result = digest_value((metadata, payloads)); logger.debug("_split_digest exit digest=%s", result[:12]); return result

def _duplicate_split(cases: tuple[ObserverCase, ...], payloads: tuple[str, ...] | None = None) -> str:
    logger.debug("_duplicate_split entry count=%d", len(cases))
    ids, groups = _case_ids(cases), _group_ids(cases)
    payloads = case_payload_digests(cases) if payloads is None else payloads
    result = "duplicate-case-id" if len(set(ids)) != len(ids) else ("duplicate-group-id" if len(set(groups)) != len(groups) else ("duplicate-payload" if len(set(payloads)) != len(payloads) else ""))
    logger.debug("_duplicate_split exit result=%s", result); return result


# Parity evidence

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
    lean = _check_lean(LEAN_DIR / "VeyraObserverSynthesis.lean")
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

