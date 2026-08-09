from vam.src import optimize, parse_vmasm
from vam.src.optimizer_witness import CLAIM, optimizer_witness_ledger, stable_digest

BANNED_STATUS_WORDS = ("proof-grade", "complete", "verified theorem")


def _accepted_program():
    return parse_vmasm('''
REZ %r1, "phase"
NOD %r2, %r1, "a"
NOD %r3, %r1, "b"
TACT %r4, %r2, %r3, "step"
BREATH %r5, %r4
MODE %r6, %r5
OBSERVER %r7, "kind"
COMPRESS %r8, %r6, %r7
COMPRESS %r9, %r6, %r7
ECHO %r10, %r8, %r9, %r7
CERT %r11, "compressed-kind", %r10, "same compressed witness"
''')


def _rejected_obstruction_program():
    return parse_vmasm('''
REZ %r1, "phase"
OBSERVER %r2, "kind"
OBSERVER %r3, "kind"
COMPRESS %r4, %r1, %r1
COMPRESS %r5, %r1, %r1
OBSERVE %r6, %r1, %r1
ECHO %r7, %r4, %r5, %r3
CERT %r8, "obstruction-case", %r6, "non-echo evidence"
OBSTRUCT %r9, "manual-after-obstruction", %r4
''')


def test_optimizer_witness_ledger_is_deterministic_twice():
    program = _accepted_program()

    first = optimizer_witness_ledger(program)
    second = optimizer_witness_ledger(program)

    assert first == second
    assert len(first["ledger_digest"]) == 64
    assert first["ledger_digest"] == stable_digest({k: v for k, v in first.items() if k != "ledger_digest"})
    assert first["boundary"] == "bounded-witness-ledger"
    assert first["claim"] == CLAIM
    assert first["status"] == "bounded-regression-match"


def test_optimizer_witness_digest_fields_match_payload_sections():
    ledger = optimizer_witness_ledger(_accepted_program())
    digests = ledger["digests"]

    assert digests["original_instruction_rows"] == stable_digest(ledger["original_instruction_rows"])
    assert digests["optimized_instruction_rows"] == stable_digest(ledger["optimized_instruction_rows"])
    assert digests["optimizer_rows"] == stable_digest(ledger["optimizer_rows"])
    assert digests["equivalence_summary_checks"] == stable_digest(ledger["equivalence_summary"])
    assert digests["semantic_core_report"] == stable_digest(ledger["semantic_core_report"])


def test_optimizer_witness_preserves_accepted_and_rejected_optimizer_rows():
    program = _rejected_obstruction_program()
    report = optimize(program)
    ledger = optimizer_witness_ledger(program)

    expected_accepted = [row.detail for row in report.accepted_rows]
    expected_rejected = [row.detail for row in report.rejected_rows]
    actual_accepted = [row["detail"] for row in ledger["optimizer_rows"]["accepted"]]
    actual_rejected = [row["detail"] for row in ledger["optimizer_rows"]["rejected"]]

    assert actual_accepted == expected_accepted
    assert actual_rejected == expected_rejected
    assert actual_accepted
    assert actual_rejected
    assert any("obstruction" in detail for detail in actual_rejected)


def test_optimizer_witness_includes_bounded_obligation_ledger():
    ledger = optimizer_witness_ledger(_rejected_obstruction_program())
    obligations = ledger["optimizer_obligation_ledger"]

    assert obligations["boundary"] == "proof-obligation-ledger"
    assert obligations["claim"] == "obligation-map-not-proof"
    assert {row["pass_name"] for row in obligations["rows"]} == {
        "observer-alias",
        "compress-alias",
        "compress-idempotent",
        "dead-shadow",
    }
    assert any(row["coverage_status"] == "rejected-covered" for row in obligations["coverage"])
    assert ledger["digests"]["optimizer_obligation_ledger"] == stable_digest(obligations)


def test_optimizer_witness_includes_obstruction_and_rejected_certificate_case():
    ledger = optimizer_witness_ledger(_rejected_obstruction_program())
    original_core = ledger["semantic_core_report"]["original"]
    optimized_core = ledger["semantic_core_report"]["optimized"]

    assert original_core["obstructions"]
    assert optimized_core["obstructions"]
    assert original_core["registers"]["%r8"]["data"]["accepted"] is False
    assert optimized_core["registers"]["%r8"]["data"]["accepted"] is False
    assert ledger["equivalence_summary"]["status"] == "equivalent"
    assert ledger["equivalence_summary"]["checks"]


def test_optimizer_witness_positive_statuses_do_not_overclaim():
    ledger = optimizer_witness_ledger(_accepted_program())
    status_text = "\n".join(_status_values(ledger)).lower()

    for word in BANNED_STATUS_WORDS:
        assert word not in status_text


def _status_values(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"status", "verdict", "claim", "boundary"}:
                yield str(item)
            yield from _status_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _status_values(item)
