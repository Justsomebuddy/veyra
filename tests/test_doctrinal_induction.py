from collections import Counter
from dataclasses import asdict, replace
from hashlib import sha256
import json

import pytest

from src.core.doctrinal_induction import (
    BOUNDARY,
    AllDepthLicense,
    InductionDoctrine,
    PropertyContract,
    depth_bomb_contract,
    divides_family_contract,
    doctrinal_induction_checklist,
    license_all_depth,
    name_peeking_contract,
    uniformity_witness,
)
from src.core.intrinsic_arithmetic import one, successor, zero
from src.core.native_runtime import nod, rez

DOCTRINE = InductionDoctrine("di1.demo.v1", "stitch-one-block")


def _block(width: int):
    value = one()
    for _ in range(width - 1):
        value = successor(value)
    return value


def _anchor(name: str = "di1-work"):
    return nod(rez(name), name)


def test_divides_family_licensed_to_depth_twelve():
    license_row = license_all_depth(
        DOCTRINE, divides_family_contract(_block(3)), _anchor(), tuple(range(1, 13))
    )
    assert isinstance(license_row, AllDepthLicense)
    assert license_row.status == "licensed"
    assert license_row.obstruction == "none"
    assert license_row.base_valid
    assert license_row.uniformity is not None and license_row.uniformity.echoed
    assert license_row.max_depth == 12
    assert len(license_row.probes) == 12
    assert all(row.valid for row in license_row.probes)
    digests = [row.digest for row in license_row.probes]
    assert len(set(digests)) == 12
    assert license_row.boundary == BOUNDARY


def test_divides_family_receipt_chain_is_depth_sensitive():
    first = license_all_depth(DOCTRINE, divides_family_contract(_block(2)), _anchor(), (1, 2, 3))
    second = license_all_depth(DOCTRINE, divides_family_contract(_block(2)), _anchor(), (1, 2, 3))
    assert [row.digest for row in first.probes] == [row.digest for row in second.probes]
    wider = license_all_depth(DOCTRINE, divides_family_contract(_block(4)), _anchor(), (1, 2, 3))
    assert [row.digest for row in wider.probes] != [row.digest for row in first.probes]


def test_uniformity_holds_for_divides_family():
    witness = uniformity_witness(DOCTRINE, divides_family_contract(_block(3)))
    assert witness.status == "witnessed"
    assert witness.echoed
    assert witness.left_digest == witness.right_digest != ""


def test_name_peeking_step_is_rejected_by_renaming_echo():
    witness = uniformity_witness(DOCTRINE, name_peeking_contract())
    assert witness.status == "blocked"
    assert witness.obstruction == "nonuniform-step"
    assert witness.left_digest != witness.right_digest
    license_row = license_all_depth(DOCTRINE, name_peeking_contract(), _anchor(), (1, 2, 3))
    assert license_row.status == "blocked"
    assert license_row.obstruction == "nonuniform-step"


def test_depth_bomb_blocks_at_its_exact_depth():
    license_row = license_all_depth(
        DOCTRINE, depth_bomb_contract(_block(3), 5), _anchor(), tuple(range(1, 9))
    )
    assert license_row.status == "blocked"
    assert license_row.obstruction == "step-invalid-at-depth:5"
    assert license_row.probes[0].depth == 5
    assert not license_row.probes[0].valid


def test_silent_block_is_blocked():
    from src.core.intrinsic_arithmetic import zero

    license_row = license_all_depth(DOCTRINE, divides_family_contract(zero()), _anchor(), (1, 2))
    assert license_row.status == "blocked"
    assert license_row.obstruction == "silent-block"


def test_empty_probe_depths_blocked():
    license_row = license_all_depth(DOCTRINE, divides_family_contract(_block(2)), _anchor(), ())
    assert license_row.status == "blocked"
    assert license_row.obstruction == "empty-or-invalid-probe-depths"


def test_probe_depth_zero_blocked():
    license_row = license_all_depth(DOCTRINE, divides_family_contract(_block(2)), _anchor(), (0, 3))
    assert license_row.status == "blocked"
    assert license_row.obstruction == "empty-or-invalid-probe-depths"


def test_transform_is_local_not_recomputation():
    factory = divides_family_contract(_block(3))
    anchor = _anchor()
    contract = factory(anchor)
    subject = contract.subject_base(anchor)
    evidence = contract.establish_base(anchor, subject)
    for _ in range(3):
        following = contract.subject_step(subject)
        evidence = contract.transform_step(anchor, subject, following, evidence)
        subject = following
    assert contract.validate(anchor, subject, evidence) is True
    assert len(evidence.steps) == 4
    assert evidence.steps[-1].after == ()
    assert evidence.status == "exact"


def test_checklist_present():
    checklist = doctrinal_induction_checklist()
    assert len(checklist) == 5
    assert any("anchor-renaming echo" in item for item in checklist)
    assert any("nothing here is proved" in item for item in checklist)


def test_late_name_peek_is_rejected_because_uniformity_replays_to_probe_depth():
    from src.core.doctrinal_induction import late_name_peeking_contract

    shallow = uniformity_witness(DOCTRINE, late_name_peeking_contract(3))
    assert shallow.status == "witnessed"  # a depth-2 replay cannot see the leak
    deep = uniformity_witness(DOCTRINE, late_name_peeking_contract(3), depth=3)
    assert deep.status == "blocked"
    assert deep.obstruction == "nonuniform-step"
    license_row = license_all_depth(DOCTRINE, late_name_peeking_contract(3), _anchor(), tuple(range(1, 13)))
    assert license_row.status == "blocked"
    assert license_row.obstruction == "nonuniform-step"
    assert license_row.uniformity is not None and not license_row.uniformity.echoed


