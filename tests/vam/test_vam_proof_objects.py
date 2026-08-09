from vam.src.proof_objects import (
    NO_OVERCLAIM_BOUNDARY,
    ProofAtom,
    ProofConjunction,
    proof_conjunction_from_cases,
    proof_conjunction_from_shell_carrier,
    proof_object_json,
)


def test_all_verified_conjunction_from_finite_cases():
    cases = (
        {"id": "case:a", "environment": "env-a", "status": "verified"},
        {"id": "case:b", "environment": "env-b", "status": "verified"},
    )

    conjunction = proof_conjunction_from_cases(cases, id="thm:finite")

    assert conjunction.status == "verified"
    assert [child.status for child in conjunction.children] == ["verified", "verified"]
    assert conjunction.accepted_certificate is False
    assert "not proof-assistant proof" in conjunction.as_dict()["boundary"]


def test_blocked_child_dominates_conjunction_status():
    conjunction = ProofConjunction(
        "manual:block",
        (
            ProofAtom("a", "ready row", "finite_theorem_case", "verified"),
            ProofAtom("b", "blocked row", "finite_theorem_case", "blocked", obstruction="echo mismatch"),
        ),
    )

    assert conjunction.status == "blocked"
    assert conjunction.as_dict()["children"][1]["status"] == "blocked"
    assert conjunction.as_dict()["children"][1]["obstruction"] == "echo mismatch"


def test_open_child_keeps_conjunction_open_without_overclaim():
    conjunction = proof_conjunction_from_cases(
        (
            {"id": "case:a", "environment": "env-a", "status": "verified"},
            {"id": "case:b", "environment": "env-b", "status": "conjectural"},
        ),
        id="thm:open",
    )

    assert conjunction.status == "open"
    assert [child.status for child in conjunction.children] == ["verified", "open"]
    assert "accepted VAM certificate" in proof_object_json(conjunction)


def test_shell_boundary_rejects_certificate_claim_without_leaking_claim_text():
    carrier = {
        "source": "shell(echo(nod:a,nod:a,observer:kind))",
        "boundary": "finite shell conjunction carrier only; no VAM certificate claim",
        "certificate_claim": "must-not-leak-into-boundary",
        "rows": ({"source": "echo(nod:a,nod:a,observer:kind)", "status": "transported", "register": "r1"},),
    }

    conjunction = proof_conjunction_from_shell_carrier(carrier)
    data = conjunction.as_dict()

    assert conjunction.status == "blocked"
    assert data["certificate_claim_rejected"] is True
    assert data["accepted_certificate"] is False
    assert NO_OVERCLAIM_BOUNDARY in data["boundary"]
    assert "external certificate claim rejected" in data["boundary"]
    assert "must-not-leak-into-boundary" not in data["boundary"]
    assert data["children"][0]["status"] == "blocked"
