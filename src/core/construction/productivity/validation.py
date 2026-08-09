"""Exact source and finite-stage snapshots for provisional P1-D1."""

from __future__ import annotations

import logging
from typing import NoReturn

from ..infinity_prefix import (
    InfinityPrefixValidationError, PrefixAlphabet, snapshot_prefix_alphabet,
)
from .digest import (
    generator_digest, policy_digest, program_digest, required_output_bytes,
    source_digest,
)
from .types import (
    ExecutionPolicy, PeriodicPrefixStage, PeriodicProgram, ProductiveProcessSource,
)

logger = logging.getLogger(__name__)
PROGRAM_VERSION = "p1-d1-periodic-v1"
POLICY_VERSION = "p1-d1-policy-v1"
TOTALITY_BASIS_ID = "p1-d1-periodic-modulo-total-v1"
RESTRICTION_LAW_ID = "p1-d1-prefix-restriction-v1"
OUTPUT_ENCODING_ID = "veyra.p1d1.periodic-prefix-stage.v1"
MAX_PERIOD_SYMBOLS = 4096
MAX_POLICY_DEPTH = 1_000_000
MAX_POLICY_OUTPUT_BYTES = 64_000_000


class ProductivityValidationError(ValueError):
    """An exact D1 representation, binding, or structural rule failed."""


def _reject(reason: str) -> NoReturn:
    logger.error("productivity rejected reason=%s", reason)
    raise ProductivityValidationError(reason)


def _hex_digest(value: str, field: str) -> str:
    logger.debug("_hex_digest entry field=%s", field)
    if type(value) is not str or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        _reject(f"invalid-{field}")
    logger.debug("_hex_digest exit field=%s", field)
    return value


def snapshot_productivity_alphabet(value: PrefixAlphabet) -> PrefixAlphabet:
    """Normalize I1 alphabet validation, including malformed UTF-8."""
    logger.debug("snapshot_productivity_alphabet entry")
    try:
        result = snapshot_prefix_alphabet(value)
    except (InfinityPrefixValidationError, UnicodeError) as exc:
        logger.error("snapshot_productivity_alphabet rejected")
        raise ProductivityValidationError("invalid-productivity-alphabet") from exc
    logger.debug("snapshot_productivity_alphabet exit symbols=%d", len(result.symbols))
    return result


def build_periodic_program(
    alphabet: PrefixAlphabet, period: tuple[str, ...], version: str = PROGRAM_VERSION,
) -> PeriodicProgram:
    """Construct the sole allowlisted closed periodic grammar."""
    logger.debug("build_periodic_program entry")
    alphabet = snapshot_productivity_alphabet(alphabet)
    if type(version) is not str or version != PROGRAM_VERSION:
        _reject("unknown-periodic-program-version")
    if type(period) is not tuple or not 1 <= len(period) <= MAX_PERIOD_SYMBOLS:
        _reject("invalid-period")
    allowed = frozenset(alphabet.symbols)
    rows: list[str] = []
    for symbol in period:
        if type(symbol) is not str or symbol not in allowed:
            _reject("foreign-or-nonexact-period-symbol")
        rows.append(symbol)
    captured = tuple(rows)
    result = PeriodicProgram(
        PROGRAM_VERSION, alphabet, captured,
        program_digest(PROGRAM_VERSION, alphabet.symbols, captured),
    )
    logger.debug("build_periodic_program exit period=%d", len(captured))
    return result


def snapshot_periodic_program(value: PeriodicProgram) -> PeriodicProgram:
    """Deep-rebuild one program and reject stale nested mutation."""
    logger.debug("snapshot_periodic_program entry")
    if type(value) is not PeriodicProgram:
        _reject("periodic-program-must-be-exact")
    try:
        expected = build_periodic_program(value.alphabet, value.period, value.version)
        supplied = _hex_digest(value.program_digest, "program-digest")
    except AttributeError:
        _reject("periodic-program-missing-fields")
    if supplied != expected.program_digest:
        _reject("periodic-program-drift")
    logger.debug("snapshot_periodic_program exit")
    return expected


def build_execution_policy(
    max_depth: int, max_output_bytes: int, version: str = POLICY_VERSION,
) -> ExecutionPolicy:
    """Construct one bounded operational policy, never generator identity."""
    logger.debug("build_execution_policy entry")
    if type(version) is not str or version != POLICY_VERSION:
        _reject("unknown-execution-policy-version")
    if type(max_depth) is not int or not 0 <= max_depth <= MAX_POLICY_DEPTH:
        _reject("invalid-policy-max-depth")
    if type(max_output_bytes) is not int or not 1 <= max_output_bytes <= MAX_POLICY_OUTPUT_BYTES:
        _reject("invalid-policy-max-output-bytes")
    result = ExecutionPolicy(
        POLICY_VERSION, max_depth, max_output_bytes,
        policy_digest(POLICY_VERSION, max_depth, max_output_bytes),
    )
    logger.debug("build_execution_policy exit")
    return result


