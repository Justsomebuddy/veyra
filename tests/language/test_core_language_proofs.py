from src.core.language_proof import proof_language_checklist, proof_summary, trace_veyra_proof


def test_trace_records_kind_and_inference_steps():
    trace = trace_veyra_proof("echo(nod:a,nod:b,observer:kind)")
    assert trace.parse_ok
    assert trace.final_check.status == "ready"
    assert trace.steps[-1].rule == "infer.echo"
    assert trace.steps[-1].output_status == "ready"
    assert any(step.rule == "kind.nod" for step in trace.steps)


def test_trace_records_source_spans():
    trace = trace_veyra_proof("tact(nod:a,nod:b)")
    tact = trace.steps[-1]
    assert tact.rule == "kind.tact"
    assert tact.span.start == 0
    assert tact.span.end == len("tact(nod:a,nod:b)")
    assert tact.input_kinds == ("nod", "nod")


def test_blocked_echo_keeps_obstruction():
    trace = trace_veyra_proof("echo(nod:a,nod:b,observer:trace)")
    assert trace.final_check.status == "blocked"
    assert trace.steps[-1].output_status == "blocked"
    assert "echo mismatch" in trace.steps[-1].obstruction


def test_parse_error_becomes_proof_trace():
    trace = trace_veyra_proof("echo(nod:a,nod:b,observer:kind")
    assert not trace.parse_ok
    assert trace.final_check.status == "blocked"
    assert trace.steps == trace.steps[:1]
    assert trace.steps[0].rule == "grammar.parse"


def test_proof_summary_counts_statuses():
    trace = trace_veyra_proof("echo(nod:a,nod:b,observer:trace)")
    summary = proof_summary(trace)
    assert summary.steps == len(trace.steps)
    assert summary.blocked >= 1
    assert summary.final_status == "blocked"


def test_proof_language_checklist_v03():
    assert proof_language_checklist() == (
        "rule-name",
        "source-span",
        "input-kinds",
        "input-statuses",
        "output-status",
        "obstruction",
        "trace-summary",
    )
