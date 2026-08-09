from fractions import Fraction

from src.core.category_like import (
    category_closure_rows,
    category_invariant_rows,
    category_like_checklist,
    category_like_examples,
    category_like_morphisms,
    category_like_summary,
    category_universal_shadow_rows,
    compose_morphisms,
    morphism_graph,
)


def test_category_like_objects_are_finite_observer_clouds():
    objects = category_like_examples()
    assert [obj.name for obj in objects] == ["A", "B", "C", "D"]
    assert objects[0].shadows == (Fraction(0), Fraction(1), Fraction(2))
    assert objects[-1].observer == "ratio-shadow"


def test_category_like_morphisms_close_over_targets():
    rows = category_closure_rows()
    assert [row.status for row in rows] == ["closed", "closed", "closed", "closed"]
    assert rows[1].graph == ((Fraction(0), Fraction(1)), (Fraction(1), Fraction(2)), (Fraction(2), Fraction(3)))
    assert all(row.obstruction == "none" for row in rows)


def test_category_like_composition_uses_transformer_schemas():
    _, f, g, h = category_like_morphisms()
    gf = compose_morphisms(g, f, "g∘f")
    hgf = compose_morphisms(h, gf, "h∘g∘f")
    assert gf.transformer.degree == 1
    assert morphism_graph(hgf) == ((Fraction(0), Fraction(4)), (Fraction(1), Fraction(6)), (Fraction(2), Fraction(8)))


def test_category_like_invariants_include_counterexample():
    rows = category_invariant_rows()
    assert [row.status for row in rows] == ["invariant", "broken"]
    assert rows[0].name == "sample-count"
    assert rows[1].obstruction == "translation-changes-total"


def test_category_like_universal_shadows_are_bounded_not_full_category():
    rows = category_universal_shadow_rows()
    assert [row.status for row in rows] == ["exact", "exact", "blocked"]
    assert rows[-1].obstruction == "object-shadow-mismatch"
    assert len(category_like_checklist()) == 4
    assert category_like_summary() == {"objects": 4, "morphisms": 4, "closed": 4, "invariants": 2, "broken": 1, "universal": 3, "blocked": 1, "checklist": 4}
