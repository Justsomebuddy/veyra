"""Closed typed observer DSL with no caller-supplied executable semantics."""

from __future__ import annotations

from itertools import combinations
import logging

from .types import ClosedObserverGrammar, ClosedObserverTerm, ClosedValue
from ...proof_core_codec import canonical_json, digest_data

logger = logging.getLogger(__name__)
SEMANTICS_VERSION = "veyra-closed-observer-dsl-v1"
OPS = frozenset({"column", "xor", "pair"})
MAX_ARITY = 64
MAX_DEPTH = 8
MAX_COST = 64
MAX_TERMS = 4096
MAX_VALUE_UNITS = 4096


class ClosedDslError(ValueError):
    """Stable rejection from syntax, typing, canonicality, or resource checks."""

    def __init__(self, reason: str) -> None:
        logger.error("ClosedDslError entry reason=%s", reason)
        self.reason = reason
        super().__init__(reason)
        logger.debug("ClosedDslError exit")


def grammar_data(grammar: ClosedObserverGrammar) -> dict[str, object]:
    """Encode a grammar as canonical JSON-compatible tagged data."""
    logger.debug("grammar_data entry")
    validate_grammar(grammar)
    result = {
        "tag": "closed-observer-grammar-v1",
        "semantics": SEMANTICS_VERSION,
        "grammar_id": grammar.grammar_id,
        "input_arity": grammar.input_arity,
        "bit_columns": list(grammar.bit_columns),
        "allowed_ops": list(grammar.allowed_ops),
        "max_xor_width": grammar.max_xor_width,
        "max_depth": grammar.max_depth,
        "max_cost": grammar.max_cost,
    }
    logger.debug("grammar_data exit")
    return result


def grammar_from_data(data: object) -> ClosedObserverGrammar:
    """Strictly decode a canonical grammar object with exact keys."""
    logger.debug("grammar_from_data entry")
    keys = {
        "tag",
        "semantics",
        "grammar_id",
        "input_arity",
        "bit_columns",
        "allowed_ops",
        "max_xor_width",
        "max_depth",
        "max_cost",
    }
    if (
        type(data) is not dict
        or set(data) != keys
        or data.get("tag") != "closed-observer-grammar-v1"
        or data.get("semantics") != SEMANTICS_VERSION
    ):
        raise ClosedDslError("grammar-shape")
    if (
        type(data["bit_columns"]) is not list
        or len(data["bit_columns"]) > MAX_ARITY
        or type(data["allowed_ops"]) is not list
        or len(data["allowed_ops"]) > len(OPS)
    ):
        raise ClosedDslError("grammar-shape")
    try:
        result = ClosedObserverGrammar(
            data["grammar_id"],
            data["input_arity"],
            tuple(data["bit_columns"]),
            tuple(data["allowed_ops"]),
            data["max_xor_width"],
            data["max_depth"],
            data["max_cost"],
        )
    except (TypeError, KeyError) as exc:
        logger.error("grammar_from_data decode error")
        raise ClosedDslError("grammar-shape") from exc
    validate_grammar(result)
    if canonical_json(grammar_data(result)) != canonical_json(data):
        raise ClosedDslError("noncanonical-grammar")
    logger.debug("grammar_from_data exit")
    return result


def term_data(term: ClosedObserverTerm) -> dict[str, object]:
    """Encode one bounded AST as canonical tagged data."""
    logger.debug("term_data entry op=%s", getattr(term, "op", "<invalid>"))
    active: set[int] = set()
    budget = [0]

    def encode(node: ClosedObserverTerm, depth: int) -> dict[str, object]:
        logger.debug("term_data.encode entry depth=%d", depth)
        if type(node) is not ClosedObserverTerm or id(node) in active:
            raise ClosedDslError("cyclic-term")
        if (
            type(node.indices) is not tuple
            or len(node.indices) > MAX_ARITY
            or type(node.children) is not tuple
            or len(node.children) > 2
        ):
            raise ClosedDslError("term-shape")
        budget[0] += 1
        if budget[0] > 65536 or depth > MAX_DEPTH:
            raise ClosedDslError("ast-resource-limit")
        active.add(id(node))
        result = {
            "tag": "closed-observer-term-v1",
            "op": node.op,
            "indices": list(node.indices),
            "children": [encode(child, depth + 1) for child in node.children],
        }
        active.remove(id(node))
        logger.debug("term_data.encode exit depth=%d", depth)
        return result

    result = encode(term, 0)
    logger.debug("term_data exit nodes=%d", budget[0])
    return result


