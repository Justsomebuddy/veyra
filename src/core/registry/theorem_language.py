"""Legacy finite-obligation Core Language v0.9 fixture harness."""

from __future__ import annotations
from dataclasses import dataclass
import logging
import re
from collections.abc import Iterable, Mapping
from ..language import VeyraKind, expr_kind, infer_veyra, parse_veyra

logger = logging.getLogger(__name__)
FINITE_OBLIGATION_EVIDENCE_CLASS = "finite-obligation"
_IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
_PLACEHOLDER = re.compile(r"\$([A-Za-z][A-Za-z0-9_-]*)")
_LEFT_DELIMITERS = frozenset({"(", ","})
_RIGHT_DELIMITERS = frozenset({")", ","})


def template_variables(template: str) -> tuple[str, ...]:
    """Return placeholders that occupy complete expression positions."""
    logger.debug("template_variables entry template=%r", template)
    matches = tuple(_PLACEHOLDER.finditer(template))
    starts = frozenset(match.start() for match in matches)
    if any(char == "$" and index not in starts for index, char in enumerate(template)):
        logger.error("template_variables invalid placeholder syntax template=%r", template)
        raise ValueError("invalid theorem placeholder syntax")
    for match in matches:
        left = template[: match.start()].rstrip()
        right = template[match.end() :].lstrip()
        if (left and left[-1] not in _LEFT_DELIMITERS) or (
            right and right[0] not in _RIGHT_DELIMITERS
        ):
            logger.error(
                "template_variables placeholder is not expression token token=%s",
                match.group(0),
            )
            raise ValueError(
                f"theorem placeholder {match.group(0)} must occupy a complete expression"
            )
    result = tuple(match.group(1) for match in matches)
    logger.debug("template_variables exit variables=%r", result)
    return result


def substitute_template(template: str, assignments: Mapping[str, str]) -> str:
    """Substitute exact ``$identifier`` tokens without prefix capture."""
    logger.debug(
        "substitute_template entry template=%r assignment_count=%d",
        template,
        len(assignments),
    )
    template_variables(template)
    if any("$" in value for value in assignments.values()):
        logger.error("substitute_template replacement contains placeholder marker")
        raise ValueError("theorem assignment cannot contain a placeholder marker")

    def replacement(match: re.Match[str]) -> str:
        logger.debug("substitute_template.replacement entry token=%s", match.group(0))
        name = match.group(1)
        value = assignments.get(name)
        if value is None:
            logger.error("substitute_template.replacement missing assignment name=%s", name)
            raise ValueError(f"missing theorem assignment ${name}")
        logger.debug("substitute_template.replacement exit name=%s", name)
        return value

    result = _PLACEHOLDER.sub(replacement, template)
    logger.debug("substitute_template exit result=%r", result)
    return result
@dataclass(frozen=True)
class TheoremQuantifier:
    """A quantified variable declaration."""

    name: str
    kind: VeyraKind
@dataclass(frozen=True)
class TheoremProposition:
    """A status predicate over a Veyra expression template."""

    expected_status: str
    template: str
@dataclass(frozen=True)
class TheoremStatement:
    """Parsed theorem object with quantifiers and a logical connective."""

    name: str
    quantifiers: tuple[TheoremQuantifier, ...]
    assumptions: tuple[TheoremProposition, ...]
    conclusions: tuple[TheoremProposition, ...]
    connective: str


def exact_statement_graph(
    statement: object,
    statement_type: type,
    quantifier_type: type,
    proposition_type: type,
) -> bool:
    """Accept only the immutable dataclass graph owned by the legacy harness."""
    logger.debug("exact_statement_graph entry type=%s", type(statement).__name__)
    result = (
        type(statement) is statement_type
        and type(statement.name) is str
        and type(statement.connective) is str
        and type(statement.quantifiers) is tuple
        and type(statement.assumptions) is tuple
        and type(statement.conclusions) is tuple
        and all(type(item) is quantifier_type for item in statement.quantifiers)
        and all(
            type(item.name) is str and type(item.kind) is VeyraKind
            for item in statement.quantifiers
        )
        and all(
            type(item) is proposition_type
            for item in statement.assumptions + statement.conclusions
        )
        and all(
            type(item.expected_status) is str and type(item.template) is str
            for item in statement.assumptions + statement.conclusions
        )
    )
    logger.debug("exact_statement_graph exit result=%s", result)
    return result


