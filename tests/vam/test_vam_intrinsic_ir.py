"""R12.2 tests for the isolated typed intrinsic VAM sidecar IR."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from hashlib import sha256
import json
from pathlib import Path

import pytest

import vam.src as legacy_vam
from vam.src.assembly import parse_vmasm
from vam.src.bytecode import MAGIC, VERSION, VamBytecodeError, encode_vmbc
from vam.src.dense import DENSE_MAGIC, DENSE_VERSION, encode_dense
from vam.src.interpreter import execute
from vam.src.intrinsic_ir import (
    INTRINSIC_IR_SCHEMA,
    MAX_OBSTRUCTION_PATH,
    MAX_OBSTRUCTIONS,
    MAX_RECURRENCE_TACTS,
    IntrinsicIRError,
    crest_mark_ir,
    intrinsic_ir_data,
    pulse_ir,
    silence_ir,
    validate_intrinsic_ir,
)
from vam.src.intrinsic_ir_types import (
    IntrinsicAnchorIR,
    IntrinsicBlockedIR,
    IntrinsicDomainBlockedIR,
    IntrinsicEchoIR,
    IntrinsicMarkIR,
    IntrinsicMarkValueIR,
    IntrinsicMismatchIR,
    IntrinsicObstructionCodeIR,
    IntrinsicObstructionIR,
    IntrinsicPairValueIR,
    IntrinsicPathStepIR,
    IntrinsicReadyIR,
    IntrinsicRecurrenceIR,
    IntrinsicRecurrenceValueIR,
    IntrinsicTactIR,
)
from vam.src.model import Instruction
from vam.src.opcodes import opcode_rows
from vam.src.report import PROFILE, canonical_report
from src.core.paths import PROJECT_ROOT


def _obstruction(*path: IntrinsicPathStepIR) -> IntrinsicObstructionIR:
    return IntrinsicObstructionIR(IntrinsicObstructionCodeIR.TAIL_OF_SILENCE, path)


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def test_anchor_silence_pulse_and_mark_have_exact_diagnostic_shapes():
    silence = silence_ir()
    pulse = pulse_ir(silence)
    assert intrinsic_ir_data(IntrinsicAnchorIR()) == {
        "schema": INTRINSIC_IR_SCHEMA,
        "value": {"tag": "anchor", "name": "intrinsic-origin", "mark": "intrinsic-origin"},
    }
    assert intrinsic_ir_data(silence)["value"] == {
        "tag": "recurrence",
        "tacts": [],
        "anchor": {"tag": "anchor", "name": "intrinsic-origin", "mark": "intrinsic-origin"},
    }
    assert intrinsic_ir_data(pulse)["value"] == {
        "tag": "recurrence",
        "tacts": [
            {
                "tag": "tact",
                "start": "intrinsic-origin",
                "end": "intrinsic-origin",
                "mark": "intrinsic-successor",
            }
        ],
        "anchor": None,
    }
    assert crest_mark_ir(silence) is IntrinsicMarkIR.SILENT
    assert crest_mark_ir(pulse) is IntrinsicMarkIR.PULSE
    assert intrinsic_ir_data(IntrinsicMarkIR.PULSE)["value"] == {"tag": "mark", "value": "pulse"}


def test_exact_image_invariant_and_tuple_containers_fail_closed():
    invalid = (
        IntrinsicRecurrenceIR((), None),
        IntrinsicRecurrenceIR((IntrinsicTactIR(),), IntrinsicAnchorIR()),
        IntrinsicRecurrenceIR([], IntrinsicAnchorIR()),  # type: ignore[arg-type]
        IntrinsicRecurrenceIR(("tact",), None),  # type: ignore[arg-type]
    )
    for value in invalid:
        with pytest.raises(IntrinsicIRError, match="invalid-recurrence-ir"):
            validate_intrinsic_ir(value)


def test_frozen_types_and_hostile_subclasses_are_rejected():
    anchor = IntrinsicAnchorIR()
    with pytest.raises((FrozenInstanceError, TypeError)):
        anchor.extra = "mutable"  # type: ignore[attr-defined]
    with pytest.raises(AttributeError):
        object.__setattr__(anchor, "evil", anchor)

    mutated = silence_ir()
    object.__setattr__(mutated, "tacts", [])
    with pytest.raises(IntrinsicIRError, match="invalid-recurrence-ir"):
        validate_intrinsic_ir(mutated)

    class AnchorSubclass(IntrinsicAnchorIR):
        pass

    with pytest.raises(IntrinsicIRError, match="invalid-intrinsic-node"):
        validate_intrinsic_ir(AnchorSubclass())
    with pytest.raises(IntrinsicIRError, match="invalid-intrinsic-node"):
        validate_intrinsic_ir({"tag": "anchor"})
    with pytest.raises(IntrinsicIRError, match="pulse-tail-not-recurrence"):
        pulse_ir(IntrinsicAnchorIR())


def test_ready_blocked_and_all_three_echo_outcomes_are_disjoint():
    recurrence = IntrinsicRecurrenceValueIR(pulse_ir(silence_ir()))
    silent = IntrinsicMarkValueIR(IntrinsicMarkIR.SILENT)
    pulsed = IntrinsicMarkValueIR(IntrinsicMarkIR.PULSE)
    pair = IntrinsicPairValueIR(recurrence, pulsed)
    obstruction = _obstruction(IntrinsicPathStepIR.APPLY_TAIL)
    values = (
        IntrinsicReadyIR(pair),
        IntrinsicBlockedIR((obstruction,)),
        IntrinsicEchoIR(pair),
        IntrinsicMismatchIR(silent, pulsed),
        IntrinsicDomainBlockedIR((obstruction,), ()),
    )
    assert [intrinsic_ir_data(value)["value"]["tag"] for value in values] == [
        "ready",
        "blocked",
        "echo",
        "mismatch",
        "domain-blocked",
    ]
    assert intrinsic_ir_data(pair)["value"]["left"]["tag"] == "recurrence-value"
    assert intrinsic_ir_data(pair)["value"]["right"]["tag"] == "mark-value"


def test_mismatch_requires_distinct_responses_of_one_kind():
    silent = IntrinsicMarkValueIR(IntrinsicMarkIR.SILENT)
    pulsed = IntrinsicMarkValueIR(IntrinsicMarkIR.PULSE)
    recurrence = IntrinsicRecurrenceValueIR(silence_ir())
    assert intrinsic_ir_data(IntrinsicMismatchIR(silent, pulsed))["value"]["tag"] == "mismatch"
    with pytest.raises(IntrinsicIRError, match="invalid-mismatch"):
        intrinsic_ir_data(IntrinsicMismatchIR(silent, silent))
    with pytest.raises(IntrinsicIRError, match="invalid-mismatch-kind"):
        intrinsic_ir_data(IntrinsicMismatchIR(silent, recurrence))


def test_obstruction_paths_follow_closed_outer_to_inner_r11_grammar():
    nested = _obstruction(
        IntrinsicPathStepIR.PAIR_LEFT,
        IntrinsicPathStepIR.APPLY_CREST,
        IntrinsicPathStepIR.APPLY_TAIL,
    )
    assert intrinsic_ir_data(nested)["value"]["path"] == [
        "pair-left",
        "apply-crest",
        "apply-tail",
    ]
    invalid = (
        IntrinsicObstructionIR(IntrinsicObstructionCodeIR.TAIL_OF_SILENCE, ()),
        _obstruction(IntrinsicPathStepIR.APPLY_CREST),
        _obstruction(
            IntrinsicPathStepIR.APPLY_TAIL,
            IntrinsicPathStepIR.PAIR_LEFT,
            IntrinsicPathStepIR.APPLY_TAIL,
        ),
        _obstruction(
            IntrinsicPathStepIR.APPLY_CREST,
            IntrinsicPathStepIR.APPLY_CREST,
            IntrinsicPathStepIR.APPLY_TAIL,
        ),
        IntrinsicObstructionIR("tail-of-silence", (IntrinsicPathStepIR.APPLY_TAIL,)),  # type: ignore[arg-type]
    )
    for value in invalid:
        with pytest.raises(IntrinsicIRError, match="invalid-obstruction"):
            intrinsic_ir_data(value)
    with pytest.raises(IntrinsicIRError, match="invalid-obstruction"):
        intrinsic_ir_data(IntrinsicBlockedIR((nested, nested)))
    with pytest.raises(IntrinsicIRError, match="invalid-obstruction-set"):
        intrinsic_ir_data(IntrinsicBlockedIR(()))
    with pytest.raises(IntrinsicIRError, match="invalid-domain-obstruction-set"):
        intrinsic_ir_data(IntrinsicDomainBlockedIR((), ()))


def test_cycles_and_broad_resource_exhaustion_fail_closed_but_dag_aliasing_is_allowed():
    mark = IntrinsicMarkValueIR(IntrinsicMarkIR.PULSE)
    shared = IntrinsicPairValueIR(mark, mark)
    assert intrinsic_ir_data(shared)["value"]["left"] == intrinsic_ir_data(shared)["value"]["right"]

    cyclic = IntrinsicPairValueIR(mark, mark)
    object.__setattr__(cyclic, "left", cyclic)
    with pytest.raises(IntrinsicIRError, match="circular-intrinsic-value"):
        intrinsic_ir_data(cyclic)

    broad = mark
    for _ in range(12):
        broad = IntrinsicPairValueIR(broad, broad)
    with pytest.raises(IntrinsicIRError, match="intrinsic-resource-limit"):
        intrinsic_ir_data(broad)


def test_recurrence_obstruction_and_path_limits_have_exact_boundaries():
    maximum = IntrinsicRecurrenceIR((IntrinsicTactIR(),) * MAX_RECURRENCE_TACTS, None)
    assert len(intrinsic_ir_data(maximum)["value"]["tacts"]) == MAX_RECURRENCE_TACTS
    with pytest.raises(IntrinsicIRError, match="recurrence-resource-limit"):
        pulse_ir(maximum)

    maximum_path = _obstruction(
        *((IntrinsicPathStepIR.PAIR_LEFT,) * (MAX_OBSTRUCTION_PATH - 1)),
        IntrinsicPathStepIR.APPLY_TAIL,
    )
    assert len(intrinsic_ir_data(maximum_path)["value"]["path"]) == MAX_OBSTRUCTION_PATH
    too_long = _obstruction(IntrinsicPathStepIR.PAIR_LEFT, *maximum_path.path)
    with pytest.raises(IntrinsicIRError, match="invalid-obstruction"):
        intrinsic_ir_data(too_long)

    many = tuple(
        _obstruction(
            *(IntrinsicPathStepIR.PAIR_RIGHT if index >> bit & 1 else IntrinsicPathStepIR.PAIR_LEFT for bit in range(11)),
            IntrinsicPathStepIR.APPLY_TAIL,
        )
        for index in range(MAX_OBSTRUCTIONS)
    )
    assert len(intrinsic_ir_data(IntrinsicBlockedIR(many))["value"]["obstructions"]) == MAX_OBSTRUCTIONS


def test_sidecar_import_leaves_legacy_wire_opcodes_and_reports_byte_exact():
    program = parse_vmasm((PROJECT_ROOT / "vam/examples/minimal_echo.vmasm").read_text())
    vam0 = encode_vmbc(program)
    vamd = encode_dense(program)
    report = _canonical_bytes(canonical_report(program, execute(program)))
    opcodes = _canonical_bytes(opcode_rows())
    assert (MAGIC, VERSION, DENSE_MAGIC, DENSE_VERSION, PROFILE) == (
        b"VAM0",
        1,
        b"VAMD",
        1,
        "vam0-ref-v1",
    )
    assert (len(vam0), sha256(vam0).hexdigest()) == (
        1128,
        "8b641b5eb56899653f5548d8a0d5ec9f6c9b7015c4691fedc19b79e51d597143",
    )
    assert (len(vamd), sha256(vamd).hexdigest()) == (
        255,
        "a93930bb32ef8b3af293a3fded78944b96025858c483b66bc66719171dbdf923",
    )
    assert sha256(report).hexdigest() == "0039f902437451fc65b27b34876265d251ce10067b3af57c8bfdfe2115f76e89"
    assert sha256(opcodes).hexdigest() == "ba43dc501b704d6435b5945d7f8ede6e5d419a52e537d2f71d5f11e6255da470"
    assert "IntrinsicAnchorIR" not in legacy_vam.__all__
    with pytest.raises(VamBytecodeError, match="unsupported argument type"):
        encode_vmbc([Instruction("REZ", ("%r0", IntrinsicAnchorIR()), 1)])
