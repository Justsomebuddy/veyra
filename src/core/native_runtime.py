"""Native Veyra F4 runtime objects before school shadows."""
from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

NativeResponse = str | int | tuple[object, ...]
NativeObject = "Rez | Nod | Tact | Breath | Mode | NativeObserver"

@dataclass(frozen=True)
class Rez:
    """A residue: an executable distinction token, not a number/string shadow."""
    name: str

@dataclass(frozen=True)
class Nod:
    """A directed address into a residue."""
    residue: Rez
    mark: str

@dataclass(frozen=True)
class Tact:
    """A contact from one nod to another."""
    start: Nod
    end: Nod
    mark: str = "touch"

@dataclass(frozen=True)
class Breath:
    """A finite contiguous run of tacts."""
    tacts: tuple[Tact, ...]
    anchor: Nod | None = None

@dataclass(frozen=True)
class Mode:
    """A recurrent breath accepted as a native mode."""
    breath: Breath
    observer: str = "native-cycle"

@dataclass(frozen=True)
class NativeObserver:
    """An observer that derives a response from native behavior."""
    name: str
    response: Callable[[NativeObject], NativeResponse]

@dataclass(frozen=True)
class NativeEcho:
    """Observer-indexed echo result between native objects."""
    observer: str
    left: NativeResponse
    right: NativeResponse
    echoed: bool

@dataclass(frozen=True)
class NativeObstruction:
    """A first-class native runtime blockage."""
    stage: str
    reason: str
    residue: tuple[str, ...]

@dataclass(frozen=True)
class NativeShadowRow:
    """A school-readable row derived after native observation."""
    native_kind: str
    observer: str
    response: NativeResponse
    boundary: str

def rez(name: str) -> Rez:
    """Create a native residue."""
    logger.debug("rez entry name=%s", name)
    result = Rez(name or "∅")
    logger.debug("rez exit result=%r", result)
    return result

def nod(source: Rez, mark: str | None = None) -> Nod:
    """Create a native nod addressed into a residue."""
    logger.debug("nod entry source=%r mark=%s", source, mark)
    result = Nod(source, mark or source.name)
    logger.debug("nod exit result=%r", result)
    return result

def tact(start: Nod, end: Nod, mark: str = "touch") -> Tact:
    """Create a directed native contact."""
    logger.debug("tact entry start=%r end=%r mark=%s", start, end, mark)
    result = Tact(start, end, mark)
    logger.debug("tact exit result=%r", result)
    return result

def nod_key(item: Nod) -> str:
    """Return the stable native nod key used by observers."""
    logger.debug("nod_key entry item=%r", item)
    result = f"{item.residue.name}:{item.mark}"
    logger.debug("nod_key exit result=%s", result)
    return result

def breath_boundary(item: Breath) -> tuple[Nod, Nod] | None:
    """Return start/end nods for a nonempty breath."""
    logger.debug("breath_boundary entry count=%d", len(item.tacts))
    result = (item.anchor, item.anchor) if not item.tacts and item.anchor is not None else None if not item.tacts else (item.tacts[0].start, item.tacts[-1].end)
    logger.debug("breath_boundary exit result=%r", result)
    return result

def silent_breath(anchor: Nod) -> Breath:
    """Create the anchored silent breath used by intrinsic zero."""
    logger.debug("silent_breath entry anchor=%r", anchor)
    result = Breath((), anchor)
    logger.debug("silent_breath exit result=%r", result)
    return result

def breath(*tacts: Tact) -> Breath | NativeObstruction:
    """Assemble contiguous contacts into a native breath.

    Contiguity compares nods by host structural equality — the finest external
    shadow test under the docs/06 §3 license, not an eliminated equality.
    """
    logger.debug("breath entry count=%d", len(tacts))
    if not tacts:
        result = NativeObstruction("breath", "empty-breath", ())
        logger.debug("breath exit obstruction=%r", result)
        return result
    for left, right in zip(tacts, tacts[1:]):
        if left.end != right.start:
            result = NativeObstruction("breath", "non-contiguous-tacts", (nod_key(left.end), nod_key(right.start)))
            logger.debug("breath exit obstruction=%r", result)
            return result
    result = Breath(tuple(tacts))
    logger.debug("breath exit result=%r", result)
    return result

