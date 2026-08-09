from vam.src.highlevel import compile_highlevel_source, lower_highlevel_source


def comparable(program):
    return [inst.comparable() for inst in program]


def test_claim_seed_lowers_to_core_and_compiles_to_vam():
    result = compile_highlevel_source("claim same := echo(nod:a,nod:a) under observer:length")

    assert result.ok
    assert result.core_source == "echo(nod:a,nod:a,observer:length)"
    assert result.lowering.name == "same"
    ops = [op for op, _ in comparable(result.compile_result.program)]
    assert "ECHO" in ops
    assert result.compile_result.cert_register is not None
    assert result.compile_result.program[-1].args[1] == "hl:claim:same"


def test_process_seed_lowers_single_echo_body():
    result = compile_highlevel_source("process demo { echo(mode(breath(tact(nod:a,nod:b),tact(nod:b,nod:a))),mode(breath(tact(nod:a,nod:b),tact(nod:b,nod:a)))) under length }", certify=False)

    assert result.ok
    assert result.lowering.source_kind == "process"
    assert result.core_source.endswith(",observer:length)")
    assert result.compile_result.cert_register is None
    assert result.compile_result.program[-1].op == "ECHO"


def test_invalid_highlevel_syntax_returns_structured_diagnostic():
    result = compile_highlevel_source("claim bad echo(nod:a,nod:a) under length")

    assert not result.ok
    assert result.compile_result is None
    assert result.diagnostic.error_class == "hl.syntax"
    assert result.diagnostic.line == 1
    assert result.diagnostic.expected == "process NAME { ... } or claim NAME := ..."
    assert "proves no theorem" in result.diagnostic.no_overclaim_note


def test_core_lowering_failure_is_wrapped_as_diagnostic():
    result = compile_highlevel_source("claim bad := echo(rez(nod:a),nod:a) under length")

    assert not result.ok
    assert result.core_source == "echo(rez(nod:a),nod:a,observer:length)"
    assert result.diagnostic.error_class.startswith("core.")
    assert result.diagnostic.core_diagnostic is not None


def test_theorem_like_syntax_remains_unsupported_non_claim():
    lowered = lower_highlevel_source("theorem THM-HL-001 { claim echo p with q under length }")

    assert lowered.error_class == "hl.unsupported_theorem"
    assert lowered.no_overclaim_note.endswith("proves no theorem")
