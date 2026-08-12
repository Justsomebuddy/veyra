"""Conflict-graph classification of bounded finite G4 exact gluings."""

from __future__ import annotations

from itertools import combinations
import logging

from .observer_patch_atlas import (
    Pair,
    exact_gluing_criterion,
    generated_echo_closure,
    local_echo_relation,
    local_observer_section,
    observer_patch,
    observer_patch_atlas,
    pairwise_overlap_rows,
)
from .observer_patch_gluing_types import (
    ConflictEdge,
    DisjointSingletonNonuniqueness,
    ExactGluingClassification,
    QuotientConflictGraph,
    QuotientPartition,
)
from .observer_patch_validation import (
    LocalObserverSection,
    ObserverPatch,
    ObserverPatchAtlas,
    validate_atlas_shape,
    validate_section_shape,
)

logger = logging.getLogger(__name__)

G4_CONFLICT_GRAPH_SCHEMA = "veyra.g4.quotient-conflict-graph.v1"
G4_GLUING_CLASSIFICATION_SCHEMA = "veyra.g4.exact-gluing-classification.v1"
MAX_G4_CLASSIFICATION_NODES = 8
MAX_G4_CLASSIFICATION_PATCHES = 64
MAX_G4_CLASSIFICATION_PARTITIONS = 4_140
MAX_G4_IDENTIFIER_BYTES = 128
MAX_G4_CONFLICT_EDGES = (
    MAX_G4_CLASSIFICATION_NODES * (MAX_G4_CLASSIFICATION_NODES - 1) // 2
)


def quotient_conflict_graph(
    atlas: ObserverPatchAtlas,
    sections: tuple[LocalObserverSection, ...],
) -> QuotientConflictGraph:
    """Build the graph whose edges record within-patch quotient conflicts."""
    logger.debug("quotient_conflict_graph entry")
    atlas, sections = _classification_inputs(atlas, sections)
    generated = generated_echo_closure(atlas, sections)
    classes = _relation_classes(atlas.universe, generated)
    class_index = {
        node: index for index, block in enumerate(classes) for node in block
    }
    edges: set[ConflictEdge] = set()
    for patch in atlas.patches:
        indices = sorted({class_index[node] for node in patch.nodes})
        edges.update(combinations(indices, 2))
    frozen_edges = tuple(sorted(edges))
    class_count = len(classes)
    complete = len(frozen_edges) == class_count * (class_count - 1) // 2
    result = QuotientConflictGraph(
        G4_CONFLICT_GRAPH_SCHEMA, classes, frozen_edges, complete
    )
    logger.debug(
        "quotient_conflict_graph exit classes=%d edges=%d complete=%s",
        class_count,
        len(frozen_edges),
        complete,
    )
    return result


def conflict_safe_quotient_partitions(
    graph: QuotientConflictGraph,
) -> tuple[QuotientPartition, ...]:
    """Enumerate canonical quotient partitions with conflict-independent blocks."""
    logger.debug("conflict_safe_quotient_partitions entry")
    graph = _validate_conflict_graph(graph)
    conflicts = set(graph.edges)
    output: list[QuotientPartition] = []
    for partition in _set_partitions(len(graph.quotient_classes)):
        if all(
            _edge(left, right) not in conflicts
            for block in partition
            for left, right in combinations(block, 2)
        ):
            output.append(partition)
    if len(output) > MAX_G4_CLASSIFICATION_PARTITIONS:
        logger.error("conflict_safe_quotient_partitions output limit exceeded")
        raise ValueError("g4-classification-partition-limit")
    result = tuple(output)
    logger.debug("conflict_safe_quotient_partitions exit count=%d", len(result))
    return result


