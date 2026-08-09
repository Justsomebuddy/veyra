import pytest

from src.core.modes import Mode
from src.core.tact_similarity import aura_cost, aura_cost_map, cyclic_tact_aura_echoes, cyclic_tact_auras, jaccard_similarity, tact_aura_cost_rows


def test_cyclic_tact_auras_capture_context_not_identity():
    auras = cyclic_tact_auras([Mode.from_word("abac")], ("a", "b", "c"))
    assert auras["b"].marks == frozenset({"L1:a", "R1:a"})
    assert auras["c"].marks == frozenset({"L1:a", "R1:a"})
    assert "L1:b" in auras["a"].marks
    assert "R1:c" in auras["a"].marks


def test_aura_similarity_makes_context_twins_cheap():
    auras = cyclic_tact_auras([Mode.from_word("abac")], ("a", "b", "c"))
    assert jaccard_similarity(auras["b"], auras["c"]) == 1.0
    assert aura_cost(auras["b"], auras["c"]) == 0.25
    assert aura_cost(auras["a"], auras["c"]) == 1.0


def test_aura_cost_map_drives_weighted_defaults():
    costs = aura_cost_map([Mode.from_word("abac")], ("a", "b", "c"))
    assert costs[("b", "c")] == 0.25
    assert costs[("c", "b")] == 0.25
    assert costs[("a", "c")] == 1.0


def test_tact_aura_cost_rows_and_radius_validation():
    rows = tact_aura_cost_rows([Mode.from_word("abac")], ("a", "b", "c"))
    assert any(row["expected"] == "b" and row["actual"] == "c" and row["cost"] == 0.25 for row in rows)
    with pytest.raises(ValueError):
        cyclic_tact_auras([Mode.from_word("ab")], radius=0)


def test_cyclic_tact_aura_echoes_are_structured_before_text_shadow():
    echoes = cyclic_tact_aura_echoes([Mode.from_word("abac")], ("a", "b", "c"))
    assert echoes["b"].text_marks() == frozenset({"L1:a", "R1:a"})
    assert all(mark.side in {"L", "R"} and mark.distance == 1 for mark in echoes["b"].marks)
