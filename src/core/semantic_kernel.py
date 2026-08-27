"""Strict bridge from Core Language expressions to native Veyra values."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import logging
from collections.abc import Iterable

from .language import KNOWN_OBSERVERS, VeyraExpr, expr_kind, normal_text, normalize_veyra, parse_veyra
from .native_runtime import (
    Breath, Mode, NativeEcho, NativeObject, NativeObstruction, NativeObserver,
    Nod, Rez, Tact, breath, echo_native, mode, native_observers, nod, rez, tact,
)

logger = logging.getLogger(__name__)
AXIOM_ORDER = ("AX-REZ", "AX-NOD", "AX-TACT", "AX-BREATH", "AX-MODE", "AX-OBSERVER", "AX-ECHO", "AX-OBSTRUCTION")
RULE_AXIOMS: dict[str, tuple[str, ...]] = {
    "SK-REZ": ("AX-REZ",), "SK-NOD": ("AX-NOD",), "SK-NOD-ATOM": ("AX-REZ", "AX-NOD"),
    "SK-TACT": ("AX-TACT",), "SK-BREATH": ("AX-BREATH",), "SK-MODE": ("AX-MODE",),
    "SK-OBSERVER": ("AX-OBSERVER",), "SK-ECHO": ("AX-ECHO",), "SK-SHELL": (),
    "SK-BREATH-BLOCK": ("AX-BREATH", "AX-OBSTRUCTION"), "SK-MODE-BLOCK": ("AX-MODE", "AX-OBSTRUCTION"),
    "SK-ECHO-BLOCK": ("AX-ECHO", "AX-OBSTRUCTION"), "SK-ECHO-UNKNOWN": ("AX-ECHO",),
    "SK-SHELL-BLOCK": ("AX-OBSTRUCTION",), "SK-SHELL-UNKNOWN": (),
    "SK-OBSTRUCT": ("AX-OBSTRUCTION",), "SK-BLOCK": ("AX-OBSTRUCTION",),
    "SK-UNKNOWN": ("AX-OBSERVER", "AX-OBSTRUCTION"),
}
RULE_ARITY: dict[str, int | tuple[int, None]] = {
    "SK-REZ": 0, "SK-NOD-ATOM": 0, "SK-OBSERVER": 0, "SK-OBSTRUCT": 0,
    "SK-NOD": 1, "SK-TACT": 2, "SK-MODE": 1, "SK-ECHO": 3,
    "SK-BREATH": (1, None), "SK-SHELL": (1, None), "SK-MODE-BLOCK": 1,
    "SK-ECHO-BLOCK": 3, "SK-ECHO-UNKNOWN": 3, "SK-SHELL-BLOCK": (1, None), "SK-SHELL-UNKNOWN": (1, None),
}


@dataclass(frozen=True)
class DerivationReceipt:
    """One content-addressed semantic rule application."""
    receipt_id: str
    rule_id: str
    premise_ids: tuple[str, ...]
    subject: str
    status: str
    conclusion: str
    obstruction: str
    digest: str


@dataclass(frozen=True)
class ReceiptCheck:
    """Integrity and dependency result for a receipt graph."""
    ok: bool
    errors: tuple[str, ...]
    axiom_closure: tuple[str, ...]


@dataclass(frozen=True)
class SemanticResult:
    """Strict evaluation result with replayable derivation evidence."""
    status: str
    value: object | None
    obstruction: str
    receipts: tuple[DerivationReceipt, ...]

    @property
    def ok(self) -> bool:
        """Return whether evaluation produced a ready native value."""
        logger.debug("SemanticResult.ok entry status=%s", self.status)
        result = self.status == "ready"
        logger.debug("SemanticResult.ok exit result=%s", result)
        return result

    @property
    def axioms(self) -> tuple[str, ...]:
        """Derive, never declare, the exact axiom closure of the receipts."""
        logger.debug("SemanticResult.axioms entry receipts=%d", len(self.receipts))
        result = axiom_closure(self.receipts)
        logger.debug("SemanticResult.axioms exit result=%r", result)
        return result


def _kind_response(obj: NativeObject) -> str:
    logger.debug("_kind_response entry obj=%r", obj)
    result = "observer" if isinstance(obj, NativeObserver) else type(obj).__name__.lower()
    logger.debug("_kind_response exit result=%s", result)
    return result


def _label_response(obj: NativeObject) -> str:
    logger.debug("_label_response entry obj=%r", obj)
    result = obj.name if isinstance(obj, (Rez, NativeObserver)) else obj.mark if isinstance(obj, (Nod, Tact)) else "unlabelled"
    logger.debug("_label_response exit result=%s", result)
    return result


def _stable(value: object) -> str:
    logger.debug("_stable entry type=%s", type(value).__name__)
    if isinstance(value, Rez): data: object = ["rez", value.name]
    elif isinstance(value, Nod): data = ["nod", json.loads(_stable(value.residue)), value.mark]
    elif isinstance(value, Tact): data = ["tact", json.loads(_stable(value.start)), json.loads(_stable(value.end)), value.mark]
    elif isinstance(value, Breath):
        anchor = [["anchor", json.loads(_stable(value.anchor))]] if not value.tacts and value.anchor is not None else []
        data = ["breath", *anchor, *[json.loads(_stable(item)) for item in value.tacts]]
    elif isinstance(value, Mode): data = ["mode", json.loads(_stable(value.breath)), value.observer]
    elif isinstance(value, NativeObserver): data = ["observer", value.name]
    elif isinstance(value, NativeEcho): data = ["echo", value.observer, value.left, value.right, value.echoed]
    elif isinstance(value, NativeObstruction): data = ["obstruction", value.stage, value.reason, value.residue]
    elif isinstance(value, tuple): data = [json.loads(_stable(item)) for item in value]
    else: data = value
    result = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    logger.debug("_stable exit result=%s", result)
    return result


def _trace_response(obj: NativeObject) -> str:
    """Return the injective canonical-serialization response.

    Echo under `trace` therefore coincides with metalanguage equality of exact
    structure (docs/06 §3 license): `trace` is the maximal discrete observer,
    a deliberately God's-eye shadow — not evidence that equality was
    eliminated, and never a substitute for coarser indexed observers.
    """
    logger.debug("_trace_response entry obj=%r", obj)
    result = _stable(obj)
    logger.debug("_trace_response exit result=%s", result)
    return result


def observer_adapter(name: str) -> NativeObserver | None:
    """Resolve every Core observer name to a native observer adapter.

    `KNOWN_OBSERVERS` is a deliberately closed, bounded census for this Core
    Language slice — a scope boundary, not a claim that observerhood is
    globally enumerable or that these five exhaust admissible observers.
    """
    logger.debug("observer_adapter entry name=%s", name)
    canonical = {item.name: item for item in native_observers()}
    adapters = {"kind": NativeObserver("kind", _kind_response), "label": NativeObserver("label", _label_response),
                "trace": NativeObserver("trace", _trace_response), "length": canonical["length"], "boundary": canonical["boundary"]}
    result = adapters.get(name) if name in KNOWN_OBSERVERS else None
    if result is None: logger.error("observer_adapter unknown name=%s", name)
    logger.debug("observer_adapter exit result=%r", result)
    return result


def _receipt(rule: str, premises: tuple[str, ...], subject: str, status: str, value: object, obstruction: str = "") -> DerivationReceipt:
    logger.debug("_receipt entry rule=%s premises=%r subject=%s", rule, premises, subject)
    conclusion = _stable(value)
    body = json.dumps([rule, premises, subject, status, conclusion, obstruction], separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(body.encode()).hexdigest()
    result = DerivationReceipt(f"R-{digest[:20]}", rule, premises, subject, status, conclusion, obstruction, digest)
    logger.debug("_receipt exit id=%s", result.receipt_id)
    return result


def _merge(*groups: tuple[DerivationReceipt, ...], root: DerivationReceipt) -> tuple[DerivationReceipt, ...]:
    logger.debug("_merge entry groups=%d root=%s", len(groups), root.receipt_id)
    rows: dict[str, DerivationReceipt] = {}
    for item in (*[row for group in groups for row in group], root):
        if item.receipt_id in rows and rows[item.receipt_id] != item:
            logger.error("_merge receipt collision id=%s", item.receipt_id)
            raise ValueError(f"receipt collision {item.receipt_id}")
        rows[item.receipt_id] = item
    result = tuple(rows.values())
    logger.debug("_merge exit count=%d", len(result))
    return result


def _finish(rule: str, expr: VeyraExpr, children: tuple[SemanticResult, ...], status: str, value: object | None, obstruction: str = "") -> SemanticResult:
    logger.debug("_finish entry rule=%s status=%s", rule, status)
    premises = tuple(child.receipts[-1].receipt_id for child in children)
    root = _receipt(rule, premises, normal_text(expr), status, value, obstruction)
    result = SemanticResult(status, value, obstruction, _merge(*(child.receipts for child in children), root=root))
    logger.debug("_finish exit receipt=%s", root.receipt_id)
    return result


def _eval(expr: VeyraExpr) -> SemanticResult:
    logger.debug("_eval entry expr=%r", expr)
    typed = expr_kind(expr)
    if not typed.ok:
        logger.error("_eval bad assembly obstruction=%s", typed.obstruction)
        return _finish("SK-BLOCK", expr, (), "blocked", None, typed.obstruction)
    if expr.label is not None or not expr.args:
        label = expr.label or ("kind" if expr.head == "observer" else expr.head)
        if expr.head == "rez": result = _finish("SK-REZ", expr, (), "ready", rez(label))
        elif expr.head == "nod": result = _finish("SK-NOD-ATOM", expr, (), "ready", nod(rez(label), label))
        elif expr.head == "observer":
            obs = observer_adapter(label)
            result = _finish("SK-OBSERVER" if obs else "SK-UNKNOWN", expr, (), "ready" if obs else "unknown", obs, "" if obs else f"unknown observer {label}")
        elif expr.head == "obstruct": result = _finish("SK-OBSTRUCT", expr, (), "blocked", NativeObstruction("core", label, ()))
        else: result = _finish("SK-BLOCK", expr, (), "blocked", None, f"unsupported native atom {expr.head}")
        logger.debug("_eval exit atomic status=%s", result.status)
        return result
    children = tuple(_eval(arg) for arg in expr.args)
    failed = next((item for item in children if item.status == "blocked"), None)
    unknown = next((item for item in children if item.status == "unknown"), None)
    if failed or unknown:
        state = failed or unknown
        blocked_rules = {"breath": "SK-BREATH-BLOCK", "mode": "SK-MODE-BLOCK", "echo": "SK-ECHO-BLOCK", "shell": "SK-SHELL-BLOCK"}
        unknown_rules = {"echo": "SK-ECHO-UNKNOWN", "shell": "SK-SHELL-UNKNOWN"}
        rule = blocked_rules.get(expr.head, "SK-BLOCK") if failed else unknown_rules.get(expr.head, "SK-UNKNOWN")
        result = _finish(rule, expr, children, state.status, state.value, state.obstruction)
        logger.debug("_eval exit propagated status=%s", result.status)
        return result
    values = tuple(item.value for item in children)
    if expr.head == "nod": value = nod(values[0]); rule = "SK-NOD"
    elif expr.head == "tact": value = tact(values[0], values[1]); rule = "SK-TACT"
    elif expr.head == "breath": value = breath(*values); rule = "SK-BREATH"
    elif expr.head == "mode": value = mode(values[0]); rule = "SK-MODE"
    elif expr.head == "echo": value = echo_native(values[0], values[1], values[2]); rule = "SK-ECHO"
    elif expr.head == "shell": value = values; rule = "SK-SHELL"
    else:
        logger.error("_eval unsupported head=%s", expr.head)
        return _finish("SK-BLOCK", expr, children, "blocked", None, f"unsupported native head {expr.head}")
    obstruction = value.reason if isinstance(value, NativeObstruction) else ("echo mismatch" if isinstance(value, NativeEcho) and not value.echoed else "")
    status = "blocked" if obstruction else "ready"
    blocked_rule = {"SK-BREATH": "SK-BREATH-BLOCK", "SK-MODE": "SK-MODE-BLOCK", "SK-ECHO": "SK-ECHO-BLOCK"}.get(rule, "SK-BLOCK")
    result = _finish(blocked_rule if obstruction else rule, expr, children, status, value, obstruction)
    logger.debug("_eval exit status=%s value=%r", result.status, result.value)
    return result


def evaluate_native(expr: VeyraExpr | str) -> SemanticResult:
    """Normalize and strictly evaluate a Core expression in the native runtime."""
    logger.debug("evaluate_native entry expr=%r", expr)
    try:
        parsed = parse_veyra(expr) if isinstance(expr, str) else expr
        result = _eval(normalize_veyra(parsed))
    except (TypeError, ValueError) as exc:
        logger.error("evaluate_native parse/eval error=%s", exc)
        subject = expr if isinstance(expr, str) else repr(expr)
        root = _receipt("SK-BLOCK", (), subject, "blocked", None, str(exc))
        result = SemanticResult("blocked", None, str(exc), (root,))
    logger.debug("evaluate_native exit status=%s", result.status)
    return result


def verify_receipts(receipts: Iterable[DerivationReceipt]) -> ReceiptCheck:
    """Reject unknown, malformed, disconnected, non-replayable receipt graphs."""
    rows = tuple(receipts); logger.debug("verify_receipts entry count=%d", len(rows))
    errors: list[str] = []; table = {row.receipt_id: row for row in rows}
    if len(table) != len(rows): errors.append("duplicate-receipt-id")
    for row in rows:
        if row.rule_id not in RULE_AXIOMS: errors.append(f"unknown-rule:{row.rule_id}")
        errors.extend(f"dangling:{row.receipt_id}:{pid}" for pid in row.premise_ids if pid not in table)
        arity = RULE_ARITY.get(row.rule_id)
        if isinstance(arity, int) and len(row.premise_ids) != arity: errors.append(f"bad-arity:{row.receipt_id}")
        if isinstance(arity, tuple) and len(row.premise_ids) < arity[0]: errors.append(f"bad-arity:{row.receipt_id}")
    visiting: set[str] = set(); visited: set[str] = set()
    def visit(rid: str) -> None:
        logger.debug("verify_receipts.visit entry rid=%s", rid)
        if rid in visiting: errors.append(f"cycle:{rid}"); logger.error("verify_receipts cycle rid=%s", rid); return
        if rid in visited: logger.debug("verify_receipts.visit exit cached"); return
        visiting.add(rid)
        for pid in table[rid].premise_ids:
            if pid in table: visit(pid)
        visiting.remove(rid); visited.add(rid); logger.debug("verify_receipts.visit exit rid=%s", rid)
    for rid in table: visit(rid)
    referenced = {pid for row in rows for pid in row.premise_ids if pid in table}
    roots = set(table) - referenced
    if len(roots) != 1: errors.append("graph-roots:" + str(len(roots)))
    if len(roots) == 1:
        reachable: set[str] = set(); stack = [next(iter(roots))]
        while stack:
            rid = stack.pop()
            if rid not in reachable:
                reachable.add(rid); stack.extend(pid for pid in table[rid].premise_ids if pid in table)
        if reachable != set(table): errors.append("disconnected-receipts")
    for row in rows:
        try:
            conclusion = json.loads(row.conclusion)
            rebuilt = _receipt(row.rule_id, row.premise_ids, row.subject, row.status, conclusion, row.obstruction)
            if rebuilt.digest != row.digest or rebuilt.receipt_id != row.receipt_id: errors.append(f"tampered:{row.receipt_id}")
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            logger.error("verify_receipts malformed conclusion id=%s error=%s", row.receipt_id, exc)
            errors.append(f"tampered:{row.receipt_id}")
    if not errors and len(roots) == 1:
        actual = evaluate_native(table[next(iter(roots))].subject).receipts
        if actual != rows: errors.append("graph-replay-mismatch")
    used = {axiom for row in rows if row.rule_id in RULE_AXIOMS for axiom in RULE_AXIOMS[row.rule_id]}
    closure = tuple(axiom for axiom in AXIOM_ORDER if axiom in used) if not errors else ()
    result = ReceiptCheck(not errors, tuple(dict.fromkeys(errors)), closure)
    logger.debug("verify_receipts exit ok=%s errors=%r", result.ok, result.errors)
    return result


def axiom_closure(receipts: Iterable[DerivationReceipt]) -> tuple[str, ...]:
    """Return the checked exact axiom union induced by receipt rules."""
    logger.debug("axiom_closure entry")
    checked = verify_receipts(receipts)
    if not checked.ok:
        logger.error("axiom_closure invalid errors=%r", checked.errors)
        raise ValueError("invalid receipt graph: " + ";".join(checked.errors))
    logger.debug("axiom_closure exit result=%r", checked.axiom_closure)
    return checked.axiom_closure


def replay_receipts(source: VeyraExpr | str, receipts: Iterable[DerivationReceipt]) -> ReceiptCheck:
    """Re-evaluate a source and require byte-stable receipt equality."""
    expected = tuple(receipts); logger.debug("replay_receipts entry expected=%d", len(expected))
    checked = verify_receipts(expected); actual = evaluate_native(source).receipts
    errors = checked.errors + (() if actual == expected else ("replay-mismatch",))
    result = ReceiptCheck(not errors, errors, checked.axiom_closure if not errors else ())
    logger.debug("replay_receipts exit ok=%s", result.ok)
    return result
