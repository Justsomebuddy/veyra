"""Ordered observer proof artifact replay and anti-forgery tests."""

from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.observer_core_artifact import (
    MAX_ARTIFACT_TEXT_BYTES,
    ObserverProofArtifact,
    ObserverProofNode,
    make_observer_proof_artifact,
    observer_artifact_json,
    verify_observer_proof_artifact,
)
from src.core.observer_core_kernel import crest_observer
from src.core.observer_core_lean_render import render_observer_core_lean
from src.core.observer_core_proof_types import (
    CrestPulseEcho,
    EmbedR7,
    EqualityReadyEcho,
    ObserverProof,
    TailSilenceObstruction,
)
from src.core.proof_core_types import EqRefl, ProofContext, Pulse, Silence


def _proof() -> EqualityReadyEcho:
    return EqualityReadyEcho(crest_observer(), EmbedR7(EqRefl(Pulse(Silence()))))


def _artifact() -> ObserverProofArtifact:
    return make_observer_proof_artifact("THM-R11-TEST", ProofContext(), _proof())


def _replace_node(
    artifact: ObserverProofArtifact,
    index: int,
    node: ObserverProofNode,
) -> ObserverProofArtifact:
    nodes = list(artifact.nodes)
    nodes[index] = node
    return replace(artifact, nodes=tuple(nodes))


def test_artifact_binds_ordered_graph_r7_origin_and_outcomes() -> None:
    artifact = _artifact()
    assert len(artifact.nodes) == 2
    assert artifact.nodes[0].rule == "embed-r7"
    assert artifact.nodes[1].rule == "equality-ready-echo"
    assert artifact.nodes[1].premise_ids == (artifact.nodes[0].node_id,)
    assert artifact.r7_artifact_digests == (artifact.nodes[0].r7_artifact_digest,)
    assert artifact.r7_artifact_digests[0]
    assert '"r7_artifact"' in artifact.nodes[0].payload
    assert '"observer"' in artifact.nodes[1].payload
    assert '"tag":"echoes"' in artifact.statement
    assert '"tag":"echo"' in artifact.outcome
    assert artifact.rule_closure == ("embed-r7", "equality-ready-echo")
    assert artifact.observer_law_closure == ("equality-ready-echo",)
    assert "r7-proof-kernel" in artifact.support
    assert "observer-structural-totality" in artifact.support
    assert verify_observer_proof_artifact(artifact, ProofContext(), _proof()).ok
    assert observer_artifact_json(artifact) == observer_artifact_json(_artifact())


def test_tail_artifact_binds_exact_obstruction_path_without_r7_origin() -> None:
    proof = TailSilenceObstruction()
    artifact = make_observer_proof_artifact("THM-R11-TAIL", ProofContext(), proof)
    assert artifact.r7_artifact_digests == ()
    assert artifact.obstruction_paths == '[["apply-tail"]]'
    assert '"code":"tail-of-silence"' in artifact.outcome
    assert artifact.observer_law_closure == ("tail-silence-obstruction",)
    assert verify_observer_proof_artifact(artifact, ProofContext(), proof).ok


def test_digest_and_node_content_drift_are_rejected() -> None:
    artifact = _artifact()
    forged_digest = replace(artifact, proof_digest="0" * 64)
    assert not verify_observer_proof_artifact(forged_digest, ProofContext(), _proof()).ok
    node = replace(artifact.nodes[1], inferred_outcome="{}")
    forged_node = _replace_node(artifact, 1, node)
    assert not verify_observer_proof_artifact(forged_node, ProofContext(), _proof()).ok


def test_r7_artifact_digest_and_origin_drift_are_rejected() -> None:
    artifact = _artifact()
    node = replace(artifact.nodes[0], r7_artifact_digest="f" * 64)
    forged = _replace_node(artifact, 0, node)
    assert not verify_observer_proof_artifact(forged, ProofContext(), _proof()).ok
    other = EqualityReadyEcho(crest_observer(), EmbedR7(EqRefl(Silence())))
    assert not verify_observer_proof_artifact(artifact, ProofContext(), other).ok


def test_reordered_and_duplicate_nodes_are_rejected() -> None:
    artifact = _artifact()
    reordered = replace(artifact, nodes=tuple(reversed(artifact.nodes)))
    check = verify_observer_proof_artifact(reordered, ProofContext(), _proof())
    assert not check.ok
    assert any("reordered-observer-nodes" in item for item in check.errors)
    duplicate = replace(artifact, nodes=artifact.nodes + (artifact.nodes[0],))
    check = verify_observer_proof_artifact(duplicate, ProofContext(), _proof())
    assert not check.ok
    assert any("duplicate-observer-node" in item for item in check.errors)


def test_cyclic_dangling_and_disconnected_graphs_are_rejected() -> None:
    artifact = _artifact()
    root = replace(artifact.nodes[1], premise_ids=(artifact.nodes[1].node_id,))
    cyclic = _replace_node(artifact, 1, root)
    check = verify_observer_proof_artifact(cyclic, ProofContext(), _proof())
    assert not check.ok
    assert any("circular-observer-graph" in item for item in check.errors)
    dangling_root = replace(artifact.nodes[1], premise_ids=("ON-missing",))
    dangling = _replace_node(artifact, 1, dangling_root)
    check = verify_observer_proof_artifact(dangling, ProofContext(), _proof())
    assert not check.ok
    assert any("dangling-observer-premise" in item for item in check.errors)
    disconnected = replace(artifact, root_id=artifact.nodes[0].node_id)
    check = verify_observer_proof_artifact(disconnected, ProofContext(), _proof())
    assert not check.ok
    assert any("disconnected-observer-graph" in item for item in check.errors)


