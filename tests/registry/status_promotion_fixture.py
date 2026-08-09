"""Shared exact fixture for focused P2-S tests."""

from src.core.status_promotion import (
    EvidenceStatus as S, JudgmentKind as K, PositiveProvenance as P,
    assumption_node, claim_descriptor, evidence_field, index_binding,
    premise_artifact, promotion_audit_request, promotion_policy, promotion_registry,
)
from src.core.status_promotion_digest import digest


def _d(label: str) -> str:
    return digest("test.p2s.v1", (("label", label.encode()),))


def valid_case():
    registry = promotion_registry()
    doctrine = index_binding("doctrine", _d("doctrine"))
    scope = index_binding("scope", _d("scope"))
    stage = index_binding("stage", _d("stage"))
    premises = (
        premise_artifact(
            "seed", "seed-source", _d("seed"), (doctrine,),
            (evidence_field("seed", _d("seed-evidence")),),
        ),
        premise_artifact(
            "program", "closed-program", _d("program"), (scope, stage),
            (evidence_field("replay", _d("replay")),),
        ),
    )
    conclusion = claim_descriptor(
        "claim-generation", K.GENERABLE, S.ESTABLISHED_RELATIVE_TO_SCOPE,
        P.EXECUTABLE_REPLAY, (doctrine, scope, stage), registry,
    )
    assumptions = (
        assumption_node("a0", "source-bound", (), _d("a0")),
        assumption_node("a1", "replay-bound", ("a0",), _d("a1")),
    )
    request = promotion_audit_request(
        "p1-b-finite-generation-v1", premises, assumptions, conclusion, registry,
    )
    return registry, promotion_policy(), request
