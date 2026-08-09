from src.core.geometry import TremorCorridor, event_from_ints, event_shadow
from src.core.geometry_relations import quarter_turn_relabel, relabel_event, translation_relabel
from src.core.geometry_theorems import compose_relabels, identity_relabel, line_shell_intersections, pythagorean_card, relabel_composition_card, sas_card, sss_card
from src.core.ratio import ratio_from_ints, ratio_shadow


def test_pythagorean_card_right_and_blocked():
    origin = event_from_ints((0, 0), "o")
    east = event_from_ints((3, 0), "e")
    north = event_from_ints((0, 4), "n")
    bad = event_from_ints((1, 1), "bad")
    assert pythagorean_card(origin, east, north).relation == "proven"
    assert pythagorean_card(origin, east, bad).obstruction == "non-right-apex"


def test_sss_and_sas_cards():
    left = (event_from_ints((0, 0)), event_from_ints((3, 0)), event_from_ints((0, 4)))
    shifted = (event_from_ints((10, 10)), event_from_ints((13, 10)), event_from_ints((10, 14)))
    wrong = (event_from_ints((0, 0)), event_from_ints((2, 0)), event_from_ints((0, 4)))
    assert sss_card(left, shifted).relation == "congruent"
    assert sas_card(left, shifted).relation == "congruent"
    assert sas_card(left, wrong).obstruction == "side-dot-mismatch"


def test_line_shell_intersections_two_tangent_none():
    diameter = TremorCorridor(event_from_ints((-10, 0)), event_from_ints((10, 0)), "diameter")
    tangent = TremorCorridor(event_from_ints((5, -1)), event_from_ints((5, 1)), "tangent")
    miss = TremorCorridor(event_from_ints((6, -1)), event_from_ints((6, 1)), "miss")
    center = event_from_ints((0, 0), "c")
    two = line_shell_intersections(diameter, center, ratio_from_ints(25))
    assert two.relation == "two"
    assert tuple(ratio_shadow(x) for x in two.parameters) == (ratio_shadow(ratio_from_ints(1, 4)), ratio_shadow(ratio_from_ints(3, 4)))
    assert line_shell_intersections(tangent, center, ratio_from_ints(25)).relation == "tangent"
    assert line_shell_intersections(miss, center, ratio_from_ints(25)).obstruction == "no-real-crossing"


def test_relabel_identity_and_composition_cards():
    point = event_from_ints((2, 3), "p")
    assert event_shadow(relabel_event(identity_relabel(), point)) == (2, 3)
    composed = compose_relabels(quarter_turn_relabel(), translation_relabel(1, -2))
    assert event_shadow(relabel_event(composed, point)) == event_shadow(relabel_event(quarter_turn_relabel(), relabel_event(translation_relabel(1, -2), point)))
    assert relabel_composition_card(quarter_turn_relabel(), translation_relabel(1, -2), point).relation == "proven"
