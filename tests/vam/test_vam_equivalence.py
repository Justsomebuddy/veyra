from vam.src import Instruction, optimize, parse_vmasm
from vam.src.equivalence import summarize_equivalence


def _safe_program():
    return parse_vmasm('''
REZ %r1, "phase"
NOD %r2, %r1, "0"
NOD %r3, %r1, "1"
TACT %r4, %r2, %r3, "step"
BREATH %r5, %r4
MODE %r6, %r5
OBSERVER %r7, "kind"
COMPRESS %r8, %r6, %r7
COMPRESS %r9, %r6, %r7
ECHO %r10, %r8, %r9, %r7
CERT %r11, "compressed-kind", %r10, "same compressed witness"
''')


def test_optimizer_safe_program_summarizes_as_equivalent():
    program = _safe_program()
    report = optimize(program)
    summary = summarize_equivalence(program, report.optimized)

    assert summary.status == "equivalent"
    assert summary.safe is True
    assert summary.original_ops == len(program)
    assert summary.optimized_ops == len(report.optimized)
    assert summary.original_ops > summary.optimized_ops
    assert summary.check("report-fingerprint").status == "equivalent"
    assert summary.check("cert-acceptance").original == (("compressed-kind", True),)
    assert summary.check("obstruction-count").original == 0


def test_rejected_nested_obstruction_case_preserves_summary():
    program = parse_vmasm('''
REZ %r1, "phase"
OBSERVER %r2, "kind"
COMPRESS %r3, %r1, %r1
COMPRESS %r4, %r1, %r1
ECHO %r5, %r3, %r4, %r2
''')
    report = optimize(program)
    summary = summarize_equivalence(program, report.optimized)

    assert report.optimized == tuple(program)
    assert summary.status == "equivalent"
    assert summary.verdict == "safe"
    assert summary.check("cert-acceptance").original == ()
    assert summary.check("obstruction-count").original == 2


def test_mutated_optimized_program_root_mismatch_is_blocked():
    program = _safe_program()
    report = optimize(program)
    mutated = tuple(
        Instruction(inst.op, ("%r7", "label"), inst.line)
        if inst.op == "OBSERVER"
        else inst
        for inst in report.optimized
    )
    summary = summarize_equivalence(program, mutated)

    assert summary.status == "blocked"
    assert summary.safe is False
    assert summary.verdict == "non-safe"
    assert summary.check("report-fingerprint").status == "blocked"
    assert summary.check("cert-acceptance").status == "equivalent"
    assert summary.check("root-evidence").status == "blocked"


def test_mutated_optimized_program_cert_boundary_change_is_blocked_by_report_fingerprint():
    program = _safe_program()
    report = optimize(program)
    mutated = tuple(
        Instruction(inst.op, inst.args[:3] + ("different boundary",), inst.line)
        if inst.op == "CERT"
        else inst
        for inst in report.optimized
    )
    summary = summarize_equivalence(program, mutated)

    assert summary.status == "blocked"
    assert summary.safe is False
    assert summary.verdict == "non-safe"
    assert summary.check("cert-acceptance").status == "equivalent"
    assert summary.check("root-evidence").status == "blocked"
    assert summary.check("report-fingerprint").status == "blocked"
