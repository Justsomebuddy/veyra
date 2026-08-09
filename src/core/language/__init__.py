"""Veyra Core Language v0.1: grammar, types, echo, normalization, inference."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import logging
logger = logging.getLogger(__name__)
class VeyraKind(str, Enum):
    """Core expression kinds."""
    REZ = "rez"; NOD = "nod"; TACT = "tact"; BREATH = "breath"; MODE = "mode"
    TRACE = "trace"; WEIGHT = "weight"; RELATION = "relation"; OBSERVER = "observer"
    OBSTRUCTION = "obstruction"; VALUE = "value"
@dataclass(frozen=True)
class VeyraExpr:
    """Parsed expression node."""
    head: str
    args: tuple["VeyraExpr", ...] = ()
    label: str | None = None
@dataclass(frozen=True)
class VeyraCheck:
    """Type/inference result."""
    ok: bool
    status: str
    kind: VeyraKind | None
    obstruction: str = ""
@dataclass(frozen=True)
class VeyraInterpretation:
    """Full interpreter result."""
    source: str
    parsed: VeyraExpr
    normal: str
    check: VeyraCheck
    semantic: dict[str, object]
@dataclass(frozen=True)
class SchoolTranslation:
    """One school-to-Veyra translation row."""
    school: str
    veyra: str
    note: str
ATOM_KINDS = {"rez", "nod", "observer", "value", "obstruct"}
KNOWN_OBSERVERS = {"kind", "label", "length", "trace", "boundary"}
class _Parser:
    """Recursive atom/call parser."""
    def __init__(self, source: str) -> None:
        logger.debug("_Parser.__init__ entry len=%d", len(source))
        self.source = source; self.index = 0
        logger.debug("_Parser.__init__ exit")
    def parse(self) -> VeyraExpr:
        logger.debug("_Parser.parse entry")
        expr = self.expr(); self.skip()
        if self.index != len(self.source):
            logger.error("_Parser.parse trailing index=%d", self.index)
            raise ValueError(f"trailing source at {self.index}")
        logger.debug("_Parser.parse exit expr=%r", expr)
        return expr
    def expr(self) -> VeyraExpr:
        logger.debug("_Parser.expr entry index=%d", self.index)
        self.skip(); head = self.name().lower(); self.skip(); char = self.peek()
        if char == ":":
            self.index += 1; result = VeyraExpr(head, (), self.label().strip().lower())
        elif char == "(":
            self.index += 1; args: list[VeyraExpr] = []; self.skip()
            if self.peek() != ")":
                while True:
                    args.append(self.expr()); self.skip()
                    if self.peek() != ",":
                        break
                    self.index += 1
            if self.peek() != ")":
                logger.error("_Parser.expr missing close index=%d", self.index)
                raise ValueError(f"missing ')' at {self.index}")
            self.index += 1; result = VeyraExpr(head, tuple(args))
        else:
            result = VeyraExpr(head)
        logger.debug("_Parser.expr exit result=%r", result)
        return result
    def name(self) -> str:
        logger.debug("_Parser.name entry index=%d", self.index)
        start = self.index
        while self.index < len(self.source) and (self.source[self.index].isalnum() or self.source[self.index] in "_-τ"):
            self.index += 1
        if start == self.index:
            logger.error("_Parser.name empty index=%d", self.index)
            raise ValueError(f"expected name at {self.index}")
        result = self.source[start:self.index]
        logger.debug("_Parser.name exit result=%s", result)
        return result
    def label(self) -> str:
        logger.debug("_Parser.label entry index=%d", self.index)
        start = self.index
        while self.index < len(self.source) and self.source[self.index] not in ",)":
            self.index += 1
        if start == self.index:
            logger.error("_Parser.label empty index=%d", self.index)
            raise ValueError(f"expected label at {self.index}")
        result = self.source[start:self.index]
        logger.debug("_Parser.label exit result=%s", result)
        return result
    def skip(self) -> None:
        logger.debug("_Parser.skip entry index=%d", self.index)
        while self.index < len(self.source) and self.source[self.index].isspace():
            self.index += 1
        logger.debug("_Parser.skip exit index=%d", self.index)
    def peek(self) -> str:
        logger.debug("_Parser.peek entry index=%d", self.index)
        result = self.source[self.index] if self.index < len(self.source) else ""
        logger.debug("_Parser.peek exit result=%r", result)
        return result
def parse_veyra(source: str) -> VeyraExpr:
    """Parse one Veyra expression."""
    logger.debug("parse_veyra entry source=%r", source)
    result = _Parser(source).parse()
    logger.debug("parse_veyra exit result=%r", result)
    return result
def expr_kind(expr: VeyraExpr) -> VeyraCheck:
    """Return kind check for an expression."""
    logger.debug("expr_kind entry expr=%r", expr)
    try:
        result = VeyraCheck(True, "ready", _kind_inner(expr))
    except ValueError as exc:
        result = VeyraCheck(False, "blocked", None, str(exc))
    logger.debug("expr_kind exit result=%r", result)
    return result
def _kind_inner(expr: VeyraExpr) -> VeyraKind:
    logger.debug("_kind_inner entry expr=%r", expr)
    if expr.label is not None:
        if expr.head == "obstruct":
            result = VeyraKind.OBSTRUCTION
        elif expr.head in ATOM_KINDS:
            result = VeyraKind(expr.head)
        else:
            logger.error("_kind_inner unknown atom=%s", expr.head)
            raise ValueError(f"unknown atom kind {expr.head}")
        logger.debug("_kind_inner exit result=%s", result)
        return result
    child = tuple(_kind_inner(arg) for arg in expr.args)
    ok = {
        "rez": child == (), "nod": child in {(), (VeyraKind.REZ,)},
        "tact": child == (VeyraKind.NOD, VeyraKind.NOD),
        "breath": bool(child) and all(k == VeyraKind.TACT for k in child),
        "mode": child == (VeyraKind.BREATH,), "trace": len(child) == 1,
        "weight": child == (VeyraKind.TRACE, VeyraKind.VALUE),
        "observer": child == (), "echo": len(child) == 3 and child[2] == VeyraKind.OBSERVER,
        "shell": bool(child) and all(k == VeyraKind.RELATION for k in child),
        "obstruct": child == (),
    }.get(expr.head, False)
    if not ok:
        logger.error("_kind_inner bad assembly head=%s child=%r", expr.head, child)
        raise ValueError(f"bad assembly {expr.head}{child}")
    result = VeyraKind.OBSTRUCTION if expr.head == "obstruct" else VeyraKind.RELATION if expr.head in {"echo", "shell"} else VeyraKind(expr.head)
    logger.debug("_kind_inner exit result=%s", result)
    return result
def normalize_veyra(expr: VeyraExpr) -> VeyraExpr:
    """Return canonical expression form."""
    logger.debug("normalize_veyra entry expr=%r", expr)
    args = tuple(normalize_veyra(arg) for arg in expr.args)
    if expr.head == "shell":
        args = tuple(sorted(args, key=normal_text))
    if expr.head == "echo" and len(args) == 3:
        args = tuple(sorted(args[:2], key=normal_text)) + (args[2],)
    result = VeyraExpr(expr.head.lower(), args, expr.label.strip().lower() if expr.label else None)
    logger.debug("normalize_veyra exit result=%r", result)
    return result
def normal_text(expr: VeyraExpr) -> str:
    """Render canonical text."""
    logger.debug("normal_text entry expr=%r", expr)
    result = f"{expr.head}:{expr.label}" if expr.label is not None else expr.head if not expr.args else f"{expr.head}(" + ",".join(normal_text(a) for a in expr.args) + ")"
    logger.debug("normal_text exit result=%s", result)
    return result
def infer_veyra(expr: VeyraExpr) -> VeyraCheck:
    """Infer status through the single strict native semantic kernel."""
    logger.debug("infer_veyra entry expr=%r", expr)
    typed = expr_kind(expr)
    if not typed.ok:
        logger.debug("infer_veyra exit typed=%r", typed)
        return typed
    normal = normalize_veyra(expr)
    from ..kernel.semantic_kernel import evaluate_native
    native = evaluate_native(normal)
    result = VeyraCheck(native.status == "ready", native.status, typed.kind, native.obstruction)
    logger.debug("infer_veyra exit result=%r", result)
    return result
def _school_length_shadow(expr: VeyraExpr) -> int:
    logger.debug("_school_length_shadow entry expr=%r", expr)
    result = len(expr.label) if expr.label is not None else len(expr.args) if expr.head == "breath" else sum(_school_length_shadow(arg) for arg in expr.args)
    logger.debug("_school_length_shadow exit result=%d", result)
    return result
def _school_boundary_shadow(expr: VeyraExpr) -> tuple[str, str] | str:
    logger.debug("_school_boundary_shadow entry expr=%r", expr)
    if expr.head == "tact" and len(expr.args) == 2:
        result: tuple[str, str] | str = (normal_text(expr.args[0]), normal_text(expr.args[1]))
    elif expr.head in {"breath", "mode"} and expr.args:
        seq = expr.args if expr.head == "breath" else expr.args[0].args
        first, last = _school_boundary_shadow(seq[0]), _school_boundary_shadow(seq[-1])
        result = (first[0], last[1]) if isinstance(first, tuple) and isinstance(last, tuple) else "opaque"
    else:
        result = "opaque"
    logger.debug("_school_boundary_shadow exit result=%r", result)
    return result
def _nod_labels(expr: VeyraExpr) -> tuple[str, ...]:
    logger.debug("_nod_labels entry expr=%r", expr)
    if expr.head == "nod" and expr.label is not None:
        result = (expr.label,)
    else:
        result = tuple(label for arg in expr.args for label in _nod_labels(arg))
    logger.debug("_nod_labels exit result=%r", result)
    return result

def semantic_shadow(expr: VeyraExpr, domain: str = "generic") -> dict[str, object]:
    """Project expression into a declared external domain."""
    logger.debug("semantic_shadow entry domain=%s expr=%r", domain, expr)
    normal = normalize_veyra(expr); labels = _nod_labels(normal); length = _school_length_shadow(normal)
    result: dict[str, object] = {"domain": domain, "kind": str(expr_kind(normal).kind), "normal": normal_text(normal)}
    if domain == "arithmetic":
        result["length"] = length
    elif domain == "geometry":
        result["boundary"] = _school_boundary_shadow(normal)
    elif domain == "logic":
        check = infer_veyra(normal); result.update({"status": check.status, "obstruction": check.obstruction})
    elif domain == "analysis":
        result.update({"length": length, "variation": max(0, length - 1), "boundary": _school_boundary_shadow(normal)})
    elif domain == "topology":
        boundary = _school_boundary_shadow(normal); result.update({"boundary": boundary, "component_count": len(set(labels)), "deformation_class": (boundary, len(set(labels)))})
    elif domain == "probability":
        result.update({"outcomes": labels, "sample_space": tuple(sorted(set(labels))), "sample_size": len(labels)})
    elif domain == "statistics":
        support = tuple(sorted(set(labels))); result.update({"sample_size": len(labels), "support_size": len(support), "length": length})
    logger.debug("semantic_shadow exit result=%r", result)
    return result
def interpret_veyra(source: str, domain: str = "generic") -> VeyraInterpretation:
    """Parse, type-check, normalize, infer, and shadow source."""
    logger.debug("interpret_veyra entry source=%r domain=%s", source, domain)
    parsed = parse_veyra(source); normal = normalize_veyra(parsed); check = infer_veyra(normal)
    result = VeyraInterpretation(source, parsed, normal_text(normal), check, semantic_shadow(normal, domain))
    logger.debug("interpret_veyra exit result=%r", result)
    return result
def school_translation_table() -> tuple[SchoolTranslation, ...]:
    """Return first school-to-Veyra translation table."""
    logger.debug("school_translation_table entry")
    result = (
        SchoolTranslation("object", "typed Veyra expression", "objecthood is parse/type acceptance"),
        SchoolTranslation("equality", "echo(left,right,observer:trace)", "identity becomes observer-indexed indistinguishability"),
        SchoolTranslation("number", "mode(breath(...))", "numbers shadow closed transition lengths"),
        SchoolTranslation("point", "nod(rez:distinction)", "point is distinction residue"),
        SchoolTranslation("segment", "breath(tact(nod:a,nod:b),...)", "segment is directed finite transfer"),
        SchoolTranslation("proof", "infer_veyra(term).status == ready", "proof is rule-checked readiness"),
        SchoolTranslation("counterexample", "infer_veyra(term).status == blocked", "failed echo/assembly records obstruction"),
        SchoolTranslation("normal form", "normal_text(normalize_veyra(term))", "comparison goes through canonical trace"),
        SchoolTranslation("model", "semantic_shadow(term, domain)", "external math is a declared shadow"),
    )
    logger.debug("school_translation_table exit count=%d", len(result))
    return result
def core_language_checklist() -> tuple[str, ...]:
    """Return the nine priority core-language layers covered by v0.1."""
    logger.debug("core_language_checklist entry")
    result = ("grammar", "types", "assembly-rules", "echo-relation", "inference-logic", "normal-form", "semantic-shadows", "minimal-interpreter", "school-translation-table")
    logger.debug("core_language_checklist exit count=%d", len(result))
    return result
