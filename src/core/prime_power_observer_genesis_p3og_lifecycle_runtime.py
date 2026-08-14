"""Native finite-word runtime for authority-free P3-OG first closure."""

from __future__ import annotations

import logging

from .prime_power_observer_genesis_p3og_lifecycle_codec import lifecycle_digest
from .prime_power_observer_genesis_p3og_lifecycle_source import (
    validate_formation_source,
)
from .prime_power_observer_genesis_p3og_lifecycle_types import (
    FirstClosureStatus,
    FormationBoundary,
    FormationState,
    FormationTickReceipt,
    P3OGFirstClosureEvidence,
    P3OGFormationSource,
    P3OG_LIFECYCLE_NONCLAIMS,
)
from .prime_power_observer_genesis_p3og_machine_internal import (
    _initial_state_validated,
)
from .prime_power_observer_genesis_p3og_types import P3OGSource

logger = logging.getLogger(__name__)
EVIDENCE_VERSION = "p3og-first-closure-evidence-v1"


def _least_closure_index(word: tuple[int, ...], limit: int) -> int | None:
    """Return the least bounded nonconstant return no later than ``limit``."""
    logger.debug("p3og.lifecycle.least_closure entry limit=%d", limit)
    if type(word) is not tuple or not word or type(limit) is not int:
        logger.error("p3og.lifecycle.least_closure invalid input")
        raise ValueError("p3og-formation-word")
    upper = min(limit, len(word) - 1)
    seen = {word[0]}
    result = None
    for index in range(1, upper + 1):
        seen.add(word[index])
        if word[index] == word[0] and len(seen) >= 2:
            result = index
            break
    logger.debug("p3og.lifecycle.least_closure exit index=%r", result)
    return result


def _formation_state(
    formation_source: P3OGFormationSource,
    boundary: FormationBoundary,
    cursor: int,
) -> FormationState:
    """Construct one state from trusted lifecycle source fields."""
    logger.debug(
        "p3og.lifecycle.state entry boundary=%s cursor=%d",
        boundary.value,
        cursor,
    )
    try:
        run_id = lifecycle_digest(
            "formation-run",
            formation_source.source_digest,
            formation_source.selected_seed_digest,
        )
        fields = (
            run_id,
            formation_source.source_digest,
            formation_source.selected_seed_digest,
            boundary,
            cursor,
            formation_source.formation_word[cursor],
            cursor,
        )
        result = FormationState(
            *fields,
            lifecycle_digest("formation-state", *fields),
        )
    except (AttributeError, IndexError, TypeError, UnicodeError, ValueError) as exc:
        logger.error("p3og.lifecycle.state error type=%s", type(exc).__name__)
        raise
    logger.debug("p3og.lifecycle.state exit state=%s", result.state_digest[:12])
    return result


def _validate_formation_state(
    formation_source: P3OGFormationSource,
    state: FormationState,
) -> FormationState:
    """Validate one exact state before a native tick consumes it."""
    logger.debug("p3og.lifecycle.validate_state entry")
    if type(state) is not FormationState:
        logger.error("p3og.lifecycle.validate_state wrong outer type")
        raise ValueError("p3og-formation-state-type")
    try:
        exact_scalars = (
            type(state.run_id) is str
            and type(state.formation_source_digest) is str
            and type(state.seed_digest) is str
            and type(state.boundary) is FormationBoundary
            and type(state.cursor) is int
            and type(state.current_symbol) is int
            and type(state.tick_count) is int
            and type(state.state_digest) is str
        )
        if not exact_scalars:
            logger.error("p3og.lifecycle.validate_state malformed scalars")
            raise ValueError("p3og-formation-state-malformed")
        if not 0 <= state.cursor < len(formation_source.formation_word):
            logger.error("p3og.lifecycle.validate_state cursor outside word")
            raise ValueError("p3og-formation-state-cursor")
        least = _least_closure_index(
            formation_source.formation_word,
            state.cursor,
        )
        unreachable = least is not None and least < state.cursor
        if unreachable:
            valid = False
        else:
            expected_boundary = FormationBoundary.ALIVE if least == state.cursor else FormationBoundary.UNFORMED
            expected = _formation_state(
                formation_source,
                expected_boundary,
                state.cursor,
            )
            valid = state == expected
    except (AttributeError, IndexError, TypeError, UnicodeError, ValueError) as exc:
        logger.error(
            "p3og.lifecycle.validate_state malformed type=%s",
            type(exc).__name__,
        )
        raise ValueError("p3og-formation-state-malformed") from exc
    if unreachable:
        logger.error("p3og.lifecycle.validate_state cursor follows first closure")
        raise ValueError("p3og-formation-state-unreachable")
    if not valid:
        logger.error("p3og.lifecycle.validate_state state drift")
        raise ValueError("p3og-formation-state-drift")
    logger.debug("p3og.lifecycle.validate_state exit state=%s", state.state_digest[:12])
    return state


