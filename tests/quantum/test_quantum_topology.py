from src.core.quantum_topology import (
    braid_shadow,
    loop_action,
    qbraid_order_rows,
    qtopo_echo,
    qtopo_echo_rows,
    qtopo_logical_rows,
    qtopo_obstruction_rows,
    quantum_topology_summary,
    topo_signature,
    topo_shape,
    topo_deformed_shape,
    topo_broken_shape,
    vtopo_qubit,
)


def test_local_deformation_preserves_topological_signature():
    assert topo_signature(topo_shape()) == topo_signature(topo_deformed_shape())
    rows = qtopo_echo_rows()
    assert len(rows) == 3
    assert all(row.status == "ready" for row in rows)


def test_topology_break_is_obstruction():
    assert topo_signature(topo_shape()) != topo_signature(topo_broken_shape())
    rows = qtopo_obstruction_rows()
    assert len(rows) == 1
    assert rows[0].status == "ready"
    assert rows[0].obstruction == "topology-echo-break"


def test_contractible_and_noncontractible_loop_logical_shadows():
    q0 = vtopo_qubit(0)
    assert loop_action(q0, "contractible").logical == 0
    assert loop_action(q0, "noncontractible").logical == 1
    rows = {row.loop: row for row in qtopo_logical_rows()}
    assert rows["contractible"].logical_echo is True
    assert rows["noncontractible"].topo_echo is True
    assert rows["noncontractible"].logical_echo is False


def test_same_topology_can_hide_logical_difference():
    q0 = vtopo_qubit(0)
    q1 = loop_action(q0, "noncontractible")
    assert qtopo_echo(q0, q1) is True
    assert q0.logical != q1.logical


def test_braid_order_noncommutation_row():
    assert braid_shadow(("s1", "s2")) != braid_shadow(("s2", "s1"))
    row = qbraid_order_rows()[0]
    assert row.status == "ready"
    assert row.echo is False


def test_quantum_topology_summary_blocks_overclaim():
    assert quantum_topology_summary() == {
        "topo_qubits": 2,
        "deformation_echoes": 3,
        "logical_rows": 2,
        "obstructions": 1,
        "braid_rows": 1,
        "overclaims": 0,
    }
