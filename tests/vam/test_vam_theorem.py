from collections.abc import Iterator, Mapping

from src.core.language import VeyraKind
from src.core.theorem_language import (
    TheoremEnvironment,
    TheoremProposition,
    TheoremQuantifier,
    TheoremStatement,
    default_theorem_environments,
    parse_theorem_statement,
)
from vam.src.theorem import lower_theorem_source, lower_theorem_statement


class ExistsQuantifier:
    name = "x"
    kind = "nod"
    quantifier = "exists"


def test_ready_finite_theorem_lowers_to_verified_vam_record_with_cases():
    source = "theorem echo_kind_reflexive forall x:nod :: ready(echo($x,$x,observer:kind)) -> ready(echo($x,$x,observer:kind))"
    record = lower_theorem_source(source, default_theorem_environments()[:1], module="tests")
    obj = record.as_vam_object()
    case = record.finite_cases[0]

    assert record.id == "vam:tests:echo_kind_reflexive"
    assert record.proof_status == "verified"
    assert len(record.obligations) == 2
    assert {row.status for row in record.obligations} == {"verified"}
    assert record.binders == ({"name": "x", "kind": "nod", "quantifier": "forall"},)
    assert case.status == "verified"
    assert case.quantifiers == ({"name": "x", "kind": "nod", "quantifier": "forall", "value": "nod:a", "status": "bound"},)
    assert len(case.assumptions) == 1
    assert len(case.conclusions) == 1
    assert obj.kind == "Theorem"
    assert obj.field("proof_status") == "verified"
    assert obj.field("finite_cases")[0]["status"] == "verified"


def test_missing_environment_has_no_executable_cases_and_stays_open():
    statement = parse_theorem_statement("theorem needs_y forall x:nod,y:nod :: ready(echo($x,$y,observer:kind))")
    env = TheoremEnvironment("missing-y", {"x": "nod:a"})
    record = lower_theorem_statement(statement, (env,), requested_status="verified")

    assert record.proof_status == "open"
    assert record.finite_cases == ()
    assert record.environments[0].status == "open"
    assert record.obligations[0].role == "environment"
    assert record.obligations[0].category == "wf.quantifier"
    assert "missing $y" in record.obligations[0].obstruction
    assert any("no executable finite obligation cases" in item for item in record.diagnostics)


def test_false_expected_status_blocks_the_finite_case_not_verified():
    source = "theorem trace_should_pass forall x:nod,y:nod :: ready(echo($x,$y,observer:trace))"
    record = lower_theorem_source(source, (TheoremEnvironment("mismatch", {"x": "nod:a", "y": "nod:b"}),), requested_status="verified")

    assert record.proof_status == "blocked"
    assert record.finite_cases[0].status == "blocked"
    assert record.obligations[0].status == "blocked"
    assert record.obligations[0].expected_status == "ready"
    assert record.obligations[0].actual_status == "blocked"
    assert "echo mismatch" in record.finite_cases[0].obstruction


def test_opaque_executable_semantics_block_without_proof_assistant_claim():
    source = "theorem unknown_observer forall x:nod :: unknown(echo($x,$x,observer:aura))"
    record = lower_theorem_source(source, (TheoremEnvironment("nod-a", {"x": "nod:a"}),))

    assert record.proof_status == "blocked"
    assert record.finite_cases[0].status == "blocked"
    assert record.obligations[0].status == "blocked"
    assert record.obligations[0].category == "semantics.opaque"
    assert record.obligations[0].actual_status == "unknown"
    assert any("not proof-assistant semantics" in item for item in record.diagnostics)
    assert any("non-proof boundary" in item for item in record.diagnostics)


def test_unsupported_quantifier_shape_is_open_with_no_executable_cases():
    statement = object.__new__(TheoremStatement)
    object.__setattr__(statement, "name", "exists_boundary")
    object.__setattr__(statement, "quantifiers", (ExistsQuantifier(),))
    object.__setattr__(statement, "assumptions", ())
    object.__setattr__(statement, "conclusions", (TheoremProposition("ready", "echo($x,$x,observer:kind)"),))
    object.__setattr__(statement, "connective", "asserts")
    record = lower_theorem_statement(statement, (TheoremEnvironment("nod-a", {"x": "nod:a"}),), requested_status="verified")

    assert record.proof_status == "open"
    assert record.finite_cases == ()
    assert record.binders == ({"name": "x", "kind": "nod", "quantifier": "exists"},)
    assert record.obligations[0].role == "quantifier"
    assert record.obligations[0].status == "open"
    assert "unsupported quantifier shape: exists" in record.obligations[0].obstruction


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


class _StatefulProposition:
    expected_status = "ready"

    @property
    def template(self):
        return "echo($y,$y,observer:trace)"


class _EvilStatus:
    def __hash__(self):
        return hash("ready")

    def __eq__(self, other):
        return other in {"ready", "blocked"}


def test_vam_uses_one_environment_snapshot_for_check_and_carriers():
    statement = parse_theorem_statement(
        "theorem stable forall x:nod :: ready(echo($x,$x,observer:trace))"
    )
    assignments = _ChangingAssignments()
    record = lower_theorem_statement(
        statement,
        (TheoremEnvironment("changing", assignments),),
        requested_status="verified",
    )
    assert record.proof_status == "verified"
    assert record.obligations[0].source == "echo(nod:a,nod:a,observer:trace)"
    assert record.finite_cases[0].quantifiers[0]["value"] == "nod:a"
    assert record.environments[0].as_dict()["assignments"] == {"x": "nod:a"}
    assert assignments.reads == 1


def test_noncanonical_direct_statement_never_lowers_as_verified():
    statement = TheoremStatement(
        "forged",
        (TheoremQuantifier("x", VeyraKind.NOD),),
        (),
        (_StatefulProposition(),),
        "asserts",
    )
    record = lower_theorem_statement(
        statement,
        (TheoremEnvironment("forged", {"x": "nod:a", "y": "nod:b"}),),
        requested_status="verified",
    )
    assert record.proof_status == "open"
    assert record.finite_cases == ()


def test_overloaded_expected_status_never_lowers_as_verified():
    statement = TheoremStatement(
        "forged_status",
        (TheoremQuantifier("x", VeyraKind.NOD), TheoremQuantifier("y", VeyraKind.NOD)),
        (),
        (TheoremProposition(_EvilStatus(), "echo($x,$y,observer:trace)"),),
        "asserts",
    )
    record = lower_theorem_statement(
        statement,
        (TheoremEnvironment("mismatch", {"x": "nod:a", "y": "nod:b"}),),
        requested_status="verified",
    )
    assert record.proof_status == "open"
    assert record.finite_cases == ()


def test_duplicate_environment_names_never_merge_into_verified_cases():
    statement = parse_theorem_statement(
        "theorem duplicate_env forall x:nod :: blocked(echo($x,nod:a,observer:trace))"
    )
    record = lower_theorem_statement(
        statement,
        (
            TheoremEnvironment("duplicate", {"x": "nod:b"}),
            TheoremEnvironment("duplicate", {"x": "nod:c"}),
        ),
        requested_status="verified",
    )
    assert record.proof_status == "open"
    assert record.finite_cases == ()
