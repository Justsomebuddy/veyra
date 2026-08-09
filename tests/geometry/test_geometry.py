from src.core.geometry import EventPoint, TremorCorridor, corridor_contains, corridor_interpolate, corridor_midpoint, corridor_parameter, event_from_ints, event_shadow, squared_separation, triangle_area, turn_2d
from src.core.ratio import ratio_from_ints, ratio_shadow


def test_corridor_midpoint_and_squared_separation():
    start = event_from_ints((0, 0), "a")
    end = event_from_ints((3, 4), "b")
    corridor = TremorCorridor(start, end, "ab")
    assert ratio_shadow(squared_separation(start, end)) == 25
    assert event_shadow(corridor_midpoint(corridor)) == (ratio_shadow(ratio_from_ints(3, 2)), ratio_shadow(ratio_from_ints(2)))


def test_corridor_interpolation_contains_and_parameter():
    corridor = TremorCorridor(event_from_ints((0, 0)), event_from_ints((6, 3)), "diag")
    point = corridor_interpolate(corridor, ratio_from_ints(1, 3))
    off = EventPoint((ratio_from_ints(2), ratio_from_ints(2)), "off")
    assert event_shadow(point) == (2, 1)
    assert corridor_contains(corridor, point)
    assert ratio_shadow(corridor_parameter(corridor, point)) == ratio_shadow(ratio_from_ints(1, 3))
    assert not corridor_contains(corridor, off)


def test_turn_and_triangle_area():
    origin = event_from_ints((0, 0), "o")
    east = event_from_ints((1, 0), "e")
    north = event_from_ints((0, 1), "n")
    turn = turn_2d(origin, east, north)
    assert turn.status == "exact"
    assert turn.orientation == "left"
    assert ratio_shadow(triangle_area(origin, east, north)) == ratio_shadow(ratio_from_ints(1, 2))


def test_flat_turn_and_degenerate_corridor():
    a = event_from_ints((1, 1), "a")
    b = event_from_ints((1, 1), "b")
    corridor = TremorCorridor(a, b, "silent")
    assert corridor_contains(corridor, a)
    assert ratio_shadow(corridor_parameter(corridor, a)) == 0
    assert turn_2d(event_from_ints((0, 0)), event_from_ints((1, 1)), event_from_ints((2, 2))).orientation == "flat"
