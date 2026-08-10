"""Text `.vmasm` assembler/disassembler for VAM v0.2."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Iterable

from .model import Instruction

logger = logging.getLogger(__name__)


def _strip_comment(line: str) -> str:
    in_string = False
    escaped = False
    out: list[str] = []
    for char in line:
        if escaped:
            out.append(char)
            escaped = False
            continue
        if char == "\\" and in_string:
            out.append(char)
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            out.append(char)
            continue
        if char == ";" and not in_string:
            break
        out.append(char)
    return "".join(out).strip()


def _split_args(rest: str) -> list[str]:
    args: list[str] = []
    current: list[str] = []
    in_string = False
    escaped = False
    for char in rest:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\" and in_string:
            current.append(char)
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            current.append(char)
            continue
        if char == "," and not in_string:
            args.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    tail = "".join(current).strip()
    if tail:
        args.append(tail)
    return args


def _parse_arg(token: str) -> Any:
    if token.startswith('"') and token.endswith('"'):
        return json.loads(token)
    if token.startswith("%r") and token[2:].isdigit():
        return token
    if token.isdigit() or (token.startswith("-") and token[1:].isdigit()):
        return int(token)
    return token


def parse_vmasm(source: str) -> list[Instruction]:
    """Parse VAM assembly text into instruction IR."""
    logger.debug("parse_vmasm entry chars=%d", len(source))
    program: list[Instruction] = []
    for line_no, raw in enumerate(source.splitlines(), start=1):
        line = _strip_comment(raw)
        if not line:
            continue
        parts = line.split(None, 1)
        op = parts[0].upper()
        args = tuple(_parse_arg(arg) for arg in _split_args(parts[1] if len(parts) == 2 else ""))
        program.append(Instruction(op, args, line_no))
    logger.debug("parse_vmasm exit instructions=%d", len(program))
    return program


def _format_arg(arg: Any) -> str:
    if isinstance(arg, str) and arg.startswith("%r") and arg[2:].isdigit():
        return arg
    if isinstance(arg, int):
        return str(arg)
    return json.dumps(str(arg), ensure_ascii=False)


def disassemble(program: Iterable[Instruction]) -> str:
    """Render instruction IR back to canonical `.vmasm` text."""
    program = list(program)
    logger.debug("disassemble entry instructions=%d", len(program))
    rows = []
    for inst in program:
        args = ", ".join(_format_arg(arg) for arg in inst.args)
        rows.append(f"{inst.op} {args}" if args else inst.op)
    result = "\n".join(rows) + ("\n" if rows else "")
    logger.debug("disassemble exit chars=%d", len(result))
    return result


def read_vmasm(path: str | Path) -> list[Instruction]:
    """Read and parse a `.vmasm` file."""
    logger.debug("read_vmasm entry path=%s", path)
    program = parse_vmasm(Path(path).read_text(encoding="utf-8"))
    logger.debug("read_vmasm exit instructions=%d", len(program))
    return program
