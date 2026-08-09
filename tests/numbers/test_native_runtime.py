from src.core.native_runtime import Breath, Mode, NativeObstruction, echo_native, mode, native_runtime_report, native_shadow_rows, nod, observe_native, rez, shadow_from_native, stitch, tact, breath


def test_native_objects_assemble_without_shadow_parser():
    a, b = nod(rez("a")), nod(rez("b"))
    run = breath(tact(a, b, "rise"), tact(b, a, "fall"))
    wrapped = mode(run)
    assert isinstance(run, Breath)
    assert isinstance(wrapped, Mode)
    assert observe_native(wrapped, "length") == 2


def test_breath_and_stitch_reject_boundary_mismatch():
    a, b, c = nod(rez("a")), nod(rez("b")), nod(rez("c"))
    bad = breath(tact(a, b), tact(c, a))
    assert isinstance(bad, NativeObstruction)
    assert bad.reason == "non-contiguous-tacts"
    left = breath(tact(a, b))
    right = breath(tact(c, a))
    assert isinstance(left, Breath) and isinstance(right, Breath)
    assert isinstance(stitch(left, right), NativeObstruction)


def test_open_breath_blocks_mode_but_closed_breath_passes():
    a, b = nod(rez("a")), nod(rez("b"))
    open_run = breath(tact(a, b, "rise"))
    closed_run = breath(tact(a, b, "rise"), tact(b, a, "fall"))
    assert isinstance(open_run, Breath) and isinstance(closed_run, Breath)
    assert isinstance(mode(open_run), NativeObstruction)
    assert isinstance(mode(closed_run), Mode)


def test_observer_echo_and_shadows_are_derived_rows():
    a, b = nod(rez("a")), nod(rez("b"))
    first = breath(tact(a, b, "rise"), tact(b, a, "fall"))
    second = breath(tact(a, b, "rise"), tact(b, a, "fall"))
    assert isinstance(first, Breath) and isinstance(second, Breath)
    assert echo_native(first, second, "shape").echoed
    rows = native_shadow_rows(mode(first))
    assert {row.observer for row in rows} == {"boundary", "length", "shape", "residue"}
    assert all(row.boundary == "observer-derived; not primary ontology" for row in rows)
    assert shadow_from_native(mode(first), "length").response == 2


def test_native_runtime_report_is_ready():
    assert native_runtime_report() == {"objects": 5, "checklist": 5, "mode_ready": True, "shape_echo": True, "shadows": 4}
