from pathlib import Path

from vam.src import (
    compile_source,
    compile_to_vmasm,
    decode_vmbc,
    disassemble,
    encode_vmbc,
    execute,
    optimize,
    parse_vmasm,
    run_vmasm,
)
from src.core.paths import PROJECT_ROOT


def comparable(program):
    return [inst.comparable() for inst in program]


def test_minimal_echo_program_accepts_certificate():
    source = (PROJECT_ROOT / "vam/examples/minimal_echo.vmasm").read_text()
    state = run_vmasm(source)

    assert len(state.trace) == 12
    assert len(state.certs) == 1
    assert state.certs[0].field("claim") == "length-echo"
    assert state.certs[0].field("accepted") is True
    assert state.registers["%r11"].kind == "Echo"
    assert state.registers["%r11"].field("passed") is True


def test_vmasm_round_trip_preserves_instruction_ir():
    source = (PROJECT_ROOT / "vam/examples/minimal_echo.vmasm").read_text()
    program = parse_vmasm(source)
    round_trip = parse_vmasm(disassemble(program))

    assert comparable(round_trip) == comparable(program)


def test_invalid_breath_becomes_obstruction_not_certificate():
    source = """
REZ %r1, \"phase\"
BREATH %r2, %r1
OBSERVER %r3, \"length\"
CERT %r4, \"bad-breath\", %r2, \"must fail\"
"""
    state = execute(parse_vmasm(source))

    assert state.registers["%r2"].kind == "Obstruction"
    assert state.registers["%r4"].kind == "Certificate"
    assert state.registers["%r4"].field("accepted") is False
    assert state.certs == []
    assert len(state.obstructions) == 1


def test_vam0_binary_round_trip_preserves_instruction_ir():
    source = (PROJECT_ROOT / "vam/examples/minimal_echo.vmasm").read_text()
    program = parse_vmasm(source)
    blob = encode_vmbc(program)
    decoded = decode_vmbc(blob)

    assert blob.startswith(b"VAM0")
    assert comparable(decoded) == comparable(program)
    assert run_vmasm(disassemble(decoded)).certs[0].field("accepted") is True


def test_vam0_rejects_bad_magic():
    source = (PROJECT_ROOT / "vam/examples/minimal_echo.vmasm").read_text()
    blob = b"NOPE" + encode_vmbc(parse_vmasm(source))[4:]

    try:
        decode_vmbc(blob)
    except ValueError as exc:
        assert "magic" in str(exc)
    else:
        raise AssertionError("bad VAM0 magic was accepted")


def test_optimizer_aliases_observer_and_removes_dead_shadow():
    source = '''
REZ %r1, "phase"
NOD %r2, %r1, "0"
NOD %r3, %r1, "1"
TACT %r4, %r2, %r3, "step"
BREATH %r5, %r4
MODE %r6, %r5
OBSERVER %r7, "length"
OBSERVER %r8, "length"
OBSERVE %r9, %r6, %r8
ECHO %r10, %r6, %r6, %r8
CERT %r11, "self-length", %r10, "finite optimizer test"
'''
    program = parse_vmasm(source)
    report = optimize(program)
    optimized_state = execute(report.optimized)

    assert len(report.optimized) == len(program) - 2
    assert [row.action for row in report.accepted_rows] == ["remove", "remove"]
    assert report.rejected_rows == ()
    assert optimized_state.certs[0].field("accepted") is True
    assert all("%r8" not in inst.args[1:] for inst in report.optimized)


def test_optimizer_rejects_removing_obstruction_shadow():
    program = parse_vmasm('''
REZ %r1, "phase"
OBSERVE %r2, %r1, %r1
''')
    report = optimize(program)

    assert len(report.optimized) == len(program)
    assert len(report.rejected_rows) == 1
    assert "obstruction" in report.rejected_rows[0].detail


def core_echo_source():
    return "echo(mode(breath(tact(nod:a,nod:b),tact(nod:b,nod:a))),mode(breath(tact(nod:b,nod:a),tact(nod:a,nod:b))),observer:length)"


def test_core_language_compiles_to_vam_and_executes_certificate():
    result = compile_source(core_echo_source())
    report = optimize(result.program)
    state = execute(report.optimized)

    assert result.root_register.startswith("%r")
    assert result.cert_register is not None
    assert any(inst.op == "ECHO" for inst in result.program)
    assert state.certs[0].field("accepted") is True
    assert not state.obstructions


def test_core_language_compile_round_trips_through_vam0():
    result = compile_source(core_echo_source(), claim="core-length")
    decoded = decode_vmbc(encode_vmbc(result.program))
    state = execute(decoded)

    assert comparable(decoded) == comparable(result.program)
    assert state.certs[0].field("claim") == "core-length"
    assert state.certs[0].field("accepted") is True


def test_compile_to_vmasm_contains_expected_ops():
    text = compile_to_vmasm(core_echo_source())
    program = parse_vmasm(text)

    assert "ECHO" in text
    assert "CERT" in text
    assert comparable(program) == comparable(compile_source(core_echo_source()).program)


def test_core_language_trace_observer_blocks_after_lowering():
    source = "echo(mode(breath(tact(nod:a,nod:b),tact(nod:b,nod:a))),mode(breath(tact(nod:b,nod:a),tact(nod:a,nod:b))),observer:trace)"
    result = compile_source(source, claim="core-trace")
    state = execute(result.program)

    assert state.registers[result.root_register].field("passed") is False
    assert state.certs == []


def test_core_language_boundary_observer_blocks_after_lowering():
    source = "echo(mode(breath(tact(nod:a,nod:b),tact(nod:b,nod:a))),mode(breath(tact(nod:b,nod:a),tact(nod:a,nod:b))),observer:boundary)"
    result = compile_source(source, claim="core-boundary")
    state = execute(result.program)

    assert state.registers[result.root_register].field("passed") is False
    assert state.registers[result.root_register].field("left").field("value") == ("mode", ("breath", "a:a", "a:a"), "native-cycle")
    assert state.certs == []
