"""Exact P3-C1 pure-relation positive fixture."""

from src.core.generated_confluence import (
    StateRank,
    continuation_edge,
    continuation_state,
    generated_local_peaks,
    generated_reachable,
    local_join_cell,
    ranked_continuation_system,
)


def positive_package():
    states = tuple(continuation_state(name, "node", name.encode()) for name in ("v", "w", "x", "y", "z"))
    edges = (
        continuation_edge("wv", "w", "v", "step", b"wv"),
        continuation_edge("xy", "x", "y", "step", b"xy"),
        continuation_edge("xz", "x", "z", "step", b"xz"),
        continuation_edge("yw", "y", "w", "step", b"yw"),
        continuation_edge("zw", "z", "w", "step", b"zw"),
    )
    ranks = tuple(
        StateRank(name, rank)
        for name, rank in (
            ("v", 0),
            ("w", 1),
            ("x", 3),
            ("y", 2),
            ("z", 2),
        )
    )
    system = ranked_continuation_system(
        "p3c1-doctrine",
        "fixture-system",
        "v1",
        states,
        edges,
        ("x",),
        ranks,
    )
    reachable, _ = generated_reachable(system)
    peaks = generated_local_peaks(system)
    path_map = {("xy", "xz"): (("yw",), ("zw",)), ("xz", "xy"): (("zw",), ("yw",))}
    cells = tuple(
        local_join_cell(
            system,
            peak.peak_id,
            *path_map[(peak.left_edge_id, peak.right_edge_id)],
            "w",
        )
        for peak in peaks
    )
    return system, cells
