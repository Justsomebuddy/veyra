"""Canonical executable-content binding for theorem-promotion handlers."""
from __future__ import annotations

from collections.abc import Callable
import logging
from types import CodeType, FunctionType
from typing import cast

from .proof_core_codec import canonical_json, digest_data

logger = logging.getLogger(__name__)
HANDLER_EXECUTABLE_DOMAIN = "veyra-layer-theorem-handler-executable-v1"


def _constant_data(value: object) -> object:
    """Encode exact code constants without repr- or address-dependent values."""
    logger.debug(
        "layer_theorem_contract_executable._constant_data entry type=%s",
        type(value).__name__,
    )
    if value is None or type(value) in {bool, int, str}:
        result: object = {"type": type(value).__name__, "value": value}
    elif type(value) is bytes:
        result = {"type": "bytes", "hex": value.hex()}
    elif type(value) is float:
        result = {"type": "float", "hex": value.hex()}
    elif type(value) is complex:
        result = {
            "type": "complex",
            "real": value.real.hex(),
            "imag": value.imag.hex(),
        }
    elif type(value) is tuple:
        result = {"type": "tuple", "items": [_constant_data(item) for item in value]}
    elif type(value) is frozenset:
        items = [_constant_data(item) for item in value]
        result = {
            "type": "frozenset",
            "items": sorted(items, key=canonical_json),
        }
    elif type(value) is CodeType:
        result = {"type": "code", "value": _code_data(value)}
    elif value is Ellipsis:
        result = {"type": "ellipsis"}
    else:
        logger.error(
            "layer_theorem_contract_executable constant rejected type=%s",
            type(value).__name__,
        )
        raise TypeError("unsupported-handler-code-constant")
    logger.debug(
        "layer_theorem_contract_executable._constant_data exit type=%s",
        type(value).__name__,
    )
    return result


def _code_data(code: CodeType) -> dict[str, object]:
    """Return line/path-independent executable semantics for one code object."""
    logger.debug(
        "layer_theorem_contract_executable._code_data entry name=%s",
        code.co_name,
    )
    result = {
        "name": code.co_name,
        "qualname": code.co_qualname,
        "argcount": code.co_argcount,
        "posonlyargcount": code.co_posonlyargcount,
        "kwonlyargcount": code.co_kwonlyargcount,
        "nlocals": code.co_nlocals,
        "stacksize": code.co_stacksize,
        "flags": code.co_flags,
        "bytecode": code.co_code.hex(),
        "constants": [_constant_data(item) for item in code.co_consts],
        "names": list(code.co_names),
        "varnames": list(code.co_varnames),
        "freevars": list(code.co_freevars),
        "cellvars": list(code.co_cellvars),
        "exceptiontable": code.co_exceptiontable.hex(),
    }
    logger.debug(
        "layer_theorem_contract_executable._code_data exit name=%s bytes=%d",
        code.co_name,
        len(code.co_code),
    )
    return result


def _function_data(function: Callable[..., object]) -> dict[str, object]:
    """Bind one exact Python function's identity, code, and call defaults."""
    logger.debug(
        "layer_theorem_contract_executable._function_data entry type=%s",
        type(function).__name__,
    )
    if type(function) is not FunctionType:
        logger.error(
            "layer_theorem_contract_executable function rejected type=%s",
            type(function).__name__,
        )
        raise TypeError("unsupported-theorem-handler-callable")
    exact_function = cast(FunctionType, function)
    result = {
        "module": exact_function.__module__,
        "qualname": exact_function.__qualname__,
        "code": _code_data(exact_function.__code__),
        "defaults": _constant_data(exact_function.__defaults__),
        "kwdefaults": (
            None
            if exact_function.__kwdefaults__ is None
            else {
                key: _constant_data(value)
                for key, value in sorted(exact_function.__kwdefaults__.items())
            }
        ),
    }
    logger.debug(
        "layer_theorem_contract_executable._function_data exit function=%s",
        exact_function.__qualname__,
    )
    return result


def handler_executable_digest(
    handler_id: str,
    handlers: tuple[tuple[str, Callable[..., object]], ...],
) -> str:
    """Digest ordered executable slots for one exact promotion handler."""
    logger.debug(
        "handler_executable_digest entry handler=%s slots=%d",
        handler_id,
        len(handlers),
    )
    if type(handler_id) is not str or not handler_id:
        logger.error("handler_executable_digest invalid handler id")
        raise ValueError("invalid-theorem-handler-id")
    if type(handlers) is not tuple:
        logger.error(
            "handler_executable_digest invalid manifest type=%s",
            type(handlers).__name__,
        )
        raise TypeError("invalid-theorem-handler-manifest")
    names = tuple(name for name, _ in handlers)
    if (
        any(type(name) is not str or not name for name in names)
        or len(names) != len(set(names))
    ):
        logger.error("handler_executable_digest invalid slot names=%r", names)
        raise ValueError("invalid-theorem-handler-slots")
    result = digest_data(
        {
            "handler_id": handler_id,
            "handlers": [
                {"slot": name, "function": _function_data(function)}
                for name, function in handlers
            ],
        },
        HANDLER_EXECUTABLE_DOMAIN,
    )
    logger.debug(
        "handler_executable_digest exit handler=%s digest=%s",
        handler_id,
        result,
    )
    return result
