import vam.src.optimizer as optimizer_module

from vam.src import execute, optimize, parse_vmasm
from vam.src.equivalence import summarize_equivalence


def ops(report):
    return [inst.comparable() for inst in report.optimized]


def row_details(report, pass_name):
    return [row.detail for row in report.rows if row.pass_name == pass_name]


def test_dead_shadow_keeps_overwritten_obstruction_candidate():
    program = parse_vmasm('''
OBSERVER %r1, "length"
REZ %r2, "phase"
OBSERVE %r3, %r2, %r2
REZ %r3, "overwrite"
''')
    report = optimize(program)

    assert ops(report) == [inst.comparable() for inst in program]
    assert any("multiple definitions" in detail for detail in row_details(report, "dead-shadow"))
    assert execute(report.optimized).obstructions[0].field("claim") == "observe-requires-observer"


def test_dead_shadow_detects_nested_obstruction_in_compressed_shadow():
    program = parse_vmasm('''
REZ %r1, "phase"
COMPRESS %r2, %r1, %r1
''')
    report = optimize(program)

    assert ops(report) == [inst.comparable() for inst in program]
    assert len(report.rejected_rows) == 1
    assert report.rejected_rows[0].pass_name == "dead-shadow"
    assert "obstruction" in report.rejected_rows[0].detail
    assert execute(report.optimized).registers["%r2"].field("shadow").kind == "Obstruction"


def test_duplicate_compress_aliases_identical_safe_source_and_observer():
    program = parse_vmasm('''
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
    report = optimize(program)
    state = execute(report.optimized)

    assert len(report.optimized) == len(program) - 1
    assert any(row.pass_name == "compress-alias" and row.accepted for row in report.rows)
    assert all("%r9" not in inst.args[1:] for inst in report.optimized)
    assert state.certs[0].field("accepted") is True


def test_duplicate_compress_rejects_when_shadow_contains_obstruction():
    program = parse_vmasm('''
REZ %r1, "phase"
OBSERVER %r2, "kind"
COMPRESS %r3, %r1, %r1
COMPRESS %r4, %r1, %r1
ECHO %r5, %r3, %r4, %r2
''')
    report = optimize(program)

    assert ops(report) == [inst.comparable() for inst in program]
    assert any(row.pass_name == "compress-alias" and not row.accepted for row in report.rows)
    assert any("obstruction" in detail for detail in row_details(report, "compress-alias"))
    state = execute(report.optimized)
    assert state.registers["%r3"].field("shadow").kind == "Obstruction"
    assert state.registers["%r4"].field("shadow").kind == "Obstruction"


def test_duplicate_compress_rejects_when_source_has_multiple_definitions():
    program = parse_vmasm('''
REZ %r1, "phase-a"
OBSERVER %r2, "label"
COMPRESS %r3, %r1, %r2
REZ %r1, "phase-b"
COMPRESS %r4, %r1, %r2
ECHO %r5, %r3, %r4, %r2
''')
    report = optimize(program)

    assert ops(report) == [inst.comparable() for inst in program]
    assert any("multiple definitions" in detail for detail in row_details(report, "compress-alias"))


def test_idempotent_compress_aliases_same_observer_visible_context():
    program = parse_vmasm('''
REZ %r1, "phase"
OBSERVER %r2, "kind"
COMPRESS %r3, %r1, %r2
COMPRESS %r4, %r3, %r2
ECHO %r5, %r3, %r4, %r2
CERT %r6, "idempotent-compress", %r5, "same observer visible"
''')
    report = optimize(program)
    state = execute(report.optimized)

    assert len(report.optimized) == len(program) - 1
    assert any(row.pass_name == "compress-idempotent" and row.accepted for row in report.rows)
    assert any("same-observer-visible" in detail for detail in row_details(report, "compress-idempotent"))
    assert all("%r4" not in inst.args[1:] for inst in report.optimized)
    assert state.certs[0].field("accepted") is True


def test_idempotent_compress_rejects_obstruction_target():
    program = parse_vmasm('''
REZ %r1, "phase"
OBSERVER %r2, "kind"
OBSERVE %r3, %r1, %r1
COMPRESS %r4, %r3, %r2
COMPRESS %r5, %r4, %r2
ECHO %r6, %r4, %r5, %r2
''')
    report = optimize(program)

    assert ops(report) == [inst.comparable() for inst in program]
    assert any(row.pass_name == "compress-idempotent" and not row.accepted for row in report.rows)
    assert any("target obstruction" in detail for detail in row_details(report, "compress-idempotent"))
    assert execute(report.optimized).obstructions[0].field("claim") == "observe-requires-observer"


def test_idempotent_compress_rejects_nested_obstruction_source():
    program = parse_vmasm('''
REZ %r1, "phase"
COMPRESS %r2, %r1, %r1
COMPRESS %r3, %r2, %r1
ECHO %r4, %r2, %r3, %r1
''')
    report = optimize(program)

    assert ops(report) == [inst.comparable() for inst in program]
    assert any(row.pass_name == "compress-idempotent" and not row.accepted for row in report.rows)
    assert any("nested obstruction" in detail for detail in row_details(report, "compress-idempotent"))
    assert execute(report.optimized).registers["%r2"].field("shadow").kind == "Obstruction"


def test_idempotent_compress_preserves_execution_summary():
    program = parse_vmasm('''
REZ %r1, "phase"
OBSERVER %r2, "kind"
COMPRESS %r3, %r1, %r2
COMPRESS %r4, %r3, %r2
ECHO %r5, %r3, %r4, %r2
CERT %r6, "idempotent-compress", %r5, "same observer visible"
''')
    report = optimize(program)
    summary = summarize_equivalence(program, report.optimized)

    assert summary.status == "equivalent"
    assert summary.safe is True
    assert summary.check("cert-acceptance").original == (("idempotent-compress", True),)
    assert summary.check("obstruction-count").original == 0


def test_optimizer_does_not_execute_each_definition_prefix(monkeypatch):
    rows = ['OBSERVER %r1, "kind"', 'REZ %r2, "phase"']
    next_reg = 3
    for index in range(24):
        left, right, echo, cert = (f"%r{next_reg + offset}" for offset in range(4))
        rows.extend([
            f"COMPRESS {left}, %r2, %r1",
            f"COMPRESS {right}, %r2, %r1",
            f"ECHO {echo}, {left}, {right}, %r1",
            f'CERT {cert}, "duplicate-{index}", {echo}, "same observer"',
        ])
        next_reg += 4
    program = parse_vmasm("\n".join(rows))
    calls = 0
    original_execute = optimizer_module.execute

    def counted_execute(candidate):
        nonlocal calls
        calls += 1
        return original_execute(candidate)

    monkeypatch.setattr(optimizer_module, "execute", counted_execute)

    report = optimize(program)

    assert calls <= 1
    assert any(row.pass_name == "compress-alias" and row.accepted for row in report.rows)
