import pytest

from vam.src.model import Instruction
from vam.src.opcodes import (
    OPCODES_BY_CODE,
    OPCODES_BY_NAME,
    OpcodeValidationError,
    classify_instruction,
    classify_program,
    opcode_rows,
    opcode_table,
    opcode_table_from_rows,
)


def test_opcode_ids_and_names_are_unique() -> None:
    table = opcode_table()
    assert len({spec.code for spec in table}) == len(table)
    assert len({spec.name for spec in table}) == len(table)
    assert set(OPCODES_BY_NAME) == {spec.name for spec in table}
    assert set(OPCODES_BY_CODE) == {spec.code for spec in table}


def test_classifies_current_ops_and_flags() -> None:
    program = [
        Instruction("REZ", ("%r1", "root"), 1),
        Instruction("NOD", ("%r2", "%r1", "a"), 2),
        Instruction("NOD", ("%r3", "%r1", "b"), 3),
        Instruction("TACT", ("%r4", "%r2", "%r3", "edge"), 4),
        Instruction("BREATH", ("%r5", "%r4", "%r4"), 5),
        Instruction("MODE", ("%r6", "%r5"), 6),
        Instruction("OBSERVER", ("%r7", "length"), 7),
        Instruction("OBSERVE", ("%r8", "%r6", "%r7"), 8),
        Instruction("COMPRESS", ("%r9", "%r6", "%r7"), 9),
        Instruction("ECHO", ("%r10", "%r6", "%r6", "%r7"), 10),
        Instruction("OBSTRUCT", ("%r11", "manual-stop", "%r10"), 11),
        Instruction("CERT", ("%r12", "self-length", "%r10", "metadata-only"), 12),
    ]
    rows = classify_program(program)
    assert [row.code for row in rows] == [1, 2, 2, 3, 4, 5, 6, 7, 10, 8, 9, 11]
    assert rows[4].operand_classes == ("dest_reg", "reg", "reg")
    assert rows[9].side_effect is True
    assert rows[10].obstruction is True
    assert rows[11].certificate is True


def test_rejects_bad_arity() -> None:
    with pytest.raises(OpcodeValidationError, match="REZ expected 2 operands"):
        classify_instruction(Instruction("REZ", ("%r1",), 1))
    with pytest.raises(OpcodeValidationError, match="BREATH expected >=2 operands"):
        classify_instruction(Instruction("BREATH", ("%r1",), 2))


def test_rejects_bad_operand_class() -> None:
    with pytest.raises(OpcodeValidationError, match="operand 1 expected dest_reg"):
        classify_instruction(Instruction("REZ", ("not_a_register", "root"), 1))
    with pytest.raises(OpcodeValidationError, match="operand 2 expected reg"):
        classify_instruction(Instruction("NOD", ("%r2", "not_a_register", "a"), 2))
    with pytest.raises(OpcodeValidationError, match="operand 2 expected claim"):
        classify_instruction(Instruction("CERT", ("%r3", "%r1", "%r2", "boundary"), 3))


def test_rejects_unknown_opcode() -> None:
    with pytest.raises(OpcodeValidationError, match="unknown VAM opcode"):
        classify_instruction(Instruction("SPIN", ("%r1",), 1))


def test_metadata_rows_round_trip() -> None:
    rows = opcode_rows()
    rebuilt = opcode_table_from_rows(rows)
    assert tuple(spec.to_row() for spec in rebuilt) == rows
