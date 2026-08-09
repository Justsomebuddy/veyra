"""Canonical executable-content binding for theorem-promotion handlers.

A handler is bound by the source text that defines it, not by the compiled code
object.  Source is what a reviewer reads and what a tamper would have to change;
bytecode additionally encodes the compiler that produced it, which would pin the
project to one CPython build and make the digest unreproducible on any other.
"""
from __future__ import annotations

from collections.abc import Callable
import inspect
import logging
import textwrap
from types import CodeType, FunctionType
from typing import cast

from .proof_core_codec import canonical_json, digest_data

logger = logging.getLogger(__name__)
HANDLER_EXECUTABLE_DOMAIN = "veyra-layer-theorem-handler-executable-v2"


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
    """Return the interpreter-independent signature of one code object."""
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
    }
    logger.debug(
        "layer_theorem_contract_executable._code_data exit name=%s",
        code.co_name,
    )
    return result


def _source_text(function: FunctionType) -> str:
    """Return the exact defining source of one handler, without its indent."""
    logger.debug(
        "layer_theorem_contract_executable._source_text entry function=%s",
        function.__qualname__,
    )
    try:
        source = inspect.getsource(function)
    except (OSError, TypeError) as exc:
        logger.error(
            "layer_theorem_contract_executable source unavailable function=%s",
            function.__qualname__,
        )
        raise ValueError("theorem-handler-source-unavailable") from exc
    return textwrap.dedent(source).replace("\r\n", "\n").rstrip() + "\n"


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
        "signature": _code_data(exact_function.__code__),
        "source": _source_text(exact_function),
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
