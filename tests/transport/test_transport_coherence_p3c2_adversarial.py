"""Hostile-shape, transplant, partial-map, and separation attacks for P3-C2."""

from dataclasses import replace
import pytest
from src.core.transport_coherence import (
    GeneratedTransportCoherence,
    HigherCellStructureStatus,
    SetoidClassRow,
    TransportCoherenceError,
    TransportMapEntry,
    TransportResourceLimit,
    cofinal_boundary_reconciliation,
    edge_transport_map,
    generated_transport_coherence,
    generated_transport_filler,
    state_setoid_carrier,
    total_transport_doctrine,
    validate_transport_result,
)
from src.core.transport_coherence_counterpressure import ATTACK_IDS, required_transport_attacks
from src.core.transport_coherence_common import digest
from src.core.transport_coherence_examples import positive_example
from src.core.transport_coherence_formal import capture_theorem_source
from transport_coherence_fixture import exact_transport_package

pytestmark = pytest.mark.requires_lean


class Hostile:
    def __getattribute__(self, name):
        raise AssertionError(f"hostile touched {name}")

    def __eq__(self, other):
        raise AssertionError("hostile equality touched")


def test_all_seventeen_mandatory_attacks_pass():
    value = generated_transport_coherence(exact_transport_package())
    rows = required_transport_attacks(value)
    assert tuple(x.attack_id for x in rows) == ATTACK_IDS and len(rows) == 17
    assert all(x.passed for x in rows)


def test_hostile_result_rejected_before_replay_or_equality():
    with pytest.raises(TransportCoherenceError):
        validate_transport_result(exact_transport_package(max_values=1), Hostile())


def test_prior_result_and_p3t_shaped_partial_adapter_have_no_raw_lane():
    package = exact_transport_package()
    value = generated_transport_coherence(package)
    for alien in (value, {"domain": ("ready",), "partial_map": True}, lambda x: x):
        with pytest.raises(TransportCoherenceError):
            generated_transport_coherence(alien)


def test_foreign_edge_map_and_endpoint_commitment_transplants_fail():
    package = exact_transport_package()
    maps = package.doctrine.edge_maps
    with pytest.raises(TransportCoherenceError):
        total_transport_doctrine(
            package.system, "alien", package.doctrine.carriers, (replace(maps[0], edge_commitment="0" * 64), *maps[1:])
        )


def test_proper_domain_intersection_is_not_total_transport():
    package = exact_transport_package()
    edge = next(x for x in package.system.edges if x.edge_id == "xy")
    carriers = {x.state_id: x for x in package.doctrine.carriers}
    with pytest.raises(TransportCoherenceError):
        edge_transport_map(
            edge.edge_id, edge.edge_commitment, carriers["x"], carriers["y"], (TransportMapEntry("0", "0"),)
        )
    raw = next(row for row in package.doctrine.edge_maps if row.edge_id == "xy")
    entries = raw.entries[:1]
    forged_digest = digest(
        "veyra.p3c2.edge-map.v1",
        (
            ("edge", raw.edge_id.encode()),
            ("edge-commitment", raw.edge_commitment.encode()),
            ("source", raw.source_carrier_digest.encode()),
            ("target", raw.target_carrier_digest.encode()),
            ("entry-0", f"{entries[0].source_value_id}\0{entries[0].target_value_id}".encode()),
        ),
    )
    forged = replace(raw, entries=entries, map_digest=forged_digest)
    maps = tuple(forged if row.edge_id == raw.edge_id else row for row in package.doctrine.edge_maps)
    with pytest.raises(TransportCoherenceError):
        total_transport_doctrine(package.system, "forged-partial", package.doctrine.carriers, maps)


def test_setoid_nonrespect_is_rejected_at_map_construction():
    package = exact_transport_package()
    carriers = {x.state_id: x for x in package.doctrine.carriers}
    edge = next(x for x in package.system.edges if x.edge_id == "xy")
    collapsed = state_setoid_carrier(
        "x",
        carriers["x"].state_commitment,
        carriers["x"].values,
        (SetoidClassRow("0", "same"), SetoidClassRow("1", "same")),
    )
    with pytest.raises(TransportCoherenceError):
        edge_transport_map(
            edge.edge_id,
            edge.edge_commitment,
            collapsed,
            carriers["y"],
            (TransportMapEntry("0", "0"), TransportMapEntry("1", "1")),
        )


def test_c22_does_not_manufacture_an_admitted_higher_cell_structure():
    value = generated_transport_coherence(exact_transport_package())
    assert value.higher_cell_structure is HigherCellStructureStatus.NOT_IMPLEMENTED
    assert "higher-cell-structure-coherence-not-implemented" in value.nonclaims
    assert not hasattr(value, "three_cell_universe")


def test_result_status_digest_and_nonclaims_mutations_fail_closed():
    package = exact_transport_package()
    value = generated_transport_coherence(package)
    mutants = (
        replace(value, status="established"),
        replace(value, result_digest="0" * 64),
        replace(value, nonclaims=value.nonclaims[:-1]),
    )
    for mutant in mutants:
        with pytest.raises(TransportCoherenceError):
            validate_transport_result(package, mutant)


