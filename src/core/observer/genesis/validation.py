"""Construction and strict validation of P1-E1 doctrine and source."""

from __future__ import annotations

import logging

from .adapter import (
    ADAPTER_ID, _derive_machine, compare_with_derived, snapshot_machine,
)
from .digest import (
    adapter_digest, doctrine_digest, policy_digest, source_digest,
)
from .native import (
    ObserverGenesisValidationError, exact_text, hex_digest,
    snapshot_and_replay_genealogy,
)
from .types import (
    FiniteObserverMachine, GenesisResourcePolicy, ModeSpec,
    ObserverGenesisDoctrine, ObserverGenesisSource,
)

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

SOURCE_VERSION = "p1-e1-source-v1"

POLICY_VERSION = "p1-e1-resource-policy-v1"

DOCTRINE_VERSION = "p1-e1-doctrine-v1"

DOCTRINE_ID = "P1E1-primitive-rooted-observer-genesis"

CLOSURE_LAW_ID = "p1-e1-total-table-closure-v1"

RECURRENCE_LAW_ID = "p1-e1-evidence-path-return-v1"

HARD_MAX_TRANSITION_ROWS = 24

HARD_MAX_REACHABILITY_CHECKS = 24

HARD_MAX_CONTINUATION_STEPS = 128

HARD_MAX_RETURN_WORD_STEPS = 256

HARD_MAX_RESPONSE_CHECKS = 130

HARD_MAX_ENCODED_BYTES = 16_384

def _reject(reason: str) -> None:
    logger.error("observer genesis validation rejected reason=%s", reason)
    raise ObserverGenesisValidationError(reason)

def _bound(value: int, field: str, maximum: int, *, allow_zero: bool = True) -> int:
    logger.debug("_bound entry field=%s", field)
    lower = 0 if allow_zero else 1
    if type(value) is not int or not lower <= value <= maximum:
        _reject(f"invalid-{field}")
    logger.debug("_bound exit field=%s", field)
    return value

def build_resource_policy(
    max_transition_rows: int = HARD_MAX_TRANSITION_ROWS,
    max_reachability_checks: int = HARD_MAX_REACHABILITY_CHECKS,
    max_continuation_steps: int = HARD_MAX_CONTINUATION_STEPS,
    max_return_word_steps: int = HARD_MAX_RETURN_WORD_STEPS,
    max_response_checks: int = HARD_MAX_RESPONSE_CHECKS,
    max_encoded_bytes: int = HARD_MAX_ENCODED_BYTES,
    version: str = POLICY_VERSION,
) -> GenesisResourcePolicy:
    """Build explicit operational caps; zero may intentionally force refusal."""
    logger.debug("build_resource_policy entry")
    if type(version) is not str or version != POLICY_VERSION:
        _reject("unknown-genesis-policy-version")
    values = (
        _bound(max_transition_rows, "max-transition-rows", HARD_MAX_TRANSITION_ROWS),
        _bound(max_reachability_checks, "max-reachability-checks", HARD_MAX_REACHABILITY_CHECKS),
        _bound(max_continuation_steps, "max-continuation-steps", HARD_MAX_CONTINUATION_STEPS),
        _bound(max_return_word_steps, "max-return-word-steps", HARD_MAX_RETURN_WORD_STEPS),
        _bound(max_response_checks, "max-response-checks", HARD_MAX_RESPONSE_CHECKS),
        _bound(max_encoded_bytes, "max-encoded-bytes", HARD_MAX_ENCODED_BYTES),
    )
    provisional = GenesisResourcePolicy(version, *values, "0" * 64)
    result = GenesisResourcePolicy(version, *values, policy_digest(provisional))
    logger.debug("build_resource_policy exit")
    return result

def snapshot_resource_policy(value: GenesisResourcePolicy) -> GenesisResourcePolicy:
    """Rebuild policy and reject nested cap/digest mutation."""
    logger.debug("snapshot_resource_policy entry")
    if type(value) is not GenesisResourcePolicy:
        _reject("genesis-resource-policy-must-be-exact")
    try:
        expected = build_resource_policy(
            value.max_transition_rows, value.max_reachability_checks,
            value.max_continuation_steps, value.max_return_word_steps,
            value.max_response_checks, value.max_encoded_bytes, value.version,
        )
        supplied = hex_digest(value.policy_digest, "genesis-policy-digest")
    except AttributeError:
        _reject("genesis-resource-policy-missing-fields")
    if supplied != expected.policy_digest:
        _reject("genesis-resource-policy-drift")
    logger.debug("snapshot_resource_policy exit")
    return expected