def statement_errors(
    name: object,
    quantifiers: tuple[TheoremQuantifier, ...],
    assumptions: tuple[TheoremProposition, ...],
    conclusions: tuple[TheoremProposition, ...],
    connective: object,
) -> tuple[str, ...]:
    """Return fail-closed structural errors for a legacy theorem statement."""
    logger.debug("statement_errors entry theorem=%r", name)
    errors: list[str] = []
    if not isinstance(name, str) or not _IDENTIFIER.fullmatch(name):
        errors.append("bad theorem name")
    names: list[str] = []
    for quantifier in quantifiers:
        if not isinstance(quantifier.name, str) or not _IDENTIFIER.fullmatch(quantifier.name):
            errors.append("bad quantifier name")
        elif quantifier.name in names:
            errors.append(f"duplicate quantifier {quantifier.name}")
        else:
            names.append(quantifier.name)
        if not isinstance(quantifier.kind, VeyraKind):
            errors.append(f"bad quantifier kind {quantifier.name}")
    if not conclusions:
        errors.append("no conclusions")
    if connective not in {"asserts", "implies", "iff"}:
        errors.append("bad connective")
    if connective == "asserts" and assumptions:
        errors.append("assertion cannot contain assumptions")
    if connective in {"implies", "iff"} and not assumptions:
        errors.append(f"{connective} requires assumptions")
    declared = frozenset(names)
    for proposition in assumptions + conclusions:
        if proposition.expected_status not in {"ready", "blocked", "unknown"}:
            errors.append("bad proposition status")
        if not isinstance(proposition.template, str) or not proposition.template.strip():
            errors.append("empty proposition template")
            continue
        try:
            variables = frozenset(template_variables(proposition.template))
        except ValueError as exc:
            errors.append(str(exc))
            continue
        unknown = variables - declared
        if unknown:
            errors.append(f"undeclared theorem placeholder ${sorted(unknown)[0]}")
    result = tuple(dict.fromkeys(errors))
    logger.debug("statement_errors exit count=%d", len(result))
    return result
@dataclass(frozen=True)
class TheoremEnvironment:
    """Finite witness assignment for quantified theorem variables."""

    name: str
    assignments: Mapping[str, str]


@dataclass(frozen=True)
class ProofObligation:
    """One checked obligation produced by a theorem statement."""

    theorem: str
    environment: str
    role: str
    source: str
    expected_status: str
    actual_status: str
    status: str
    obstruction: str = ""


@dataclass(frozen=True)
class TheoremCheck:
    """Aggregate result for finite theorem obligations."""

    theorem: str
    status: str
    obligations: tuple[ProofObligation, ...]
    blocked: tuple[str, ...]
    evidence_class: str = FINITE_OBLIGATION_EVIDENCE_CLASS

    def __post_init__(self) -> None:
        logger.debug("TheoremCheck.__post_init__ entry theorem=%s", self.theorem)
        if self.evidence_class != FINITE_OBLIGATION_EVIDENCE_CLASS:
            logger.error(
                "TheoremCheck.__post_init__ invalid evidence_class=%r",
                self.evidence_class,
            )
            raise ValueError("theorem check evidence class must be finite-obligation")
        logger.debug("TheoremCheck.__post_init__ exit theorem=%s", self.theorem)


def parse_theorem_statement(source: str) -> TheoremStatement:
    """Parse `theorem name forall x:kind :: prop -> prop` syntax."""
    logger.debug("parse_theorem_statement entry source=%r", source)
    if "::" not in source:
        logger.error("parse_theorem_statement missing separator")
        raise ValueError("missing theorem body separator '::'")
    header, body = (part.strip() for part in source.split("::", 1))
    match = re.fullmatch(r"theorem\s+([A-Za-z][\w-]*)\s+forall\s+(.+)", header)
    if not match:
        logger.error("parse_theorem_statement bad header=%s", header)
        raise ValueError("bad theorem header")
    name = match.group(1)
    quantifiers = _parse_quantifiers(match.group(2))
    connective, left, right = _split_body(body)
    assumptions = tuple(_parse_prop(part) for part in _split_conjunction(left)) if right else ()
    conclusions = tuple(_parse_prop(part) for part in _split_conjunction(right or left))
    declared = frozenset(quantifier.name for quantifier in quantifiers)
    for prop in assumptions + conclusions:
        unknown = frozenset(template_variables(prop.template)) - declared
        if unknown:
            logger.error(
                "parse_theorem_statement undeclared placeholders=%r",
                sorted(unknown),
            )
            raise ValueError(f"undeclared theorem placeholder ${sorted(unknown)[0]}")
    result = TheoremStatement(name, quantifiers, assumptions, conclusions, connective)
    logger.debug("parse_theorem_statement exit result=%r", result)
    return result


