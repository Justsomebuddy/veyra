import pytest

from src.core.native_runtime import NativeEcho
from src.core.semantic_kernel import evaluate_native
from vam.src import compile_source, execute
from vam.src.compiler import VamCompileError

LEFT = "mode(breath(tact(nod:a,nod:b),tact(nod:b,nod:a)))"
RIGHT = "mode(breath(tact(nod:b,nod:a),tact(nod:a,nod:b)))"
NATIVE_TERMS = (
    "rez:a",
    "nod",
    "nod:a",
    "tact(nod:a,nod:b)",
    "breath(tact(nod:a,nod:b),tact(nod:b,nod:a))",
    LEFT,
    "observer:kind",
)


@pytest.mark.parametrize("observer", ("kind", "label", "length", "trace", "boundary"))
def test_compiled_vam_observations_equal_strict_core_native_semantics(observer):
    source = f"echo({LEFT},{RIGHT},observer:{observer})"
    native = evaluate_native(source)
    compiled = compile_source(source, certify=False)
    echo = execute(compiled.program).registers[compiled.root_register]
    assert isinstance(native.value, NativeEcho)
    assert echo.field("left").field("value") == native.value.left
    assert echo.field("right").field("value") == native.value.right
    assert echo.field("passed") is native.value.echoed


@pytest.mark.parametrize("term", NATIVE_TERMS)
@pytest.mark.parametrize("observer", ("kind", "label", "length", "trace", "boundary"))
def test_every_native_core_kind_has_the_same_vam_observer_response(term, observer):
    source = f"echo({term},{term},observer:{observer})"
    native = evaluate_native(source)
    compiled = compile_source(source, certify=False)
    echo = execute(compiled.program).registers[compiled.root_register]
    assert isinstance(native.value, NativeEcho)
    assert echo.field("left").field("value") == native.value.left
    assert echo.field("right").field("value") == native.value.right
    assert echo.field("passed") is True


def test_core_and_compiler_share_strict_open_mode_obstruction():
    source = "mode(breath(tact(nod:a,nod:b)))"
    assert evaluate_native(source).obstruction == "open-breath"
    with pytest.raises(VamCompileError, match="open-breath"):
        compile_source(source, certify=False)