def term_from_data(data: object, *, node_limit: int = 65536) -> ClosedObserverTerm:
    """Strictly decode an occurrence-bounded AST."""
    logger.debug("term_from_data entry node_limit=%d", node_limit)
    budget = [0]

    def decode(node: object, depth: int) -> ClosedObserverTerm:
        logger.debug("term_from_data.decode entry depth=%d", depth)
        budget[0] += 1
        if budget[0] > node_limit or depth > MAX_DEPTH:
            raise ClosedDslError("ast-resource-limit")
        if (
            type(node) is not dict
            or set(node) != {"tag", "op", "indices", "children"}
            or node.get("tag") != "closed-observer-term-v1"
        ):
            raise ClosedDslError("term-shape")
        if type(node["indices"]) is not list or type(node["children"]) is not list:
            raise ClosedDslError("term-shape")
        if len(node["indices"]) > MAX_ARITY or len(node["children"]) > 2:
            raise ClosedDslError("term-shape")
        result = ClosedObserverTerm(
            node["op"],
            tuple(node["indices"]),
            tuple(decode(child, depth + 1) for child in node["children"]),
        )
        logger.debug("term_from_data.decode exit depth=%d", depth)
        return result

    result = decode(data, 0)
    if canonical_json(term_data(result)) != canonical_json(data):
        raise ClosedDslError("noncanonical-term")
    logger.debug("term_from_data exit nodes=%d", budget[0])
    return result


def validate_grammar(grammar: ClosedObserverGrammar) -> None:
    """Validate closed grammar shape and hard resource ceilings."""
    logger.debug("validate_grammar entry")
    if (
        type(grammar) is not ClosedObserverGrammar
        or type(grammar.grammar_id) is not str
        or not grammar.grammar_id
        or not _utf8_within(grammar.grammar_id, 256)
    ):
        raise ClosedDslError("invalid-grammar")
    ints = (grammar.input_arity, grammar.max_xor_width, grammar.max_depth, grammar.max_cost)
    if (
        any(type(value) is not int for value in ints)
        or not 1 <= grammar.input_arity <= MAX_ARITY
        or not 1 <= grammar.max_xor_width <= grammar.input_arity
        or not 0 <= grammar.max_depth <= MAX_DEPTH
        or not 1 <= grammar.max_cost <= MAX_COST
    ):
        raise ClosedDslError("invalid-grammar-budget")
    if (
        type(grammar.bit_columns) is not tuple
        or len(grammar.bit_columns) > grammar.input_arity
        or tuple(sorted(set(grammar.bit_columns))) != grammar.bit_columns
        or any(type(index) is not int or not 0 <= index < grammar.input_arity for index in grammar.bit_columns)
    ):
        raise ClosedDslError("invalid-bit-columns")
    if (
        type(grammar.allowed_ops) is not tuple
        or len(grammar.allowed_ops) > len(OPS)
        or tuple(sorted(set(grammar.allowed_ops))) != grammar.allowed_ops
        or not grammar.allowed_ops
        or any(op not in OPS for op in grammar.allowed_ops)
    ):
        raise ClosedDslError("invalid-allowed-ops")
    logger.debug("validate_grammar exit")


