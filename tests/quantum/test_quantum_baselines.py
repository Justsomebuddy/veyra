from src.core.quantum_baselines import quantum_baseline_checklist, quantum_baseline_rows, quantum_baseline_summary


def test_quantum_baseline_rows_cover_current_quantum_results():
    rows = quantum_baseline_rows()
    assert [row.result_id for row in rows] == [
        "Q-HH", "Q-XX", "Q-CNOT-NORM", "Q-BELL-NONFACT", "Q-ZX-SHADOW", "Q-NO-CLONE",
        "Q2-SYNDROME", "Q2-ECHO-SPLIT", "Q2-DOUBLE-ERROR",
        "Q4-TOPO-ECHO", "Q5-QEC-ECHO", "Q5-QEC-AMBIGUITY", "Q6-GATE-ID", "Q7-ERROR-OBS", "Q8-QFT-PERIOD", "Q9-CIRCUIT-COMPRESS",
    ]
    assert all(row.status == "benchmarked" for row in rows)


def test_quantum_baseline_summary_blocks_advantage_claims():
    summary = quantum_baseline_summary()
    assert summary == {
        "rows": 16,
        "benchmarked": 16,
        "families": 10,
        "q1_rows": 6,
        "q2_rows": 3,
        "q4_rows": 1,
        "q5_rows": 2,
        "q6_rows": 1,
        "q7_rows": 1,
        "q8_rows": 1,
        "q9_rows": 1,
        "stronger_claims": 0,
        "overclaims": 0,
        "all_status": True,
    }


def test_quantum_baseline_families_include_stabilizer_and_tensor():
    families = {row.baseline_family for row in quantum_baseline_rows()}
    assert "stabilizer-tableau" in families
    assert "tensor-product" in families
    assert "classical-linear-algebra" in families
    assert "graph-topology" in families
    assert "classical-matrix-algebra" in families
    assert "classical-debugging" in families
    assert "classical-fourier-analysis" in families
    assert "classical-compiler-peephole" in families


def test_quantum_baseline_checklist_keeps_nonclaim_boundary():
    text = "\n".join(quantum_baseline_checklist())
    assert "each current finite Q-Veyra row" in text
    assert "zero stronger" in text
