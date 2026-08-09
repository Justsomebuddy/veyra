"""Certificate for the native Veyra F4 runtime."""
from __future__ import annotations
import logging
from ..certify_types import Certificate
from ..native_runtime import Breath, Mode, NativeObstruction, echo_native, mode, native_runtime_checklist, native_shadow_rows, nod, rez, stitch, tact, breath

logger = logging.getLogger(__name__)

def certify_native_runtime_f4() -> Certificate:
    """Certify native rez/nod/tact/breath/mode behavior before shadows."""
    logger.debug("certify_native_runtime_f4 entry")
    a, b, c = nod(rez("a")), nod(rez("b")), nod(rez("c"))
    left = breath(tact(a, b, "rise"))
    right = breath(tact(b, a, "fall"))
    closed = stitch(left, right) if isinstance(left, Breath) and isinstance(right, Breath) else left
    wrapped = mode(closed) if isinstance(closed, Breath) else closed
    open_breath = breath(tact(a, c, "drift"))
    open_mode = mode(open_breath) if isinstance(open_breath, Breath) else open_breath
    echo = echo_native(closed, closed, "shape") if isinstance(closed, Breath) else None
    shadows = native_shadow_rows(wrapped) if isinstance(wrapped, Mode) else ()
    passed = isinstance(wrapped, Mode) and isinstance(open_mode, NativeObstruction) and bool(echo and echo.echoed) and len(shadows) == 4 and len(native_runtime_checklist()) == 5 and all("observer-derived" in row.boundary for row in shadows)
    detail = f"mode={isinstance(wrapped, Mode)} open={getattr(open_mode, 'reason', '')} shadows={len(shadows)}"
    result = Certificate("native_runtime_f4", "native rez/nod/tact/breath/mode runtime with observer-derived shadows", passed, detail, 1)
    logger.debug("certify_native_runtime_f4 exit result=%r", result)
    return result