def exact_gluing_relation_from_quotient_partition(
    graph: QuotientConflictGraph,
    partition: QuotientPartition,
) -> frozenset[Pair]:
    """Lift one canonical conflict-safe quotient partition to the nod universe."""
    logger.debug("exact_gluing_relation_from_quotient_partition entry")
    graph = _validate_conflict_graph(graph)
    partition = _validate_quotient_partition(
        partition, len(graph.quotient_classes)
    )
    conflicts = set(graph.edges)
    if any(
        _edge(left, right) in conflicts
        for block in partition
        for left, right in combinations(block, 2)
    ):
        logger.error("quotient partition merges a conflict edge")
        raise ValueError("g4-quotient-partition-not-conflict-safe")
    quotient_block = {
        class_index: block_index
        for block_index, block in enumerate(partition)
        for class_index in block
    }
    node_block = {
        node: quotient_block[class_index]
        for class_index, quotient_class in enumerate(graph.quotient_classes)
        for node in quotient_class
    }
    nodes = tuple(node for block in graph.quotient_classes for node in block)
    result = frozenset(
        _pair(left, right)
        for left in nodes
        for right in nodes
        if node_block[left] == node_block[right]
    )
    logger.debug(
        "exact_gluing_relation_from_quotient_partition exit pairs=%d", len(result)
    )
    return result


def classify_exact_gluings(
    atlas: ObserverPatchAtlas,
    sections: tuple[LocalObserverSection, ...],
) -> ExactGluingClassification:
    """Classify exact gluings and independently audit the finite bijection."""
    logger.debug("classify_exact_gluings entry")
    atlas, sections = _classification_inputs(atlas, sections)
    matching_family = all(
        row.compatible for row in pairwise_overlap_rows(atlas, sections)
    )
    criterion = exact_gluing_criterion(atlas, sections)
    generated = generated_echo_closure(atlas, sections)
    graph = quotient_conflict_graph(atlas, sections)
    safe = (
        conflict_safe_quotient_partitions(graph)
        if criterion.exact_gluing_exists
        else ()
    )
    lifted = {
        exact_gluing_relation_from_quotient_partition(graph, partition)
        for partition in safe
    }
    direct = _direct_exact_gluing_relations(atlas, sections)
    classification_holds = lifted == direct
    unique = len(direct) == 1
    uniqueness_iff = unique == (
        criterion.exact_gluing_exists and graph.complete
    )
    result = ExactGluingClassification(
        G4_GLUING_CLASSIFICATION_SCHEMA,
        matching_family,
        criterion,
        generated,
        graph,
        safe,
        len(direct),
        classification_holds,
        unique,
        uniqueness_iff,
    )
    logger.debug(
        "classify_exact_gluings exit exists=%s count=%d classified=%s unique=%s",
        criterion.exact_gluing_exists,
        len(direct),
        classification_holds,
        unique,
    )
    return result


def disjoint_singleton_nonuniqueness() -> DisjointSingletonNonuniqueness:
    """Return the minimal exact-gluing existence-without-uniqueness witness."""
    logger.debug("disjoint_singleton_nonuniqueness entry")
    atlas = observer_patch_atlas(
        ("a", "b"),
        (observer_patch("A", ("a",)), observer_patch("B", ("b",))),
    )
    sections = (
        local_observer_section(atlas, "A", (("a",),)),
        local_observer_section(atlas, "B", (("b",),)),
    )
    classification = classify_exact_gluings(atlas, sections)
    identity = frozenset({("a", "a"), ("b", "b")})
    universal = frozenset({("a", "a"), ("a", "b"), ("b", "b")})
    exact = _relation_is_exact(atlas, sections, identity) and _relation_is_exact(
        atlas, sections, universal
    )
    result = DisjointSingletonNonuniqueness(
        classification, identity, universal, exact, identity != universal
    )
    logger.debug(
        "disjoint_singleton_nonuniqueness exit both_exact=%s distinct=%s",
        result.both_exact,
        result.distinct,
    )
    return result