def term_kind_cost(term: ClosedObserverTerm, grammar: ClosedObserverGrammar) -> tuple[str, int]:
    """Derive output kind and audited cost; never trust fields in the AST."""
    logger.debug("term_kind_cost entry")
    validate_grammar(grammar)
    active: set[int] = set()
    nodes = [0]

    def visit(node: ClosedObserverTerm, depth: int) -> tuple[str, int]:
        logger.debug("term_kind_cost.visit entry depth=%d", depth)
        if type(node) is not ClosedObserverTerm or id(node) in active:
            raise ClosedDslError("cyclic-term")
        active.add(id(node))
        nodes[0] += 1
        if nodes[0] > 65536 or depth > grammar.max_depth:
            raise ClosedDslError("ast-resource-limit")
        if node.op not in grammar.allowed_ops or type(node.indices) is not tuple or type(node.children) is not tuple:
            raise ClosedDslError("term-not-in-grammar")
        if node.op == "column":
            if (
                len(node.indices) != 1
                or node.children
                or type(node.indices[0]) is not int
                or not 0 <= node.indices[0] < grammar.input_arity
            ):
                raise ClosedDslError("column-shape")
            result = ("scalar", 1)
        elif node.op == "xor":
            if (
                node.children
                or not 2 <= len(node.indices) <= grammar.max_xor_width
                or tuple(sorted(set(node.indices))) != node.indices
                or any(index not in grammar.bit_columns for index in node.indices)
            ):
                raise ClosedDslError("xor-shape")
            result = ("scalar", len(node.indices))
        elif node.op == "pair":
            if node.indices or len(node.children) != 2:
                raise ClosedDslError("pair-shape")
            left, right = (visit(child, depth + 1) for child in node.children)
            if (
                left[0] != "scalar"
                or right[0] != "scalar"
                or canonical_json(term_data(node.children[0])) > canonical_json(term_data(node.children[1]))
            ):
                raise ClosedDslError("pair-type-or-order")
            result = ("pair", 1 + left[1] + right[1])
        else:
            raise ClosedDslError("unknown-op")
        if result[1] > grammar.max_cost:
            raise ClosedDslError("term-cost-limit")
        active.remove(id(node))
        logger.debug("term_kind_cost.visit exit depth=%d", depth)
        return result

    result = visit(term, 0)
    logger.debug("term_kind_cost exit cost=%d", result[1])
    return result


def evaluate_closed_term(term: ClosedObserverTerm, row: ClosedValue, grammar: ClosedObserverGrammar) -> ClosedValue:
    """Evaluate fixed semantics over one canonical row without callbacks."""
    logger.debug("evaluate_closed_term entry")
    term_kind_cost(term, grammar)
    if type(row) is not tuple or len(row) != grammar.input_arity:
        raise ClosedDslError("row-shape")

    def evaluate(node: ClosedObserverTerm) -> ClosedValue:
        logger.debug("evaluate_closed_term.evaluate entry op=%s", node.op)
        if node.op == "column":
            result = row[node.indices[0]]
        elif node.op == "xor":
            values = tuple(row[index] for index in node.indices)
            if any(type(value) not in {bool, int} or int(value) not in {0, 1} for value in values):
                raise ClosedDslError("non-bit-xor-input")
            result = sum(int(value) for value in values) % 2
        elif node.op == "pair":
            result = (evaluate(node.children[0]), evaluate(node.children[1]))
        else:
            raise ClosedDslError("unknown-op")
        _validate_canonical(result)
        logger.debug("evaluate_closed_term.evaluate exit op=%s", node.op)
        return result

    result = evaluate(term)
    logger.debug("evaluate_closed_term exit")
    return result