def snapshot_execution_policy(value: ExecutionPolicy) -> ExecutionPolicy:
    """Recompute exact policy identity and reject policy mutation."""
    logger.debug("snapshot_execution_policy entry")
    if type(value) is not ExecutionPolicy:
        _reject("execution-policy-must-be-exact")
    try:
        expected = build_execution_policy(value.max_depth, value.max_output_bytes, value.version)
        supplied = _hex_digest(value.policy_digest, "policy-digest")
    except AttributeError:
        _reject("execution-policy-missing-fields")
    if supplied != expected.policy_digest:
        _reject("execution-policy-drift")
    logger.debug("snapshot_execution_policy exit")
    return expected


def build_productive_source(
    program: PeriodicProgram, totality_basis_id: str, restriction_law_id: str,
    output_encoding_id: str, policy: ExecutionPolicy,
) -> ProductiveProcessSource:
    """Bind allowlisted structural laws separately from the execution policy."""
    logger.debug("build_productive_source entry")
    program = snapshot_periodic_program(program)
    policy = snapshot_execution_policy(policy)
    if (
        type(totality_basis_id) is not str or totality_basis_id != TOTALITY_BASIS_ID
        or type(restriction_law_id) is not str or restriction_law_id != RESTRICTION_LAW_ID
        or type(output_encoding_id) is not str or output_encoding_id != OUTPUT_ENCODING_ID
    ):
        _reject("unknown-productivity-basis-law-or-encoding")
    generator = generator_digest(
        program.program_digest, totality_basis_id, restriction_law_id, output_encoding_id
    )
    result = ProductiveProcessSource(
        program, totality_basis_id, restriction_law_id, output_encoding_id, policy,
        generator, source_digest(generator, policy.policy_digest),
    )
    logger.debug("build_productive_source exit")
    return result


def snapshot_productive_source(value: ProductiveProcessSource) -> ProductiveProcessSource:
    """Deep-rebuild the sole D1 source; no target or witness table is accepted."""
    logger.debug("snapshot_productive_source entry")
    if type(value) is not ProductiveProcessSource:
        _reject("productive-process-source-must-be-exact")
    try:
        expected = build_productive_source(
            value.program, value.totality_basis_id, value.restriction_law_id,
            value.output_encoding_id, value.policy,
        )
        generator = _hex_digest(value.generator_digest, "generator-digest")
        supplied = _hex_digest(value.source_digest, "source-digest")
    except AttributeError:
        _reject("productive-process-source-missing-fields")
    if generator != expected.generator_digest or supplied != expected.source_digest:
        _reject("productive-process-source-drift")
    logger.debug("snapshot_productive_source exit")
    return expected


def snapshot_periodic_prefix_stage(
    value: PeriodicPrefixStage, source: ProductiveProcessSource,
    expected_depth: int, expected_encoded_bytes: int,
) -> PeriodicPrefixStage:
    """Validate an exact D1 stage against the fixed periodic formula."""
    logger.debug("snapshot_periodic_prefix_stage entry")
    source = snapshot_productive_source(source)
    if type(value) is not PeriodicPrefixStage:
        _reject("periodic-prefix-stage-must-be-exact")
    try:
        depth, symbols, encoding = value.depth, value.symbols, value.output_encoding_id
    except AttributeError:
        _reject("periodic-prefix-stage-missing-fields")
    if (
        type(expected_depth) is not int or expected_depth < 0
        or type(expected_encoded_bytes) is not int or expected_encoded_bytes < 0
        or type(depth) is not int or depth != expected_depth
        or type(symbols) is not tuple or len(symbols) != expected_depth
    ):
        _reject("invalid-periodic-prefix-stage")
    if type(encoding) is not str or encoding != source.output_encoding_id:
        _reject("periodic-prefix-stage-encoding-drift")
    period = source.program.period
    if required_output_bytes(expected_depth, period, encoding) != expected_encoded_bytes:
        _reject("periodic-prefix-stage-byte-bound-drift")
    captured: list[str] = []
    for index, symbol in enumerate(symbols):
        if type(symbol) is not str or symbol != period[index % len(period)]:
            _reject("periodic-prefix-stage-formula-drift")
        captured.append(symbol)
    result = PeriodicPrefixStage(depth, tuple(captured), source.output_encoding_id)
    logger.debug("snapshot_periodic_prefix_stage exit depth=%d", depth)
    return result