def g4_gluing_classification_boundary() -> tuple[str, ...]:
    """Return the fixed interpretation boundary of the G4 continuation."""
    logger.debug("g4_gluing_classification_boundary entry")
    result = (
        "finite-declared-cover-and-local-partitions-only",
        "matching-family-language-requires-pairwise-compatibility",
        "existence-fragment-reduced-to-eqrel-amalgamation",
        "classification-assumes-exact-gluing-existence",
        "uniqueness-is-separate-from-existence",
        "no-general-sheaf-effective-descent-stack-or-topology-claim",
        "no-physical-contextuality-novelty-or-promotion-claim",
    )
    logger.debug("g4_gluing_classification_boundary exit count=%d", len(result))
    return result


def _classification_inputs(
    atlas: object, sections: object
) -> tuple[ObserverPatchAtlas, tuple[LocalObserverSection, ...]]:
    """Precharge and capture one bounded exact classification input."""
    logger.debug("_classification_inputs entry")
    if (
        type(atlas) is not ObserverPatchAtlas
        or type(atlas.universe) is not tuple
        or not 1 <= len(atlas.universe) <= MAX_G4_CLASSIFICATION_NODES
        or type(atlas.patches) is not tuple
        or not 1 <= len(atlas.patches) <= MAX_G4_CLASSIFICATION_PATCHES
    ):
        logger.error("_classification_inputs atlas resource limit")
        raise ValueError("g4-classification-atlas-resource-limit")
    if type(sections) is not tuple or len(sections) != len(atlas.patches):
        logger.error("_classification_inputs section cardinality mismatch")
        raise ValueError("g4-classification-section-cardinality")
    identifiers: list[object] = [*atlas.universe]
    for patch in atlas.patches:
        if type(patch) is not ObserverPatch:
            logger.error("_classification_inputs patch exact type rejected")
            raise ValueError("g4-classification-patch-must-be-exact")
        identifiers.append(patch.name)
        if type(patch.nodes) is not tuple or len(patch.nodes) > MAX_G4_CLASSIFICATION_NODES:
            logger.error("_classification_inputs patch node limit")
            raise ValueError("g4-classification-patch-resource-limit")
        identifiers.extend(patch.nodes)
    for section in sections:
        if type(section) is not LocalObserverSection:
            logger.error("_classification_inputs section exact type rejected")
            raise ValueError("g4-classification-section-must-be-exact")
        identifiers.append(section.patch_name)
        if type(section.blocks) is not tuple or len(section.blocks) > MAX_G4_CLASSIFICATION_NODES:
            logger.error("_classification_inputs section block limit")
            raise ValueError("g4-classification-section-resource-limit")
        total_nodes = 0
        for block in section.blocks:
            if type(block) is not tuple or len(block) > MAX_G4_CLASSIFICATION_NODES:
                logger.error("_classification_inputs section block resource limit")
                raise ValueError("g4-classification-section-resource-limit")
            total_nodes += len(block)
            identifiers.extend(block)
        if total_nodes > MAX_G4_CLASSIFICATION_NODES:
            logger.error("_classification_inputs section node limit")
            raise ValueError("g4-classification-section-resource-limit")
    try:
        identifiers_ok = all(
            type(value) is str
            and bool(value)
            and len(value.encode("utf-8")) <= MAX_G4_IDENTIFIER_BYTES
            for value in identifiers
        )
    except UnicodeError as exc:
        logger.error("_classification_inputs identifier encoding rejected error=%s", exc)
        raise ValueError("g4-classification-identifier-encoding") from exc
    if not identifiers_ok:
        logger.error("_classification_inputs identifier resource limit")
        raise ValueError("g4-classification-identifier-resource-limit")
    checked_atlas: ObserverPatchAtlas = validate_atlas_shape(atlas)
    captured = tuple(validate_section_shape(section) for section in sections)
    section_ids = tuple(section.patch_name for section in captured)
    if len(set(section_ids)) != len(section_ids):
        logger.error("_classification_inputs duplicate section")
        raise ValueError("g4-classification-duplicate-section")
    result = (checked_atlas, captured)
    logger.debug("_classification_inputs exit nodes=%d", len(checked_atlas.universe))
    return result