def test_artifact_type_subclass_is_rejected() -> None:
    class ForgedArtifact(ObserverProofArtifact):
        pass

    artifact = _artifact()
    forged = ForgedArtifact(*artifact.__dict__.values())
    check = verify_observer_proof_artifact(forged, ProofContext(), _proof())
    assert not check.ok
    assert any("invalid-observer-artifact-schema" in item for item in check.errors)
    class AttributeTrap:
        def __getattribute__(self, name: str) -> object:
            if name == "theorem_id":
                raise RuntimeError("attribute trap")
            return object.__getattribute__(self, name)
    check = verify_observer_proof_artifact(AttributeTrap(), ProofContext(), _proof())
    assert not check.ok


def test_renderer_type_guards_precede_attacker_dunder_access() -> None:
    class AttributeTrap:
        def __getattribute__(self, name: str) -> object:
            if name == "theorem_id":
                raise RuntimeError("attribute trap")
            return object.__getattribute__(self, name)

    class StringTrap:
        def __str__(self) -> str:
            raise RuntimeError("string trap")

    with pytest.raises(ValueError, match="invalid-observer-artifact-type"):
        render_observer_core_lean(AttributeTrap(), "0" * 64)
    with pytest.raises(ValueError, match="invalid-r10-binding-digest"):
        render_observer_core_lean(_artifact(), StringTrap())


def test_artifact_graph_and_theorem_resources_are_bounded() -> None:
    artifact = _artifact()
    oversized = replace(artifact, nodes=artifact.nodes * 129)
    assert not verify_observer_proof_artifact(oversized, ProofContext(), _proof()).ok
    oversized = replace(artifact, theorem_id="x" * 257)
    assert not verify_observer_proof_artifact(oversized, ProofContext(), _proof()).ok
    node = replace(artifact.nodes[0], premise_ids=("a", "b"))
    oversized = _replace_node(artifact, 0, node)
    check = verify_observer_proof_artifact(oversized, ProofContext(), _proof())
    assert not check.ok and "invalid-observer-premises" in check.errors
    oversized = replace(artifact, support=("🙂" * (MAX_ARTIFACT_TEXT_BYTES // 4 + 1),))
    check = verify_observer_proof_artifact(oversized, ProofContext(), _proof())
    assert not check.ok and "observer-artifact-text-limit" in check.errors
    with pytest.raises(ValueError, match="observer-artifact-text-limit"):
        observer_artifact_json(oversized)
    huge_premise = replace(artifact.nodes[1], premise_ids=("x" * (MAX_ARTIFACT_TEXT_BYTES + 1),))
    check = verify_observer_proof_artifact(_replace_node(artifact, 1, huge_premise), ProofContext(), _proof())
    assert not check.ok and "observer-artifact-text-limit" in check.errors
    half = MAX_ARTIFACT_TEXT_BYTES // 2 + 1
    aggregate_nodes = tuple(replace(node, payload="x" * half) for node in artifact.nodes)
    check = verify_observer_proof_artifact(replace(artifact, nodes=aggregate_nodes), ProofContext(), _proof())
    assert not check.ok and "observer-artifact-text-limit" in check.errors


def test_node_type_subclass_is_rejected() -> None:
    class ForgedNode(ObserverProofNode):
        pass

    artifact = _artifact()
    forged_node = ForgedNode(*artifact.nodes[0].__dict__.values())
    forged = replace(artifact, nodes=(forged_node, artifact.nodes[1]))
    check = verify_observer_proof_artifact(forged, ProofContext(), _proof())
    assert not check.ok
    assert any("invalid-observer-nodes" in item for item in check.errors)


@pytest.mark.parametrize(
    "proof",
    [
        EmbedR7(EqRefl(Silence())),
        EqualityReadyEcho(crest_observer(), EmbedR7(EqRefl(Pulse(Silence())))),
        CrestPulseEcho(Silence(), Pulse(Silence())),
        TailSilenceObstruction(),
    ],
)
def test_every_observer_rule_has_a_complete_replayable_artifact(proof: ObserverProof) -> None:
    artifact = make_observer_proof_artifact("THM-R11-ALL", ProofContext(), proof)
    assert verify_observer_proof_artifact(artifact, ProofContext(), proof).ok
    assert artifact.nodes
    assert artifact.root_id == artifact.nodes[-1].node_id


@pytest.mark.parametrize(
    "field",
    [
        "statement",
        "outcome",
        "obstruction_paths",
        "rule_closure",
        "observer_law_closure",
        "support",
        "r7_artifact_digests",
    ],
)
def test_every_top_level_semantic_binding_rejects_drift(field: str) -> None:
    artifact = _artifact()
    value = getattr(artifact, field)
    if isinstance(value, str):
        forged_value = value + " "
    else:
        forged_value = value + ("forged",)
    forged = replace(artifact, **{field: forged_value})
    assert not verify_observer_proof_artifact(forged, ProofContext(), _proof()).ok
