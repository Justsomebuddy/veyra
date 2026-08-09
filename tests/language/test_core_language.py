from src.core.language import (
    VeyraKind,
    core_language_checklist,
    expr_kind,
    infer_veyra,
    interpret_veyra,
    normal_text,
    normalize_veyra,
    parse_veyra,
    school_translation_table,
    semantic_shadow,
)


def mode_source(left="a", right="b"):
    return f"mode(breath(tact(nod:{left},nod:{right}),tact(nod:{right},nod:{left})))"


def test_parse_and_typecheck_mode_expression():
    expr = parse_veyra(mode_source())
    check = expr_kind(expr)
    assert check.ok
    assert check.kind == VeyraKind.MODE


def test_bad_assembly_is_blocked():
    check = expr_kind(parse_veyra("tact(nod:a,value:bad)"))
    assert not check.ok
    assert check.status == "blocked"
    assert "bad assembly" in check.obstruction


def test_echo_replaces_equality_by_observer():
    src = f"echo({mode_source('a','b')},{mode_source('b','a')},observer:length)"
    result = infer_veyra(parse_veyra(src))
    assert result.ok
    assert result.status == "ready"


def test_trace_observer_blocks_nonidentical_terms():
    src = f"echo({mode_source('a','b')},{mode_source('b','a')},observer:trace)"
    result = infer_veyra(parse_veyra(src))
    assert not result.ok
    assert result.status == "blocked"
    assert "echo mismatch" in result.obstruction


def test_normal_form_sorts_echo_pair():
    left = parse_veyra(f"echo({mode_source('b','a')},{mode_source('a','b')},observer:length)")
    right = parse_veyra(f"echo({mode_source('a','b')},{mode_source('b','a')},observer:length)")
    assert normal_text(normalize_veyra(left)) == normal_text(normalize_veyra(right))


def test_semantic_shadows_are_domain_declared():
    expr = parse_veyra(mode_source())
    assert semantic_shadow(expr, "arithmetic")["length"] == 2
    assert semantic_shadow(expr, "geometry")["boundary"] == ("nod:a", "nod:a")
    assert semantic_shadow(expr, "analysis")["variation"] == 1
    assert semantic_shadow(expr, "topology")["component_count"] == 2
    assert semantic_shadow(expr, "probability")["sample_space"] == ("a", "b")
    assert semantic_shadow(expr, "statistics")["support_size"] == 2


def test_minimal_interpreter_returns_logic_status():
    src = f"echo({mode_source('a','b')},{mode_source('b','a')},observer:length)"
    result = interpret_veyra(src, "logic")
    assert result.check.status == "ready"
    assert result.semantic["status"] == "ready"


def test_translation_table_and_nine_core_items():
    assert len(core_language_checklist()) == 9
    rows = school_translation_table()
    assert len(rows) == 9
    assert {row.school for row in rows} >= {"equality", "number", "proof", "model"}