def check_theorem_statement(statement: TheoremStatement, environments: Iterable[TheoremEnvironment]) -> TheoremCheck:
    """Check finite proof obligations for a theorem statement."""
    theorem_name = statement.name if type(statement) is TheoremStatement and type(statement.name) is str else "<invalid>"
    logger.debug("check_theorem_statement entry theorem=%s", theorem_name)
    obligations: list[ProofObligation] = []
    blocked: list[str] = []
    if not exact_statement_graph(
        statement, TheoremStatement, TheoremQuantifier, TheoremProposition,
    ):
        logger.error("check_theorem_statement noncanonical statement graph")
        return TheoremCheck(
            theorem_name, "blocked", (), ("invalid-statement:noncanonical object graph",),
        )
    validation_errors = statement_errors(
        statement.name,
        statement.quantifiers,
        statement.assumptions,
        statement.conclusions,
        statement.connective,
    )
    if validation_errors:
        logger.error(
            "check_theorem_statement invalid statement theorem=%r errors=%r",
            statement.name,
            validation_errors,
        )
        return TheoremCheck(
            statement.name,
            "blocked",
            (),
            tuple(f"invalid-statement:{error}" for error in validation_errors),
        )
    finite_environments = tuple(environments)
    if not finite_environments:
        logger.error("check_theorem_statement no finite environments theorem=%s", statement.name)
        blocked.append("no-finite-environments")
    environment_names = tuple(environment.name for environment in finite_environments)
    duplicates = tuple(dict.fromkeys(
        name for name in environment_names if environment_names.count(name) > 1
    ))
    if duplicates:
        logger.error("check_theorem_statement duplicate environments=%r", duplicates)
        reasons = tuple(f"duplicate-environment-name:{name}" for name in duplicates)
        return TheoremCheck(statement.name, "blocked", (), reasons)
    for env in finite_environments:
        try:
            assignments = dict(env.assignments.items())
        except (AttributeError, TypeError, ValueError) as exc:
            logger.error(
                "check_theorem_statement invalid environment env=%r error=%s",
                env.name,
                exc,
            )
            blocked.append(f"{env.name}:invalid assignments")
            continue
        declared = frozenset(quantifier.name for quantifier in statement.quantifiers)
        stable_env = TheoremEnvironment(
            env.name, {name: value for name, value in assignments.items() if name in declared},
        )
        env_errors = _environment_errors(statement, stable_env)
        if env_errors:
            blocked.extend(f"{env.name}:{err}" for err in env_errors)
            continue
        rows = [_check_prop(statement.name, stable_env, "assumption", prop) for prop in statement.assumptions]
        rows.extend(_check_prop(statement.name, stable_env, "conclusion", prop) for prop in statement.conclusions)
        obligations.extend(rows)
        if any(row.status != "ready" for row in rows):
            blocked.append(env.name)
    result = TheoremCheck(statement.name, "ready" if not blocked else "blocked", tuple(obligations), tuple(blocked))
    logger.debug("check_theorem_statement exit status=%s obligations=%d", result.status, len(result.obligations))
    return result


def theorem_obligation_rows() -> tuple[ProofObligation, ...]:
    """Return default F2 obligation rows, including a blocked diagnostic."""
    logger.debug("theorem_obligation_rows entry")
    good = parse_theorem_statement(
        "theorem echo_kind_reflexive forall x:nod :: ready(echo($x,$x,observer:kind))"
    )
    bad = parse_theorem_statement(
        "theorem trace_echo_false forall x:nod,y:nod :: ready(echo($x,$y,observer:trace))"
    )
    environments = default_theorem_environments()
    result = (
        check_theorem_statement(good, environments[:2]).obligations
        + check_theorem_statement(bad, environments[2:]).obligations
    )
    logger.debug("theorem_obligation_rows exit count=%d", len(result))
    return result


def default_theorem_environments() -> tuple[TheoremEnvironment, ...]:
    """Return finite theorem-language fixtures."""
    logger.debug("default_theorem_environments entry")
    result = (
        TheoremEnvironment("nod-a", {"x": "nod:a", "y": "nod:a"}),
        TheoremEnvironment("nod-b", {"x": "nod:b", "y": "nod:b"}),
        TheoremEnvironment("trace-mismatch", {"x": "nod:a", "y": "nod:b"}),
    )
    logger.debug("default_theorem_environments exit count=%d", len(result))
    return result


