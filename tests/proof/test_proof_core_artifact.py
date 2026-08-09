from dataclasses import replace
import json

import pytest

from src.core.proof_core_artifact import (
    ProofNodeArtifact, artifact_json, canonical_json, make_proof_artifact,
    verify_proof_artifact,
)
from src.core.proof_core_types import (
    Assume, Bound, CoreType, EqRefl, EqSym, EqTrans, Equal, ForallElim,
    ImpElim, ImpIntro, Implies, NativeLaw, NativeLawId, ProofContext, Pulse,
    ResonanceIntro, Silence, ForallIntro,
)


def resonance_artifact_proof():
    equality = NativeLaw(NativeLawId.WEAVE_UNIT_RIGHT, (Bound(0),))
    return ForallIntro(
        CoreType.RECURRENCE,
        ResonanceIntro(Bound(0), Bound(0), Pulse(Silence()), equality),
    )


def resonance_artifact():
    return make_proof_artifact("THM-R7-001", ProofContext(), resonance_artifact_proof())


def transitive_artifact():
    law = NativeLaw(NativeLawId.STITCH_SILENCE_LEFT, (Bound(0),))
    proof = EqTrans(law, EqSym(law))
    return make_proof_artifact("THM-R7-TRANS-TEST", ProofContext((CoreType.RECURRENCE,), ()), proof)


def test_artifact_is_deterministic_connected_and_canonical():
    first, second = resonance_artifact(), resonance_artifact()
    assert first == second
    assert verify_proof_artifact(first).ok
    rendered = artifact_json(first)
    assert rendered == canonical_json(json.loads(rendered))
    assert len(first.nodes) == 3
    assert all(len(node.node_id) == 67 for node in first.nodes)
    assert first.proof_digest in rendered


def test_artifact_codec_replays_every_supported_rule_shape():
    proposition = Equal(Silence(), Silence())
    universal = ForallIntro(CoreType.RECURRENCE, EqRefl(Bound(0)))
    law = NativeLaw(NativeLawId.STITCH_SILENCE_LEFT, (Bound(0),))
    cases = (
        (ProofContext((), (proposition,)), Assume(0)),
        (ProofContext(), ImpIntro(proposition, Assume(0))),
        (ProofContext((), (Implies(proposition, proposition), proposition)), ImpElim(Assume(0), Assume(1))),
        (ProofContext(), universal),
        (ProofContext(), ForallElim(universal, Silence())),
        (ProofContext(), EqRefl(Silence())),
        (ProofContext(), EqSym(EqRefl(Silence()))),
        (ProofContext((CoreType.RECURRENCE,), ()), EqTrans(law, EqSym(law))),
        (ProofContext((CoreType.RECURRENCE,), ()), law),
        (ProofContext(), resonance_artifact_proof()),
    )
    for index, (context, proof) in enumerate(cases):
        artifact = make_proof_artifact(f"RULE-CODEC-{index}", context, proof)
        assert verify_proof_artifact(artifact).ok


def test_canonical_json_refuses_repr_float_and_non_string_keys():
    with pytest.raises(TypeError, match="noncanonical"):
        canonical_json(object())
    with pytest.raises(TypeError, match="noncanonical"):
        canonical_json(1.5)
    with pytest.raises(TypeError, match="noncanonical"):
        canonical_json({1: "not-a-string-key"})


@pytest.mark.parametrize(
    "mutation",
    (
        lambda item: replace(item, proof_digest="0" * 64),
        lambda item: replace(item, statement=canonical_json({"tag": "equal", "left": {"tag": "silence"}, "right": {"tag": "silence"}})),
        lambda item: replace(item, rule_closure=()),
        lambda item: replace(item, native_law_closure=()),
        lambda item: replace(item, theorem_id=""),
    ),
)
def test_forged_artifact_metadata_is_rejected(mutation):
    assert not verify_proof_artifact(mutation(resonance_artifact())).ok


def test_forged_node_payload_conclusion_and_id_are_rejected():
    artifact = resonance_artifact()
    node = artifact.nodes[0]
    variants = (
        replace(node, payload=node.payload + " "),
        replace(node, inferred_conclusion=canonical_json({"tag": "equal", "left": {"tag": "silence"}, "right": {"tag": "silence"}})),
        replace(node, node_id="PN-" + "0" * 24),
    )
    for forged in variants:
        nodes = tuple(forged if item.node_id == node.node_id else item for item in artifact.nodes)
        assert not verify_proof_artifact(replace(artifact, nodes=nodes)).ok


def test_dangling_disconnected_and_circular_graphs_are_rejected():
    artifact = resonance_artifact()
    root = next(item for item in artifact.nodes if item.node_id == artifact.root_id)
    dangling = replace(root, premise_ids=("PN-missing",))
    dangling_nodes = tuple(dangling if item.node_id == root.node_id else item for item in artifact.nodes)
    assert not verify_proof_artifact(replace(artifact, nodes=dangling_nodes)).ok

    extra_artifact = make_proof_artifact("extra", ProofContext(), EqRefl(Silence()))
    disconnected_nodes = tuple(sorted(artifact.nodes + extra_artifact.nodes, key=lambda item: item.node_id))
    assert not verify_proof_artifact(replace(artifact, nodes=disconnected_nodes)).ok

    circular = replace(root, premise_ids=(root.node_id,))
    circular_nodes = tuple(circular if item.node_id == root.node_id else item for item in artifact.nodes)
    assert not verify_proof_artifact(replace(artifact, nodes=circular_nodes)).ok


def test_ordered_premise_reversal_and_context_reuse_are_rejected():
    artifact = transitive_artifact()
    root = next(item for item in artifact.nodes if item.node_id == artifact.root_id)
    reversed_root = replace(root, premise_ids=tuple(reversed(root.premise_ids)))
    nodes = tuple(reversed_root if item.node_id == root.node_id else item for item in artifact.nodes)
    assert not verify_proof_artifact(replace(artifact, nodes=nodes)).ok

    child = next(item for item in resonance_artifact().nodes if item.rule == "native-law")
    forged_child = replace(child, context_digest="0" * 64)
    source = resonance_artifact()
    nodes = tuple(forged_child if item.node_id == child.node_id else item for item in source.nodes)
    assert not verify_proof_artifact(replace(source, nodes=nodes)).ok


def test_duplicate_nodes_and_unknown_rule_are_rejected():
    artifact = resonance_artifact()
    assert not verify_proof_artifact(replace(artifact, nodes=artifact.nodes + (artifact.nodes[0],))).ok
    node = artifact.nodes[0]
    unknown = ProofNodeArtifact(node.node_id, "forged-rule", node.payload, node.premise_ids, node.context_digest, node.inferred_conclusion)
    nodes = tuple(unknown if item.node_id == node.node_id else item for item in artifact.nodes)
    assert not verify_proof_artifact(replace(artifact, nodes=nodes)).ok


def test_verifier_is_nonthrowing_for_runtime_container_forgery():
    artifact = resonance_artifact()
    assert not verify_proof_artifact(replace(artifact, nodes=[object()])).ok
    assert not verify_proof_artifact(replace(artifact, rule_closure=[])).ok
