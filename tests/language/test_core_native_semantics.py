from src.core.language import KNOWN_OBSERVERS
from src.core.native_runtime import (
    Breath, Mode, NativeEcho, NativeObstruction, NativeObserver, mode, nod, rez,
    silent_breath,
)
from src.core.semantic_kernel import evaluate_native, observer_adapter


def test_strict_evaluator_builds_existing_native_values():
    run = evaluate_native("breath(tact(nod:a,nod:a))")
    wrapped = evaluate_native("mode(breath(tact(nod:a,nod:a)))")
    assert run.ok and isinstance(run.value, Breath)
    assert wrapped.ok and isinstance(wrapped.value, Mode)


def test_strict_evaluator_preserves_native_assembly_obstructions():
    non_contiguous = evaluate_native("breath(tact(nod:a,nod:b),tact(nod:c,nod:a))")
    open_mode = evaluate_native("mode(breath(tact(nod:a,nod:b)))")
    assert non_contiguous.status == "blocked"
    assert isinstance(non_contiguous.value, NativeObstruction)
    assert non_contiguous.value.reason == "non-contiguous-tacts"
    assert open_mode.status == "blocked"
    assert isinstance(open_mode.value, NativeObstruction)
    assert open_mode.value.reason == "open-breath"


def test_all_core_observer_names_are_native_adapters():
    adapters = {name: observer_adapter(name) for name in KNOWN_OBSERVERS}
    assert set(adapters) == KNOWN_OBSERVERS
    assert all(isinstance(value, NativeObserver) for value in adapters.values())
    assert adapters["length"].name == "length"
    assert adapters["trace"].name == "trace"


def test_echo_and_shell_are_native_relations():
    echo = evaluate_native("echo(nod:a,nod:b,observer:kind)")
    shell = evaluate_native("shell(echo(nod:a,nod:b,observer:kind),echo(nod:a,nod:a,observer:label))")
    assert echo.ok and isinstance(echo.value, NativeEcho) and echo.value.echoed
    assert shell.ok and len(shell.value) == 2
    mismatch = evaluate_native("echo(nod:a,nod:b,observer:label)")
    assert mismatch.status == "blocked"
    assert isinstance(mismatch.value, NativeEcho) and not mismatch.value.echoed


def test_unknown_observer_is_unknown_not_an_exception():
    result = evaluate_native("echo(nod:a,nod:b,observer:future-eye)")
    assert result.status == "unknown"
    assert "unknown observer future-eye" in result.obstruction


def test_anchored_silent_modes_remain_distinct_under_trace_and_boundary():
    left = mode(silent_breath(nod(rez("zero:left"))))
    right = mode(silent_breath(nod(rez("zero:right"))))
    assert isinstance(left, Mode) and isinstance(right, Mode)
    for name in ("trace", "boundary"):
        observer = observer_adapter(name)
        assert observer is not None
        assert observer.response(left) != observer.response(right)
