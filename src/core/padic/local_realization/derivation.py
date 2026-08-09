"""Pure positive N3 derivation from freshly replayed raw dependencies."""

from __future__ import annotations

import logging

from ..completion.types import PadicCompletionJudgment
from ..family_introduction.types import N1FamilyJudgment
from .common import digest, realized_digest
from .sources import THEOREM_IDS, _family_digest
from .types import (
    BridgeDependencyUnion, N34Status, N3Kind, N3RealizationJudgment, N3Request,
    N34_NONCLAIMS,
)

logger = logging.getLogger(__name__)


def derive_n3_judgment(request: N3Request, replay: N1FamilyJudgment,
                       pomega2_replay: PadicCompletionJudgment,
                       ledger: BridgeDependencyUnion) -> N3RealizationJudgment:
    """Derive an N3 judgment only from its raw request, fresh N1 replay, and ledger."""
    logger.debug("derive_n3_judgment entry")
    if (replay.package_digest != request.n1.package_digest
            or pomega2_replay.package_digest != request.pomega2.package_digest
            or request.pomega2.theorem_source.theorem_ids[6] not in pomega2_replay.theorem_ids):
        raise RuntimeError("fresh raw N1/POMEGA2 replay identity mismatch")
    family = _family_digest(request.n1)
    introduction = replay.introduction_evidence_digest
    realized = realized_digest(family, request.pomega2.doctrine.carrier_id,
        request.pomega2.theorem_source.theorem_ids[6], ledger.ledger_digest)
    coordinate = digest("veyra.p3n3.coordinate-evidence.v1", (("realized", realized.encode()),
        ("family", family.encode()), ("theorem", THEOREM_IDS[1].encode()),
        ("ledger", ledger.ledger_digest.encode())))
    judgment = digest("veyra.p3n3.judgment.v1", (("request", request.request_digest.encode()),
        ("family", family.encode()), ("introduction", introduction.encode()),
        ("realized", realized.encode()), ("coordinate", coordinate.encode()),
        ("ledger", ledger.ledger_digest.encode())))
    if len({request.n1.package_digest, request.pomega2.package_digest,
            request.theorem.source_digest, family, introduction, realized,
            coordinate, judgment}) != 8:
        raise RuntimeError("internal N3 digest-domain collision")
    result = N3RealizationJudgment(N34Status.ESTABLISHED,
        N3Kind.LOCAL_REALIZATION_ESTABLISHED_RELATIVE_TO_EXACT_POMEGA2,
        request.n1.package_digest, request.pomega2.package_digest,
        request.theorem.source_digest, ledger.ledger_digest, family, introduction,
        realized, coordinate, THEOREM_IDS[:2], ledger.theorem_axiom_closure, 0,
        N34_NONCLAIMS, judgment)
    logger.debug("derive_n3_judgment exit")
    return result


def revalidate_n3_derivation(request: N3Request, replay: N1FamilyJudgment,
                             pomega2_replay: PadicCompletionJudgment,
                             ledger: BridgeDependencyUnion,
                             value: N3RealizationJudgment) -> N3RealizationJudgment:
    """Freshly rederive one equal-but-distinct role judgment."""
    logger.debug("revalidate_n3_derivation entry")
    expected = derive_n3_judgment(request, replay, pomega2_replay, ledger)
    if value != expected or value is expected:
        raise RuntimeError("internal role N3 revalidation mismatch")
    logger.debug("revalidate_n3_derivation exit")
    return expected
