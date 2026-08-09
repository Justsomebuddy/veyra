from collections.abc import Iterator, Mapping
from dataclasses import replace

import pytest

from src.core.language import VeyraKind
from src.core.layer_theorem_contracts import theorem_contract_registry
from src.core.theorem_language import (
    FINITE_OBLIGATION_EVIDENCE_CLASS,
    TheoremEnvironment,
    TheoremProposition,
    TheoremQuantifier,
    TheoremStatement,
    check_theorem_statement,
    default_theorem_environments,
    parse_theorem_statement,
    theorem_language_checklist,
    theorem_obligation_rows,
)


def test_theorem_parser_accepts_quantified_assertion():
    statement = parse_theorem_statement("theorem echo_kind_reflexive forall x:nod :: ready(echo($x,$x,observer:kind))")
    assert statement.name == "echo_kind_reflexive"
    assert statement.quantifiers[0].name == "x"
    assert statement.quantifiers[0].kind.value == "nod"
    assert statement.connective == "asserts"
    assert statement.conclusions[0].expected_status == "ready"


def test_theorem_checker_builds_ready_obligations():
    statement = parse_theorem_statement("theorem echo_kind_reflexive forall x:nod :: ready(echo($x,$x,observer:kind))")
    check = check_theorem_statement(statement, default_theorem_environments()[:2])
    assert check.status == "ready"
    assert len(check.obligations) == 2
    assert {row.actual_status for row in check.obligations} == {"ready"}


def test_overlapping_variable_names_are_substituted_as_exact_tokens():
    statement = parse_theorem_statement("theorem overlap forall x:nod,xy:nod :: ready(echo($x,$xy,observer:kind))")
    environment = TheoremEnvironment("overlap", {"x": "nod:a", "xy": "nod:b"})
    check = check_theorem_statement(statement, (environment,))
    assert check.status == "ready"
    assert check.obligations[0].source == "echo(nod:a,nod:b,observer:kind)"


def test_repeated_placeholder_substitutes_each_exact_occurrence():
    statement = parse_theorem_statement("theorem repeated forall x:nod :: ready(echo($x,$x,observer:trace))")
    environment = TheoremEnvironment("repeated", {"x": "nod:a"})
    check = check_theorem_statement(statement, (environment,))
    assert check.status == "ready"
    assert check.obligations[0].source == "echo(nod:a,nod:a,observer:trace)"


def test_missing_overlapping_assignment_blocks_without_partial_replacement():
    statement = parse_theorem_statement("theorem missing forall x:nod,xy:nod :: ready(echo($x,$xy,observer:kind))")
    check = check_theorem_statement(
        statement,
        (TheoremEnvironment("missing", {"x": "nod:a"}),),
    )
    assert check.status == "blocked"
    assert check.obligations == ()
    assert check.blocked == ("missing:missing $xy",)


def test_duplicate_quantifier_is_rejected_before_evaluation():
    with pytest.raises(ValueError, match="duplicate quantifier"):
        parse_theorem_statement("theorem duplicate forall x:nod,x:nod :: ready(echo($x,$x,observer:kind))")


@pytest.mark.parametrize("placeholder", ("$$x", "$1", "$"))
def test_invalid_placeholder_syntax_is_rejected(placeholder):
    with pytest.raises(ValueError, match="invalid theorem placeholder syntax"):
        parse_theorem_statement(f"theorem syntax forall x:nod :: ready(echo({placeholder},$x,observer:kind))")


def test_undeclared_placeholder_is_not_prefix_replaced():
    with pytest.raises(ValueError, match=r"undeclared theorem placeholder \$xy"):
        parse_theorem_statement("theorem undeclared forall x:nod :: ready(echo($x,$xy,observer:kind))")


def test_malformed_replacement_source_blocks_before_substitution():
    statement = parse_theorem_statement("theorem malformed forall x:nod :: ready(echo($x,$x,observer:kind))")
    check = check_theorem_statement(
        statement,
        (TheoremEnvironment("malformed", {"x": "nod:a)"}),),
    )
    assert check.status == "blocked"
    assert check.obligations == ()
    assert check.blocked[0].startswith("malformed:invalid $x:")


def test_empty_finite_environment_set_is_not_vacuously_ready():
    statement = parse_theorem_statement("theorem empty forall x:nod :: ready(echo($x,$x,observer:kind))")
    check = check_theorem_statement(statement, ())
    assert check.status == "blocked"
    assert check.blocked == ("no-finite-environments",)


def test_direct_statement_construction_cannot_bypass_parser_invariants():
    statement = TheoremStatement(
        "forged",
        (TheoremQuantifier("x", VeyraKind.NOD),),
        (),
        (TheoremProposition("ready", "echo($y,$y,observer:trace)"),),
        "asserts",
    )
    check = check_theorem_statement(
        statement,
        (TheoremEnvironment("forged", {"x": "nod:a", "y": "nod:b"}),),
    )
    assert check.status == "blocked"
    assert check.obligations == ()
    assert "undeclared theorem placeholder $y" in check.blocked[0]


def test_direct_empty_statement_is_blocked():
    parsed = parse_theorem_statement(
        "theorem valid forall x:nod :: ready(echo($x,$x,observer:trace))"
    )
    forged = replace(parsed, conclusions=())
    check = check_theorem_statement(forged, default_theorem_environments()[:1])
    assert check.status == "blocked"
    assert check.blocked == ("invalid-statement:no conclusions",)


class _ChangingAssignments(Mapping[str, str]):
    def __init__(self) -> None:
        self.reads = 0

    def __getitem__(self, key: str) -> str:
        self.reads += 1
        return "nod:a" if self.reads == 1 else "nod:b"

    def __iter__(self) -> Iterator[str]:
        return iter(("x",))

    def __len__(self) -> int:
        return 1


