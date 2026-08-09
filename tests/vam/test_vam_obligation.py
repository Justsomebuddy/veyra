import json

from src.core.theorem_language import TheoremEnvironment, default_theorem_environments
from vam.src.obligation import (
    NO_CERTIFICATE_NOTE,
    VamObligationRow,
    obligation_instructions,
    obligation_json,
    obligation_batch_is_transport_only,
    obligation_rows_from_obligations,
    obligation_rows_from_theorem,
    obligation_status,
)
from vam.src.theorem import lower_theorem_source


def test_verified_theorem_produces_verified_finite_obligation_ir_rows():
    source = "theorem echo_kind_reflexive forall x:nod :: ready(echo($x,$x,observer:kind))"
    record = lower_theorem_source(source, default_theorem_environments()[:2], module="tests")
    rows = obligation_rows_from_theorem(record)
    summary = obligation_status(rows)
    instructions = obligation_instructions(rows)

    assert len(rows) == 2
    assert {row.status for row in rows} == {"verified"}
    assert summary.as_dict() == {
        "total": 2,
        "verified": 2,
        "open": 0,
        "blocked": 0,
        "all_verified": True,
        "accepted_certificate": False,
        "no_overclaim_note": NO_CERTIFICATE_NOTE,
    }
    assert instructions[0].op == "OBLIGATION"
    assert instructions[0].args[:6] == (
        "echo_kind_reflexive:nod-a:conclusion:0",
        "echo_kind_reflexive",
        "nod-a",
        "conclusion",
        "proof.finite",
        "verified",
    )


def test_blocked_and_open_obligations_remain_visible_in_ir():
    blocked = lower_theorem_source(
        "theorem trace_should_pass forall x:nod,y:nod :: ready(echo($x,$y,observer:trace))",
        (TheoremEnvironment("mismatch", {"x": "nod:a", "y": "nod:b"}),),
        requested_status="verified",
    )
    open_record = lower_theorem_source(
        "theorem needs_y forall x:nod,y:nod :: ready(echo($x,$y,observer:kind))",
        (TheoremEnvironment("missing-y", {"x": "nod:a"}),),
        requested_status="verified",
    )

    blocked_rows = obligation_rows_from_theorem(blocked)
    open_rows = obligation_rows_from_theorem(open_record)

    assert blocked.proof_status == "blocked"
    assert blocked_rows[0].status == "blocked"
    assert blocked_rows[0].category == "boundary.no_overclaim"
    assert "echo mismatch" in blocked_rows[0].obstruction
    assert open_record.proof_status == "open"
    assert open_rows[0].status == "open"
    assert open_rows[0].category == "wf.quantifier"
    assert "missing $y" in open_rows[0].obstruction


def test_obligation_dict_and_json_ordering_are_stable():
    source = "theorem echo_kind_reflexive forall x:nod :: ready(echo($x,$x,observer:kind))"
    record = lower_theorem_source(source, default_theorem_environments()[:1], module="tests")
    rows = obligation_rows_from_theorem(record)
    first = rows[0].as_dict()
    encoded = obligation_json(rows)

    assert list(first) == [
        "version",
        "index",
        "op",
        "id",
        "theorem",
        "environment",
        "role",
        "category",
        "source",
        "expected_status",
        "actual_status",
        "status",
        "theorem_proof_status",
        "trust_boundary",
        "obstruction",
        "accepted_certificate",
        "no_overclaim_note",
    ]
    assert encoded == obligation_json(rows)
    assert json.loads(encoded)[0] == first


def test_obligation_ir_alone_never_implies_accepted_certificate():
    source = "theorem echo_kind_reflexive forall x:nod :: ready(echo($x,$x,observer:kind))"
    record = lower_theorem_source(source, default_theorem_environments()[:1], module="tests")
    rows = obligation_rows_from_theorem(record)
    direct_rows = obligation_rows_from_obligations(record.obligations)

    assert record.proof_status == "verified"
    assert rows[0].accepted_certificate is False
    assert rows[0].as_dict()["accepted_certificate"] is False
    assert rows[0].as_dict()["no_overclaim_note"] == NO_CERTIFICATE_NOTE
    assert obligation_status(rows).accepted_certificate is False
    assert direct_rows[0].theorem_proof_status == "unknown"
    assert direct_rows[0].accepted_certificate is False


def test_transport_only_gate_accepts_mixed_verified_open_blocked_rows_without_certificates():
    rows = (
        VamObligationRow(
            index=0,
            id="mixed:verified",
            theorem="mixed",
            environment="env-a",
            role="conclusion",
            category="proof.finite",
            source="source-a",
            expected_status="verified",
            actual_status="verified",
            status="verified",
            theorem_proof_status="unknown",
            trust_boundary="",
        ),
        VamObligationRow(
            index=1,
            id="mixed:open",
            theorem="mixed",
            environment="env-b",
            role="premise",
            category="wf.quantifier",
            source="source-b",
            expected_status="open",
            actual_status="open",
            status="open",
            theorem_proof_status="unknown",
            trust_boundary="",
        ),
        VamObligationRow(
            index=2,
            id="mixed:blocked",
            theorem="mixed",
            environment="env-c",
            role="premise",
            category="boundary.no_overclaim",
            source="source-c",
            expected_status="blocked",
            actual_status="blocked",
            status="blocked",
            theorem_proof_status="unknown",
            trust_boundary="",
            obstruction="transport gate blocked",
        ),
    )

    summary = obligation_status(rows)

    assert summary.as_dict() == {
        "total": 3,
        "verified": 1,
        "open": 1,
        "blocked": 1,
        "all_verified": False,
        "accepted_certificate": False,
        "no_overclaim_note": NO_CERTIFICATE_NOTE,
    }
    assert obligation_batch_is_transport_only(rows) is True


def test_transport_only_gate_rejects_batches_with_accepted_certificates():
    rows = (
        VamObligationRow(
            index=0,
            id="certified:verified",
            theorem="mixed",
            environment="env-a",
            role="conclusion",
            category="proof.finite",
            source="source-a",
            expected_status="verified",
            actual_status="verified",
            status="verified",
            theorem_proof_status="unknown",
            trust_boundary="",
            accepted_certificate=True,
        ),
    )

    summary = obligation_status(rows)

    assert summary.accepted_certificate is True
    assert obligation_batch_is_transport_only(rows) is False