def test_working_property_must_match_the_fresh_uniformity_property():
    working = _anchor()
    inner_factory = divides_family_contract(_block(2))

    def factory(anchor):
        inner = inner_factory(anchor)
        return replace(
            inner,
            property_id="working-property" if anchor == working else "different-property",
        )

    # Agreement of the two fresh replays does not license another property.
    assert uniformity_witness(DOCTRINE, factory, depth=3).status == "witnessed"
    license_row = license_all_depth(DOCTRINE, factory, working, (1, 3))
    assert license_row.status == "blocked"
    assert license_row.obstruction == "working-chain-nonuniform"


def test_matching_property_id_does_not_hide_a_different_working_family():
    working = _anchor()
    working_factory = divides_family_contract(_block(3))
    fresh_factory = divides_family_contract(_block(2))

    def factory(anchor):
        return (working_factory if anchor == working else fresh_factory)(anchor)

    license_row = license_all_depth(DOCTRINE, factory, working, (3,))
    assert license_row.status == "blocked"
    assert license_row.obstruction == "working-chain-nonuniform"
    assert license_row.property_id == "di1.divides-family.v1"
    assert license_row.base_valid
    assert license_row.uniformity is not None and license_row.uniformity.echoed
    assert license_row.probes == ()


@pytest.mark.parametrize("different_middle", (False, True))
def test_mutable_evidence_is_bound_at_each_depth_before_it_is_overwritten(different_middle):
    working = _anchor()

    def factory(anchor):
        evidence = {"depth": 1, "tag": "uniform"}

        def transform(a, previous, current, prior):
            assert prior is evidence
            prior["depth"] += 1
            prior["tag"] = (
                "working-only"
                if different_middle and anchor == working and prior["depth"] == 2
                else "uniform"
            )
            return prior

        return PropertyContract(
            "mutable-evidence-family",
            zero,
            successor,
            lambda a, subject: evidence,
            transform,
            lambda a, subject, proof: proof["depth"] == len(subject.breath.tacts) + 1,
            lambda proof, rename: f"mutable[{proof['depth']};{proof['tag']}]",
        )

    # At depth 3 all current evidence is identical again. The chain must retain
    # an earlier difference, including when depth 2 is not a requested probe.
    license_row = license_all_depth(DOCTRINE, factory, working, (1, 3))
    assert license_row.status == ("blocked" if different_middle else "licensed")
    assert license_row.obstruction == ("working-chain-nonuniform" if different_middle else "none")


@pytest.mark.parametrize("probes", ((1,), (3,), (1, 3), (3, 1, 3), ()))
def test_binding_does_not_repeat_working_execution_callbacks(probes):
    working = nod(rez("separate-residue"), "separate-mark")
    calls = Counter()
    inner_factory = divides_family_contract(_block(2))

    def factory(anchor):
        calls[(anchor, "factory")] += 1
        assert calls[(anchor, "factory")] == 1
        inner = inner_factory(anchor)

        def counted(method):
            def invoke(*args):
                calls[(anchor, method)] += 1
                return getattr(inner, method)(*args)
            return invoke

        return replace(inner, **{
            method: counted(method)
            for method in ("subject_base", "subject_step", "establish_base", "transform_step", "validate")
        })

    license_row = license_all_depth(DOCTRINE, factory, working, probes)
    assert calls[(working, "factory")] == 1
    depth = max(probes, default=0)
    for method in ("subject_base", "establish_base"):
        assert calls[(working, method)] == bool(probes)
    for method in ("subject_step", "transform_step"):
        assert calls[(working, method)] == max(0, depth - 1)
    assert calls[(working, "validate")] == depth
    assert sum(count for (anchor, method), count in calls.items() if method == "factory") == (3 if probes else 1)
    assert license_row.status == ("licensed" if probes else "blocked")
    assert license_row.obstruction == ("none" if probes else "empty-or-invalid-probe-depths")


@pytest.mark.parametrize("family,width,probes,expected_digest", (
    ("divides", 3, (1, 2, 3, 5), "e11e13b55a092a5453a4241c38fc014ef747fe2f394f138bd553d17187fc0b60"),
    ("divides", 5, (1, 2, 3, 5), "bb3816060a7351734eac2bebe98fbb14abda7057ab5ff2b8ea58a0ca12296953"),
    ("fermat", 3, (1, 2, 3), "52f5efffbf80ff37c52edfc5efb8826f5b1a9b097d7fa88ab66355b21ef01fc0"),
    ("fermat", 5, (1, 2, 3), "aca574a8a0aca447613eb6d3580c2d80a1093a8ddf1d432f3d71b99ec266695f"),
))
def test_working_binding_preserves_complete_valid_license_dtos(family, width, probes, expected_digest):
    from src.core.orbit_partition import fermat_family_contract

    factory = divides_family_contract(_block(width)) if family == "divides" else fermat_family_contract(width)
    license_row = license_all_depth(
        InductionDoctrine("binding-baseline.v1", "basis"),
        factory,
        nod(rez("binding-work-residue"), "binding-work-mark"),
        probes,
    )
    assert license_row.status == "licensed"
    encoded = json.dumps(asdict(license_row), sort_keys=True, separators=(",", ":")).encode()
    assert sha256(encoded).hexdigest() == expected_digest
