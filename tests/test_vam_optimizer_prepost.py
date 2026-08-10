from dataclasses import asdict
from pathlib import Path

import pytest

from scripts.project_hygiene import line_limit
from vam.src.optimizer_prepost import (
    BOUNDARY,
    CLAIM,
    OVERCLAIM_TERMS,
    OptimizerPrePostWitness,
    assert_no_optimizer_prepost_overclaim_terms,
    optimizer_prepost_witness_payload,
    optimizer_prepost_witness_rows,
    optimizer_prepost_witness_summary,
)

EXPECTED_PASSES = (
    "observer-alias",
    "compress-alias",
    "compress-idempotent",
    "compress-idempotent",
    "compress-idempotent",
    "compress-idempotent",
    "dead-shadow",
)
EXPECTED_LOCAL_LAWS = (
    "observer-alias.lookup-invariant",
    "compress-alias.same-pair-local-law",
    "compress-idempotent.same-observer-local-law",
    "compress-idempotent.visible-use-observer-local-law",
    "compress-idempotent.different-observer-reject-local-law",
    "compress-idempotent.obstruction-boundary-reject-local-law",
    "dead-shadow.unused-lookup-local-law",
)
EXPECTED_PROGRAMS = (
    "observer-alias-duplicate-kind",
    "compress-alias-same-pair",
    "compress-idempotent-same-observer",
    "compress-idempotent-visible-observe-use",
    "compress-idempotent-different-observer-reject",
    "compress-idempotent-obstruction-boundary-reject",
    "dead-shadow-unused-compress",
)


def test_optimizer_prepost_rows_are_deterministic_and_ordered():
    first = optimizer_prepost_witness_rows()
    second = optimizer_prepost_witness_rows()

    assert first == second
    assert len(first) == 7
    assert [row.pass_name for row in first] == list(EXPECTED_PASSES)
    assert [row.local_law for row in first] == list(EXPECTED_LOCAL_LAWS)
    assert [row.program_name for row in first] == list(EXPECTED_PROGRAMS)
    assert all(isinstance(row, OptimizerPrePostWitness) for row in first)
    assert all(row.boundary == BOUNDARY for row in first)
    assert all(row.claim == CLAIM for row in first)


def test_optimizer_prepost_rows_are_accepted_equivalent_and_bounded():
    rows = optimizer_prepost_witness_rows()

    assert [row.accepted for row in rows] == [True, True, True, True, False, False, True]
    assert all(row.equivalence_status == "equivalent" for row in rows)
    assert all(row.precondition_status == "witnessed" for row in rows)
    assert all(row.postcondition_status == "preserved" for row in rows)
    assert [row.optimized_delta for row in rows] == [1, 1, 1, 1, 0, 0, 1]
    assert rows[0].optimizer_detail == "%r2->%r1 kind=kind"
    assert rows[1].optimizer_detail == "%r4->%r3 source=%r1 observer=%r2"
    assert rows[2].optimizer_detail.startswith("%r4->%r3 prior_source=%r1")
    assert rows[3].optimizer_detail.startswith("%r4->%r3 prior_source=%r1")
    assert rows[4].optimizer_detail == "keep %r5: observer differs source=%r4 observer=%r3 prior=%r2"
    assert rows[5].optimizer_detail == "keep %r4: candidate feeds OBSTRUCT evidence boundary"
    assert rows[6].optimizer_detail == "drop unused COMPRESS %r3"


def test_optimizer_prepost_payload_matches_rows_and_is_stable():
    rows = optimizer_prepost_witness_rows()
    payload = optimizer_prepost_witness_payload()

    assert payload == tuple(asdict(row) for row in rows)
    assert payload == optimizer_prepost_witness_payload()
    assert payload[0]["boundary"] == BOUNDARY
    assert payload[0]["claim"] == CLAIM
    assert [row["local_law"] for row in payload] == list(EXPECTED_LOCAL_LAWS)


def test_optimizer_prepost_summary_is_deterministic_and_bounded():
    summary = optimizer_prepost_witness_summary()

    assert summary == optimizer_prepost_witness_summary()
    assert summary == {
        "total_rows": 7,
        "accepted_rows": 5,
        "safe_equivalence_rows": 7,
        "local_laws": EXPECTED_LOCAL_LAWS,
        "boundary": BOUNDARY,
        "claim": CLAIM,
    }


def test_optimizer_prepost_overclaim_guard_accepts_rows_payload_and_summary():
    rows = optimizer_prepost_witness_rows()
    payload = optimizer_prepost_witness_payload()
    summary = optimizer_prepost_witness_summary()

    assert_no_optimizer_prepost_overclaim_terms(rows)
    assert_no_optimizer_prepost_overclaim_terms(payload)
    assert_no_optimizer_prepost_overclaim_terms(summary)
    for term in OVERCLAIM_TERMS:
        assert term not in str((rows, payload, summary)).lower()


def test_optimizer_prepost_overclaim_guard_rejects_out_of_boundary_text():
    payload = dict(optimizer_prepost_witness_payload()[0])
    payload["claim"] = "whole-optimizer correctness"

    with pytest.raises(ValueError, match="overclaim term present"):
        assert_no_optimizer_prepost_overclaim_terms((payload,))


def test_optimizer_prepost_module_stays_within_project_target():
    path = Path("vam/src/optimizer_prepost.py")

    assert len(path.read_text(encoding="utf-8").splitlines()) <= line_limit(path)