def stitch(left: Breath, right: Breath) -> Breath | NativeObstruction:
    """Stitch two breaths when their boundary nods agree.

    Boundary agreement uses host structural equality (docs/06 §3 license).
    """
    logger.debug("stitch entry left=%r right=%r", left, right)
    lb, rb = breath_boundary(left), breath_boundary(right)
    if lb is None or rb is None or lb[1] != rb[0]:
        residue = (() if lb is None else (nod_key(lb[1]),)) + (() if rb is None else (nod_key(rb[0]),))
        result = NativeObstruction("stitch", "boundary-mismatch", residue)
        logger.debug("stitch exit obstruction=%r", result)
        return result
    tacts = left.tacts + right.tacts
    result = Breath(tacts, (left.anchor or right.anchor) if not tacts else None)
    logger.debug("stitch exit result=%r", result)
    return result

def mode(item: Breath, observer: NativeObserver | None = None) -> Mode | NativeObstruction:
    """Wrap a breath as a mode only when recurrence closes natively or by observer.

    Default closure (`observer is None`) compares boundary nods by host
    structural equality — the finest external test (docs/06 §3), recorded as
    the `native-cycle` observer name. It is not an eliminated equality; pass an
    observer explicitly for coarser, explicitly indexed closure.
    """
    logger.debug("mode entry breath=%r observer=%r", item, observer)
    boundary = breath_boundary(item)
    if boundary is None:
        result = NativeObstruction("mode", "empty-breath", ())
        logger.debug("mode exit obstruction=%r", result)
        return result
    start, end = boundary
    closed = start == end or (observer is not None and observer.response(start) == observer.response(end))
    if not closed:
        result = NativeObstruction("mode", "open-breath", (nod_key(start), nod_key(end)))
        logger.debug("mode exit obstruction=%r", result)
        return result
    result = Mode(item, "native-cycle" if observer is None else observer.name)
    logger.debug("mode exit result=%r", result)
    return result

def _boundary_response(obj: NativeObject) -> NativeResponse:
    logger.debug("_boundary_response entry obj=%r", obj)
    if isinstance(obj, Rez):
        result: NativeResponse = ("rez", obj.name)
    elif isinstance(obj, Nod):
        result = ("nod", nod_key(obj))
    elif isinstance(obj, Tact):
        result = ("tact", nod_key(obj.start), nod_key(obj.end))
    elif isinstance(obj, Breath):
        b = breath_boundary(obj); result = ("breath", "∅") if b is None else ("breath", nod_key(b[0]), nod_key(b[1]))
    elif isinstance(obj, Mode):
        result = ("mode", _boundary_response(obj.breath), obj.observer)
    elif isinstance(obj, NativeObserver):
        result = ("observer", obj.name)
    else:
        result = ("unknown", type(obj).__name__)
    logger.debug("_boundary_response exit result=%r", result)
    return result

def _length_response(obj: NativeObject) -> NativeResponse:
    logger.debug("_length_response entry obj=%r", obj)
    if isinstance(obj, Mode):
        result: NativeResponse = len(obj.breath.tacts)
    elif isinstance(obj, Breath):
        result = len(obj.tacts)
    elif isinstance(obj, (Rez, Nod, Tact)):
        result = 1
    else:
        result = 1
    logger.debug("_length_response exit result=%r", result)
    return result

def _shape_response(obj: NativeObject) -> NativeResponse:
    logger.debug("_shape_response entry obj=%r", obj)
    if isinstance(obj, Tact):
        result: NativeResponse = (obj.mark,)
    elif isinstance(obj, (Breath, Mode)):
        breath_obj = obj.breath if isinstance(obj, Mode) else obj
        result = tuple(t.mark for t in breath_obj.tacts)
    else:
        result = _boundary_response(obj)
    logger.debug("_shape_response exit result=%r", result)
    return result

