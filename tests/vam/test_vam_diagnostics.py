from vam.src.diagnostics import compile_source_with_diagnostics


def test_valid_current_echo_modes_compile_with_certificate():
    source = "echo(mode(breath(tact(nod:a,nod:b),tact(nod:b,nod:a))),mode(breath(tact(nod:b,nod:a),tact(nod:a,nod:b))),observer:length)"

    result = compile_source_with_diagnostics(source)

    assert result.ok
    assert result.diagnostic is None
    assert result.compile_result is not None
    assert result.compile_result.cert_register is not None
    assert result.compile_result.program[-1].op == "CERT"


def test_unsupported_observer_reports_stable_diagnostic_and_no_certificate():
    result = compile_source_with_diagnostics("echo(nod:a,nod:a,observer:weight)")

    assert not result.ok
    assert result.compile_result is None
    assert result.diagnostic is not None
    assert result.diagnostic.error_class == "lower.unsupported_observer"
    assert result.diagnostic.compile_phase == "lower"
    assert "weight" in result.diagnostic.message
    assert result.diagnostic.normalized_text == "observer:weight"
    assert "not compiled or certified" in result.diagnostic.no_overclaim_note


def test_syntactically_bad_source_reports_parse_diagnostic():
    result = compile_source_with_diagnostics("echo(nod:a,nod:a,observer:length")

    assert not result.ok
    assert result.compile_result is None
    assert result.diagnostic is not None
    assert result.diagnostic.error_class == "parse.syntax"
    assert result.diagnostic.compile_phase == "parse"
    assert result.diagnostic.expected == "')'"
    assert result.diagnostic.found == "EOF"
    assert result.diagnostic.no_overclaim_note is None


def test_unsupported_core_expression_reports_lowering_diagnostic():
    source = "weight(nod:a)"

    result = compile_source_with_diagnostics(source, certify=False)

    assert not result.ok
    assert result.compile_result is None
    assert result.diagnostic is not None
    assert result.diagnostic.error_class == "lower.unsupported_head"
    assert result.diagnostic.compile_phase == "lower"
    assert result.diagnostic.normalized_text == source
    assert "unsupported Core expression" in result.diagnostic.message