def _formation_seed_state_validated(
    formation_source: P3OGFormationSource,
) -> FormationState:
    """Create the exact non-ALIVE seed state for one validated source."""
    logger.debug("p3og.lifecycle.seed_state entry")
    result = _formation_state(formation_source, FormationBoundary.UNFORMED, 0)
    logger.debug("p3og.lifecycle.seed_state exit state=%s", result.state_digest[:12])
    return result


def _formation_tick_validated(
    formation_source: P3OGFormationSource,
    state: FormationState,
) -> tuple[FormationState, FormationTickReceipt]:
    """Consume the next committed symbol without caller-controlled input."""
    logger.debug("p3og.lifecycle.tick entry")
    state = _validate_formation_state(formation_source, state)
    if state.boundary is FormationBoundary.ALIVE:
        logger.error("p3og.lifecycle.tick rejected already alive state")
        raise ValueError("p3og-formation-already-closed")
    next_cursor = state.cursor + 1
    if next_cursor >= len(formation_source.formation_word):
        logger.error("p3og.lifecycle.tick formation word exhausted")
        raise ValueError("p3og-formation-word-exhausted")
    least = _least_closure_index(formation_source.formation_word, next_cursor)
    boundary = FormationBoundary.ALIVE if least == next_cursor else FormationBoundary.UNFORMED
    after = _formation_state(formation_source, boundary, next_cursor)
    receipt_fields = (
        next_cursor,
        after.current_symbol,
        state.state_digest,
        after.state_digest,
        boundary is FormationBoundary.ALIVE,
    )
    receipt = FormationTickReceipt(
        *receipt_fields,
        lifecycle_digest("formation-tick", *receipt_fields),
    )
    logger.debug(
        "p3og.lifecycle.tick exit index=%d boundary=%s",
        next_cursor,
        boundary.value,
    )
    return after, receipt


def run_p3og_first_closure(
    source: P3OGSource,
    formation_source: P3OGFormationSource,
) -> P3OGFirstClosureEvidence:
    """Replay one validated selected word to its least bounded closure."""
    logger.debug("p3og.lifecycle.run entry")
    try:
        source, formation_source = validate_formation_source(source, formation_source)
        result = _run_p3og_first_closure_validated(source, formation_source)
    except (AttributeError, IndexError, TypeError, UnicodeError, ValueError) as exc:
        logger.error("p3og.lifecycle.run error type=%s", type(exc).__name__)
        raise
    logger.debug("p3og.lifecycle.run exit status=%s", result.status.value)
    return result


def _run_p3og_first_closure_validated(
    source: P3OGSource,
    formation_source: P3OGFormationSource,
) -> P3OGFirstClosureEvidence:
    """Replay an already validated finite word and bind its exact genealogy."""
    logger.debug("p3og.lifecycle.run_validated entry")
    initial = _formation_seed_state_validated(formation_source)
    state = initial
    receipts: list[FormationTickReceipt] = []
    while state.boundary is FormationBoundary.UNFORMED and state.cursor + 1 < len(formation_source.formation_word):
        state, receipt = _formation_tick_validated(formation_source, state)
        receipts.append(receipt)
    captured = tuple(receipts)
    if state.boundary is FormationBoundary.ALIVE:
        status = FirstClosureStatus.WITNESSED
        reason = "least-nontrivial-return-witnessed"
        closure_index: int | None = state.cursor
        selected = source.seeds[formation_source.selection.selected_index]
        pressure_entry_state_digest: str | None = _initial_state_validated(
            source,
            selected,
        ).state_digest
    else:
        status = FirstClosureStatus.REFUTED
        reason = "formation-word-exhausted-without-closure"
        closure_index = None
        pressure_entry_state_digest = None
    genealogy = lifecycle_digest(
        "formation-genealogy",
        formation_source.source_digest,
        initial,
        captured,
        state,
    )
    fields = (
        EVIDENCE_VERSION,
        formation_source.source_digest,
        initial,
        captured,
        state,
        closure_index,
        pressure_entry_state_digest,
        status,
        reason,
        genealogy,
        0,
        P3OG_LIFECYCLE_NONCLAIMS,
    )
    result = P3OGFirstClosureEvidence(
        *fields,
        lifecycle_digest("first-closure-evidence", *fields),
    )
    logger.debug(
        "p3og.lifecycle.run_validated exit status=%s ticks=%d",
        status.value,
        len(captured),
    )
    return result
