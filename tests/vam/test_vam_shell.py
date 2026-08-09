from vam.src.compiler import compile_source
from vam.src.interpreter import execute
from vam.src.shell import NON_CERTIFICATE_BOUNDARY, decode_shell_carrier_label


def comparable(program):
    return [inst.comparable() for inst in program]


def shell_carrier(compiled, state):
    root = state.registers[compiled.root_register]
    assert root.kind == "Rez"
    return decode_shell_carrier_label(root.field("label"))


def test_supported_finite_shell_lowers_and_executes_deterministically():
    source = "shell(echo(nod:a,nod:a,observer:length),echo(nod:b,nod:b,observer:kind))"

    first = compile_source(source)
    second = compile_source(source)
    state = execute(first.program)
    carrier = shell_carrier(first, state)

    assert comparable(first.program) == comparable(second.program)
    assert first.cert_register is None
    assert [inst.op for inst in first.program].count("ECHO") == 2
    assert all(inst.op != "CERT" for inst in first.program)
    assert state.certs == []
    assert state.obstructions == []
    assert carrier["status"] == "transported"
    assert carrier["transported"] is True
    assert carrier["certificate_claim"] is None
    assert [row["status"] for row in carrier["rows"]] == ["transported", "transported"]


def test_blocked_shell_child_becomes_executable_obstruction_not_certificate():
    source = "shell(echo(nod:a,nod:bbb,observer:label),echo(nod:c,nod:c,observer:kind))"

    result = compile_source(source)
    state = execute(result.program)
    carrier = shell_carrier(result, state)

    assert result.cert_register is None
    assert [inst.op for inst in result.program].count("ECHO") == 2
    assert any(inst.op == "OBSTRUCT" for inst in result.program)
    assert state.certs == []
    assert len(state.obstructions) == 1
    assert carrier["status"] == "blocked"
    assert carrier["transported"] is False
    assert [row["status"] for row in carrier["rows"]] == ["blocked", "transported"]
    assert len(carrier["obstruction_registers"]) == 1


def test_unsupported_shell_child_blocks_conjunction_carrier():
    source = "shell(echo(nod:a,nod:a,observer:weight))"

    compiled = compile_source(source)
    state = execute(compiled.program)
    carrier = shell_carrier(compiled, state)

    assert compiled.cert_register is None
    assert compiled.program[-2].op == "OBSTRUCT"
    assert state.certs == []
    assert len(state.obstructions) == 1
    assert carrier["status"] == "blocked"
    assert [row["status"] for row in carrier["rows"]] == ["unsupported"]
    assert len(carrier["obstruction_registers"]) == 1


def test_shell_carrier_keeps_explicit_non_certificate_boundary():
    source = "shell(echo(nod:a,nod:a,observer:kind))"

    compiled = compile_source(source, certify=True, claim="must-not-leak-into-shell")
    state = execute(compiled.program)
    carrier = shell_carrier(compiled, state)

    assert compiled.cert_register is None
    assert state.certs == []
    assert all(inst.op != "CERT" for inst in compiled.program)
    assert carrier["status"] == "transported"
    assert carrier["certificate_claim"] is None
    assert carrier["boundary"] == NON_CERTIFICATE_BOUNDARY
    assert "must-not-leak-into-shell" not in state.registers[compiled.root_register].field("label")