def test_hard_first_policy_type_attack_is_sanitized():
    package = exact_transport_package()
    bad = replace(package.policy, max_values=True)
    with pytest.raises(TransportCoherenceError):
        generated_transport_coherence(replace(package, policy=bad))


def test_resource_refusal_stays_distinct_from_open_and_refuted():
    value = generated_transport_coherence(positive_example(max_map_entries=1).package)
    assert type(value) is TransportResourceLimit and not isinstance(value, GeneratedTransportCoherence)


def test_nested_hostile_payload_is_rejected_without_repr_or_equality_hook():
    package = exact_transport_package()
    carrier = package.doctrine.carriers[0]
    poisoned_value = replace(carrier.values[0], payload=Hostile())
    poisoned_carrier = replace(carrier, values=(poisoned_value, *carrier.values[1:]))
    poisoned_doctrine = replace(package.doctrine, carriers=(poisoned_carrier, *package.doctrine.carriers[1:]))
    with pytest.raises(TransportCoherenceError):
        generated_transport_coherence(replace(package, doctrine=poisoned_doctrine))


def test_negative_policy_and_hostile_result_fields_fail_sanitized():
    package = exact_transport_package()
    with pytest.raises(TransportCoherenceError):
        generated_transport_coherence(replace(package, policy=replace(package.policy, max_values=-1)))
    value = generated_transport_coherence(package)
    for mutant in (
        replace(value, assumption_ledger_digest=Hostile()),
        replace(value, finite_tlgc_scope=Hostile()),
    ):
        with pytest.raises(TransportCoherenceError):
            validate_transport_result(package, mutant)


def test_duplicate_carrier_and_hostile_cofinal_shape_are_rejected():
    package = exact_transport_package()
    with pytest.raises(TransportCoherenceError):
        total_transport_doctrine(
            package.system,
            "duplicate-carrier",
            (package.doctrine.carriers[0], *package.doctrine.carriers),
            package.doctrine.edge_maps,
        )
    filler = generated_transport_filler(package, "x", ("xy",), ("xz",), "w", ("yw",), ("zw",))
    with pytest.raises(TransportCoherenceError):
        cofinal_boundary_reconciliation(package, filler, filler, Hostile(), (), ())


def test_hostile_formal_source_field_is_rejected_before_equality():
    source = exact_transport_package().theorem_source
    with pytest.raises(TransportCoherenceError):
        capture_theorem_source(replace(source, version=Hostile()))


def test_huge_result_tuple_is_rejected_before_hostile_children():
    package = exact_transport_package()
    value = generated_transport_coherence(package)
    rows = (Hostile(),) * 16385
    mutant = replace(value, global_fillers=rows, global_boundary_count=len(rows))
    with pytest.raises(TransportCoherenceError):
        validate_transport_result(package, mutant)


def test_exact_shape_bypasses_poisoned_dict_callbacks():
    from dataclasses import dataclass
    from src.core.transport_coherence_common import exact_shape

    class BombDict(dict):
        def __iter__(self):
            raise AssertionError("BombDict iterator called")

        def keys(self):
            raise AssertionError("BombDict keys called")

    @dataclass
    class Probe:
        value: int

        def __getattribute__(self, name):
            if name == "__dict__":
                return BombDict(value=1)
            return object.__getattribute__(self, name)

    exact_shape(Probe(1), Probe, "probe")


def test_semantic_work_refusal_happens_before_filler_search(monkeypatch):
    from src.core import transport_coherence_runtime as runtime

    established = generated_transport_coherence(positive_example().package)
    package = positive_example(max_semantic_work=established.semantic_work - 1).package

    def bomb(*args, **kwargs):
        raise AssertionError("semantic search ran after refusal")

    monkeypatch.setattr(runtime, "derive_indexed_global_fillers", bomb)
    value = generated_transport_coherence(package)
    assert type(value) is TransportResourceLimit


def test_global_search_snapshots_sources_once_not_inside_apply_loops(monkeypatch):
    from src.core import transport_coherence_index as index_module
    from src.core.transport_coherence_paths import derive_global_fillers

    package = exact_transport_package()
    calls = {"system": 0, "doctrine": 0}
    real_system = index_module.snapshot_ranked_system
    real_doctrine = index_module.snapshot_transport_doctrine

    def system(raw):
        calls["system"] += 1
        return real_system(raw)

    def doctrine(system_value, raw):
        calls["doctrine"] += 1
        return real_doctrine(system_value, raw)

    monkeypatch.setattr(index_module, "snapshot_ranked_system", system)
    monkeypatch.setattr(index_module, "snapshot_transport_doctrine", doctrine)
    assert len(derive_global_fillers(package.system, package.doctrine, 16384)) == 72
    assert calls == {"system": 1, "doctrine": 1}


def test_huge_nested_path_is_rejected_before_hostile_items():
    package = exact_transport_package()
    value = generated_transport_coherence(package)
    filler = value.global_fillers[0]
    poison = replace(filler, left_boundary=(Hostile(),) * 129)
    mutant = replace(value, global_fillers=(poison,), global_boundary_count=1)
    with pytest.raises(TransportCoherenceError):
        validate_transport_result(package, mutant)
