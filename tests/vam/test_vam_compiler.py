import pytest

from vam.src import compile_source, compile_to_vmasm, execute, parse_vmasm
from vam.src.compiler import SUPPORTED_OBSERVERS, VamCompileError


def comparable(program):
    return [inst.comparable() for inst in program]


@pytest.mark.parametrize("observer", sorted(SUPPORTED_OBSERVERS))
def test_supported_observers_lower_to_observer_instruction(observer):
    source = "observer" if observer == "kind" else f"observer:{observer}"
    result = compile_source(source, certify=False)

    assert comparable(result.program) == [("OBSERVER", ("%r1", observer))]
    assert result.root_register == "%r1"
    assert result.cert_register is None


def test_unsupported_observer_raises_vam_compile_error():
    with pytest.raises(VamCompileError, match="observer"):
        compile_source("observer:unknown", certify=False)


def test_certify_false_omits_certificate_instruction():
    result = compile_source("echo(nod:a,nod:a,observer:kind)", certify=False)

    assert result.cert_register is None
    assert all(inst.op != "CERT" for inst in result.program)
    assert result.program[-1].op == "ECHO"
    assert result.program[-1].args[0] == result.root_register


def test_compile_to_vmasm_parses_back_to_compiler_ir():
    source = "echo(mode(breath(tact(nod:a,nod:b),tact(nod:b,nod:a))),mode(breath(tact(nod:b,nod:a),tact(nod:a,nod:b))),observer:length)"
    text = compile_to_vmasm(source, claim="round-trip")
    parsed = parse_vmasm(text)
    compiled = compile_source(source, claim="round-trip").program

    assert text.endswith("\n")
    assert comparable(parsed) == comparable(compiled)


def test_compiler_rejects_bad_core_assembly_before_emitting_ir():
    with pytest.raises(VamCompileError, match="bad Core expression"):
        compile_source("rez(nod:a)", certify=False)

    with pytest.raises(VamCompileError, match="bad Core expression"):
        compile_source("mode(nod:a)", certify=False)

    with pytest.raises(VamCompileError, match="strict Core semantics"):
        compile_source("mode(breath(tact(nod:a,nod:b)))", certify=False)


def test_vam_observer_parity_counts_native_atoms_as_one():
    source = "echo(rez:abc,rez:d,observer:length)"
    result = compile_source(source, certify=False)
    state = execute(result.program)

    assert state.registers[result.root_register].field("passed") is True


def test_vam_label_observer_treats_compounds_as_unlabeled():
    source = "echo(tact(nod:a,nod:b),tact(nod:c,nod:d),observer:label)"
    result = compile_source(source, certify=False)
    state = execute(result.program)

    assert state.registers[result.root_register].field("passed") is True