def enumerate_closed_terms(grammar: ClosedObserverGrammar, construction_limit: int) -> tuple[ClosedObserverTerm, ...]:
    """Enumerate the complete finite grammar or fail at the construction cap."""
    logger.debug("enumerate_closed_terms entry limit=%d", construction_limit)
    validate_grammar(grammar)
    if type(construction_limit) is not int or not 1 <= construction_limit <= 65536:
        raise ClosedDslError("construction-limit")
    accepted: list[ClosedObserverTerm] = []
    scalar: list[ClosedObserverTerm] = []
    attempted = 0

    def consider(term: ClosedObserverTerm, *, scalar_term: bool) -> None:
        nonlocal attempted
        logger.debug("enumerate_closed_terms.consider entry op=%s", term.op)
        attempted += 1
        if attempted > construction_limit:
            raise ClosedDslError("catalog-cutoff")
        try:
            term_kind_cost(term, grammar)
        except ClosedDslError as exc:
            if exc.reason in {"term-cost-limit", "ast-resource-limit"}:
                logger.debug("enumerate_closed_terms.consider rejected reason=%s", exc.reason)
                return
            raise
        accepted.append(term)
        if scalar_term:
            scalar.append(term)
        logger.debug("enumerate_closed_terms.consider exit accepted=%d", len(accepted))

    if "column" in grammar.allowed_ops:
        for index in range(grammar.input_arity):
            consider(ClosedObserverTerm("column", (index,)), scalar_term=True)
    if "xor" in grammar.allowed_ops:
        for width in range(2, grammar.max_xor_width + 1):
            for indices in combinations(grammar.bit_columns, width):
                consider(ClosedObserverTerm("xor", indices), scalar_term=True)
    scalar_ordered = tuple(sorted(scalar, key=lambda term: canonical_json(term_data(term))))
    if "pair" in grammar.allowed_ops and grammar.max_depth >= 1:
        for index, left in enumerate(scalar_ordered):
            for right in scalar_ordered[index:]:
                consider(ClosedObserverTerm("pair", children=(left, right)), scalar_term=False)
    if not accepted:
        raise ClosedDslError("empty-catalog")
    result = tuple(
        sorted(accepted, key=lambda term: (term_kind_cost(term, grammar)[1], canonical_json(term_data(term))))
    )
    logger.debug("enumerate_closed_terms exit count=%d", len(result))
    return result


def grammar_digest(grammar: ClosedObserverGrammar) -> str:
    """Return the domain-separated closed grammar identity."""
    logger.debug("grammar_digest entry")
    result = digest_data(grammar_data(grammar), "veyra.closed-observer.grammar.v1")
    logger.debug("grammar_digest exit digest=%s", result[:12])
    return result


def terms_digest(terms: tuple[ClosedObserverTerm, ...], grammar: ClosedObserverGrammar) -> str:
    """Bind an ordered, typed term catalog."""
    logger.debug("terms_digest entry type=%s", type(terms).__name__)
    if type(terms) is not tuple or not 1 <= len(terms) <= MAX_TERMS:
        raise ClosedDslError("term-count")
    for term in terms:
        term_kind_cost(term, grammar)
    result = digest_data([term_data(term) for term in terms], "veyra.closed-observer.terms.v1")
    logger.debug("terms_digest exit digest=%s", result[:12])
    return result


def observer_program_digest(
    grammar: ClosedObserverGrammar,
    terms: tuple[ClosedObserverTerm, ...],
) -> str:
    """Bind the grammar identity and ordered closed term suite as one program."""
    logger.debug("observer_program_digest entry count=%d", len(terms))
    result = digest_data(
        {
            "grammar_digest": grammar_digest(grammar),
            "terms_digest": terms_digest(terms, grammar),
        },
        "veyra.closed-observer.program-suite.v1",
    )
    logger.debug("observer_program_digest exit digest=%s", result[:12])
    return result


def closed_rows_digest(rows: tuple[ClosedValue, ...]) -> str:
    """Bind one bounded ordered closed-worker row suite."""
    logger.debug("closed_rows_digest entry type=%s", type(rows).__name__)
    if type(rows) is not tuple or not 1 <= len(rows) <= 8192:
        raise ClosedDslError("row-count")
    encoded = []
    units = 0
    for row in rows:
        units += _validate_canonical(row)
        if units > 262_144:
            raise ClosedDslError("row-work-limit")
        encoded.append(canonical_value_data(row))
    result = digest_data(encoded, "veyra.closed-observer.rows.v1")
    logger.debug("closed_rows_digest exit digest=%s", result[:12])
    return result


