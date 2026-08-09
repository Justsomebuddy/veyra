from vam.src.compiler import compile_source
from vam.src.highlevel_v1 import lower_hl1_source


def comparable(program):
    return [inst.comparable() for inst in program]


def test_observer_alias_and_claim_lower_to_core_and_compile():
    source = "observer length_obs := length\nprocess demo { claim same := echo(nod:a,nod:a) under length_obs }"
    result = lower_hl1_source(source)

    assert result.ok
    assert result.source_kind == "claim"
    assert result.name == "same"
    assert result.core_source == "echo(nod:a,nod:a,observer:length)"
    compiled = compile_source(result.core_source, certify=False)
    assert comparable(compiled.program)[-1][0] == "ECHO"


def test_unknown_observer_is_rejected_before_compiler_runs():
    result = lower_hl1_source("claim bad := echo(nod:a,nod:a) under unknown_obs")

    assert not result.ok
    assert result.diagnostic.error_class == "hl.unsupported_observer"
    assert "unsupported observer" in result.diagnostic.message


def test_theorem_verified_and_proof_tokens_are_rejected():
    for source in [
        "theorem THM { claim same := echo(nod:a,nod:a) under length }",
        "claim same := echo(nod:a,nod:a) under length status verified",
        "claim same := proof object under length",
    ]:
        result = lower_hl1_source(source)
        assert not result.ok
        assert result.diagnostic.error_class in {
            "hl.unsupported_theorem",
            "hl.unsupported_verified_status",
            "hl.unsupported_proof",
        }


def test_straight_line_process_block_lowers_yield_expression():
    source = "process demo { rez a\nnod b from a\nyield b }"
    result = lower_hl1_source(source)

    assert result.ok
    assert result.source_kind == "process"
    assert result.core_source == "nod(rez:a)"
    compiled = compile_source(result.core_source, certify=False)
    assert comparable(compiled.program)[-1][0] == "NOD"