def _relation_classes(
    universe: tuple[str, ...], relation: frozenset[Pair]
) -> tuple[tuple[str, ...], ...]:
    """Return ordered equivalence classes using universe-first representatives."""
    logger.debug("_relation_classes entry nodes=%d", len(universe))
    remaining = set(universe)
    classes: list[tuple[str, ...]] = []
    for node in universe:
        if node not in remaining:
            continue
        block = tuple(item for item in universe if _pair(node, item) in relation)
        classes.append(block)
        remaining.difference_update(block)
    result = tuple(classes)
    logger.debug("_relation_classes exit classes=%d", len(result))
    return result


def _set_partitions(size: int) -> tuple[QuotientPartition, ...]:
    """Enumerate first-occurrence-canonical set partitions of range(size)."""
    logger.debug("_set_partitions entry size=%d", size)
    if type(size) is not int or not 1 <= size <= MAX_G4_CLASSIFICATION_NODES:
        logger.error("_set_partitions invalid size=%r", size)
        raise ValueError("g4-classification-partition-size")
    partitions: list[list[list[int]]] = [[[0]]]
    for item in range(1, size):
        next_partitions: list[list[list[int]]] = []
        for partition in partitions:
            for block_index in range(len(partition)):
                amended = [block.copy() for block in partition]
                amended[block_index].append(item)
                next_partitions.append(amended)
            next_partitions.append([block.copy() for block in partition] + [[item]])
        partitions = next_partitions
        if len(partitions) > MAX_G4_CLASSIFICATION_PARTITIONS:
            logger.error("_set_partitions Bell bound exceeded")
            raise ValueError("g4-classification-partition-limit")
    result = tuple(
        tuple(tuple(block) for block in partition) for partition in partitions
    )
    logger.debug("_set_partitions exit count=%d", len(result))
    return result


def _direct_exact_gluing_relations(
    atlas: ObserverPatchAtlas,
    sections: tuple[LocalObserverSection, ...],
) -> set[frozenset[Pair]]:
    """Independently enumerate all universe partitions and exact restrictions."""
    logger.debug("_direct_exact_gluing_relations entry")
    output: set[frozenset[Pair]] = set()
    for partition in _set_partitions(len(atlas.universe)):
        relation = frozenset(
            _pair(atlas.universe[left], atlas.universe[right])
            for block in partition
            for left in block
            for right in block
        )
        if _relation_is_exact(atlas, sections, relation):
            output.add(relation)
    logger.debug("_direct_exact_gluing_relations exit count=%d", len(output))
    return output


def _relation_is_exact(
    atlas: ObserverPatchAtlas,
    sections: tuple[LocalObserverSection, ...],
    relation: frozenset[Pair],
) -> bool:
    """Check exact restriction independently of the conflict construction."""
    logger.debug("_relation_is_exact entry pairs=%d", len(relation))
    section_map = {section.patch_name: section for section in sections}
    result = all(
        frozenset(
            pair
            for pair in relation
            if pair[0] in patch.nodes and pair[1] in patch.nodes
        )
        == local_echo_relation(section_map[patch.name])
        for patch in atlas.patches
    )
    logger.debug("_relation_is_exact exit result=%s", result)
    return result


