from src.core.depth_packs import binomial_symmetry_card
from src.core.geometry import event_from_ints
from src.core.geometry_theorems import pythagorean_card
from veyra_sage.all import VeyraProofGraph, VeyraProofObject


def test_veyra_proof_graph_summary_and_domain_index():
    graph = VeyraProofGraph()
    summary = graph.summary()
    domains = graph.domain_index()
    assert summary["theorem_specs"] == 19
    assert summary["definition_edges"] > 0
    assert summary["curriculum_edges"] == 12
    assert "geometry" in domains
    assert "pythagorean-separation" in domains["geometry"]


def test_veyra_proof_object_checks_executable_card():
    graph = VeyraProofGraph()
    proof = graph.proof_object("binomial-symmetry")
    assert isinstance(proof, VeyraProofObject)
    assert proof.depends_on("DEF-117")
    checked = proof.check(binomial_symmetry_card(6, 2))
    assert checked.status == "ready"
    assert checked.as_dict()["obstruction"] == "none"


def test_veyra_proof_graph_dependency_queries():
    graph = VeyraProofGraph()
    assert "DEF-088" in graph.definition_dependencies("pythagorean-separation")
    assert "pythagorean-separation" in graph.theorems_using("DEF-088")
    geometry = graph.proof_objects("geometry")
    assert all(item.hook.startswith("geometry.") for item in geometry)


def test_veyra_proof_graph_curriculum_paths():
    graph = VeyraProofGraph()
    assert graph.curriculum_successors("probability") == ("statistics",)
    assert "probability" in graph.curriculum_predecessors("statistics")
    assert graph.curriculum_path("arithmetic-ratios", "statistics") == (
        "arithmetic-ratios",
        "combinatorics",
        "probability",
        "statistics",
    )


def test_veyra_proof_object_blocks_bad_card():
    graph = VeyraProofGraph()
    proof = graph.proof_object("pythagorean-separation")
    bad = pythagorean_card(event_from_ints((0, 0)), event_from_ints((3, 0)), event_from_ints((1, 1)))
    checked = proof.check(bad)
    assert checked.status == "blocked"
    assert checked.obstruction == "non-right-apex"