def canonical_value_data(value: ClosedValue) -> object:
    """Encode a bounded categorical value without Python-specific objects."""
    logger.debug("canonical_value_data entry")
    _validate_canonical(value)
    if type(value) is bool:
        result: object = {"tag": "bool", "value": value}
    elif type(value) is int:
        result = {"tag": "int", "value": value}
    elif type(value) is str:
        result = {"tag": "str", "value": value}
    else:
        result = {"tag": "tuple", "value": [canonical_value_data(item) for item in value]}
    logger.debug("canonical_value_data exit")
    return result


def canonical_value_from_data(data: object, depth: int = 0) -> ClosedValue:
    """Strictly decode one tagged categorical value."""
    logger.debug("canonical_value_from_data entry depth=%d", depth)
    budget = [0]

    def decode(node: object, current_depth: int) -> ClosedValue:
        logger.debug("canonical_value_from_data.decode entry depth=%d", current_depth)
        budget[0] += 1
        if budget[0] > MAX_VALUE_UNITS:
            raise ClosedDslError("canonical-size")
        if type(node) is not dict or type(node.get("tag")) is not str or current_depth > 16:
            raise ClosedDslError("canonical-data-shape")
        tag = node["tag"]
        if tag in {"bool", "int", "str"} and set(node) == {"tag", "value"}:
            raw = node["value"]
            if tag == "bool" and type(raw) is bool:
                result: ClosedValue = raw
            elif tag == "int" and type(raw) is int:
                result = raw
            elif tag == "str" and type(raw) is str:
                result = raw
            else:
                raise ClosedDslError("canonical-data-type")
        elif tag == "tuple" and set(node) == {"tag", "value"} and type(node["value"]) is list:
            if len(node["value"]) > MAX_VALUE_UNITS:
                raise ClosedDslError("canonical-size")
            result = tuple(decode(item, current_depth + 1) for item in node["value"])
        else:
            raise ClosedDslError("canonical-data-shape")
        _validate_canonical(result, current_depth)
        logger.debug("canonical_value_from_data.decode exit depth=%d", current_depth)
        return result

    result = decode(data, depth)
    if canonical_json(canonical_value_data(result)) != canonical_json(data):
        raise ClosedDslError("noncanonical-value-data")
    logger.debug("canonical_value_from_data exit depth=%d", depth)
    return result


def _validate_canonical(value: ClosedValue, depth: int = 0) -> int:
    logger.debug("_validate_canonical entry depth=%d", depth)
    if depth > 16:
        raise ClosedDslError("canonical-depth")
    if type(value) is bool:
        result = 1
    elif type(value) is str:
        if not _utf8_within(value, 4096):
            raise ClosedDslError("string-size")
        result = 1
    elif type(value) is int:
        if value.bit_length() > 32768:
            raise ClosedDslError("integer-size")
        result = 1
    elif type(value) is tuple:
        result = 1
        for item in value:
            result += _validate_canonical(item, depth + 1)
            if result > MAX_VALUE_UNITS:
                raise ClosedDslError("canonical-size")
    else:
        raise ClosedDslError("noncanonical-value")
    if result > MAX_VALUE_UNITS:
        raise ClosedDslError("canonical-size")
    logger.debug("_validate_canonical exit units=%d", result)
    return result


def _utf8_within(value: str, byte_limit: int) -> bool:
    """Check bounded UTF-8 without encoding an unbounded Python string."""
    logger.debug("_utf8_within entry chars=%d limit=%d", len(value), byte_limit)
    if len(value) > byte_limit:
        logger.debug("_utf8_within exit valid=False")
        return False
    try:
        valid = len(value.encode("utf-8")) <= byte_limit
    except UnicodeError:
        valid = False
    logger.debug("_utf8_within exit valid=%s", valid)
    return valid