def _residue_response(obj: NativeObject) -> NativeResponse:
    logger.debug("_residue_response entry obj=%r", obj)
    if isinstance(obj, Rez):
        result: NativeResponse = (obj.name,)
    elif isinstance(obj, Nod):
        result = (obj.residue.name,)
    elif isinstance(obj, Tact):
        result = (obj.start.residue.name, obj.end.residue.name)
    elif isinstance(obj, (Breath, Mode)):
        breath_obj = obj.breath if isinstance(obj, Mode) else obj
        result = ((breath_obj.anchor.residue.name,) if not breath_obj.tacts and breath_obj.anchor is not None else tuple(dict.fromkeys(x for t in breath_obj.tacts for x in (t.start.residue.name, t.end.residue.name))))
    else:
        result = ()
    logger.debug("_residue_response exit result=%r", result)
    return result

def native_observers() -> tuple[NativeObserver, ...]:
    """Return canonical native observers; none is a primary shadow model."""
    logger.debug("native_observers entry")
    result = (NativeObserver("boundary", _boundary_response), NativeObserver("length", _length_response), NativeObserver("shape", _shape_response), NativeObserver("residue", _residue_response))
    logger.debug("native_observers exit count=%d", len(result))
    return result

def _observer(name: str | NativeObserver) -> NativeObserver:
    logger.debug("_observer entry name=%r", name)
    if isinstance(name, NativeObserver):
        logger.debug("_observer exit existing=%r", name)
        return name
    table = {item.name: item for item in native_observers()}
    result = table[name]
    logger.debug("_observer exit result=%r", result)
    return result

def observe_native(obj: NativeObject, observer: str | NativeObserver) -> NativeResponse:
    """Observe a native object without changing its ontology."""
    logger.debug("observe_native entry obj=%r observer=%r", obj, observer)
    obs = _observer(observer)
    result = obs.response(obj)
    logger.debug("observe_native exit result=%r", result)
    return result

def echo_native(left: NativeObject, right: NativeObject, observer: str | NativeObserver) -> NativeEcho:
    """Compare native objects by an explicit observer response."""
    logger.debug("echo_native entry left=%r right=%r observer=%r", left, right, observer)
    obs = _observer(observer)
    lval, rval = obs.response(left), obs.response(right)
    result = NativeEcho(obs.name, lval, rval, lval == rval)
    logger.debug("echo_native exit result=%r", result)
    return result

def native_shadow_rows(obj: NativeObject) -> tuple[NativeShadowRow, ...]:
    """Derive school-readable rows after native observation."""
    logger.debug("native_shadow_rows entry obj=%r", obj)
    kind = type(obj).__name__.lower()
    result = tuple(NativeShadowRow(kind, obs.name, obs.response(obj), "observer-derived; not primary ontology") for obs in native_observers())
    logger.debug("native_shadow_rows exit count=%d", len(result))
    return result

def shadow_from_native(obj: NativeObject, observer: str) -> NativeShadowRow:
    """Return one observer-derived shadow row."""
    logger.debug("shadow_from_native entry obj=%r observer=%s", obj, observer)
    result = next(row for row in native_shadow_rows(obj) if row.observer == observer)
    logger.debug("shadow_from_native exit result=%r", result)
    return result

def native_runtime_checklist() -> tuple[str, ...]:
    """Return F4 runtime acceptance checks."""
    logger.debug("native_runtime_checklist entry")
    result = ("rez/nod/tact/breath/mode are concrete runtime objects", "breaths require contiguous tact boundaries", "modes reject open recurrence as obstruction", "echo is observer-indexed over native responses", "school shadows are derived observer rows")
    logger.debug("native_runtime_checklist exit count=%d", len(result))
    return result

def native_runtime_report() -> dict[str, object]:
    """Return a compact executable F4 smoke report."""
    logger.debug("native_runtime_report entry")
    a, b = nod(rez("a")), nod(rez("b"))
    first = breath(tact(a, b, "rise"), tact(b, a, "fall"))
    second = breath(tact(a, b, "rise"), tact(b, a, "fall"))
    wrapped = mode(first) if isinstance(first, Breath) else first
    echo = echo_native(first, second, "shape") if isinstance(first, Breath) and isinstance(second, Breath) else None
    result = {"objects": 5, "checklist": len(native_runtime_checklist()), "mode_ready": isinstance(wrapped, Mode), "shape_echo": bool(echo and echo.echoed), "shadows": len(native_shadow_rows(wrapped)) if isinstance(wrapped, Mode) else 0}
    logger.debug("native_runtime_report exit result=%r", result)
    return result
