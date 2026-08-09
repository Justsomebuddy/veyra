from src.core.geometry import TremorCorridor, event_from_ints, event_shadow, squared_separation
from src.core.geometry_relations import circle_shell, corridor_congruence, parallel_corridors_2d, quarter_turn_relabel, relabel_event, scale_relabel, translation_relabel, triangle_congruence, triangle_signature
from src.core.ratio import ratio_from_ints, ratio_shadow


def test_corridor_congruence_and_circle_shell():
    horizontal = TremorCorridor(event_from_ints((0, 0)), event_from_ints((5, 0)), "h")
    vertical = TremorCorridor(event_from_ints((2, 2)), event_from_ints((2, 7)), "v")
    cert = corridor_congruence(horizontal, vertical)
    assert cert.relation == "congruent"
    assert ratio_shadow(cert.left_measure) == 25
    assert circle_shell(event_from_ints((0, 0)), ratio_from_ints(25), event_from_ints((3, 4))).relation == "on"
    assert circle_shell(event_from_ints((0, 0)), ratio_from_ints(25), event_from_ints((1, 1))).relation == "inside"


def test_triangle_congruence_preserves_or_allows_turn():
    left = (event_from_ints((0, 0)), event_from_ints((3, 0)), event_from_ints((0, 4)))
    shifted = (event_from_ints((10, 10)), event_from_ints((13, 10)), event_from_ints((10, 14)))
    mirrored = (event_from_ints((0, 0)), event_from_ints((0, 4)), event_from_ints((3, 0)))
    assert triangle_signature(*left).orientation == "left"
    assert triangle_congruence(left, shifted).relation == "congruent"
    assert triangle_congruence(left, mirrored).obstruction == "turn-mismatch"
    assert triangle_congruence(left, mirrored, preserve_turn=False).relation == "congruent"


def test_parallel_corridor_certificate():
    a = TremorCorridor(event_from_ints((0, 0)), event_from_ints((2, 2)), "a")
    b = TremorCorridor(event_from_ints((0, 1)), event_from_ints((2, 3)), "b")
    c = TremorCorridor(event_from_ints((0, 0)), event_from_ints((1, 0)), "c")
    assert parallel_corridors_2d(a, b).relation == "parallel"
    assert parallel_corridors_2d(a, c).relation == "turning"


def test_plane_relabels_and_separation_effects():
    point = event_from_ints((1, 2), "p")
    assert event_shadow(relabel_event(translation_relabel(5, -1), point)) == (6, 1)
    assert event_shadow(relabel_event(quarter_turn_relabel(), point)) == (-2, 1)
    a = event_from_ints((0, 0), "a")
    b = event_from_ints((3, 4), "b")
    qa = relabel_event(quarter_turn_relabel(), a)
    qb = relabel_event(quarter_turn_relabel(), b)
    sa = relabel_event(scale_relabel(2), a)
    sb = relabel_event(scale_relabel(2), b)
    assert ratio_shadow(squared_separation(qa, qb)) == 25
    assert ratio_shadow(squared_separation(sa, sb)) == 100