def theorem_language_checklist() -> tuple[str, ...]:
    """Return F2 theorem-language capabilities."""
    logger.debug("theorem_language_checklist entry")
    result = (
        "theorem names",
        "forall quantifiers",
        "typed variables",
        "status propositions",
        "implication/equivalence parsing",
        "finite proof obligations",
        "blocked diagnostics",
    )
    logger.debug("theorem_language_checklist exit count=%d", len(result))
    return result


def _parse_quantifiers(text: str) -> tuple[TheoremQuantifier, ...]:
    logger.debug("_parse_quantifiers entry text=%s", text)
    rows = []
    for part in text.split(","):
        pieces = tuple(piece.strip() for piece in part.split(":"))
        if len(pieces) != 2 or not _IDENTIFIER.fullmatch(pieces[0]):
            logger.error("_parse_quantifiers bad declaration=%r", part)
            raise ValueError(f"bad quantifier declaration {part!r}")
        name, kind = pieces
        if any(row.name == name for row in rows):
            logger.error("_parse_quantifiers duplicate name=%s", name)
            raise ValueError(f"duplicate quantifier {name!r}")
        try:
            rows.append(TheoremQuantifier(name, VeyraKind(kind)))
        except ValueError as exc:
            logger.error("_parse_quantifiers bad kind name=%s kind=%s", name, kind)
            raise ValueError(f"bad quantifier kind {kind!r}") from exc
    result = tuple(rows)
    logger.debug("_parse_quantifiers exit count=%d", len(result))
    return result


def _split_body(body: str) -> tuple[str, str, str]:
    logger.debug("_split_body entry body=%s", body)
    for op, name in (("<->", "iff"), ("->", "implies")):
        parts = _split_top_level(body, op)
        if parts:
            result = (name, parts[0].strip(), parts[1].strip())
            logger.debug("_split_body exit result=%r", result)
            return result
    result = ("asserts", body.strip(), "")
    logger.debug("_split_body exit result=%r", result)
    return result


def _split_top_level(text: str, op: str) -> tuple[str, str] | None:
    logger.debug("_split_top_level entry op=%s", op)
    depth = 0
    for index, char in enumerate(text):
        depth += char == "("
        depth -= char == ")"
        if depth == 0 and text.startswith(op, index):
            return text[:index], text[index + len(op) :]
    logger.debug("_split_top_level exit none")
    return None


def _split_conjunction(text: str) -> tuple[str, ...]:
    logger.debug("_split_conjunction entry text=%s", text)
    result = tuple(part.strip() for part in re.split(r"\s+&\s+", text) if part.strip())
    logger.debug("_split_conjunction exit count=%d", len(result))
    return result


def _parse_prop(text: str) -> TheoremProposition:
    logger.debug("_parse_prop entry text=%s", text)
    match = re.fullmatch(r"(ready|blocked|unknown)\((.*)\)", text.strip())
    if not match:
        logger.error("_parse_prop bad proposition=%s", text)
        raise ValueError(f"bad proposition {text!r}")
    result = TheoremProposition(match.group(1), match.group(2).strip())
    logger.debug("_parse_prop exit result=%r", result)
    return result


def _environment_errors(statement: TheoremStatement, env: TheoremEnvironment) -> tuple[str, ...]:
    logger.debug("_environment_errors entry theorem=%s env=%s", statement.name, env.name)
    errors = []
    for quant in statement.quantifiers:
        source = env.assignments.get(quant.name)
        if source is None:
            errors.append(f"missing ${quant.name}")
            continue
        if not isinstance(source, str) or "$" in source:
            errors.append(f"invalid ${quant.name}: replacement must be placeholder-free text")
            continue
        try:
            check = expr_kind(parse_veyra(source))
        except ValueError as exc:
            logger.error(
                "_environment_errors invalid replacement env=%s variable=%s error=%s",
                env.name,
                quant.name,
                exc,
            )
            errors.append(f"invalid ${quant.name}: {exc}")
            continue
        if check.kind != quant.kind:
            errors.append(f"kind ${quant.name} expected {quant.kind.value} got {check.kind}")
    result = tuple(errors)
    logger.debug("_environment_errors exit count=%d", len(result))
    return result


def _check_prop(theorem: str, env: TheoremEnvironment, role: str, prop: TheoremProposition) -> ProofObligation:
    logger.debug("_check_prop entry theorem=%s env=%s role=%s", theorem, env.name, role)
    source = substitute_template(prop.template, env.assignments)
    check = infer_veyra(parse_veyra(source))
    status = "ready" if check.status == prop.expected_status else "blocked"
    result = ProofObligation(
        theorem, env.name, role, source, prop.expected_status, check.status, status, check.obstruction
    )
    logger.debug("_check_prop exit result=%r", result)
    return result