def test_environment_mapping_is_snapshotted_before_validation_and_substitution():
    statement = parse_theorem_statement(
        "theorem stable forall x:nod :: ready(echo($x,$x,observer:trace))"
    )
    assignments = _ChangingAssignments()
    check = check_theorem_statement(
        statement,
        (TheoremEnvironment("changing", assignments),),
    )
    assert check.status == "ready"
    assert check.obligations[0].source == "echo(nod:a,nod:a,observer:trace)"
    assert assignments.reads == 1


@pytest.mark.parametrize(
    "template",
    (
        "ready(echo(nod:prefix$x,nod:prefix$x,observer:trace))",
        "ready(echo($xτ,$xτ,observer:trace))",
    ),
)
def test_placeholder_must_occupy_complete_expression_position(template):
    with pytest.raises(ValueError, match="must occupy a complete expression"):
        parse_theorem_statement(f"theorem token forall x:nod :: {template}")


def test_assignment_cannot_inject_placeholder_marker():
    statement = parse_theorem_statement(
        "theorem inject forall x:nod :: ready(echo($x,$x,observer:trace))"
    )
    check = check_theorem_statement(
        statement,
        (TheoremEnvironment("inject", {"x": "nod:$y"}),),
    )
    assert check.status == "blocked"
    assert "replacement must be placeholder-free text" in check.blocked[0]


class _StatefulProposition:
    expected_status = "ready"

    @property
    def template(self):
        return "echo($y,$y,observer:trace)"


def test_stateful_direct_proposition_object_is_not_a_valid_statement_graph():
    statement = TheoremStatement(
        "stateful",
        (TheoremQuantifier("x", VeyraKind.NOD),),
        (),
        (_StatefulProposition(),),
        "asserts",
    )
    check = check_theorem_statement(
        statement,
        (TheoremEnvironment("stateful", {"x": "nod:a", "y": "nod:b"}),),
    )
    assert check.status == "blocked"
    assert check.blocked == ("invalid-statement:noncanonical object graph",)


class _EvilStatus:
    def __hash__(self):
        return hash("ready")

    def __eq__(self, other):
        return other in {"ready", "blocked"}


def test_overloaded_status_equality_cannot_turn_blocked_into_ready():
    statement = TheoremStatement(
        "forged_status",
        (TheoremQuantifier("x", VeyraKind.NOD), TheoremQuantifier("y", VeyraKind.NOD)),
        (),
        (TheoremProposition(_EvilStatus(), "echo($x,$y,observer:trace)"),),
        "asserts",
    )
    check = check_theorem_statement(
        statement,
        (TheoremEnvironment("mismatch", {"x": "nod:a", "y": "nod:b"}),),
    )
    assert check.status == "blocked"
    assert check.obligations == ()
    assert check.blocked == ("invalid-statement:noncanonical object graph",)


def test_unused_extra_assignment_cannot_crash_substitution():
    statement = parse_theorem_statement(
        "theorem extra forall x:nod :: ready(echo($x,$x,observer:trace))"
    )
    check = check_theorem_statement(
        statement,
        (TheoremEnvironment("extra", {"x": "nod:a", "unused": 42}),),
    )
    assert check.status == "ready"
    assert check.obligations[0].source == "echo(nod:a,nod:a,observer:trace)"


def test_duplicate_environment_names_block_before_obligation_generation():
    statement = parse_theorem_statement(
        "theorem duplicate_env forall x:nod :: blocked(echo($x,nod:a,observer:trace))"
    )
    check = check_theorem_statement(
        statement,
        (
            TheoremEnvironment("duplicate", {"x": "nod:b"}),
            TheoremEnvironment("duplicate", {"x": "nod:c"}),
        ),
    )
    assert check.status == "blocked"
    assert check.obligations == ()
    assert check.blocked == ("duplicate-environment-name:duplicate",)


def test_theorem_language_records_blocked_obligation_diagnostics():
    rows = theorem_obligation_rows()
    blocked = [row for row in rows if row.status == "blocked"]
    assert len(blocked) == 1
    assert blocked[0].expected_status == "ready"
    assert blocked[0].actual_status == "blocked"
    assert "echo mismatch" in blocked[0].obstruction


def test_finite_obligation_evidence_cannot_enter_theorem_promotion():
    statement = parse_theorem_statement("theorem legacy forall x:nod :: ready(echo($x,$x,observer:kind))")
    ledger = check_theorem_statement(statement, default_theorem_environments()[:1])
    contract = theorem_contract_registry()["intrinsic-resonance"]
    assert ledger.evidence_class == FINITE_OBLIGATION_EVIDENCE_CLASS
    assert not contract.theorem_verifier(contract, ledger)
    with pytest.raises(ValueError, match="evidence class must be finite-obligation"):
        replace(ledger, evidence_class="kernel-proof")


def test_theorem_parser_accepts_implication_and_equivalence():
    implication = parse_theorem_statement(
        "theorem kind_sym forall x:nod,y:nod :: ready(echo($x,$y,observer:kind)) -> ready(echo($y,$x,observer:kind))"
    )
    equivalence = parse_theorem_statement(
        "theorem kind_iff forall x:nod,y:nod :: ready(echo($x,$y,observer:kind)) <-> ready(echo($y,$x,observer:kind))"
    )
    assert implication.connective == "implies"
    assert equivalence.connective == "iff"
    assert theorem_language_checklist() == (
        "theorem names",
        "forall quantifiers",
        "typed variables",
        "status propositions",
        "implication/equivalence parsing",
        "finite proof obligations",
        "blocked diagnostics",
    )