def build_doctrine(
    policy: GenesisResourcePolicy,
    doctrine_id: str = DOCTRINE_ID,
    version: str = DOCTRINE_VERSION,
) -> ObserverGenesisDoctrine:
    """Build the own E1 doctrine without importing an R11/P0 doctrine."""
    logger.debug("build_doctrine entry")
    policy = snapshot_resource_policy(policy)
    if type(version) is not str or version != DOCTRINE_VERSION:
        _reject("unknown-genesis-doctrine-version")
    if type(doctrine_id) is not str or doctrine_id != DOCTRINE_ID:
        _reject("foreign-genesis-doctrine")
    provisional = ObserverGenesisDoctrine(version, doctrine_id, policy, "0" * 64)
    result = ObserverGenesisDoctrine(
        version, doctrine_id, policy, doctrine_digest(provisional),
    )
    logger.debug("build_doctrine exit")
    return result

def snapshot_doctrine(value: ObserverGenesisDoctrine) -> ObserverGenesisDoctrine:
    """Deep-capture the doctrine fingerprint and operational policy."""
    logger.debug("snapshot_doctrine entry")
    if type(value) is not ObserverGenesisDoctrine:
        _reject("observer-genesis-doctrine-must-be-exact")
    try:
        expected = build_doctrine(value.policy, value.doctrine_id, value.version)
        supplied = hex_digest(value.doctrine_digest, "genesis-doctrine-digest")
    except AttributeError:
        _reject("observer-genesis-doctrine-missing-fields")
    if supplied != expected.doctrine_digest:
        _reject("observer-genesis-doctrine-drift")
    logger.debug("snapshot_doctrine exit")
    return expected

def derive_fixed_machine(genealogy: ModeSpec) -> FiniteObserverMachine:
    """Replay raw Spec genealogy and invoke the fixed adapter with Mode only."""
    logger.debug("derive_fixed_machine entry")
    _, replayed, _ = snapshot_and_replay_genealogy(genealogy)
    result = _derive_machine(replayed)
    logger.debug("derive_fixed_machine exit")
    return result

def build_source(
    doctrine: ObserverGenesisDoctrine, genealogy: ModeSpec,
    adapter_id: str, machine: FiniteObserverMachine,
) -> ObserverGenesisSource:
    """Bind raw genealogy to the fresh whole-table adapter result."""
    logger.debug("build_source entry")
    doctrine = snapshot_doctrine(doctrine)
    captured_genealogy, replayed, native_digest = snapshot_and_replay_genealogy(genealogy)
    if type(adapter_id) is not str or adapter_id != ADAPTER_ID:
        _reject("unknown-or-callable-genesis-adapter")
    captured_machine = snapshot_machine(machine)
    derived = _derive_machine(replayed)
    compare_with_derived(captured_machine, derived)
    adapter = adapter_digest(adapter_id, native_digest, captured_machine.machine_digest)
    provisional = ObserverGenesisSource(
        SOURCE_VERSION, doctrine.doctrine_digest, captured_genealogy,
        captured_genealogy.genealogy_digest, native_digest, adapter_id, adapter,
        captured_machine, captured_machine.machine_digest, CLOSURE_LAW_ID,
        RECURRENCE_LAW_ID, "0" * 64,
    )
    result = ObserverGenesisSource(
        provisional.version, provisional.doctrine_digest, provisional.genealogy,
        provisional.genealogy_digest, provisional.native_mode_digest,
        provisional.adapter_id, provisional.adapter_digest, provisional.machine,
        provisional.machine_digest, provisional.closure_law_id,
        provisional.recurrence_law_id, source_digest(provisional),
    )
    logger.debug("build_source exit")
    return result

def snapshot_source(
    doctrine: ObserverGenesisDoctrine, value: ObserverGenesisSource,
) -> ObserverGenesisSource:
    """Replay raw source and adapter; a digest alone is never evidence."""
    logger.debug("snapshot_source entry")
    doctrine = snapshot_doctrine(doctrine)
    if type(value) is not ObserverGenesisSource:
        _reject("observer-genesis-source-must-be-exact")
    try:
        if type(value.version) is not str or value.version != SOURCE_VERSION:
            _reject("unknown-observer-genesis-source-version")
        expected = build_source(doctrine, value.genealogy, value.adapter_id, value.machine)
        supplied = (
            hex_digest(value.doctrine_digest, "source-doctrine-digest"),
            hex_digest(value.genealogy_digest, "source-genealogy-digest"),
            hex_digest(value.native_mode_digest, "source-native-mode-digest"),
            hex_digest(value.adapter_digest, "source-adapter-digest"),
            hex_digest(value.machine_digest, "source-machine-digest"),
            hex_digest(value.source_digest, "source-digest"),
        )
        laws = (value.closure_law_id, value.recurrence_law_id)
    except AttributeError:
        _reject("observer-genesis-source-missing-fields")
    expected_values = (
        expected.doctrine_digest, expected.genealogy_digest,
        expected.native_mode_digest, expected.adapter_digest,
        expected.machine_digest, expected.source_digest,
    )
    if supplied != expected_values or laws != (CLOSURE_LAW_ID, RECURRENCE_LAW_ID):
        _reject("observer-genesis-source-drift-or-transplant")
    logger.debug("snapshot_source exit")
    return expected
