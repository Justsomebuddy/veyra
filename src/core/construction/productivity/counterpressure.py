"""P1-D2 productivity counterpressure requests, evidence, and certificates."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from functools import lru_cache
from hashlib import sha256
import hmac
import logging
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import NoReturn, TypeAlias

from ...formal.catalog import _strip_lean_comments
from ...paths import TMP_DIR

logger = logging.getLogger(__name__)


# Data model

class CounterpressureRequestKind(str, Enum):
    LEDGER = "nonuniform-ledger"
    DESCENT = "natural-strict-descent-tree"
    CHOOSER = "target-dependent-chooser"
    LONG_RUN = "long-finite-run"
    SHRINKING = "shrinking-nonempty-stages"

class CounterpressureInference(str, Enum):
    LEDGER_GENERATOR = "finite-ledger-establishes-uniform-generator"
    FINITE_DEPTH_BRANCH = "arbitrary-finite-depth-implies-infinite-branch"
    POSTHOC_INDEPENDENCE = "posthoc-match-implies-target-independence"
    LONG_RUN_FAMILY = "long-finite-run-establishes-all-depth-family"
    NESTED_COMMON_POINT = "nested-nonempty-stages-imply-common-point"

class CounterpressureOutcomeKind(str, Enum):
    EVIDENCE_INSUFFICIENCY = "evidence-insufficiency"
    MATHEMATICAL_COUNTERMODEL = "mathematical-countermodel"

class CounterpressureStatus(str, Enum):
    INSUFFICIENT_TO_ESTABLISH = "insufficient-to-establish"
    REFUTES_MATHEMATICAL_IMPLICATION = "refutes-mathematical-implication"

class BasisUse(str, Enum):
    BOUND = "bound"
    NONE = "none"

class DerivationKind(str, Enum):
    LEAN_CHECKED_THEOREM = "lean-checked-theorem"

class GeneratorNonexistence(str, Enum):
    NOT_PROVED = "not-proved"

class AllDepthFamilyStatus(str, Enum):
    OPEN = "open"

class CompletedCarrierStatus(str, Enum):
    NOT_ESTABLISHED = "not-established"

class HistoricalTargetIndependence(str, Enum):
    NOT_ESTABLISHED = "not-established"

class ChooserTargetIndependence(str, Enum):
    REFUTED = "refuted"

class CounterpressureResourceBound(str, Enum):
    REQUEST_BYTES = "request-bytes"
    SYMBOLIC_COST = "symbolic-cost"

@dataclass(frozen=True)
class CounterpressureBasisSource:
    version: str
    basis_id: str
    derivation_kind: DerivationKind
    foundation_id: str
    artifact_name: str
    artifact_sha256: str
    theorem_ids: tuple[str, ...]
    toolchain_id: str
    tcb_digest: str
    basis_digest: str

@dataclass(frozen=True)
class CounterpressureAlphabet:
    version: str
    symbols: tuple[str, ...]
    alphabet_digest: str

@dataclass(frozen=True)
class LedgerRow:
    depth: int
    witness_label: str
    selector_label: str

@dataclass(frozen=True)
class NonuniformLedgerRequest:
    version: str
    rows: tuple[LedgerRow, ...]

@dataclass(frozen=True)
class DecreasingTreeRequest:
    version: str
    sample_depth: int
    basis: CounterpressureBasisSource

@dataclass(frozen=True)
class TargetChooserRequest:
    version: str
    alphabet: CounterpressureAlphabet
    target: tuple[str, ...]

@dataclass(frozen=True)
class LongRunRequest:
    version: str
    steps: int

@dataclass(frozen=True)
class ShrinkingStageRequest:
    version: str
    sample_index: int
    basis: CounterpressureBasisSource

CounterpressureRequest: TypeAlias = (
    NonuniformLedgerRequest | DecreasingTreeRequest | TargetChooserRequest |
    LongRunRequest | ShrinkingStageRequest
)

@dataclass(frozen=True)
class CounterpressurePolicy:
    version: str
    max_request_bytes: int
    max_symbolic_cost: int
    policy_digest: str

@dataclass(frozen=True)
class LedgerInsufficiencyEvidence:
    row_count: int
    depths: tuple[int, ...]
    selector_count: int
    common_source_supplied: bool
    status: CounterpressureStatus

@dataclass(frozen=True)
class DescentCountermodelEvidence:
    sample_depth: int
    witness_length: int
    first_or_none: int | None
    last_or_none: int | None
    witness_formula_digest: str
    basis_digest: str
    status: CounterpressureStatus

@dataclass(frozen=True)
class TargetDependenceEvidence:
    target_length: int
    target_digest: str
    output_digest: str
    exact_match: bool
    target_read: bool
    chooser_target_independence: ChooserTargetIndependence
    chooser_rule_id: str
    status: CounterpressureStatus

@dataclass(frozen=True)
class FiniteRunInsufficiencyEvidence:
    first_depth: int
    last_depth: int
    executed_count: int
    materialized: bool
    status: CounterpressureStatus

@dataclass(frozen=True)
class ShrinkingTailCountermodelEvidence:
    sample_index: int
    local_witness: int
    nested_from: int
    nested_into: int
    diagonal_candidate: int
    excluding_stage: int
    basis_digest: str
    status: CounterpressureStatus

CounterpressureEvidence: TypeAlias = (
    LedgerInsufficiencyEvidence | DescentCountermodelEvidence |
    TargetDependenceEvidence | FiniteRunInsufficiencyEvidence |
    ShrinkingTailCountermodelEvidence
)

@dataclass(frozen=True)
class CounterpressureCertificate:
    request_kind: CounterpressureRequestKind
    request_digest: str
    inference_id: CounterpressureInference
    outcome_kind: CounterpressureOutcomeKind
    status: CounterpressureStatus
    evidence: CounterpressureEvidence
    evidence_digest: str
    basis_use: BasisUse
    basis_digest: str | None
    policy_digest: str
    certificate_digest: str
    generator_nonexistence: GeneratorNonexistence = GeneratorNonexistence.NOT_PROVED
    all_depth_family: AllDepthFamilyStatus = AllDepthFamilyStatus.OPEN
    completed_carrier: CompletedCarrierStatus = CompletedCarrierStatus.NOT_ESTABLISHED
    historical_target_independence: HistoricalTargetIndependence = (
        HistoricalTargetIndependence.NOT_ESTABLISHED
    )
    scope: str = "counterpressure-only"

@dataclass(frozen=True)
class CounterpressureResourceLimit:
    request_kind: CounterpressureRequestKind
    request_digest: str
    failed_bound: CounterpressureResourceBound
    required_value: int
    allowed_value: int
    policy_digest: str
    refusal_digest: str
    generator_nonexistence: GeneratorNonexistence = GeneratorNonexistence.NOT_PROVED
    all_depth_family: AllDepthFamilyStatus = AllDepthFamilyStatus.OPEN
    completed_carrier: CompletedCarrierStatus = CompletedCarrierStatus.NOT_ESTABLISHED
    historical_target_independence: HistoricalTargetIndependence = (
        HistoricalTargetIndependence.NOT_ESTABLISHED
    )
    scope: str = "counterpressure-only"

CounterpressureResult: TypeAlias = CounterpressureCertificate | CounterpressureResourceLimit


# Validation primitives

logger = logging.getLogger(__name__)

MAX_NATURAL = 1_000_000_000

MAX_IDENTIFIER_BYTES = 64

class CounterpressureValidationError(ValueError):
    """A D2 representation, source, result, or commitment was invalid."""

def reject(reason: str) -> NoReturn:
    logger.error("counterpressure rejected reason=%s", reason)
    raise CounterpressureValidationError(reason)

def exact_natural(value: object, field: str) -> int:
    logger.debug("exact_natural entry field=%s", field)
    if type(value) is not int or not 0 <= value <= MAX_NATURAL:
        reject(f"invalid-{field}")
    logger.debug("exact_natural exit field=%s", field)
    return value

def exact_identifier(value: object, field: str) -> str:
    logger.debug("exact_identifier entry field=%s", field)
    if type(value) is not str or not value:
        reject(f"invalid-{field}")
    try:
        size = len(value.encode("utf-8", errors="strict"))
    except UnicodeError:
        reject(f"invalid-{field}")
    if size > MAX_IDENTIFIER_BYTES:
        reject(f"invalid-{field}")
    logger.debug("exact_identifier exit field=%s bytes=%d", field, size)
    return value

def exact_digest(value: object, field: str) -> str:
    logger.debug("exact_digest entry field=%s", field)
    if (
        type(value) is not str or len(value) != 64
        or any(ch not in "0123456789abcdef" for ch in value)
    ):
        reject(f"invalid-{field}")
    logger.debug("exact_digest exit field=%s", field)
    return value

def exact_dataclass_shape(value: object, expected_type: type, field: str) -> None:
    """Reject subclasses, missing fields, and injected instance attributes."""
    logger.debug("exact_dataclass_shape entry field=%s", field)
    if type(value) is not expected_type:
        reject(f"{field}-must-be-exact")
    if set(vars(value)) != set(expected_type.__dataclass_fields__):
        reject(f"{field}-shape-drift")
    logger.debug("exact_dataclass_shape exit field=%s", field)


# Canonical commitments

logger = logging.getLogger(__name__)

def _frame(domain: str, fields: tuple[tuple[str, bytes], ...]) -> bytes:
    logger.debug("_frame entry domain=%s fields=%d", domain, len(fields))
    output = bytearray(b"VEYRA-P1-D2\x00")
    _token(output, b"domain", domain.encode())
    _token(output, b"field-count", len(fields).to_bytes(8, "big"))
    for tag, value in fields:
        _token(output, tag.encode(), value)
    result = bytes(output)
    logger.debug("_frame exit domain=%s bytes=%d", domain, len(result))
    return result

def _token(output: bytearray, tag: bytes, value: bytes) -> None:
    logger.debug("_token entry tag=%d value=%d", len(tag), len(value))
    output.extend(len(tag).to_bytes(4, "big"))
    output.extend(tag)
    output.extend(len(value).to_bytes(8, "big"))
    output.extend(value)
    logger.debug("_token exit")

def _digest(domain: str, fields: tuple[tuple[str, bytes], ...]) -> str:
    logger.debug("_digest entry domain=%s", domain)
    result = sha256(_frame(domain, fields)).hexdigest()
    logger.debug("_digest exit domain=%s", domain)
    return result

def _nat(value: int) -> bytes:
    logger.debug("_nat entry bits=%d", value.bit_length())
    width = max(1, (value.bit_length() + 7) // 8)
    result = value.to_bytes(width, "big")
    logger.debug("_nat exit bytes=%d", len(result))
    return result

def _optional_nat(value: int | None) -> bytes:
    logger.debug("_optional_nat entry present=%s", value is not None)
    result = b"none" if value is None else b"some\x00" + _nat(value)
    logger.debug("_optional_nat exit bytes=%d", len(result))
    return result

def alphabet_digest(version: str, symbols: tuple[str, ...]) -> str:
    logger.debug("alphabet_digest entry symbols=%d", len(symbols))
    fields = [("version", version.encode()), ("count", _nat(len(symbols)))]
    fields.extend((f"symbol-{i}", symbol.encode()) for i, symbol in enumerate(symbols))
    result = _digest("veyra.p1d2.alphabet.v1", tuple(fields))
    logger.debug("alphabet_digest exit")
    return result

def basis_digest(
    version: str, basis_id: str, derivation_kind: str, foundation_id: str,
    artifact_name: str, artifact_sha256: str, theorem_ids: tuple[str, ...],
    toolchain_id: str, tcb_digest: str,
) -> str:
    logger.debug("basis_digest entry theorems=%d", len(theorem_ids))
    fields = [
        ("version", version.encode()), ("basis-id", basis_id.encode()),
        ("derivation-kind", derivation_kind.encode()),
        ("foundation-id", foundation_id.encode()),
        ("artifact-name", artifact_name.encode()),
        ("artifact-sha256", artifact_sha256.encode()),
        ("theorem-count", _nat(len(theorem_ids))),
    ]
    fields.extend((f"theorem-{i}", theorem.encode()) for i, theorem in enumerate(theorem_ids))
    fields.extend((("toolchain-id", toolchain_id.encode()), ("tcb-digest", tcb_digest.encode())))
    result = _digest("veyra.p1d2.basis.v1", tuple(fields))
    logger.debug("basis_digest exit")
    return result

def policy_digest(version: str, max_request_bytes: int, max_symbolic_cost: int) -> str:
    logger.debug("policy_digest entry")
    result = _digest("veyra.p1d2.policy.v1", (
        ("version", version.encode()), ("max-request-bytes", _nat(max_request_bytes)),
        ("max-symbolic-cost", _nat(max_symbolic_cost)),
    ))
    logger.debug("policy_digest exit")
    return result

def row_bytes(row: LedgerRow) -> bytes:
    logger.debug("row_bytes entry depth=%d", row.depth)
    result = _frame("veyra.p1d2.ledger-row.v1", (
        ("depth", _nat(row.depth)), ("witness", row.witness_label.encode()),
        ("selector", row.selector_label.encode()),
    ))
    logger.debug("row_bytes exit bytes=%d", len(result))
    return result

def _basis_bytes(source: CounterpressureBasisSource) -> bytes:
    logger.debug("_basis_bytes entry")
    fields = (
        ("version", source.version.encode()), ("basis-id", source.basis_id.encode()),
        ("derivation-kind", source.derivation_kind.value.encode()),
        ("foundation-id", source.foundation_id.encode()),
        ("artifact-name", source.artifact_name.encode()),
        ("artifact-sha256", source.artifact_sha256.encode()),
        ("theorem-count", _nat(len(source.theorem_ids))),
        *((f"theorem-{i}", value.encode()) for i, value in enumerate(source.theorem_ids)),
        ("toolchain", source.toolchain_id.encode()), ("tcb", source.tcb_digest.encode()),
        ("basis-digest", source.basis_digest.encode()),
    )
    result = _frame("veyra.p1d2.basis-source.v1", fields)
    logger.debug("_basis_bytes exit bytes=%d", len(result))
    return result

def _alphabet_bytes(value: CounterpressureAlphabet) -> bytes:
    logger.debug("_alphabet_bytes entry symbols=%d", len(value.symbols))
    fields = [("version", value.version.encode()), ("count", _nat(len(value.symbols)))]
    fields.extend((f"symbol-{i}", symbol.encode()) for i, symbol in enumerate(value.symbols))
    fields.append(("digest", value.alphabet_digest.encode()))
    result = _frame("veyra.p1d2.alphabet-source.v1", tuple(fields))
    logger.debug("_alphabet_bytes exit bytes=%d", len(result))
    return result

def request_bytes(request: CounterpressureRequest) -> bytes:
    logger.debug("request_bytes entry type=%s", type(request).__name__)
    if type(request) is NonuniformLedgerRequest:
        fields = [("version", request.version.encode()), ("count", _nat(len(request.rows)))]
        fields.extend((f"row-{i}", row_bytes(row)) for i, row in enumerate(request.rows))
        result = _frame("veyra.p1d2.request.ledger.v1", tuple(fields))
    elif type(request) is DecreasingTreeRequest:
        result = _frame("veyra.p1d2.request.descent.v1", (
            ("version", request.version.encode()), ("sample-depth", _nat(request.sample_depth)),
            ("basis", _basis_bytes(request.basis)),
        ))
    elif type(request) is TargetChooserRequest:
        fields = [
            ("version", request.version.encode()), ("alphabet", _alphabet_bytes(request.alphabet)),
            ("target-count", _nat(len(request.target))),
        ]
        fields.extend((f"target-{i}", symbol.encode()) for i, symbol in enumerate(request.target))
        result = _frame("veyra.p1d2.request.chooser.v1", tuple(fields))
    elif type(request) is LongRunRequest:
        result = _frame("veyra.p1d2.request.long-run.v1", (
            ("version", request.version.encode()), ("steps", _nat(request.steps)),
        ))
    elif type(request) is ShrinkingStageRequest:
        result = _frame("veyra.p1d2.request.shrinking.v1", (
            ("version", request.version.encode()), ("sample-index", _nat(request.sample_index)),
            ("basis", _basis_bytes(request.basis)),
        ))
    else:
        raise TypeError("unknown-counterpressure-request")
    logger.debug("request_bytes exit bytes=%d", len(result))
    return result

def request_digest(request: CounterpressureRequest) -> str:
    logger.debug("request_digest entry")
    result = sha256(request_bytes(request)).hexdigest()
    logger.debug("request_digest exit")
    return result

def symbolic_formula_digest(formula_id: str, value: int) -> str:
    logger.debug("symbolic_formula_digest entry formula=%s", formula_id)
    result = _digest("veyra.p1d2.symbolic-formula.v1", (
        ("formula-id", formula_id.encode()), ("value", _nat(value)),
    ))
    logger.debug("symbolic_formula_digest exit")
    return result

def symbol_tuple_digest(domain: str, values: tuple[str, ...]) -> str:
    logger.debug("symbol_tuple_digest entry domain=%s count=%d", domain, len(values))
    fields = [("count", _nat(len(values)))]
    fields.extend((f"value-{i}", value.encode()) for i, value in enumerate(values))
    result = _digest(f"veyra.p1d2.{domain}.v1", tuple(fields))
    logger.debug("symbol_tuple_digest exit domain=%s", domain)
    return result

def evidence_digest(evidence: CounterpressureEvidence) -> str:
    logger.debug("evidence_digest entry type=%s", type(evidence).__name__)
    if type(evidence) is LedgerInsufficiencyEvidence:
        fields = [
            ("row-count", _nat(evidence.row_count)),
            ("depth-count", _nat(len(evidence.depths))),
            *((f"depth-{i}", _nat(v)) for i, v in enumerate(evidence.depths)),
            ("selector-count", _nat(evidence.selector_count)),
            ("common-source", b"true" if evidence.common_source_supplied else b"false"),
            ("status", evidence.status.value.encode()),
        ]
        domain = "ledger"
    elif type(evidence) is DescentCountermodelEvidence:
        fields = [
            ("sample", _nat(evidence.sample_depth)), ("length", _nat(evidence.witness_length)),
            ("first", _optional_nat(evidence.first_or_none)),
            ("last", _optional_nat(evidence.last_or_none)),
            ("formula", evidence.witness_formula_digest.encode()),
            ("basis", evidence.basis_digest.encode()), ("status", evidence.status.value.encode()),
        ]
        domain = "descent"
    elif type(evidence) is TargetDependenceEvidence:
        fields = [
            ("length", _nat(evidence.target_length)), ("target", evidence.target_digest.encode()),
            ("output", evidence.output_digest.encode()),
            ("exact-match", b"true" if evidence.exact_match else b"false"),
            ("target-read", b"true" if evidence.target_read else b"false"),
            ("independence", evidence.chooser_target_independence.value.encode()),
            ("rule", evidence.chooser_rule_id.encode()), ("status", evidence.status.value.encode()),
        ]
        domain = "chooser"
    elif type(evidence) is FiniteRunInsufficiencyEvidence:
        fields = [
            ("first", _nat(evidence.first_depth)), ("last", _nat(evidence.last_depth)),
            ("count", _nat(evidence.executed_count)),
            ("materialized", b"true" if evidence.materialized else b"false"),
            ("status", evidence.status.value.encode()),
        ]
        domain = "long-run"
    elif type(evidence) is ShrinkingTailCountermodelEvidence:
        fields = [
            ("sample", _nat(evidence.sample_index)), ("witness", _nat(evidence.local_witness)),
            ("nested-from", _nat(evidence.nested_from)),
            ("nested-into", _nat(evidence.nested_into)),
            ("candidate", _nat(evidence.diagonal_candidate)),
            ("excluding", _nat(evidence.excluding_stage)),
            ("basis", evidence.basis_digest.encode()), ("status", evidence.status.value.encode()),
        ]
        domain = "shrinking"
    else:
        raise TypeError("unknown-counterpressure-evidence")
    result = _digest(f"veyra.p1d2.evidence.{domain}.v1", tuple(fields))
    logger.debug("evidence_digest exit domain=%s", domain)
    return result

def certificate_digest(value: CounterpressureCertificate) -> str:
    logger.debug("certificate_digest entry")
    result = _digest("veyra.p1d2.certificate.v1", (
        ("request-kind", value.request_kind.value.encode()),
        ("request", value.request_digest.encode()), ("inference", value.inference_id.value.encode()),
        ("outcome", value.outcome_kind.value.encode()), ("status", value.status.value.encode()),
        ("evidence", value.evidence_digest.encode()), ("basis-use", value.basis_use.value.encode()),
        ("basis", b"none" if value.basis_digest is None else value.basis_digest.encode()),
        ("policy", value.policy_digest.encode()),
        ("generator-nonexistence", value.generator_nonexistence.value.encode()),
        ("all-depth-family", value.all_depth_family.value.encode()),
        ("completed-carrier", value.completed_carrier.value.encode()),
        ("target-independence", value.historical_target_independence.value.encode()),
        ("scope", value.scope.encode()),
    ))
    logger.debug("certificate_digest exit")
    return result

def refusal_digest(value: CounterpressureResourceLimit) -> str:
    logger.debug("refusal_digest entry")
    result = _digest("veyra.p1d2.refusal.v1", (
        ("request-kind", value.request_kind.value.encode()),
        ("request", value.request_digest.encode()), ("failed", value.failed_bound.value.encode()),
        ("required", _nat(value.required_value)), ("allowed", _nat(value.allowed_value)),
        ("policy", value.policy_digest.encode()),
        ("generator-nonexistence", value.generator_nonexistence.value.encode()),
        ("all-depth-family", value.all_depth_family.value.encode()),
        ("completed-carrier", value.completed_carrier.value.encode()),
        ("target-independence", value.historical_target_independence.value.encode()),
        ("scope", value.scope.encode()),
    ))
    logger.debug("refusal_digest exit")
    return result


# The basis section historically imports this commitment under its role name.
make_basis_digest = basis_digest


# Lean basis

logger = logging.getLogger(__name__)

BASIS_VERSION = "p1-d2-basis-v1"

BASIS_ID = "p1-d2-nat-countermodels-v1"

FOUNDATION_ID = "lean4-nat-v4.30.0-rc2"

ARTIFACT_NAME = "proofs/lean/VeyraProductivityCounterpressure.lean"

ARTIFACT_SHA256 = "32ebbb960c6a3091402f3dcddf6753c5cf451a7c98357b68ff08fd13e390fcec"

LEAN_TOOLCHAIN_ID = "leanprover/lean4:v4.30.0-rc2"

LEAN_TCB_DESCRIPTOR = (
    r"veyra.p1d2.lean-runner-tcb.v1\0leanprover/lean4:v4.30.0-rc2\0lean"
    r"\0-DwarningAsError=true\0captured-private-source\0post-read-continuity"
)

LEAN_TCB_DIGEST = "8687516385b19c5799d2fe08f3c8721fee41c261aff9499205b9132dd968acff"

THEOREM_IDS = (
    "THM_D2_LEAN_001_finite_strict_descent",
    "THM_D2_LEAN_002_no_infinite_nat_descent",
    "THM_D2_LEAN_003a_self_mem",
    "THM_D2_LEAN_003b_succ_subset",
    "THM_D2_LEAN_003c_diagonal_absence",
)

_AXIOM_ROWS = (
    "THM_D2_LEAN_001_finite_strict_descent' depends on axioms: [propext, Quot.sound]",
    "THM_D2_LEAN_002_no_infinite_nat_descent' depends on axioms: [propext, Quot.sound]",
    "THM_D2_LEAN_003a_self_mem' does not depend on any axioms",
    "THM_D2_LEAN_003b_succ_subset' does not depend on any axioms",
    "THM_D2_LEAN_003c_diagonal_absence' does not depend on any axioms",
)

def counterpressure_basis_source() -> CounterpressureBasisSource:
    """Build the sole exact foundation source without compiling it yet."""
    logger.debug("counterpressure_basis_source entry")
    if sha256(LEAN_TCB_DESCRIPTOR.encode()).hexdigest() != LEAN_TCB_DIGEST:
        reject("lean-tcb-descriptor-drift")
    digest = make_basis_digest(
        BASIS_VERSION, BASIS_ID, DerivationKind.LEAN_CHECKED_THEOREM.value,
        FOUNDATION_ID, ARTIFACT_NAME, ARTIFACT_SHA256, THEOREM_IDS,
        LEAN_TOOLCHAIN_ID, LEAN_TCB_DIGEST,
    )
    result = CounterpressureBasisSource(
        BASIS_VERSION, BASIS_ID, DerivationKind.LEAN_CHECKED_THEOREM,
        FOUNDATION_ID, ARTIFACT_NAME, ARTIFACT_SHA256, tuple(list(THEOREM_IDS)),
        LEAN_TOOLCHAIN_ID, LEAN_TCB_DIGEST, digest,
    )
    logger.debug("counterpressure_basis_source exit digest=%s", digest)
    return result

def snapshot_basis_source(value: CounterpressureBasisSource) -> CounterpressureBasisSource:
    """Reject basis subclasses, field drift, and theorem-name lookalikes."""
    logger.debug("snapshot_basis_source entry")
    exact_dataclass_shape(value, CounterpressureBasisSource, "basis-source")
    expected = counterpressure_basis_source()
    try:
        exact_digest(value.artifact_sha256, "artifact-sha256")
        exact_digest(value.tcb_digest, "tcb-digest")
        exact_digest(value.basis_digest, "basis-digest")
        if type(value.theorem_ids) is not tuple:
            reject("basis-theorem-ids-must-be-exact-tuple")
        scalar_rows = (
            (value.version, expected.version), (value.basis_id, expected.basis_id),
            (value.foundation_id, expected.foundation_id),
            (value.artifact_name, expected.artifact_name),
            (value.artifact_sha256, expected.artifact_sha256),
            (value.toolchain_id, expected.toolchain_id),
            (value.tcb_digest, expected.tcb_digest),
            (value.basis_digest, expected.basis_digest),
        )
        if any(type(actual) is not str or actual != wanted for actual, wanted in scalar_rows):
            reject("basis-source-drift")
        if (
            type(value.derivation_kind) is not DerivationKind
            or value.derivation_kind is not expected.derivation_kind
            or len(value.theorem_ids) != len(expected.theorem_ids)
            or any(
                type(actual) is not str or actual != wanted
                for actual, wanted in zip(value.theorem_ids, expected.theorem_ids, strict=True)
            )
        ):
            reject("basis-source-drift")
        supplied = CounterpressureBasisSource(
            value.version, value.basis_id, value.derivation_kind, value.foundation_id,
            value.artifact_name, value.artifact_sha256, tuple(value.theorem_ids),
            value.toolchain_id, value.tcb_digest, value.basis_digest,
        )
    except AttributeError:
        reject("basis-source-missing-fields")
    if supplied != expected:
        reject("basis-source-drift")
    logger.debug("snapshot_basis_source exit")
    return expected

def check_basis_source(value: CounterpressureBasisSource) -> CounterpressureBasisSource:
    """Compile captured exact bytes and rebind cached success to live continuity."""
    logger.debug("check_basis_source entry")
    source = snapshot_basis_source(value)
    path = Path(source.artifact_name)
    try:
        payload = path.read_bytes()
    except OSError as exc:
        logger.error("check_basis_source read failed error=%s", exc)
        reject("basis-artifact-unavailable")
    actual = sha256(payload).hexdigest()
    if not hmac.compare_digest(actual, source.artifact_sha256):
        reject("basis-artifact-drift")
    _check_exact_symbols(payload, source.theorem_ids)
    if not _compile_captured(payload, source.artifact_sha256, source.toolchain_id, source.tcb_digest):
        reject("basis-lean-check-failed")
    try:
        after = path.read_bytes()
    except OSError as exc:
        logger.error("check_basis_source reread failed error=%s", exc)
        reject("basis-artifact-continuity-failed")
    if payload != after or sha256(after).hexdigest() != source.artifact_sha256:
        reject("basis-artifact-continuity-failed")
    logger.debug("check_basis_source exit")
    return counterpressure_basis_source()

def _check_exact_symbols(payload: bytes, expected: tuple[str, ...]) -> None:
    logger.debug("_check_exact_symbols entry bytes=%d", len(payload))
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeError:
        reject("basis-artifact-invalid-utf8")
    symbols = tuple(re.findall(
        r"(?m)^[ \t]*(?:theorem|lemma)[ \t]+(THM_D2_[A-Za-z0-9_]+)(?=[ \t:(])",
        _strip_lean_comments(text),
    ))
    if symbols != expected:
        reject("basis-theorem-set-drift")
    logger.debug("_check_exact_symbols exit count=%d", len(symbols))

@lru_cache(maxsize=1)
def _compile_captured(payload: bytes, artifact_digest: str, toolchain: str, tcb: str) -> bool:
    logger.debug("_compile_captured entry bytes=%d", len(payload))
    if (
        sha256(payload).hexdigest() != artifact_digest or toolchain != LEAN_TOOLCHAIN_ID
        or tcb != LEAN_TCB_DIGEST
        or sha256(LEAN_TCB_DESCRIPTOR.encode()).hexdigest() != LEAN_TCB_DIGEST
    ):
        logger.error("_compile_captured identity precheck failed")
        return False
    elan = shutil.which("elan")
    if elan is None:
        logger.error("_compile_captured elan unavailable")
        return False
    root = TMP_DIR
    try:
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="d2-lean-", dir=root) as directory:
            capture = Path(directory) / f"{artifact_digest}.lean"
            capture.write_bytes(payload)
            capture.chmod(0o600)
            completed = subprocess.run(
                [elan, "run", toolchain, "lean", "-DwarningAsError=true", capture.name],
                cwd=capture.parent, capture_output=True, text=True, timeout=120, check=False,
            )
    except (OSError, subprocess.SubprocessError) as exc:
        logger.error("_compile_captured failed error=%s", exc)
        return False
    output = completed.stdout + completed.stderr
    axioms_exact = all(row in output for row in _AXIOM_ROWS)
    result = completed.returncode == 0 and axioms_exact
    logger.debug("_compile_captured exit rc=%d axioms=%s", completed.returncode, axioms_exact)
    return result


# Requests and preflight

logger = logging.getLogger(__name__)

REQUEST_VERSION = "p1-d2-request-v1"

ALPHABET_VERSION = "p1-d2-alphabet-v1"

POLICY_VERSION = "p1-d2-policy-v1"

MAX_LEDGER_ROWS = 128

MAX_ALPHABET_SYMBOLS = 16

MAX_TARGET_SYMBOLS = 256

MAX_REQUEST_BYTES = 65_536

MAX_SYMBOLIC_COST = 100_000

DEFAULT_REQUEST_BYTES = 4096

DEFAULT_SYMBOLIC_COST = 4096

@dataclass(frozen=True)
class PreparedCounterpressureRequest:
    request: CounterpressureRequest
    kind: CounterpressureRequestKind
    canonical_bytes: bytes
    digest: str
    symbolic_cost: int

def counterpressure_alphabet(
    symbols: tuple[str, ...], version: str = ALPHABET_VERSION,
) -> CounterpressureAlphabet:
    logger.debug("counterpressure_alphabet entry")
    if type(version) is not str or version != ALPHABET_VERSION:
        reject("unknown-counterpressure-alphabet-version")
    if type(symbols) is not tuple or not 1 <= len(symbols) <= MAX_ALPHABET_SYMBOLS:
        reject("invalid-counterpressure-alphabet")
    captured = tuple(exact_identifier(value, "alphabet-symbol") for value in symbols)
    if len(frozenset(captured)) != len(captured):
        reject("duplicate-counterpressure-alphabet-symbol")
    captured = tuple(list(captured))
    result = CounterpressureAlphabet(
        ALPHABET_VERSION, captured, alphabet_digest(ALPHABET_VERSION, captured))
    logger.debug("counterpressure_alphabet exit symbols=%d", len(captured))
    return result

def snapshot_alphabet(value: CounterpressureAlphabet) -> CounterpressureAlphabet:
    logger.debug("snapshot_alphabet entry")
    exact_dataclass_shape(value, CounterpressureAlphabet, "counterpressure-alphabet")
    try:
        expected = counterpressure_alphabet(value.symbols, value.version)
        supplied = value.alphabet_digest
    except AttributeError:
        reject("counterpressure-alphabet-missing-fields")
    if type(supplied) is not str or supplied != expected.alphabet_digest:
        reject("counterpressure-alphabet-drift")
    logger.debug("snapshot_alphabet exit")
    return expected

def counterpressure_policy(
    max_request_bytes: int = DEFAULT_REQUEST_BYTES,
    max_symbolic_cost: int = DEFAULT_SYMBOLIC_COST,
    version: str = POLICY_VERSION,
) -> CounterpressurePolicy:
    logger.debug("counterpressure_policy entry")
    if type(version) is not str or version != POLICY_VERSION:
        reject("unknown-counterpressure-policy-version")
    if type(max_request_bytes) is not int or not 1 <= max_request_bytes <= MAX_REQUEST_BYTES:
        reject("invalid-policy-max-request-bytes")
    if type(max_symbolic_cost) is not int or not 1 <= max_symbolic_cost <= MAX_SYMBOLIC_COST:
        reject("invalid-policy-max-symbolic-cost")
    result = CounterpressurePolicy(
        POLICY_VERSION, max_request_bytes, max_symbolic_cost,
        policy_digest(POLICY_VERSION, max_request_bytes, max_symbolic_cost),
    )
    logger.debug("counterpressure_policy exit")
    return result

def snapshot_policy(value: CounterpressurePolicy) -> CounterpressurePolicy:
    logger.debug("snapshot_policy entry")
    exact_dataclass_shape(value, CounterpressurePolicy, "counterpressure-policy")
    try:
        expected = counterpressure_policy(
            value.max_request_bytes, value.max_symbolic_cost, value.version
        )
        supplied = value.policy_digest
    except AttributeError:
        reject("counterpressure-policy-missing-fields")
    if type(supplied) is not str or supplied != expected.policy_digest:
        reject("counterpressure-policy-drift")
    logger.debug("snapshot_policy exit")
    return expected

def ledger_request(
    rows: tuple[LedgerRow, ...], version: str = REQUEST_VERSION,
) -> NonuniformLedgerRequest:
    logger.debug("ledger_request entry")
    result = snapshot_request(NonuniformLedgerRequest(version, rows))
    logger.debug("ledger_request exit")
    return result  # type: ignore[return-value]

def decreasing_tree_request(sample_depth: int, basis: object) -> DecreasingTreeRequest:
    logger.debug("decreasing_tree_request entry")
    result = snapshot_request(
        DecreasingTreeRequest(REQUEST_VERSION, sample_depth, basis)  # type: ignore[arg-type]
    )
    logger.debug("decreasing_tree_request exit")
    return result  # type: ignore[return-value]

def target_chooser_request(
    alphabet: CounterpressureAlphabet, target: tuple[str, ...],
) -> TargetChooserRequest:
    logger.debug("target_chooser_request entry")
    result = snapshot_request(TargetChooserRequest(REQUEST_VERSION, alphabet, target))
    logger.debug("target_chooser_request exit")
    return result  # type: ignore[return-value]

def long_run_request(steps: int) -> LongRunRequest:
    logger.debug("long_run_request entry")
    result = snapshot_request(LongRunRequest(REQUEST_VERSION, steps))
    logger.debug("long_run_request exit")
    return result  # type: ignore[return-value]

def shrinking_stage_request(sample_index: int, basis: object) -> ShrinkingStageRequest:
    logger.debug("shrinking_stage_request entry")
    result = snapshot_request(
        ShrinkingStageRequest(REQUEST_VERSION, sample_index, basis)  # type: ignore[arg-type]
    )
    logger.debug("shrinking_stage_request exit")
    return result  # type: ignore[return-value]

def snapshot_request(value: CounterpressureRequest) -> CounterpressureRequest:
    """Capture a closed request before any semantic or Lean operation."""
    logger.debug("snapshot_request entry type=%s", type(value).__name__)
    if type(value) is NonuniformLedgerRequest:
        exact_dataclass_shape(value, NonuniformLedgerRequest, "ledger-request")
        result: CounterpressureRequest = _snapshot_ledger(value)
    elif type(value) is DecreasingTreeRequest:
        exact_dataclass_shape(value, DecreasingTreeRequest, "descent-request")
        _version(value.version)
        result = DecreasingTreeRequest(
            REQUEST_VERSION, exact_natural(value.sample_depth, "sample-depth"),
            snapshot_basis_source(value.basis),
        )
    elif type(value) is TargetChooserRequest:
        exact_dataclass_shape(value, TargetChooserRequest, "chooser-request")
        _version(value.version)
        alphabet = snapshot_alphabet(value.alphabet)
        if type(value.target) is not tuple or not 1 <= len(value.target) <= MAX_TARGET_SYMBOLS:
            reject("invalid-target")
        allowed = frozenset(alphabet.symbols)
        target = tuple(exact_identifier(symbol, "target-symbol") for symbol in value.target)
        if any(symbol not in allowed for symbol in target):
            reject("foreign-target-symbol")
        result = TargetChooserRequest(REQUEST_VERSION, alphabet, tuple(list(target)))
    elif type(value) is LongRunRequest:
        exact_dataclass_shape(value, LongRunRequest, "long-run-request")
        _version(value.version)
        steps = exact_natural(value.steps, "steps")
        if steps == 0:
            reject("steps-must-be-positive")
        result = LongRunRequest(REQUEST_VERSION, steps)
    elif type(value) is ShrinkingStageRequest:
        exact_dataclass_shape(value, ShrinkingStageRequest, "shrinking-request")
        _version(value.version)
        result = ShrinkingStageRequest(
            REQUEST_VERSION, exact_natural(value.sample_index, "sample-index"),
            snapshot_basis_source(value.basis),
        )
    else:
        reject("request-variant-must-be-exact")
    payload = request_bytes(result)
    if len(payload) > MAX_REQUEST_BYTES:
        reject("request-hard-byte-limit")
    logger.debug("snapshot_request exit bytes=%d", len(payload))
    return result

def _snapshot_ledger(value: NonuniformLedgerRequest) -> NonuniformLedgerRequest:
    logger.debug("_snapshot_ledger entry")
    _version(value.version)
    if type(value.rows) is not tuple or not 2 <= len(value.rows) <= MAX_LEDGER_ROWS:
        reject("invalid-ledger-rows")
    rows: list[LedgerRow] = []
    depths: list[int] = []
    selectors: list[str] = []
    for raw in value.rows:
        exact_dataclass_shape(raw, LedgerRow, "ledger-row")
        row = LedgerRow(
            exact_natural(raw.depth, "ledger-depth"),
            exact_identifier(raw.witness_label, "witness-label"),
            exact_identifier(raw.selector_label, "selector-label"),
        )
        rows.append(row)
        depths.append(row.depth)
        selectors.append(row.selector_label)
    if any(left >= right for left, right in zip(depths, depths[1:], strict=False)):
        reject("ledger-depths-must-be-strictly-increasing")
    if len(frozenset(selectors)) != len(selectors):
        reject("ledger-selectors-must-be-unique")
    result = NonuniformLedgerRequest(REQUEST_VERSION, tuple(rows))
    logger.debug("_snapshot_ledger exit rows=%d", len(rows))
    return result

def _version(value: object) -> None:
    logger.debug("_version entry")
    if type(value) is not str or value != REQUEST_VERSION:
        reject("unknown-counterpressure-request-version")
    logger.debug("_version exit")

def prepare_request(value: CounterpressureRequest) -> PreparedCounterpressureRequest:
    logger.debug("prepare_request entry")
    request = snapshot_request(value)
    payload = request_bytes(request)
    kind = request_kind(request)
    cost = symbolic_cost(request, len(payload))
    result = PreparedCounterpressureRequest(
        request, kind, bytes(payload), request_digest(request), cost)
    logger.debug("prepare_request exit kind=%s cost=%d", kind.value, cost)
    return result

def request_kind(value: CounterpressureRequest) -> CounterpressureRequestKind:
    logger.debug("request_kind entry type=%s", type(value).__name__)
    mapping = {
        NonuniformLedgerRequest: CounterpressureRequestKind.LEDGER,
        DecreasingTreeRequest: CounterpressureRequestKind.DESCENT,
        TargetChooserRequest: CounterpressureRequestKind.CHOOSER,
        LongRunRequest: CounterpressureRequestKind.LONG_RUN,
        ShrinkingStageRequest: CounterpressureRequestKind.SHRINKING,
    }
    try:
        result = mapping[type(value)]
    except KeyError:
        reject("request-variant-must-be-exact")
    logger.debug("request_kind exit kind=%s", result.value)
    return result

def symbolic_cost(request: CounterpressureRequest, request_size: int) -> int:
    logger.debug("symbolic_cost entry type=%s", type(request).__name__)
    if type(request) is NonuniformLedgerRequest:
        result = 64 + request_size + 16 * len(request.rows)
    elif type(request) is DecreasingTreeRequest:
        result = 96 + request_size + request.sample_depth.bit_length()
    elif type(request) is TargetChooserRequest:
        result = 64 + request_size + 8 * len(request.target)
    elif type(request) is LongRunRequest:
        result = 64 + request_size + request.steps.bit_length()
    elif type(request) is ShrinkingStageRequest:
        result = 96 + request_size + request.sample_index.bit_length()
    else:
        reject("request-variant-must-be-exact")
    logger.debug("symbolic_cost exit cost=%d", result)
    return result

def first_failed_bound(
    prepared: PreparedCounterpressureRequest, policy: CounterpressurePolicy,
) -> tuple[CounterpressureResourceBound, int, int] | None:
    logger.debug("first_failed_bound entry")
    if len(prepared.canonical_bytes) > policy.max_request_bytes:
        logger.debug("first_failed_bound exit failed=request-bytes")
        return (
            CounterpressureResourceBound.REQUEST_BYTES,
            len(prepared.canonical_bytes), policy.max_request_bytes,
        )
    if prepared.symbolic_cost > policy.max_symbolic_cost:
        logger.debug("first_failed_bound exit failed=symbolic-cost")
        return (
            CounterpressureResourceBound.SYMBOLIC_COST,
            prepared.symbolic_cost, policy.max_symbolic_cost,
        )
    logger.debug("first_failed_bound exit allowed")
    return None

DEFAULT_POLICY = counterpressure_policy()


# Semantic replay

logger = logging.getLogger(__name__)

CHOOSER_RULE_ID = "read-target-and-copy-v1"

DESCENT_FORMULA_ID = "canonical-descending-fin-row-v1"

def replay_counterpressure(
    request: CounterpressureRequest,
) -> tuple[
    CounterpressureInference, CounterpressureOutcomeKind, CounterpressureStatus,
    CounterpressureEvidence, BasisUse, str | None,
]:
    """Derive one closed row; caller already performed representation preflight."""
    logger.debug("replay_counterpressure entry type=%s", type(request).__name__)
    if type(request) is NonuniformLedgerRequest:
        status = CounterpressureStatus.INSUFFICIENT_TO_ESTABLISH
        evidence: CounterpressureEvidence = LedgerInsufficiencyEvidence(
            len(request.rows), tuple(row.depth for row in request.rows),
            len(frozenset(row.selector_label for row in request.rows)), False, status,
        )
        result = (
            CounterpressureInference.LEDGER_GENERATOR,
            CounterpressureOutcomeKind.EVIDENCE_INSUFFICIENCY,
            status, evidence, BasisUse.NONE, None,
        )
    elif type(request) is DecreasingTreeRequest:
        basis = check_basis_source(request.basis)
        status = CounterpressureStatus.REFUTES_MATHEMATICAL_IMPLICATION
        first = None if request.sample_depth == 0 else request.sample_depth - 1
        last = None if request.sample_depth == 0 else 0
        evidence = DescentCountermodelEvidence(
            request.sample_depth, request.sample_depth, first, last,
            symbolic_formula_digest(DESCENT_FORMULA_ID, request.sample_depth),
            basis.basis_digest, status,
        )
        result = (
            CounterpressureInference.FINITE_DEPTH_BRANCH,
            CounterpressureOutcomeKind.MATHEMATICAL_COUNTERMODEL,
            status, evidence, BasisUse.BOUND, basis.basis_digest,
        )
    elif type(request) is TargetChooserRequest:
        status = CounterpressureStatus.REFUTES_MATHEMATICAL_IMPLICATION
        target = tuple(list(request.target))
        output = tuple(list(target))
        target_commitment = symbol_tuple_digest("chooser-sequence", target)
        output_commitment = symbol_tuple_digest("chooser-sequence", output)
        evidence = TargetDependenceEvidence(
            len(target), target_commitment, output_commitment, True, True,
            ChooserTargetIndependence.REFUTED, CHOOSER_RULE_ID, status,
        )
        result = (
            CounterpressureInference.POSTHOC_INDEPENDENCE,
            CounterpressureOutcomeKind.MATHEMATICAL_COUNTERMODEL,
            status, evidence, BasisUse.NONE, None,
        )
    elif type(request) is LongRunRequest:
        status = CounterpressureStatus.INSUFFICIENT_TO_ESTABLISH
        evidence = FiniteRunInsufficiencyEvidence(
            0, request.steps, request.steps + 1, False, status,
        )
        result = (
            CounterpressureInference.LONG_RUN_FAMILY,
            CounterpressureOutcomeKind.EVIDENCE_INSUFFICIENCY,
            status, evidence, BasisUse.NONE, None,
        )
    elif type(request) is ShrinkingStageRequest:
        basis = check_basis_source(request.basis)
        status = CounterpressureStatus.REFUTES_MATHEMATICAL_IMPLICATION
        n = request.sample_index
        evidence = ShrinkingTailCountermodelEvidence(
            n, n, n + 1, n, n, n + 1, basis.basis_digest, status,
        )
        result = (
            CounterpressureInference.NESTED_COMMON_POINT,
            CounterpressureOutcomeKind.MATHEMATICAL_COUNTERMODEL,
            status, evidence, BasisUse.BOUND, basis.basis_digest,
        )
    else:
        raise TypeError("unknown-counterpressure-request")
    logger.debug("replay_counterpressure exit inference=%s", result[0].value)
    return result


# Construction runtime

logger = logging.getLogger(__name__)

def _derive_counterpressure_result(
    request: CounterpressureRequest, policy: CounterpressurePolicy,
) -> CounterpressureResult:
    """Internal nonrecursive derivation used by construction and revalidation."""
    logger.debug("_derive_counterpressure_result entry")
    prepared = prepare_request(request)
    captured_policy = snapshot_policy(policy)
    failure = first_failed_bound(prepared, captured_policy)
    if failure is not None:
        bound, required, allowed = failure
        provisional = CounterpressureResourceLimit(
            prepared.kind, prepared.digest, bound, required, allowed,
            captured_policy.policy_digest, "0" * 64,
        )
        result: CounterpressureResult = replace(
            provisional, refusal_digest=refusal_digest(provisional)
        )
        logger.debug("_derive_counterpressure_result exit refusal=%s", bound.value)
        return result
    inference, outcome, status, evidence, basis_use, basis = replay_counterpressure(
        prepared.request
    )
    evidence_commitment = evidence_digest(evidence)
    provisional_certificate = CounterpressureCertificate(
        prepared.kind, prepared.digest, inference, outcome, status, evidence,
        evidence_commitment, basis_use, basis, captured_policy.policy_digest, "0" * 64,
    )
    result = replace(
        provisional_certificate,
        certificate_digest=certificate_digest(provisional_certificate),
    )
    logger.debug("_derive_counterpressure_result exit certificate=%s", inference.value)
    return result

def counterpressure_result(
    request: CounterpressureRequest, policy: CounterpressurePolicy = DEFAULT_POLICY,
) -> CounterpressureResult:
    """Construct then internally revalidate a fresh closed D2 result."""
    logger.debug("counterpressure_result entry")
    candidate = _derive_counterpressure_result(request, policy)
    result = validate_counterpressure_result(candidate, request, policy)
    logger.debug("counterpressure_result exit type=%s", type(result).__name__)
    return result


# Result revalidation

logger = logging.getLogger(__name__)

def _exact_shape(value: object, expected_type: type, field: str) -> None:
    logger.debug("_exact_shape entry field=%s", field)
    if type(value) is not expected_type:
        reject(f"result-{field}-variant-drift")
    if set(vars(value)) != set(expected_type.__dataclass_fields__):
        reject(f"result-{field}-shape-drift")
    logger.debug("_exact_shape exit field=%s", field)

def _exact_enum(value: object, expected: object, field: str) -> None:
    logger.debug("_exact_enum entry field=%s", field)
    if type(value) is not type(expected) or value is not expected:
        reject(f"result-{field}-drift")
    logger.debug("_exact_enum exit field=%s", field)

def _exact_str(value: object, expected: str, field: str) -> None:
    logger.debug("_exact_str entry field=%s", field)
    if type(value) is not str or value != expected:
        reject(f"result-{field}-drift")
    logger.debug("_exact_str exit field=%s", field)

def _exact_int(value: object, expected: int, field: str) -> None:
    logger.debug("_exact_int entry field=%s", field)
    if type(value) is not int or value != expected:
        reject(f"result-{field}-drift")
    logger.debug("_exact_int exit field=%s", field)

def _exact_bool(value: object, expected: bool, field: str) -> None:
    logger.debug("_exact_bool entry field=%s", field)
    if type(value) is not bool or value is not expected:
        reject(f"result-{field}-drift")
    logger.debug("_exact_bool exit field=%s", field)

def _outer_permanent(value: object, expected: object) -> None:
    logger.debug("_outer_permanent entry")
    _exact_enum(value.generator_nonexistence, expected.generator_nonexistence, "generator")
    _exact_enum(value.all_depth_family, expected.all_depth_family, "all-depth")
    _exact_enum(value.completed_carrier, expected.completed_carrier, "carrier")
    _exact_enum(
        value.historical_target_independence,
        expected.historical_target_independence, "target-independence",
    )
    _exact_str(value.scope, expected.scope, "scope")
    logger.debug("_outer_permanent exit")

def _certificate_outer(
    value: CounterpressureCertificate, expected: CounterpressureCertificate,
) -> None:
    logger.debug("_certificate_outer entry")
    _exact_enum(value.request_kind, expected.request_kind, "request-kind")
    exact_digest(value.request_digest, "result-request-digest")
    _exact_str(value.request_digest, expected.request_digest, "request-digest")
    _exact_enum(value.inference_id, expected.inference_id, "inference")
    _exact_enum(value.outcome_kind, expected.outcome_kind, "outcome")
    _exact_enum(value.status, expected.status, "status")
    exact_digest(value.evidence_digest, "result-evidence-digest")
    _exact_str(value.evidence_digest, expected.evidence_digest, "evidence-digest")
    _exact_enum(value.basis_use, expected.basis_use, "basis-use")
    if expected.basis_digest is None:
        if value.basis_digest is not None:
            reject("result-basis-digest-drift")
    else:
        exact_digest(value.basis_digest, "result-basis-digest")
        _exact_str(value.basis_digest, expected.basis_digest, "basis-digest")
    exact_digest(value.policy_digest, "result-policy-digest")
    _exact_str(value.policy_digest, expected.policy_digest, "policy-digest")
    exact_digest(value.certificate_digest, "result-certificate-digest")
    _exact_str(value.certificate_digest, expected.certificate_digest, "certificate-digest")
    _outer_permanent(value, expected)
    if type(value.evidence) is not type(expected.evidence):
        reject("result-evidence-variant-drift")
    logger.debug("_certificate_outer exit")

def _validate_evidence(value: object, expected: object) -> None:
    logger.debug("_validate_evidence entry type=%s", type(value).__name__)
    if type(value) is LedgerInsufficiencyEvidence and type(expected) is LedgerInsufficiencyEvidence:
        _exact_int(value.row_count, expected.row_count, "row-count")
        if type(value.depths) is not tuple or len(value.depths) != len(expected.depths):
            reject("result-depths-shape-drift")
        for index, (actual, wanted) in enumerate(zip(value.depths, expected.depths, strict=True)):
            _exact_int(actual, wanted, f"depth-{index}")
        _exact_int(value.selector_count, expected.selector_count, "selector-count")
        _exact_bool(value.common_source_supplied, False, "common-source")
        _exact_enum(value.status, expected.status, "evidence-status")
    elif type(value) is DescentCountermodelEvidence and type(expected) is DescentCountermodelEvidence:
        _exact_int(value.sample_depth, expected.sample_depth, "descent-sample")
        _exact_int(value.witness_length, expected.witness_length, "descent-length")
        _optional_int(value.first_or_none, expected.first_or_none, "descent-first")
        _optional_int(value.last_or_none, expected.last_or_none, "descent-last")
        exact_digest(value.witness_formula_digest, "result-formula-digest")
        _exact_str(value.witness_formula_digest, expected.witness_formula_digest, "formula")
        exact_digest(value.basis_digest, "result-evidence-basis-digest")
        _exact_str(value.basis_digest, expected.basis_digest, "evidence-basis")
        _exact_enum(value.status, expected.status, "evidence-status")
    elif type(value) is TargetDependenceEvidence and type(expected) is TargetDependenceEvidence:
        _exact_int(value.target_length, expected.target_length, "target-length")
        exact_digest(value.target_digest, "result-target-digest")
        exact_digest(value.output_digest, "result-output-digest")
        _exact_str(value.target_digest, expected.target_digest, "target-digest")
        _exact_str(value.output_digest, expected.output_digest, "output-digest")
        _exact_bool(value.exact_match, True, "exact-match")
        _exact_bool(value.target_read, True, "target-read")
        _exact_enum(
            value.chooser_target_independence,
            expected.chooser_target_independence, "chooser-independence",
        )
        _exact_str(value.chooser_rule_id, expected.chooser_rule_id, "chooser-rule")
        _exact_enum(value.status, expected.status, "evidence-status")
    elif (
        type(value) is FiniteRunInsufficiencyEvidence
        and type(expected) is FiniteRunInsufficiencyEvidence
    ):
        _exact_int(value.first_depth, 0, "run-first")
        _exact_int(value.last_depth, expected.last_depth, "run-last")
        _exact_int(value.executed_count, expected.executed_count, "run-count")
        _exact_bool(value.materialized, False, "materialized")
        _exact_enum(value.status, expected.status, "evidence-status")
    elif (
        type(value) is ShrinkingTailCountermodelEvidence
        and type(expected) is ShrinkingTailCountermodelEvidence
    ):
        for name in (
            "sample_index", "local_witness", "nested_from", "nested_into",
            "diagonal_candidate", "excluding_stage",
        ):
            _exact_int(getattr(value, name), getattr(expected, name), name)
        exact_digest(value.basis_digest, "result-evidence-basis-digest")
        _exact_str(value.basis_digest, expected.basis_digest, "evidence-basis")
        _exact_enum(value.status, expected.status, "evidence-status")
    else:
        reject("result-evidence-variant-drift")
    logger.debug("_validate_evidence exit")

def _optional_int(value: object, expected: int | None, field: str) -> None:
    logger.debug("_optional_int entry field=%s", field)
    if expected is None:
        if value is not None:
            reject(f"result-{field}-drift")
    else:
        _exact_int(value, expected, field)
    logger.debug("_optional_int exit field=%s", field)

def _validate_refusal(
    value: CounterpressureResourceLimit, expected: CounterpressureResourceLimit,
) -> None:
    logger.debug("_validate_refusal entry")
    _exact_enum(value.request_kind, expected.request_kind, "request-kind")
    exact_digest(value.request_digest, "result-request-digest")
    _exact_str(value.request_digest, expected.request_digest, "request-digest")
    _exact_enum(value.failed_bound, expected.failed_bound, "failed-bound")
    _exact_int(value.required_value, expected.required_value, "required")
    _exact_int(value.allowed_value, expected.allowed_value, "allowed")
    exact_digest(value.policy_digest, "result-policy-digest")
    _exact_str(value.policy_digest, expected.policy_digest, "policy-digest")
    exact_digest(value.refusal_digest, "result-refusal-digest")
    _exact_str(value.refusal_digest, expected.refusal_digest, "refusal-digest")
    _outer_permanent(value, expected)
    if refusal_digest(value) != value.refusal_digest:
        reject("result-refusal-commitment-drift")
    logger.debug("_validate_refusal exit")

def validate_counterpressure_result(
    value: CounterpressureResult, request: CounterpressureRequest,
    policy: CounterpressurePolicy,
) -> CounterpressureResult:
    """Rederive fixed semantics; accept no prior certificate as evidence."""
    logger.debug("validate_counterpressure_result entry")
    expected = _derive_counterpressure_result(request, policy)
    if type(expected) is CounterpressureResourceLimit:
        _exact_shape(value, CounterpressureResourceLimit, "union")
        _validate_refusal(value, expected)
        logger.debug("validate_counterpressure_result exit refusal")
        return expected
    _exact_shape(value, CounterpressureCertificate, "union")
    _certificate_outer(value, expected)
    _exact_shape(value.evidence, type(expected.evidence), "evidence")
    _validate_evidence(value.evidence, expected.evidence)
    if evidence_digest(value.evidence) != value.evidence_digest:
        reject("result-evidence-commitment-drift")
    if certificate_digest(value) != value.certificate_digest:
        reject("result-certificate-commitment-drift")
    logger.debug("validate_counterpressure_result exit certificate")
    return expected


__all__ = [
    "ALPHABET_VERSION", "ARTIFACT_NAME", "ARTIFACT_SHA256", "BASIS_ID",
    "DEFAULT_POLICY", "FOUNDATION_ID", "LEAN_TCB_DIGEST", "LEAN_TOOLCHAIN_ID",
    "MAX_REQUEST_BYTES", "MAX_SYMBOLIC_COST", "POLICY_VERSION", "REQUEST_VERSION",
    "THEOREM_IDS", "AllDepthFamilyStatus", "BasisUse", "ChooserTargetIndependence",
    "CompletedCarrierStatus", "CounterpressureAlphabet", "CounterpressureBasisSource",
    "CounterpressureCertificate", "CounterpressureEvidence", "CounterpressureInference",
    "CounterpressureOutcomeKind", "CounterpressurePolicy", "CounterpressureRequest",
    "CounterpressureRequestKind", "CounterpressureResourceBound",
    "CounterpressureResourceLimit", "CounterpressureResult", "CounterpressureStatus",
    "CounterpressureValidationError", "DecreasingTreeRequest", "DerivationKind",
    "DescentCountermodelEvidence", "FiniteRunInsufficiencyEvidence",
    "GeneratorNonexistence", "HistoricalTargetIndependence",
    "LedgerInsufficiencyEvidence", "LedgerRow", "LongRunRequest",
    "NonuniformLedgerRequest", "ShrinkingStageRequest",
    "ShrinkingTailCountermodelEvidence", "TargetChooserRequest",
    "TargetDependenceEvidence", "check_basis_source", "counterpressure_alphabet",
    "counterpressure_basis_source", "counterpressure_policy", "counterpressure_result",
    "decreasing_tree_request", "ledger_request", "long_run_request",
    "shrinking_stage_request", "target_chooser_request", "validate_counterpressure_result",
]
