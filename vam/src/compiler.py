"""Lower Veyra Core Language terms into VAM instruction IR."""
from __future__ import annotations

from dataclasses import dataclass
import logging

from src.core.language import VeyraExpr, expr_kind, normal_text, normalize_veyra, parse_veyra
from src.core.native_runtime import NativeEcho, NativeObstruction
from src.core.semantic_kernel import evaluate_native

from .assembly import disassemble
from .model import Instruction

logger = logging.getLogger(__name__)
SUPPORTED_OBSERVERS = {"kind", "label", "length", "trace", "boundary"}


class VamCompileError(ValueError):
    """Raised when a Core term has no conservative VAM lowering yet."""


@dataclass(frozen=True)
class CompileResult:
    """Compiled VAM program plus the registers carrying semantic roots."""

    source: str
    program: tuple[Instruction, ...]
    root_register: str
    cert_register: str | None = None


class _Compiler:
    """Single-use Core-to-VAM lowering context."""

    def __init__(self) -> None:
        logger.debug("compiler init entry")
        self._next_register = 1
        self._program: list[Instruction] = []
        logger.debug("compiler init exit")

    @property
    def program(self) -> tuple[Instruction, ...]:
        """Return immutable emitted program."""
        return tuple(self._program)

    def emit(self, op: str, *args: object) -> str:
        """Emit one destination-style VAM instruction."""
        logger.debug("compiler emit entry op=%s argc=%d", op, len(args))
        dst = f"%r{self._next_register}"
        self._next_register += 1
        self._program.append(Instruction(op.upper(), (dst, *args)))
        logger.debug("compiler emit exit dst=%s op=%s", dst, op)
        return dst

    def compile(self, expr: VeyraExpr) -> str:
        """Compile one normalized Core expression and return its destination register."""
        logger.debug("compiler compile entry expr=%s", normal_text(expr))
        if expr.head == "rez" and not expr.args:
            result = self.emit("REZ", _label(expr, "rez"))
        elif expr.head == "nod":
            result = self._compile_nod(expr)
        elif expr.head == "tact" and len(expr.args) == 2:
            left, right = (self.compile(expr.args[0]), self.compile(expr.args[1]))
            result = self.emit("TACT", left, right, "touch")
        elif expr.head == "breath" and expr.args:
            result = self.emit("BREATH", *(self.compile(arg) for arg in expr.args))
        elif expr.head == "mode" and len(expr.args) == 1:
            result = self.emit("MODE", self.compile(expr.args[0]))
        elif expr.head == "observer" and not expr.args:
            label = _label(expr, "kind")
            if label not in SUPPORTED_OBSERVERS:
                logger.error("compiler observer unsupported label=%s", label)
                raise VamCompileError(f"unsupported observer for VAM lowering: {label}")
            result = self.emit("OBSERVER", label)
        elif expr.head == "echo" and len(expr.args) == 3:
            left, right, observer = (self.compile(expr.args[0]), self.compile(expr.args[1]), self.compile(expr.args[2]))
            result = self.emit("ECHO", left, right, observer)
        elif expr.head == "shell" and expr.args:
            from .shell import lower_shell

            result = lower_shell(self, expr)
        else:
            logger.error("compiler compile unsupported expr=%s", normal_text(expr))
            raise VamCompileError(f"unsupported Core expression for VAM lowering: {normal_text(expr)}")
        logger.debug("compiler compile exit expr=%s dst=%s", normal_text(expr), result)
        return result

    def _compile_nod(self, expr: VeyraExpr) -> str:
        logger.debug("compiler nod entry expr=%s", normal_text(expr))
        if expr.label is not None:
            rez = self.emit("REZ", expr.label)
            result = self.emit("NOD", rez, expr.label)
        elif len(expr.args) == 1 and expr.args[0].head == "rez":
            rez = self.compile(expr.args[0])
            result = self.emit("NOD", rez, _label(expr.args[0], "nod"))
        elif not expr.args:
            rez = self.emit("REZ", "nod")
            result = self.emit("NOD", rez, "nod")
        else:
            logger.error("compiler nod unsupported expr=%s", normal_text(expr))
            raise VamCompileError(f"unsupported nod form: {normal_text(expr)}")
        logger.debug("compiler nod exit dst=%s", result)
        return result


def _label(expr: VeyraExpr, fallback: str) -> str:
    logger.debug("label entry expr=%r fallback=%s", expr, fallback)
    result = expr.label if expr.label is not None else fallback
    logger.debug("label exit result=%s", result)
    return result


def compile_expr(expr: VeyraExpr, *, certify: bool = True, claim: str = "core-echo", boundary: str = "finite Core lowering") -> CompileResult:
    """Compile a Core expression into VAM IR, optionally adding a certificate row."""
    logger.debug("compile_expr entry certify=%s claim=%s", certify, claim)
    normal = normalize_veyra(expr)
    checked = expr_kind(normal)
    if not checked.ok:
        logger.error("compile_expr bad core assembly obstruction=%s", checked.obstruction)
        raise VamCompileError(f"bad Core expression for VAM lowering: {checked.obstruction}")
    semantic = evaluate_native(normal)
    relation_failure = semantic.status == "blocked" and isinstance(semantic.value, NativeEcho)
    shell_unknown = semantic.status == "unknown" and normal.head == "shell"
    if semantic.status != "ready" and not relation_failure and not shell_unknown:
        obstruction = semantic.obstruction or type(semantic.value).__name__
        logger.error("compile_expr strict semantic block obstruction=%s", obstruction)
        raise VamCompileError(f"strict Core semantics blocked VAM lowering: {obstruction}")
    if isinstance(semantic.value, NativeObstruction):
        logger.error("compile_expr native obstruction=%s", semantic.value.reason)
        raise VamCompileError(f"strict Core semantics blocked VAM lowering: {semantic.value.reason}")
    compiler = _Compiler()
    root_register = compiler.compile(normal)
    cert_register = compiler.emit("CERT", claim, root_register, boundary) if certify and normal.head != "shell" else None
    result = CompileResult(normal_text(normal), compiler.program, root_register, cert_register)
    logger.debug("compile_expr exit instructions=%d root=%s cert=%s", len(result.program), root_register, cert_register)
    return result


def compile_source(source: str, *, certify: bool = True, claim: str = "core-echo", boundary: str = "finite Core lowering") -> CompileResult:
    """Parse and compile Core Language source into VAM IR."""
    logger.debug("compile_source entry chars=%d certify=%s", len(source), certify)
    result = compile_expr(parse_veyra(source), certify=certify, claim=claim, boundary=boundary)
    logger.debug("compile_source exit instructions=%d", len(result.program))
    return result


def compile_to_vmasm(source: str, *, certify: bool = True, claim: str = "core-echo", boundary: str = "finite Core lowering") -> str:
    """Compile Core source and render canonical `.vmasm` text."""
    logger.debug("compile_to_vmasm entry chars=%d", len(source))
    result = disassemble(compile_source(source, certify=certify, claim=claim, boundary=boundary).program)
    logger.debug("compile_to_vmasm exit chars=%d", len(result))
    return result
