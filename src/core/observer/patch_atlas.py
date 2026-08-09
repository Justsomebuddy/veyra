"""Finite observer-patch atlases, their canonical shapes, and gluing obstruction.

One concept end to end: the patch, atlas, and local-section values, the
fail-closed structural validation that admits them, and the exact gluing
criterion whose failure is witnessed by a triangle counterexample.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import logging

logger = logging.getLogger(__name__)

Pair = tuple[str, str]


@dataclass(frozen=True)
class ObserverPatch:
    """A named finite patch of observer-visible nods."""

    name: str
    nodes: tuple[str, ...]


@dataclass(frozen=True)
class ObserverPatchAtlas:
    """A finite universe covered by named observer patches."""

    universe: tuple[str, ...]
    patches: tuple[ObserverPatch, ...]


@dataclass(frozen=True)
class LocalObserverSection:
    """A partition, hence an echo-equivalence, on one patch."""

    patch_name: str
    blocks: tuple[tuple[str, ...], ...]


def validate_patch_shape(patch: object) -> ObserverPatch:
    """Return an exact canonical patch or fail closed."""
    logger.debug("validate_patch_shape entry type=%s", type(patch).__name__)
    valid = type(patch) is ObserverPatch
    if valid:
        valid = type(patch.name) is str and bool(patch.name)
        valid = valid and type(patch.nodes) is tuple and bool(patch.nodes)
        valid = valid and all(type(node) is str and bool(node) for node in patch.nodes)
        valid = valid and len(set(patch.nodes)) == len(patch.nodes)
    if not valid:
        logger.error("validate_patch_shape invalid patch=%r", patch)
        raise ValueError("patch requires an exact type, nonempty name, and unique nonempty string nods")
    logger.debug("validate_patch_shape exit name=%s nodes=%d", patch.name, len(patch.nodes))
    return patch


def validate_atlas_shape(atlas: object) -> ObserverPatchAtlas:
    """Return an exact canonical, nonempty, exact-cover atlas or fail closed."""
    logger.debug("validate_atlas_shape entry type=%s", type(atlas).__name__)
    valid = type(atlas) is ObserverPatchAtlas
    if valid:
        valid = type(atlas.universe) is tuple and bool(atlas.universe)
        valid = valid and all(type(node) is str and bool(node) for node in atlas.universe)
        valid = valid and len(set(atlas.universe)) == len(atlas.universe)
        valid = valid and type(atlas.patches) is tuple and bool(atlas.patches)
    if not valid:
        logger.error("validate_atlas_shape invalid shell atlas=%r", atlas)
        raise ValueError("atlas requires an exact type and unique nonempty string universe")
    patches = tuple(validate_patch_shape(patch) for patch in atlas.patches)
    names = tuple(patch.name for patch in patches)
    universe = set(atlas.universe)
    covered = {node for patch in patches for node in patch.nodes}
    valid_cover = len(set(names)) == len(names)
    valid_cover = valid_cover and all(set(patch.nodes) <= universe for patch in patches)
    valid_cover = valid_cover and covered == universe
    if not valid_cover:
        logger.error(
            "validate_atlas_shape invalid cover names=%r universe=%r covered=%r",
            names, atlas.universe, covered,
        )
        raise ValueError("atlas patches must be uniquely named and form an exact finite cover")
    logger.debug("validate_atlas_shape exit universe=%d patches=%d", len(atlas.universe), len(patches))
    return atlas


def validate_section_shape(section: object) -> LocalObserverSection:
    """Return an exact canonical standalone local partition or fail closed."""
    logger.debug("validate_section_shape entry type=%s", type(section).__name__)
    valid = type(section) is LocalObserverSection
    if valid:
        valid = type(section.patch_name) is str and bool(section.patch_name)
        valid = valid and type(section.blocks) is tuple and bool(section.blocks)
        valid = valid and all(type(block) is tuple and bool(block) for block in section.blocks)
    flat: tuple[object, ...] = ()
    if valid:
        flat = tuple(node for block in section.blocks for node in block)
        valid = all(type(node) is str and bool(node) for node in flat)
        valid = valid and len(set(flat)) == len(flat)
    if not valid:
        logger.error("validate_section_shape invalid section=%r", section)
        raise ValueError("local section requires exact nonempty partition blocks of unique string nods")
    logger.debug("validate_section_shape exit patch=%s nodes=%d", section.patch_name, len(flat))
    return section


@dataclass(frozen=True)
class PairwiseOverlapRow:
    """Agreement of two local equivalence relations on their overlap."""

    left_patch: str
    right_patch: str
    overlap: tuple[str, ...]
    compatible: bool


@dataclass(frozen=True)
class LocalContradiction:
    """A generated equality that one local section distinguishes."""

    patch_name: str
    left: str
    right: str


@dataclass(frozen=True)
class ExactGluingCriterion:
    """Finite exact-gluing existence and its constructive witness status."""

    obstruction_count: int
    no_local_contradiction: bool
    exact_gluing_exists: bool
    witness: str
    iff_holds: bool


@dataclass(frozen=True)
class TriangleCounterexample:
    """Three singleton overlaps that pass pairwise but fail global gluing."""

    atlas: ObserverPatchAtlas
    sections: tuple[LocalObserverSection, ...]
    overlaps: tuple[PairwiseOverlapRow, ...]
    generated_relation: frozenset[Pair]
    contradictions: tuple[LocalContradiction, ...]
    criterion: ExactGluingCriterion


def observer_patch(name: str, nodes: tuple[str, ...]) -> ObserverPatch:
    """Build a nonempty finite observer patch with unique nods."""
    logger.debug("observer_patch entry name=%s nodes=%r", name, nodes)
    result = validate_patch_shape(ObserverPatch(name, nodes))
    logger.debug("observer_patch exit patch=%r", result)
    return result


def observer_patch_atlas(
    universe: tuple[str, ...], patches: tuple[ObserverPatch, ...]
) -> ObserverPatchAtlas:
    """Build a finite atlas whose patches cover exactly the declared universe."""
    logger.debug("observer_patch_atlas entry universe=%r patches=%r", universe, patches)
    result = validate_atlas_shape(ObserverPatchAtlas(universe, patches))
    logger.debug("observer_patch_atlas exit patches=%d", len(result.patches))
    return result


def local_observer_section(
    atlas: ObserverPatchAtlas, patch_name: str, blocks: tuple[tuple[str, ...], ...]
) -> LocalObserverSection:
    """Build a local section from a partition of the named patch."""
    logger.debug("local_observer_section entry patch=%s blocks=%r", patch_name, blocks)
    patch = _patch_by_name(atlas, patch_name)
    result = validate_section_shape(LocalObserverSection(patch_name, blocks))
    flat = tuple(node for block in result.blocks for node in block)
    if set(flat) != set(patch.nodes):
        logger.error("local_observer_section invalid patch=%s blocks=%r", patch_name, blocks)
        raise ValueError("local section blocks must partition the patch exactly")
    logger.debug("local_observer_section exit patch=%s block_count=%d", patch_name, len(blocks))
    return result


def local_echo_relation(section: LocalObserverSection) -> frozenset[Pair]:
    """Return the equivalence relation induced by a section partition."""
    logger.debug("local_echo_relation entry type=%s", type(section).__name__)
    section = validate_section_shape(section)
    result = frozenset(_pair(left, right) for block in section.blocks for left in block for right in block)
    logger.debug("local_echo_relation exit patch=%s pairs=%d", section.patch_name, len(result))
    return result


def generated_echo_closure(
    atlas: ObserverPatchAtlas, sections: tuple[LocalObserverSection, ...]
) -> frozenset[Pair]:
    """Return E*: the equivalence closure generated by all local equalities."""
    logger.debug("generated_echo_closure entry sections_type=%s", type(sections).__name__)
    section_map = _validated_section_map(atlas, sections)
    generators = set().union(*(local_echo_relation(section_map[patch.name]) for patch in atlas.patches))
    result = _equivalence_closure(atlas.universe, generators)
    logger.debug("generated_echo_closure exit pairs=%d", len(result))
    return result


def pairwise_overlap_rows(
    atlas: ObserverPatchAtlas, sections: tuple[LocalObserverSection, ...]
) -> tuple[PairwiseOverlapRow, ...]:
    """Check equality of local-relation restrictions on every patch overlap."""
    logger.debug("pairwise_overlap_rows entry atlas_type=%s", type(atlas).__name__)
    section_map = _validated_section_map(atlas, sections)
    rows: list[PairwiseOverlapRow] = []
    for left, right in combinations(atlas.patches, 2):
        overlap = tuple(node for node in atlas.universe if node in left.nodes and node in right.nodes)
        allowed = {_pair(x, y) for x in overlap for y in overlap}
        left_relation = local_echo_relation(section_map[left.name]) & allowed
        right_relation = local_echo_relation(section_map[right.name]) & allowed
        rows.append(PairwiseOverlapRow(left.name, right.name, overlap, left_relation == right_relation))
    result = tuple(rows)
    logger.debug("pairwise_overlap_rows exit rows=%d compatible=%d", len(result), sum(row.compatible for row in result))
    return result


def local_contradictions(
    atlas: ObserverPatchAtlas, sections: tuple[LocalObserverSection, ...]
) -> tuple[LocalContradiction, ...]:
    """Return every within-patch equality added by E* beyond its local section."""
    logger.debug("local_contradictions entry sections_type=%s", type(sections).__name__)
    section_map = _validated_section_map(atlas, sections)
    generated = generated_echo_closure(atlas, sections)
    rows: list[LocalContradiction] = []
    for patch in atlas.patches:
        local = local_echo_relation(section_map[patch.name])
        for left, right in combinations(patch.nodes, 2):
            pair = _pair(left, right)
            if pair in generated and pair not in local:
                rows.append(LocalContradiction(patch.name, left, right))
    result = tuple(rows)
    logger.debug("local_contradictions exit count=%d", len(result))
    return result


def exact_gluing_relation(
    atlas: ObserverPatchAtlas, sections: tuple[LocalObserverSection, ...]
) -> frozenset[Pair] | None:
    """Return the constructive E* global relation exactly when gluing exists."""
    logger.debug("exact_gluing_relation entry sections_type=%s", type(sections).__name__)
    contradictions = local_contradictions(atlas, sections)
    result = None if contradictions else generated_echo_closure(atlas, sections)
    logger.debug("exact_gluing_relation exit exists=%s", result is not None)
    return result


def exact_gluing_criterion(
    atlas: ObserverPatchAtlas, sections: tuple[LocalObserverSection, ...]
) -> ExactGluingCriterion:
    """Evaluate the finite theorem: exact gluing exists iff obstruction is empty."""
    logger.debug("exact_gluing_criterion entry sections_type=%s", type(sections).__name__)
    contradictions = local_contradictions(atlas, sections)
    no_contradiction = not contradictions
    gluing_exists = exact_gluing_relation(atlas, sections) is not None
    result = ExactGluingCriterion(
        len(contradictions), no_contradiction, gluing_exists,
        "generated-echo-closure" if gluing_exists else "blocked", no_contradiction == gluing_exists,
    )
    logger.debug("exact_gluing_criterion exit result=%r", result)
    return result


def triangle_counterexample() -> TriangleCounterexample:
    """Return AB~ and BC~ with CA distinguished: pairwise pass, global fail."""
    logger.debug("triangle_counterexample entry")
    patches = (
        observer_patch("AB", ("a", "b")), observer_patch("BC", ("b", "c")),
        observer_patch("CA", ("c", "a")),
    )
    atlas = observer_patch_atlas(("a", "b", "c"), patches)
    sections = (
        local_observer_section(atlas, "AB", (("a", "b"),)),
        local_observer_section(atlas, "BC", (("b", "c"),)),
        local_observer_section(atlas, "CA", (("c",), ("a",))),
    )
    result = TriangleCounterexample(
        atlas, sections, pairwise_overlap_rows(atlas, sections), generated_echo_closure(atlas, sections),
        local_contradictions(atlas, sections), exact_gluing_criterion(atlas, sections),
    )
    logger.debug("triangle_counterexample exit contradictions=%d", len(result.contradictions))
    return result


def _validated_section_map(
    atlas: ObserverPatchAtlas, sections: tuple[LocalObserverSection, ...]
) -> dict[str, LocalObserverSection]:
    logger.debug("_validated_section_map entry sections_type=%s", type(sections).__name__)
    atlas = validate_atlas_shape(atlas)
    if type(sections) is not tuple:
        logger.error("_validated_section_map noncanonical sections=%r", sections)
        raise ValueError("atlas requires an exact tuple with one local section per patch")
    checked = tuple(validate_section_shape(section) for section in sections)
    if len(checked) != len(atlas.patches) or len({section.patch_name for section in checked}) != len(checked):
        logger.error("_validated_section_map duplicate/missing sections")
        raise ValueError("atlas requires exactly one local section per patch")
    result: dict[str, LocalObserverSection] = {}
    for section in checked:
        result[section.patch_name] = local_observer_section(atlas, section.patch_name, section.blocks)
    if set(result) != {patch.name for patch in atlas.patches}:
        logger.error("_validated_section_map patch names mismatch names=%r", tuple(result))
        raise ValueError("atlas requires exactly one local section per patch")
    logger.debug("_validated_section_map exit sections=%d", len(result))
    return result


def _patch_by_name(atlas: ObserverPatchAtlas, name: str) -> ObserverPatch:
    logger.debug("_patch_by_name entry name=%s", name)
    atlas = validate_atlas_shape(atlas)
    for patch in atlas.patches:
        if patch.name == name:
            logger.debug("_patch_by_name exit found=%s", name)
            return patch
    logger.error("_patch_by_name unknown name=%s", name)
    raise ValueError(f"unknown patch: {name}")


def _equivalence_closure(nodes: tuple[str, ...], pairs: set[Pair]) -> frozenset[Pair]:
    logger.debug("_equivalence_closure entry nodes=%d generators=%d", len(nodes), len(pairs))
    adjacency = {node: {node} for node in nodes}
    for left, right in pairs:
        adjacency[left].add(right)
        adjacency[right].add(left)
    result: set[Pair] = set()
    for start in nodes:
        seen: set[str] = set()
        stack = [start]
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(adjacency[current] - seen)
        result.update(_pair(start, end) for end in seen)
    frozen = frozenset(result)
    logger.debug("_equivalence_closure exit pairs=%d", len(frozen))
    return frozen


def _pair(left: str, right: str) -> Pair:
    logger.debug("_pair entry left=%s right=%s", left, right)
    result = (left, right) if left <= right else (right, left)
    logger.debug("_pair exit pair=%r", result)
    return result
