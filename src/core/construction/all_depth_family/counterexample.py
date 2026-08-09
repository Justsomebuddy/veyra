"""Closed finite counterexamples for candidate all-depth family laws."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import logging

from .common import exact_digest, exact_identifier, exact_shape, reject
from .digest import digest, frame, text_rows
from .sources import snapshot_family_source
from .spec import snapshot_family_spec
from .types import (
    AllDepthFamilySpec, CompletedCarrierStatus, FamilyEvidenceStatus,
    FamilyIntroductionSource, LawStatus,
)

logger = logging.getLogger(__name__)


# Data model

class FamilyLaw(str, Enum):
    RELATION_REFLEXIVE = "relation-reflexive"
    RELATION_TRANSITIVE = "relation-transitive"
    RESTRICTION_CONGRUENCE = "restriction-congruence"
    RESTRICTION_IDENTITY = "restriction-identity"
    RESTRICTION_COMPOSITION = "restriction-composition"

class FamilyNonexistence(str, Enum):
    NOT_PROVED = "not-proved"

@dataclass(frozen=True)
class RelationEdge:
    left: str
    right: str

@dataclass(frozen=True)
class RestrictionRow:
    map_id: str
    source: str
    target: str

@dataclass(frozen=True)
class FiniteFamilyLawWitness:
    version: str
    law: FamilyLaw
    universe: tuple[str, ...]
    relation_edges: tuple[RelationEdge, ...]
    restriction_rows: tuple[RestrictionRow, ...]
    arguments: tuple[str, ...]
    witness_digest: str

@dataclass(frozen=True)
class CounterexampleLawVector:
    relation_reflexive: LawStatus
    relation_transitive: LawStatus
    restriction_congruence: LawStatus
    restriction_identity: LawStatus
    restriction_composition: LawStatus

@dataclass(frozen=True)
class FamilyLawCounterexampleAssessment:
    specification_digest: str
    source_digest: str
    law: FamilyLaw
    witness_digest: str
    evaluator_id: str
    evaluator_digest: str
    affected_status: LawStatus
    law_statuses: CounterexampleLawVector
    result_digest: str
    family_evidence: FamilyEvidenceStatus = FamilyEvidenceStatus.OPEN
    family_nonexistence: FamilyNonexistence = FamilyNonexistence.NOT_PROVED
    afip_introduction: bool = False
    completed_carrier: CompletedCarrierStatus = CompletedCarrierStatus.NOT_ESTABLISHED
    scope: str = "finite-candidate-law-counterexample-no-afip-impact"


# Closed witness grammar

logger = logging.getLogger(__name__)

WITNESS_VERSION = "p1-d3-law-counterexample-v1"

EVALUATOR_ID = "p1-d3-closed-finite-law-evaluator-v1"

MAX_UNIVERSE = 32

MAX_RELATION_EDGES = 1024

MAX_RESTRICTION_ROWS = 1024

_ARG_COUNTS = {
    FamilyLaw.RELATION_REFLEXIVE: 1,
    FamilyLaw.RELATION_TRANSITIVE: 3,
    FamilyLaw.RESTRICTION_CONGRUENCE: 3,
    FamilyLaw.RESTRICTION_IDENTITY: 2,
    FamilyLaw.RESTRICTION_COMPOSITION: 4,
}

def relation_edge(left: str, right: str) -> RelationEdge:
    """Build one exact directed candidate-relation edge."""
    logger.debug("relation_edge entry")
    result = RelationEdge(
        exact_identifier(left, "relation-left"), exact_identifier(right, "relation-right"),
    )
    logger.debug("relation_edge exit")
    return result

def restriction_row(map_id: str, source: str, target: str) -> RestrictionRow:
    """Build one exact finite restriction-table row."""
    logger.debug("restriction_row entry")
    result = RestrictionRow(
        exact_identifier(map_id, "restriction-map-id"),
        exact_identifier(source, "restriction-source"),
        exact_identifier(target, "restriction-target"),
    )
    logger.debug("restriction_row exit")
    return result

def _snapshot_edge(value: RelationEdge) -> RelationEdge:
    logger.debug("_snapshot_edge entry")
    exact_shape(value, RelationEdge, "relation-edge")
    try:
        result = relation_edge(value.left, value.right)
    except AttributeError:
        reject("relation-edge-missing-fields")
    logger.debug("_snapshot_edge exit")
    return result

def _snapshot_restriction(value: RestrictionRow) -> RestrictionRow:
    logger.debug("_snapshot_restriction entry")
    exact_shape(value, RestrictionRow, "restriction-row")
    try:
        result = restriction_row(value.map_id, value.source, value.target)
    except AttributeError:
        reject("restriction-row-missing-fields")
    logger.debug("_snapshot_restriction exit")
    return result

def _witness_digest(
    law: FamilyLaw, universe: tuple[str, ...], edges: tuple[RelationEdge, ...],
    rows: tuple[RestrictionRow, ...], arguments: tuple[str, ...],
) -> str:
    logger.debug("_witness_digest entry law=%s", law.value)
    edge_bytes = tuple(
        (f"edge-{i}", frame("veyra.p1d3.law-edge.v1", (
            ("left", row.left.encode()), ("right", row.right.encode()),
        ))) for i, row in enumerate(edges)
    )
    row_bytes = tuple(
        (f"restriction-{i}", frame("veyra.p1d3.restriction-row.v1", (
            ("map", row.map_id.encode()), ("source", row.source.encode()),
            ("target", row.target.encode()),
        ))) for i, row in enumerate(rows)
    )
    result = digest("veyra.p1d3.law-witness.v1", (
        ("version", WITNESS_VERSION.encode()), ("law", law.value.encode()),
        *text_rows("universe", universe),
        ("edge-count", len(edges).to_bytes(8, "big")), *edge_bytes,
        ("restriction-count", len(rows).to_bytes(8, "big")), *row_bytes,
        *text_rows("argument", arguments),
    ))
    logger.debug("_witness_digest exit")
    return result

def finite_family_law_witness(
    law: FamilyLaw, universe: tuple[str, ...], relation_edges: tuple[RelationEdge, ...],
    restriction_rows: tuple[RestrictionRow, ...], arguments: tuple[str, ...],
) -> FiniteFamilyLawWitness:
    """Capture a bounded finite model and one exact law-test argument tuple."""
    logger.debug("finite_family_law_witness entry")
    if type(law) is not FamilyLaw:
        reject("family-law-must-be-exact")
    if type(universe) is not tuple or not 1 <= len(universe) <= MAX_UNIVERSE:
        reject("invalid-law-witness-universe")
    captured_universe = tuple(exact_identifier(item, "law-universe-item") for item in universe)
    if len(set(captured_universe)) != len(captured_universe):
        reject("duplicate-law-universe-item")
    if type(relation_edges) is not tuple or len(relation_edges) > MAX_RELATION_EDGES:
        reject("invalid-relation-edge-table")
    edges = tuple(_snapshot_edge(item) for item in relation_edges)
    if len({(item.left, item.right) for item in edges}) != len(edges):
        reject("duplicate-relation-edge")
    if any(item.left not in captured_universe or item.right not in captured_universe for item in edges):
        reject("relation-edge-universe-transplant")
    if type(restriction_rows) is not tuple or len(restriction_rows) > MAX_RESTRICTION_ROWS:
        reject("invalid-restriction-table")
    rows = tuple(_snapshot_restriction(item) for item in restriction_rows)
    if len({(item.map_id, item.source) for item in rows}) != len(rows):
        reject("nondeterministic-restriction-table")
    if any(item.source not in captured_universe or item.target not in captured_universe for item in rows):
        reject("restriction-row-universe-transplant")
    if type(arguments) is not tuple or len(arguments) != _ARG_COUNTS[law]:
        reject("invalid-law-witness-arguments")
    args = tuple(exact_identifier(item, "law-witness-argument") for item in arguments)
    _validate_argument_kinds(law, captured_universe, args)
    value = _witness_digest(law, captured_universe, edges, rows, args)
    result = FiniteFamilyLawWitness(
        WITNESS_VERSION, law, captured_universe, edges, rows, args, value,
    )
    logger.debug("finite_family_law_witness exit")
    return result

def _validate_argument_kinds(law: FamilyLaw, universe: tuple[str, ...], args: tuple[str, ...]) -> None:
    logger.debug("_validate_argument_kinds entry law=%s", law.value)
    value_args = args if law in (FamilyLaw.RELATION_REFLEXIVE, FamilyLaw.RELATION_TRANSITIVE) else (
        args[1:] if law is not FamilyLaw.RESTRICTION_COMPOSITION else args[3:]
    )
    if any(item not in universe for item in value_args):
        reject("law-witness-value-argument-transplant")
    logger.debug("_validate_argument_kinds exit")

def snapshot_family_law_witness(value: FiniteFamilyLawWitness) -> FiniteFamilyLawWitness:
    """Rebuild every nested scalar before comparing the commitment."""
    logger.debug("snapshot_family_law_witness entry")
    exact_shape(value, FiniteFamilyLawWitness, "finite-family-law-witness")
    try:
        if type(value.version) is not str or value.version != WITNESS_VERSION:
            reject("law-witness-version-drift")
        exact_digest(value.witness_digest, "witness-digest")
        expected = finite_family_law_witness(
            value.law, value.universe, value.relation_edges,
            value.restriction_rows, value.arguments,
        )
    except AttributeError:
        reject("finite-family-law-witness-missing-fields")
    if value != expected:
        reject("finite-family-law-witness-drift")
    logger.debug("snapshot_family_law_witness exit")
    return expected

def witness_refutes_law(value: FiniteFamilyLawWitness) -> bool:
    """Evaluate the exact directed relation/restriction grammar, not caller booleans."""
    logger.debug("witness_refutes_law entry")
    value = snapshot_family_law_witness(value)
    edges = {(row.left, row.right) for row in value.relation_edges}
    restrictions = {(row.map_id, row.source): row.target for row in value.restriction_rows}
    args = value.arguments
    try:
        if value.law is FamilyLaw.RELATION_REFLEXIVE:
            result = (args[0], args[0]) not in edges
        elif value.law is FamilyLaw.RELATION_TRANSITIVE:
            x, y, z = args
            result = (x, y) in edges and (y, z) in edges and (x, z) not in edges
        elif value.law is FamilyLaw.RESTRICTION_CONGRUENCE:
            map_id, x, y = args
            result = (x, y) in edges and (
                restrictions[(map_id, x)], restrictions[(map_id, y)]
            ) not in edges
        elif value.law is FamilyLaw.RESTRICTION_IDENTITY:
            map_id, x = args
            result = (restrictions[(map_id, x)], x) not in edges
        else:
            upper, lower, direct, x = args
            via = restrictions[(lower, restrictions[(upper, x)])]
            result = (via, restrictions[(direct, x)]) not in edges
    except KeyError:
        reject("law-witness-missing-restriction-row")
    logger.debug("witness_refutes_law exit result=%s", result)
    return result


# Assessment runtime

logger = logging.getLogger(__name__)

def _evaluator_digest() -> str:
    logger.debug("_evaluator_digest entry")
    result = digest("veyra.p1d3.law-evaluator.v1", (
        ("evaluator", EVALUATOR_ID.encode()), ("grammar", WITNESS_VERSION.encode()),
    ))
    logger.debug("_evaluator_digest exit")
    return result

def _law_vector(law: FamilyLaw) -> CounterexampleLawVector:
    logger.debug("_law_vector entry law=%s", law.value)
    values = {name: LawStatus.OPEN for name in CounterexampleLawVector.__dataclass_fields__}
    values[law.value.replace("-", "_")] = LawStatus.REFUTED
    result = CounterexampleLawVector(**values)
    logger.debug("_law_vector exit")
    return result

def _result_digest(
    spec: str, source: str, law: FamilyLaw, witness: str,
    evaluator: str, statuses: CounterexampleLawVector,
) -> str:
    logger.debug("_result_digest entry")
    result = digest("veyra.p1d3.law-counterexample-assessment.v1", (
        ("spec", spec.encode()), ("source", source.encode()),
        ("law", law.value.encode()), ("witness", witness.encode()),
        ("evaluator", evaluator.encode()),
        *((name, value.value.encode()) for name, value in vars(statuses).items()),
        ("family-evidence", FamilyEvidenceStatus.OPEN.value.encode()),
        ("family-nonexistence", FamilyNonexistence.NOT_PROVED.value.encode()),
        ("afip-introduction", b"false"),
        ("completed-carrier", CompletedCarrierStatus.NOT_ESTABLISHED.value.encode()),
        ("scope", b"finite-candidate-law-counterexample-no-afip-impact"),
    ))
    logger.debug("_result_digest exit")
    return result

def _assess_family_law_counterexample(
    spec: AllDepthFamilySpec, source: FamilyIntroductionSource,
    witness: FiniteFamilyLawWitness,
) -> FamilyLawCounterexampleAssessment:
    logger.debug("_assess_family_law_counterexample entry")
    spec = snapshot_family_spec(spec)
    source = snapshot_family_source(source)
    witness = snapshot_family_law_witness(witness)
    if source.spec != spec:
        reject("law-counterexample-spec-source-transplant")
    if not witness_refutes_law(witness):
        reject("witness-does-not-refute-law")
    evaluator = _evaluator_digest()
    statuses = _law_vector(witness.law)
    result = FamilyLawCounterexampleAssessment(
        spec.specification_digest, source.source_digest, witness.law,
        witness.witness_digest, EVALUATOR_ID, evaluator, LawStatus.REFUTED,
        statuses, _result_digest(
            spec.specification_digest, source.source_digest, witness.law,
            witness.witness_digest, evaluator, statuses,
        ),
    )
    logger.debug("_assess_family_law_counterexample exit")
    return result

def assess_family_law_counterexample(
    spec: AllDepthFamilySpec, source: FamilyIntroductionSource,
    witness: FiniteFamilyLawWitness,
) -> FamilyLawCounterexampleAssessment:
    """Assess one finite candidate law without changing AFIP family admission."""
    logger.debug("assess_family_law_counterexample entry")
    candidate = _assess_family_law_counterexample(spec, source, witness)
    result = validate_family_law_counterexample_assessment(spec, source, witness, candidate)
    logger.debug("assess_family_law_counterexample exit")
    return result

def validate_family_law_counterexample_assessment(
    spec: AllDepthFamilySpec, source: FamilyIntroductionSource,
    witness: FiniteFamilyLawWitness, value: FamilyLawCounterexampleAssessment,
) -> FamilyLawCounterexampleAssessment:
    """Validate every result field before fresh semantic recomputation."""
    logger.debug("validate_family_law_counterexample_assessment entry")
    exact_shape(value, FamilyLawCounterexampleAssessment, "law-counterexample-assessment")
    try:
        for name in (
            "specification_digest", "source_digest", "witness_digest",
            "evaluator_digest", "result_digest",
        ):
            exact_digest(getattr(value, name), name.replace("_", "-"))
        if type(value.law) is not FamilyLaw or type(value.affected_status) is not LawStatus:
            reject("law-assessment-enum-lookalike")
        if type(value.evaluator_id) is not str or value.evaluator_id != EVALUATOR_ID:
            reject("law-assessment-evaluator-drift")
        exact_shape(value.law_statuses, CounterexampleLawVector, "counterexample-law-vector")
        if any(type(item) is not LawStatus for item in vars(value.law_statuses).values()):
            reject("law-vector-status-lookalike")
        if (
            type(value.family_evidence) is not FamilyEvidenceStatus
            or type(value.family_nonexistence) is not FamilyNonexistence
            or type(value.afip_introduction) is not bool
            or type(value.completed_carrier) is not CompletedCarrierStatus
            or type(value.scope) is not str
        ):
            reject("law-assessment-permanent-field-lookalike")
    except AttributeError:
        reject("law-counterexample-assessment-missing-fields")
    expected = _assess_family_law_counterexample(spec, source, witness)
    if value != expected:
        reject("law-counterexample-assessment-semantic-drift")
    if (
        value.affected_status is not LawStatus.REFUTED
        or value.family_evidence is not FamilyEvidenceStatus.OPEN
        or value.family_nonexistence is not FamilyNonexistence.NOT_PROVED
        or value.afip_introduction is not False
        or value.completed_carrier is not CompletedCarrierStatus.NOT_ESTABLISHED
    ):
        reject("law-counterexample-assessment-promotion")
    statuses = vars(value.law_statuses)
    affected = value.law.value.replace("-", "_")
    if statuses[affected] is not LawStatus.REFUTED or any(
        status is not LawStatus.OPEN for name, status in statuses.items() if name != affected
    ):
        reject("law-counterexample-unrelated-status-drift")
    logger.debug("validate_family_law_counterexample_assessment exit")
    return expected