def _validate_conflict_graph(value: object) -> QuotientConflictGraph:
    """Require one exact canonical bounded quotient conflict graph."""
    logger.debug("_validate_conflict_graph entry")
    if type(value) is not QuotientConflictGraph:
        logger.error("_validate_conflict_graph exact type rejected")
        raise ValueError("g4-conflict-graph-must-be-exact")
    classes = value.quotient_classes
    if (
        value.schema != G4_CONFLICT_GRAPH_SCHEMA
        or type(classes) is not tuple
        or not 1 <= len(classes) <= MAX_G4_CLASSIFICATION_NODES
        or any(
            type(block) is not tuple
            or not 1 <= len(block) <= MAX_G4_CLASSIFICATION_NODES
            for block in classes
        )
        or sum(len(block) for block in classes) > MAX_G4_CLASSIFICATION_NODES
        or any(type(node) is not str or not node for block in classes for node in block)
        or len({node for block in classes for node in block})
        != sum(len(block) for block in classes)
        or type(value.edges) is not tuple
        or len(value.edges) > MAX_G4_CONFLICT_EDGES
    ):
        logger.error("_validate_conflict_graph shape rejected")
        raise ValueError("invalid-g4-conflict-graph")
    identifiers = tuple(node for block in classes for node in block)
    try:
        identifiers_ok = all(
            len(node.encode("utf-8")) <= MAX_G4_IDENTIFIER_BYTES
            for node in identifiers
        )
    except UnicodeError as exc:
        logger.error("_validate_conflict_graph identifier encoding rejected error=%s", exc)
        raise ValueError("invalid-g4-conflict-graph-identifier") from exc
    if not identifiers_ok:
        logger.error("_validate_conflict_graph identifier resource limit")
        raise ValueError("invalid-g4-conflict-graph-identifier")
    if any(
        type(edge) is not tuple
        or len(edge) != 2
        or type(edge[0]) is not int
        or type(edge[1]) is not int
        or not 0 <= edge[0] < edge[1] < len(classes)
        for edge in value.edges
    ):
        logger.error("_validate_conflict_graph edge rejected")
        raise ValueError("invalid-g4-conflict-graph-edge")
    expected_edges = tuple(sorted(set(value.edges)))
    if expected_edges != value.edges:
        logger.error("_validate_conflict_graph edge canonicality rejected")
        raise ValueError("invalid-g4-conflict-graph-edge")
    complete = len(value.edges) == len(classes) * (len(classes) - 1) // 2
    if type(value.complete) is not bool or value.complete != complete:
        logger.error("_validate_conflict_graph completeness drift")
        raise ValueError("g4-conflict-graph-completeness-drift")
    logger.debug("_validate_conflict_graph exit classes=%d", len(classes))
    return value


def _validate_quotient_partition(
    value: object, class_count: int
) -> QuotientPartition:
    """Require one canonical exact partition of all quotient indices."""
    logger.debug("_validate_quotient_partition entry classes=%d", class_count)
    if (
        type(value) is not tuple
        or not 1 <= len(value) <= class_count
        or any(
            type(block) is not tuple or not 1 <= len(block) <= class_count
            for block in value
        )
        or sum(len(block) for block in value) > class_count
    ):
        logger.error("_validate_quotient_partition outer shape rejected")
        raise ValueError("invalid-g4-quotient-partition")
    flat: list[int] = []
    previous_first = -1
    for block in value:
        if (
            any(type(item) is not int for item in block)
            or tuple(sorted(block)) != block
            or block[0] <= previous_first
        ):
            logger.error("_validate_quotient_partition block rejected")
            raise ValueError("invalid-g4-quotient-partition")
        previous_first = block[0]
        flat.extend(block)
    if sorted(flat) != list(range(class_count)):
        logger.error("_validate_quotient_partition coverage rejected")
        raise ValueError("invalid-g4-quotient-partition-coverage")
    result = value
    logger.debug("_validate_quotient_partition exit blocks=%d", len(result))
    return result


def _edge(left: int, right: int) -> ConflictEdge:
    """Return one canonical unordered quotient edge."""
    logger.debug("_edge entry left=%d right=%d", left, right)
    result = (left, right) if left < right else (right, left)
    logger.debug("_edge exit edge=%r", result)
    return result


def _pair(left: str, right: str) -> Pair:
    """Return one canonical unordered nod pair."""
    logger.debug("classification _pair entry")
    result = (left, right) if left <= right else (right, left)
    logger.debug("classification _pair exit")
    return result
