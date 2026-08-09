from __future__ import annotations

import pytest

from vam.src.assembly import parse_vmasm
from vam.src.optimizer_completion import (
    CLAIM,
    UNRESOLVED_PREMISES,
    optimizer_corpus_skeleton,
    optimizer_theorem_skeleton,
    vamd_optimized_emission_policy,
    visible_use_guard,
)
from vam.src.model import Instruction


def _same_observer_program():
    return parse_vmasm(
        '''
REZ %r1, "phase"
OBSERVER %r2, "kind"
COMPRESS %r3, %r1, %r2
COMPRESS %r4, %r3, %r2
OBSERVE %r5, %r4, %r2
ECHO %r6, %r4, %r5, %r2
CERT %r7, "visible", %r6, "same-observer root"
'''
    )


@pytest.mark.parametrize(
    ("tail", "reason"),
    (
        ('OBSERVER %r8, "length"\nOBSERVE %r9, %r4, %r8', "not a same-observer"),
        ('CERT %r9, "direct", %r4, "unsafe"', "feeds CERT"),
        ('OBSTRUCT %r9, "unsafe", %r4', "OBSTRUCT evidence boundary"),
    ),
)
def test_visible_use_guard_rejects_foreign_and_evidence_boundary_uses(tail, reason):
    base = '''
REZ %r1, "phase"
OBSERVER %r2, "kind"
COMPRESS %r3, %r1, %r2
COMPRESS %r4, %r3, %r2
'''

    row = visible_use_guard(parse_vmasm(base + tail), "%r4", "%r2", after_index=3)

    assert row.status == "guard-rejected"
    assert reason in " ".join(row.reasons)


def test_visible_use_guard_accepts_only_same_observer_visible_positions():
    row = visible_use_guard(_same_observer_program(), "%r4", "%r2", after_index=3)

    assert row.status == "guard-satisfied"
    assert row.uses == 2
    assert row.reasons == ()


def test_visible_use_guard_rejects_redefinition_and_dead_candidate():
    duplicate = parse_vmasm(
        'REZ %r1, "a"\nREZ %r1, "b"\nOBSERVER %r2, "kind"\nOBSERVE %r3, %r1, %r2'
    )
    dead = parse_vmasm('REZ %r1, "a"')

    duplicate_row = visible_use_guard(duplicate, "%r1", "%r2", after_index=1)
    dead_row = visible_use_guard(dead, "%r1", "%r2", after_index=0)

    assert "definitions=2" in duplicate_row.reasons[0]
    assert dead_row.status == "guard-rejected"
    assert "no visible" in dead_row.reasons[-1]


def test_visible_use_guard_cannot_skip_evidence_with_forged_after_index():
    program = parse_vmasm(
        '''
REZ %r1, "candidate"
CERT %r3, "direct", %r1, "unsafe"
OBSERVE %r4, %r1, %r2
'''
    )

    row = visible_use_guard(program, "%r1", "%r2", after_index=1)

    assert row.status == "guard-rejected"
    assert row.uses == 2
    assert "does not match validated definition index=0" in " ".join(row.reasons)
    assert "feeds CERT" in " ".join(row.reasons)


@pytest.mark.parametrize(
    ("program", "candidate", "observer", "reason"),
    (
        ('REZ %r1, "candidate"\nOBSERVER %r2, "kind"\nOBSERVE %r3, %r1, %r2', "%r1", "%r2", "expected COMPRESS"),
        ('REZ %r1, "candidate"\nCOMPRESS %r3, %r1, %r2\nOBSERVE %r4, %r3, %r2', "%r3", "%r2", "observer definitions=0"),
        ('REZ %r1, "candidate"\nOBSERVER %r2, "kind"\nCOMPRESS %r3, %r1, %r2\nOBSERVE %r4, %r3, %r2', "%r3", "%r8", "does not match candidate observer"),
        ('REZ %r1, "candidate"\nOBSERVER %r2, "kind"\nCOMPRESS %r3, %r1, %r2\nOBSERVER %r2, "length"\nOBSERVE %r4, %r3, %r2', "%r3", "%r2", "observer definitions=2"),
    ),
)
def test_visible_use_guard_derives_candidate_and_observer_provenance(
    program, candidate, observer, reason,
):
    row = visible_use_guard(parse_vmasm(program), candidate, observer)

    assert row.status == "guard-rejected"
    assert reason in " ".join(row.reasons)


@pytest.mark.parametrize(
    "instruction",
    (
        Instruction("OBSERVE", ("%r2", "%r1"), 2),
        Instruction("UNKNOWN", ("%r2", "%r1"), 2),
        Instruction("observe", ("%r2", "%r1", "%r3"), 2),
    ),
)
def test_visible_use_guard_rejects_malformed_instruction_rows(instruction):
    row = visible_use_guard(
        [Instruction("REZ", ("%r1", "candidate"), 1), instruction], "%r1", "%r2"
    )

    assert row.status == "guard-rejected"
    assert row.uses == 0
    assert "malformed instruction row" in " ".join(row.reasons)


def test_whole_optimizer_skeleton_populates_evidence_but_stays_open():
    row = optimizer_theorem_skeleton("same-observer", _same_observer_program())

    assert row.equivalence_status == "equivalent"
    assert row.executable_premises_hold is True
    assert row.theorem_status == "open"
    assert row.proof_complete is False
    assert row.claim == CLAIM
    assert row.unresolved_premises == UNRESOLVED_PREMISES
    assert tuple(name for name, _ in row.pass_rows) == (
        "observer-alias",
        "compress-alias",
        "compress-idempotent",
        "dead-shadow",
    )


def test_optimizer_corpus_skeleton_is_deterministic_and_names_are_unique():
    program = _same_observer_program()
    first = optimizer_corpus_skeleton((("a", program), ("b", program)))
    second = optimizer_corpus_skeleton((("a", program), ("b", program)))

    assert first == second
    assert all(row.proof_complete is False for row in first)
    with pytest.raises(ValueError, match="names must be unique"):
        optimizer_corpus_skeleton((("a", program), ("a", program)))


def test_vamd_optimized_emission_is_explicitly_blocked_until_native_gates_exist():
    policy = vamd_optimized_emission_policy()

    assert policy.requested is True
    assert policy.allowed is False
    assert policy.status == "blocked"
    assert "not integrated" in policy.obstruction
    assert len(policy.required_gates) == 4
    assert "encoder" in policy.required_gates[0]


def test_optimizer_completion_rejects_open_or_oversized_program_sources():
    with pytest.raises(ValueError, match="bounded exact sequence"):
        visible_use_guard(iter(_same_observer_program()), "%r4", "%r2")
    oversized = [Instruction("REZ", (f"%r{index}", "x"), index) for index in range(4097)]
    with pytest.raises(ValueError, match="bounded exact sequence"):
        optimizer_theorem_skeleton("oversized", oversized)
    with pytest.raises(ValueError, match="exact instructions"):
        visible_use_guard([object()], "%r1", "%r2")  # type: ignore[list-item]
