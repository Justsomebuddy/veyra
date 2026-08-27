from src.core.doctrinal_induction import (
    BOUNDARY,
    AllDepthLicense,
    InductionDoctrine,
    depth_bomb_contract,
    divides_family_contract,
    doctrinal_induction_checklist,
    license_all_depth,
    name_peeking_contract,
    uniformity_witness,
)
from src.core.intrinsic_arithmetic import one, successor
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
