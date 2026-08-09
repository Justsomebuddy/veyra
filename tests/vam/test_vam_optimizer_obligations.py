from vam.src import optimize, parse_vmasm
from vam.src.optimizer_obligations import (
    BOUNDARY,
    CLAIM,
    OVERCLAIM_TERMS,
    assert_no_overclaim_terms,
    optimizer_obligation_coverage,
    optimizer_obligation_payload,
    optimizer_obligation_rows,
    optimizer_obligation_summary,
)


def _observer_alias_program():
    return parse_vmasm('''
OBSERVER %r1, "kind"
OBSERVER %r2, "kind"
REZ %r3, "phase"
COMPRESS %r4, %r3, %r1
ECHO %r5, %r4, %r4, %r2
''')


def _compress_alias_program():
    return parse_vmasm('''
REZ %r1, "phase"
OBSERVER %r2, "kind"
COMPRESS %r3, %r1, %r2
COMPRESS %r4, %r1, %r2
ECHO %r5, %r3, %r4, %r2
''')


def _compress_idempotent_program():
    return parse_vmasm('''
REZ %r1, "phase"
OBSERVER %r2, "kind"
COMPRESS %r3, %r1, %r2
COMPRESS %r4, %r3, %r2
ECHO %r5, %r3, %r4, %r2
''')


def _dead_shadow_program():
    return parse_vmasm('''
REZ %r1, "phase"
OBSERVER %r2, "kind"
COMPRESS %r3, %r1, %r2
''')


def _dead_shadow_rejected_program():
    return parse_vmasm('''
REZ %r1, "phase"
COMPRESS %r2, %r1, %r1
''')


def test_optimizer_obligation_rows_are_deterministic_and_cover_current_passes():
    first = optimizer_obligation_rows()
    second = optimizer_obligation_rows()

    assert first == second
    assert [row.pass_name for row in first] == [
        "observer-alias",
        "compress-alias",
        "compress-idempotent",
        "dead-shadow",
    ]
    assert all(row.boundary == BOUNDARY for row in first)
    assert all(row.claim == CLAIM for row in first)
    assert optimizer_obligation_payload()[0]["obligation_id"] == "observer-alias-boundary-v1"
    assert_no_overclaim_terms(first)


def test_optimizer_obligation_coverage_maps_all_current_pass_families():
    programs = (
        _observer_alias_program(),
        _compress_alias_program(),
        _compress_idempotent_program(),
        _dead_shadow_program(),
    )

    covered = set()
    for program in programs:
        coverage = optimizer_obligation_coverage(optimize(program).rows)
        covered.update(row.pass_name for row in coverage)
        assert coverage
        assert all(row.coverage_status == "accepted-covered" for row in coverage)

    assert covered == {row.pass_name for row in optimizer_obligation_rows()}


def test_optimizer_obligation_coverage_maps_rejected_obstruction_rows():
    report = optimize(_dead_shadow_rejected_program())
    coverage = optimizer_obligation_coverage(report.rows)

    assert any(row.pass_name == "dead-shadow" for row in coverage)
    rejected = [row for row in coverage if row.accepted is False]
    assert rejected
    assert rejected[0].coverage_status == "rejected-covered"
    assert "obstruction" in rejected[0].detail
    assert rejected[0].obligation_id == "dead-shadow-boundary-v1"


def test_optimizer_obligation_summary_and_rows_do_not_overclaim():
    report = optimize(_compress_idempotent_program())
    coverage = optimizer_obligation_coverage(report.rows)
    summary = optimizer_obligation_summary(report.rows)
    text = "\n".join(
        [str(summary)]
        + [str(row) for row in optimizer_obligation_rows()]
        + [str(row) for row in coverage]
    ).lower()

    assert summary["observer-alias"] == ()
    assert summary["compress-idempotent"] == ("accepted-covered",)
    for term in OVERCLAIM_TERMS:
        assert term not in text
    assert_no_overclaim_terms(coverage)
