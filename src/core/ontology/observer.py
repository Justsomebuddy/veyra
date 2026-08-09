"""Safe one-pass capture of untrusted closed R11 observer programs."""

from __future__ import annotations

import logging

from ..observer_core_semantics import MAX_OBSERVER_DEPTH, MAX_OBSERVER_NODES
from ..observer_core_types import Apply, Input, ObserverExpr, Pair, PrimitiveId
from .validation import PositiveOntologyValidationError

logger = logging.getLogger(__name__)


def snapshot_observer_program(value: object) -> ObserverExpr:
    """Rebuild an exact bounded observer AST before codec/logging access."""
    logger.debug("snapshot_observer_program entry")
    stack: list[tuple[str, object, int]] = [("enter", value, 0)]
    active: set[int] = set()
    values: list[ObserverExpr] = []
    nodes = 0
    while stack:
        action, node, depth = stack.pop()
        if action == "apply-exit":
            source_identity, primitive = node  # type: ignore[misc]
            active.remove(source_identity)
            values.append(Apply(primitive, values.pop()))
            continue
        if action == "pair-exit":
            active.remove(node)  # type: ignore[arg-type]
            right, left = values.pop(), values.pop()
            values.append(Pair(left, right))
            continue
        identity = id(node)
        nodes += 1
        if nodes > MAX_OBSERVER_NODES or depth > MAX_OBSERVER_DEPTH:
            logger.error("snapshot_observer_program resource limit")
            raise PositiveOntologyValidationError("observer-resource-limit")
        if identity in active:
            logger.error("snapshot_observer_program cycle rejected")
            raise PositiveOntologyValidationError("circular-observer")
        if type(node) is Input:
            values.append(Input())
        elif type(node) is Apply:
            try:
                primitive, child = node.primitive, node.child
            except AttributeError as exc:
                logger.error("snapshot_observer_program apply fields missing")
                raise PositiveOntologyValidationError("observer-missing-fields") from exc
            if type(primitive) is not PrimitiveId:
                logger.error("snapshot_observer_program primitive rejected")
                raise PositiveOntologyValidationError("invalid-observer-primitive")
            active.add(identity)
            stack.extend(
                (("apply-exit", (identity, primitive), depth), ("enter", child, depth + 1))
            )
        elif type(node) is Pair:
            try:
                left, right = node.left, node.right
            except AttributeError as exc:
                logger.error("snapshot_observer_program pair fields missing")
                raise PositiveOntologyValidationError("observer-missing-fields") from exc
            active.add(identity)
            stack.extend(
                (("pair-exit", identity, depth), ("enter", right, depth + 1), ("enter", left, depth + 1))
            )
        else:
            logger.error("snapshot_observer_program exact gate rejected")
            raise PositiveOntologyValidationError("invalid-observer-program")
    if len(values) != 1:
        logger.error("snapshot_observer_program shape rejected")
        raise PositiveOntologyValidationError("invalid-observer-shape")
    logger.debug("snapshot_observer_program exit nodes=%d", nodes)
    return values[0]
