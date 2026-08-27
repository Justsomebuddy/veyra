"""Doctrinal induction (DI-1): candidate proof-family licenses over recurrences.

Boundary: DI-1 is a RESEARCH CANDIDATE rule, not an adopted axiom. From a
base witness, a step schema, and a declared generator (the AFIP-style
totality basis), it licenses a ledger-relative all-depth *proof family*:
every finite depth replays in exactly that many step applications, and the
step schema transforms the previous derivation instead of recomputing it.
DI-1 never produces a completed carrier or an unconditional "for all"; the
P1-D2 finite-to-universal countermodels remain binding, and adopting the
generator is a doctrine act (gap-audit non-claim 8 applies to any object
reading). Uniformity is checked natively: the step derivation must be
echo-invariant under anchor renaming — an executable "the proof is about
the form of the recurrence, not its name". Shift-uniformity across depths
is a recorded OPEN refinement. Statuses are `licensed`/`blocked`, never
`proved`. Tuple slicing/length below is chain bookkeeping under the
docs/06 §3 shadow license; every mathematical acceptance goes through the
native weave/stitch reconstruction check. See
docs/180_doctrinal_induction_di1.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import logging
from typing import Callable

from .intrinsic_arithmetic import stitch, successor, weave
from .intrinsic_arithmetic_division import structural_divide
from .intrinsic_arithmetic_types import DivisionStep, StructuralDivisionProof
from .native_runtime import Mode, NativeObstruction, Nod, nod, rez

logger = logging.getLogger(__name__)

BOUNDARY = (
    "ledger-relative productive proof-family license; no completed carrier; "
    "no unconditional universal; generator adoption is a doctrine act; "
    "P1-D2 countermodels remain binding"
)
_FRESH_LEFT = "di1-fresh-alpha"
_FRESH_RIGHT = "di1-fresh-beta"
_RENAMED = "•"


@dataclass(frozen=True)
class InductionDoctrine:
    """Declared DI-1 doctrine: identity, generator basis, fixed boundary."""

    doctrine_id: str
    generator_id: str
    boundary: str = BOUNDARY


@dataclass(frozen=True)
class PropertyContract:
    """Property-specific callables consumed by the DI-1 core."""

    property_id: str
    subject_base: Callable[[Nod], Mode | NativeObstruction]
    subject_step: Callable[[Mode], Mode | NativeObstruction]
    establish_base: Callable[[Nod, Mode], object]
    transform_step: Callable[[Nod, Mode, Mode, object], object]
    validate: Callable[[Nod, Mode, object], bool | NativeObstruction]
    evidence_shape: Callable[[object, dict[str, str]], str]


@dataclass(frozen=True)
class ProofReceipt:
    """One depth of the licensed family with a chained digest."""

    doctrine_id: str
    depth: int
    subject: Mode
    evidence: object
    digest: str


@dataclass(frozen=True)
class UniformityWitness:
    """Anchor-renaming echo of the derivation at two fresh anchors."""

    left_digest: str
    right_digest: str
    echoed: bool
    status: str
    obstruction: str


@dataclass(frozen=True)
class ProbeRow:
    """One probed depth of a license replay."""

    depth: int
    valid: bool
    digest: str
    obstruction: str


@dataclass(frozen=True)
class AllDepthLicense:
    """Ledger-relative DI-1 license outcome."""

    doctrine: InductionDoctrine
    property_id: str
    base_valid: bool
    uniformity: UniformityWitness | None
    probes: tuple[ProbeRow, ...]
    max_depth: int
    status: str
    obstruction: str
    boundary: str = BOUNDARY


def _digest(parts: tuple[str, ...]) -> str:
    logger.debug("di1._digest entry parts=%d", len(parts))
    accumulator = sha256()
    for part in parts:
        encoded = part.encode("utf-8")
        accumulator.update(len(encoded).to_bytes(8, "big"))
        accumulator.update(encoded)
    result = accumulator.hexdigest()
    logger.debug("di1._digest exit digest=%s", result[:12])
    return result


def _name(rename: dict[str, str], value: str) -> str:
    logger.debug("di1._name entry value=%s", value)
    result = rename.get(value, value)
    logger.debug("di1._name exit result=%s", result)
    return result


def mode_shape(value: Mode, rename: dict[str, str]) -> str:
    """Serialize a mode with declared anchor names normalized."""
    logger.debug("di1.mode_shape entry")
    tacts = value.breath.tacts
    if not tacts and value.breath.anchor is not None:
        anchor = value.breath.anchor
        result = "mode[anchor=%s:%s]" % (
            _name(rename, anchor.residue.name), _name(rename, anchor.mark)
        )
        logger.debug("di1.mode_shape exit result=%s", result)
        return result
    parts = ";".join(
        "%s:%s>%s>%s:%s" % (
            _name(rename, item.start.residue.name), _name(rename, item.start.mark),
            item.mark,
            _name(rename, item.end.residue.name), _name(rename, item.end.mark),
        )
        for item in tacts
    )
    result = "mode[%s]" % parts
    logger.debug("di1.mode_shape exit tacts=%d", len(tacts))
    return result


def division_shape(evidence: object, rename: dict[str, str]) -> str:
    """Serialize division evidence with anchor names normalized."""
    logger.debug("di1.division_shape entry")
    if not isinstance(evidence, StructuralDivisionProof):
        result = "nondivision[%s]" % type(evidence).__name__
        logger.debug("di1.division_shape exit result=%s", result)
        return result
    steps = "|".join(
        "%d>%d" % (len(step.before), len(step.after)) for step in evidence.steps
    )
    result = "division[%s;%s;%s;%s;%s;%s]" % (
        evidence.status, evidence.reconstructs,
        mode_shape(evidence.dividend, rename), mode_shape(evidence.divisor, rename),
        mode_shape(evidence.quotient, rename), steps,
    )
    logger.debug("di1.division_shape exit steps=%d", len(evidence.steps))
    return result


def _receipt(
    doctrine: InductionDoctrine,
    contract: PropertyContract,
    depth: int,
    subject: Mode,
    evidence: object,
    previous: str,
    rename: dict[str, str],
) -> ProofReceipt:
    logger.debug("di1._receipt entry depth=%d", depth)
    digest = _digest((
        doctrine.doctrine_id, contract.property_id, str(depth),
        mode_shape(subject, rename), contract.evidence_shape(evidence, rename),
        previous,
    ))
    result = ProofReceipt(doctrine.doctrine_id, depth, subject, evidence, digest)
    logger.debug("di1._receipt exit digest=%s", digest[:12])
    return result


def _chain(
    doctrine: InductionDoctrine,
    contract: PropertyContract,
    anchor: Nod,
    depth_limit: int,
    rename: dict[str, str],
) -> tuple[ProofReceipt, ...] | tuple[str, int]:
    """Replay the family to a depth; return receipts or (obstruction, depth)."""
    logger.debug("di1._chain entry limit=%d", depth_limit)
    subject = contract.subject_base(anchor)
    if isinstance(subject, NativeObstruction):
        logger.error("di1._chain base subject blocked %r", subject)
        return (subject.reason, 1)
    evidence = contract.establish_base(anchor, subject)
    if isinstance(evidence, NativeObstruction):
        logger.error("di1._chain base evidence blocked %r", evidence)
        return (evidence.reason, 1)
    verdict = contract.validate(anchor, subject, evidence)
    if verdict is not True:
        logger.error("di1._chain base invalid verdict=%r", verdict)
        return ("base-invalid", 1)
    receipts = [_receipt(doctrine, contract, 1, subject, evidence, "", rename)]
    depth = 1
    while depth < depth_limit:
        depth += 1
        next_subject = contract.subject_step(subject)
        if isinstance(next_subject, NativeObstruction):
            logger.error("di1._chain subject blocked depth=%d", depth)
            return (next_subject.reason, depth)
        evidence = contract.transform_step(anchor, subject, next_subject, evidence)
        if isinstance(evidence, NativeObstruction):
            logger.error("di1._chain step blocked depth=%d", depth)
            return (evidence.reason, depth)
        verdict = contract.validate(anchor, next_subject, evidence)
        if verdict is not True:
            logger.error("di1._chain step invalid depth=%d", depth)
            return ("step-invalid-at-depth", depth)
        subject = next_subject
        receipts.append(
            _receipt(doctrine, contract, depth, subject, evidence, receipts[-1].digest, rename)
        )
    result = tuple(receipts)
    logger.debug("di1._chain exit receipts=%d", len(result))
    return result


def _fresh_anchor(name: str) -> Nod:
    logger.debug("di1._fresh_anchor entry name=%s", name)
    result = nod(rez(name), name)
    logger.debug("di1._fresh_anchor exit result=%r", result)
    return result


def uniformity_witness(
    doctrine: InductionDoctrine,
    contract_factory: Callable[[Nod], PropertyContract | NativeObstruction],
    depth: int = 2,
) -> UniformityWitness:
    """Check anchor-renaming echo of the derivation at two fresh anchors."""
    logger.debug("di1.uniformity_witness entry depth=%d", depth)
    digests: list[str] = []
    for name in (_FRESH_LEFT, _FRESH_RIGHT):
        anchor = _fresh_anchor(name)
        contract = contract_factory(anchor)
        if isinstance(contract, NativeObstruction):
            result = UniformityWitness("", "", False, "blocked", contract.reason)
            logger.error("di1.uniformity_witness blocked %r", result)
            return result
        chain = _chain(doctrine, contract, anchor, depth, {name: _RENAMED})
        if isinstance(chain, tuple) and chain and isinstance(chain[0], str):
            result = UniformityWitness("", "", False, "blocked", str(chain[0]))
            logger.error("di1.uniformity_witness blocked %r", result)
            return result
        digests.append(chain[-1].digest)
    echoed = digests[0] == digests[1]
    result = UniformityWitness(
        digests[0], digests[1], echoed,
        "witnessed" if echoed else "blocked",
        "none" if echoed else "nonuniform-step",
    )
    if not echoed:
        logger.error("di1.uniformity_witness nonuniform %r", result)
    logger.debug("di1.uniformity_witness exit echoed=%s", echoed)
    return result


def license_all_depth(
    doctrine: InductionDoctrine,
    contract_factory: Callable[[Nod], PropertyContract | NativeObstruction],
    working_anchor: Nod,
    probe_depths: tuple[int, ...],
) -> AllDepthLicense:
    """License a ledger-relative all-depth proof family, or block with a reason."""
    logger.debug("di1.license_all_depth entry probes=%r", probe_depths)
    probes = tuple(sorted(set(probe_depths)))
    contract = contract_factory(working_anchor)
    if isinstance(contract, NativeObstruction):
        result = AllDepthLicense(doctrine, "", False, None, (), 0, "blocked", contract.reason)
        logger.error("di1.license_all_depth blocked %r", result)
        return result
    if not probes or probes[0] < 1:
        result = AllDepthLicense(doctrine, contract.property_id, False, None, (), 0, "blocked", "empty-or-invalid-probe-depths")
        logger.error("di1.license_all_depth blocked %r", result)
        return result
    uniformity = uniformity_witness(doctrine, contract_factory)
    if uniformity.status != "witnessed":
        result = AllDepthLicense(doctrine, contract.property_id, False, uniformity, (), 0, "blocked", uniformity.obstruction)
        logger.error("di1.license_all_depth blocked %r", result)
        return result
    chain = _chain(doctrine, contract, working_anchor, probes[-1], {})
    if isinstance(chain, tuple) and chain and isinstance(chain[0], str):
        reason, depth = str(chain[0]), int(chain[1])
        rows = (ProbeRow(depth, False, "", reason),)
        result = AllDepthLicense(doctrine, contract.property_id, depth > 1, uniformity, rows, depth, "blocked", "%s:%d" % (reason, depth))
        logger.error("di1.license_all_depth blocked %r", result.obstruction)
        return result
    by_depth = {receipt.depth: receipt for receipt in chain}
    rows = tuple(ProbeRow(depth, True, by_depth[depth].digest, "none") for depth in probes)
    result = AllDepthLicense(doctrine, contract.property_id, True, uniformity, rows, probes[-1], "licensed", "none")
    logger.debug("di1.license_all_depth exit licensed max=%d", probes[-1])
    return result


def divides_family_contract(block: Mode) -> Callable[[Nod], PropertyContract | NativeObstruction]:
    """Return the contract factory for the family: block divides block·n."""
    logger.debug("di1.divides_family_contract entry")

    def factory(anchor: Nod) -> PropertyContract | NativeObstruction:
        logger.debug("di1.divides.factory entry anchor=%r", anchor)
        local_tacts = tuple(
            type(item)(anchor, anchor, item.mark) for item in block.breath.tacts
        )
        if not local_tacts:
            result = NativeObstruction("di1-divides", "silent-block", ())
            logger.error("di1.divides.factory blocked %r", result)
            return result
        from .native_runtime import Breath, mode as wrap_mode
        local_block = wrap_mode(Breath(local_tacts))
        if isinstance(local_block, NativeObstruction):
            logger.error("di1.divides.factory wrap blocked %r", local_block)
            return local_block

        def subject_base(a: Nod) -> Mode | NativeObstruction:
            logger.debug("di1.divides.subject_base entry")
            return local_block

        def subject_step(previous: Mode) -> Mode | NativeObstruction:
            logger.debug("di1.divides.subject_step entry")
            return stitch(previous, local_block)

        def establish_base(a: Nod, subject: Mode) -> object:
            logger.debug("di1.divides.establish_base entry")
            return structural_divide(subject, local_block)

        def transform_step(a: Nod, previous: Mode, current: Mode, prior: object) -> object:
            logger.debug("di1.divides.transform_step entry")
            if not isinstance(prior, StructuralDivisionProof) or prior.status != "exact":
                result = NativeObstruction("di1-divides", "prior-evidence-not-exact", ())
                logger.error("di1.divides.transform_step blocked %r", result)
                return result
            pattern = local_block.breath.tacts
            shifted = tuple(
                DivisionStep(step.before + pattern, step.after + pattern)
                for step in prior.steps
            )
            steps = shifted + (DivisionStep(pattern, ()),)
            quotient = successor(prior.quotient)
            if isinstance(quotient, NativeObstruction):
                logger.error("di1.divides.transform_step quotient blocked %r", quotient)
                return quotient
            woven = weave(local_block, quotient)
            reconstructed = woven if isinstance(woven, NativeObstruction) else stitch(woven, prior.residual)
            reconstructs = isinstance(reconstructed, Mode) and reconstructed.breath == current.breath
            result = StructuralDivisionProof(
                current, local_block, quotient, prior.residual, reconstructed,
                steps, "exact", reconstructs,
            )
            logger.debug("di1.divides.transform_step exit steps=%d", len(steps))
            return result

        def validate(a: Nod, subject: Mode, evidence: object) -> bool | NativeObstruction:
            logger.debug("di1.divides.validate entry")
            if not isinstance(evidence, StructuralDivisionProof):
                logger.error("di1.divides.validate wrong type")
                return False
            pattern = local_block.breath.tacts
            if evidence.status != "exact" or evidence.residual.breath.tacts:
                logger.error("di1.divides.validate nonexact")
                return False
            if evidence.dividend.breath != subject.breath or evidence.divisor.breath != local_block.breath:
                logger.error("di1.divides.validate subject mismatch")
                return False
            expected = subject.breath.tacts
            for step in evidence.steps:
                if step.before != expected or step.before[: len(pattern)] != pattern:
                    logger.error("di1.divides.validate chain break")
                    return False
                if step.after != step.before[len(pattern):]:
                    logger.error("di1.divides.validate drop mismatch")
                    return False
                expected = step.after
            if expected != ():
                logger.error("di1.divides.validate nonempty tail")
                return False
            woven = weave(local_block, evidence.quotient)
            rebuilt = woven if isinstance(woven, NativeObstruction) else stitch(woven, evidence.residual)
            result = isinstance(rebuilt, Mode) and rebuilt.breath == subject.breath
            if not result:
                logger.error("di1.divides.validate reconstruction failed")
            logger.debug("di1.divides.validate exit result=%s", result)
            return result

        result = PropertyContract(
            "di1.divides-family.v1", subject_base, subject_step,
            establish_base, transform_step, validate, division_shape,
        )
        logger.debug("di1.divides.factory exit")
        return result

    logger.debug("di1.divides_family_contract exit")
    return factory


def name_peeking_contract() -> Callable[[Nod], PropertyContract | NativeObstruction]:
    """Adversarial control: evidence smuggles the raw anchor name (must fail U1)."""
    logger.debug("di1.name_peeking_contract entry")

    def factory(anchor: Nod) -> PropertyContract:
        logger.debug("di1.peek.factory entry")
        from .intrinsic_arithmetic import zero

        def shape(evidence: object, rename: dict[str, str]) -> str:
            logger.debug("di1.peek.shape entry")
            return "peek[%s]" % evidence

        result = PropertyContract(
            "di1.name-peeking-control.v1",
            lambda a: zero(a),
            lambda previous: successor(previous),
            lambda a, subject: "tag:%s" % a.residue.name,
            lambda a, previous, current, prior: "tag:%s" % a.residue.name,
            lambda a, subject, evidence: True,
            shape,
        )
        logger.debug("di1.peek.factory exit")
        return result

    logger.debug("di1.name_peeking_contract exit")
    return factory


def depth_bomb_contract(block: Mode, bomb_depth: int) -> Callable[[Nod], PropertyContract | NativeObstruction]:
    """Adversarial control: the step corrupts its derivation at one exact depth."""
    logger.debug("di1.depth_bomb_contract entry bomb=%d", bomb_depth)
    base_factory = divides_family_contract(block)

    def factory(anchor: Nod) -> PropertyContract | NativeObstruction:
        logger.debug("di1.bomb.factory entry")
        inner = base_factory(anchor)
        if isinstance(inner, NativeObstruction):
            return inner
        state = {"depth": 1}

        def transform(a: Nod, previous: Mode, current: Mode, prior: object) -> object:
            logger.debug("di1.bomb.transform entry depth=%d", state["depth"])
            state["depth"] += 1
            evidence = inner.transform_step(a, previous, current, prior)
            if state["depth"] == bomb_depth and isinstance(evidence, StructuralDivisionProof):
                logger.error("di1.bomb.transform corrupting at depth=%d", bomb_depth)
                return StructuralDivisionProof(
                    evidence.dividend, evidence.divisor, evidence.quotient,
                    evidence.residual, evidence.reconstructed,
                    evidence.steps[:-1], evidence.status, evidence.reconstructs,
                )
            return evidence

        result = PropertyContract(
            "di1.depth-bomb-control.v1", inner.subject_base, inner.subject_step,
            inner.establish_base, transform, inner.validate, inner.evidence_shape,
        )
        logger.debug("di1.bomb.factory exit")
        return result

    logger.debug("di1.depth_bomb_contract exit")
    return factory


def doctrinal_induction_checklist() -> tuple[str, ...]:
    """Return the DI-1 lane acceptance checklist."""
    logger.debug("di1.checklist entry")
    result = (
        "the step schema transforms the previous derivation; validators re-check it natively",
        "uniformity is anchor-renaming echo of receipt digests at two fresh anchors",
        "licenses are ledger-relative productive families; no completed carrier, no bare universal",
        "adversarial controls exist: a name-peeking step fails U1; a depth bomb blocks at its exact depth",
        "statuses are licensed/witnessed/blocked; nothing here is proved",
    )
    logger.debug("di1.checklist exit count=%d", len(result))
    return result
