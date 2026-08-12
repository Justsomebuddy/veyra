"""Independent Python/Sage oracle for the bounded G4 gluing bridge."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, product
import logging

logger = logging.getLogger(__name__)

Pair = tuple[int, int]
Partition = tuple[tuple[int, ...], ...]
Cover = tuple[tuple[int, ...], ...]

EXPECTED_ROWS = {
    1: (1, 1, 1, 1, 1, ((1, 1),), 1),
    2: (5, 9, 9, 9, 8, ((1, 8), (2, 1)), 10),
    3: (109, 1265, 505, 481, 432, ((0, 784), (1, 432), (2, 36), (3, 12), (5, 1)), 545),
}


@dataclass(frozen=True, slots=True)
class G4ExhaustiveRow:
    """One JSON-ready exact enumeration row for a universe size."""

    nodes: int
    cover_shapes: int
    assignments: int
    matching_families: int
    gluable: int
    unique: int
    gluing_histogram: tuple[tuple[int, int], ...]
    global_witnesses: int
    classification_passed: bool

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready row without changing its mathematical content."""
        logger.debug("G4ExhaustiveRow.as_dict entry nodes=%d", self.nodes)
        result: dict[str, object] = {
            "nodes": self.nodes,
            "cover_shapes": self.cover_shapes,
            "assignments": self.assignments,
            "matching_families": self.matching_families,
            "gluable": self.gluable,
            "unique": self.unique,
            "gluing_histogram": dict(self.gluing_histogram),
            "global_witnesses": self.global_witnesses,
            "classification_passed": self.classification_passed,
        }
        logger.debug("G4ExhaustiveRow.as_dict exit")
        return result


def python_set_partitions(nodes: tuple[int, ...]) -> tuple[Partition, ...]:
    """Enumerate canonical set partitions by restricted-growth insertion."""
    logger.debug("python_set_partitions entry nodes=%r", nodes)
    if type(nodes) is not tuple or not nodes or len(nodes) > 8 or len(set(nodes)) != len(nodes):
        logger.error("python_set_partitions invalid nodes")
        raise ValueError("invalid-g4-oracle-nodes")
    partitions: list[list[list[int]]] = [[[nodes[0]]]]
    for node in nodes[1:]:
        next_rows: list[list[list[int]]] = []
        for partition in partitions:
            for index in range(len(partition)):
                amended = [block.copy() for block in partition]
                amended[index].append(node)
                next_rows.append(amended)
            next_rows.append([block.copy() for block in partition] + [[node]])
        partitions = next_rows
    result = tuple(tuple(tuple(block) for block in partition) for partition in partitions)
    logger.debug("python_set_partitions exit count=%d", len(result))
    return result


def sage_set_partitions(nodes: tuple[int, ...]) -> tuple[Partition, ...]:
    """Enumerate the same partitions through real SageMath's SetPartitions."""
    logger.debug("sage_set_partitions entry nodes=%r", nodes)
    try:
        from sage.all import SetPartitions  # type: ignore[import-not-found]
    except ImportError as exc:
        logger.error("sage_set_partitions real Sage unavailable")
        raise RuntimeError("real-sage-required-for-g4-oracle") from exc
    result = tuple(
        sorted(
            (_canonical_partition(tuple(tuple(int(node) for node in block) for block in partition)) for partition in SetPartitions(nodes)),
            key=repr,
        )
    )
    logger.debug("sage_set_partitions exit count=%d", len(result))
    return result


def exhaustive_g4_row(nodes: int, *, crosscheck_sage: bool = False) -> G4ExhaustiveRow:
    """Exhaust distinct-carrier covers, local partitions, and global gluings."""
    logger.debug("exhaustive_g4_row entry nodes=%r sage=%s", nodes, crosscheck_sage)
    if type(nodes) is not int or not 1 <= nodes <= 3:
        logger.error("exhaustive_g4_row bound rejected")
        raise ValueError("g4-oracle-nodes-must-be-1-through-3")
    universe = tuple(range(nodes))
    partitions = {patch: python_set_partitions(patch) for patch in _nonempty_subsets(universe)}
    if crosscheck_sage:
        for patch, python_rows in partitions.items():
            if set(python_rows) != set(sage_set_partitions(patch)):
                logger.error("exhaustive_g4_row Sage partition drift patch=%r", patch)
                raise RuntimeError("g4-oracle-sage-partition-drift")
    global_partitions = python_set_partitions(universe)
    global_relations = {_relation(partition) for partition in global_partitions}
    histogram: dict[int, int] = {}
    covers = _cover_shapes(universe)
    assignments = matching = gluable = unique = witnesses = 0
    classification_passed = True
    for cover in covers:
        for local_partitions in product(*(partitions[patch] for patch in cover)):
            assignments += 1
            local_relations = tuple(_relation(partition) for partition in local_partitions)
            is_matching = _matching_family(cover, local_relations)
            matching += int(is_matching)
            exact = {
                relation
                for relation in global_relations
                if _exact_restrictions(relation, cover, local_relations)
            }
            count = len(exact)
            histogram[count] = histogram.get(count, 0) + 1
            gluable += int(count > 0)
            unique += int(count == 1)
            witnesses += count
            criterion = _generated_criterion(universe, cover, local_relations)
            classified = _quotient_classification(universe, cover, local_relations, criterion)
            classification_passed = classification_passed and (bool(exact) == criterion[0]) and (classified == exact)
            classification_passed = classification_passed and ((count == 1) == (criterion[0] and criterion[2]))
    row = G4ExhaustiveRow(
        nodes,
        len(covers),
        assignments,
        matching,
        gluable,
        unique,
        tuple(sorted(histogram.items())),
        witnesses,
        classification_passed,
    )
    expected = EXPECTED_ROWS[nodes]
    observed = (
        row.cover_shapes,
        row.assignments,
        row.matching_families,
        row.gluable,
        row.unique,
        row.gluing_histogram,
        row.global_witnesses,
    )
    if observed != expected:
        logger.error("exhaustive_g4_row pinned count drift observed=%r", observed)
        raise RuntimeError("g4-oracle-pinned-count-drift")
    logger.debug("exhaustive_g4_row exit assignments=%d", assignments)
    return row


class VeyraObserverPatchGluingLab:
    """Small JSON-ready facade over the independent bounded oracle."""

    def exhaustive_summary(self, max_nodes: int = 3, *, require_sage: bool = False) -> dict[str, object]:
        """Return pinned rows and totals, optionally cross-checked by real Sage."""
        logger.debug("VeyraObserverPatchGluingLab.exhaustive_summary entry max=%r sage=%s", max_nodes, require_sage)
        if type(max_nodes) is not int or not 1 <= max_nodes <= 3:
            logger.error("exhaustive_summary invalid bound")
            raise ValueError("g4-oracle-max-nodes-must-be-1-through-3")
        rows = tuple(exhaustive_g4_row(nodes, crosscheck_sage=require_sage) for nodes in range(1, max_nodes + 1))
        result: dict[str, object] = {
            "backend": "python+real-sage" if require_sage else "python",
            "rows": tuple(row.as_dict() for row in rows),
            "covers": sum(row.cover_shapes for row in rows),
            "assignments": sum(row.assignments for row in rows),
            "matching_families": sum(row.matching_families for row in rows),
            "gluable": sum(row.gluable for row in rows),
            "unique": sum(row.unique for row in rows),
            "global_witnesses": sum(row.global_witnesses for row in rows),
            "classification_passed": all(row.classification_passed for row in rows),
            "scope": "distinct nonempty patch carriers covering U; exhaustive through n<=3",
        }
        logger.debug("VeyraObserverPatchGluingLab.exhaustive_summary exit assignments=%d", result["assignments"])
        return result


def _nonempty_subsets(universe: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    """Return every nonempty subset in bitmask order."""
    logger.debug("_nonempty_subsets entry nodes=%d", len(universe))
    result = tuple(tuple(node for index, node in enumerate(universe) if mask & (1 << index)) for mask in range(1, 1 << len(universe)))
    logger.debug("_nonempty_subsets exit count=%d", len(result))
    return result


def _cover_shapes(universe: tuple[int, ...]) -> tuple[Cover, ...]:
    """Return unordered distinct-carrier covers with exact union."""
    logger.debug("_cover_shapes entry nodes=%d", len(universe))
    subsets = _nonempty_subsets(universe)
    target = set(universe)
    result = tuple(tuple(subsets[index] for index in range(len(subsets)) if mask & (1 << index)) for mask in range(1, 1 << len(subsets)) if set().union(*(set(subsets[index]) for index in range(len(subsets)) if mask & (1 << index))) == target)
    logger.debug("_cover_shapes exit count=%d", len(result))
    return result


def _canonical_partition(partition: Partition) -> Partition:
    """Canonicalize block contents and first-node block order."""
    logger.debug("_canonical_partition entry")
    result = tuple(sorted((tuple(sorted(block)) for block in partition), key=lambda block: block[0]))
    logger.debug("_canonical_partition exit blocks=%d", len(result))
    return result


def _relation(partition: Partition) -> frozenset[Pair]:
    """Return the canonical unordered-pair equivalence relation."""
    logger.debug("oracle _relation entry blocks=%d", len(partition))
    result = frozenset((min(left, right), max(left, right)) for block in partition for left in block for right in block)
    logger.debug("oracle _relation exit pairs=%d", len(result))
    return result


def _exact_restrictions(relation: frozenset[Pair], cover: Cover, locals_: tuple[frozenset[Pair], ...]) -> bool:
    """Check equality with every local relation after restriction."""
    logger.debug("_exact_restrictions entry")
    result = all(frozenset(pair for pair in relation if pair[0] in patch and pair[1] in patch) == local for patch, local in zip(cover, locals_, strict=True))
    logger.debug("_exact_restrictions exit result=%s", result)
    return result


def _matching_family(cover: Cover, locals_: tuple[frozenset[Pair], ...]) -> bool:
    """Check equality on every pairwise overlap."""
    logger.debug("_matching_family entry")
    result = True
    for left, right in combinations(range(len(cover)), 2):
        overlap = set(cover[left]) & set(cover[right])
        allowed = {(min(x, y), max(x, y)) for x in overlap for y in overlap}
        result = result and (locals_[left] & allowed == locals_[right] & allowed)
    logger.debug("_matching_family exit result=%s", result)
    return result


def _generated_criterion(universe: tuple[int, ...], cover: Cover, locals_: tuple[frozenset[Pair], ...]) -> tuple[bool, Partition, bool]:
    """Return exact existence, E* classes, and conditional conflict completeness."""
    logger.debug("_generated_criterion entry")
    adjacency = {node: {node} for node in universe}
    for relation in locals_:
        for left, right in relation:
            adjacency[left].add(right)
            adjacency[right].add(left)
    classes: list[tuple[int, ...]] = []
    remaining = set(universe)
    for node in universe:
        if node not in remaining:
            continue
        seen: set[int] = set()
        stack = [node]
        while stack:
            current = stack.pop()
            if current not in seen:
                seen.add(current)
                stack.extend(adjacency[current] - seen)
        block = tuple(item for item in universe if item in seen)
        classes.append(block)
        remaining.difference_update(block)
    generated = _relation(tuple(classes))
    exists = _exact_restrictions(generated, cover, locals_)
    index = {node: class_index for class_index, block in enumerate(classes) for node in block}
    conflicts = {(min(index[left], index[right]), max(index[left], index[right])) for patch in cover for left, right in combinations(patch, 2) if index[left] != index[right]}
    complete = len(conflicts) == len(classes) * (len(classes) - 1) // 2
    result = (exists, tuple(classes), complete)
    logger.debug("_generated_criterion exit exists=%s complete=%s", exists, complete)
    return result


def _quotient_classification(universe: tuple[int, ...], cover: Cover, locals_: tuple[frozenset[Pair], ...], criterion: tuple[bool, Partition, bool]) -> set[frozenset[Pair]]:
    """Independently classify exact relations, hard-gated on exact existence."""
    logger.debug("_quotient_classification entry")
    exists, classes, _ = criterion
    if not exists:
        logger.debug("_quotient_classification exit gated")
        return set()
    class_index = {node: index for index, block in enumerate(classes) for node in block}
    conflicts = {(min(class_index[left], class_index[right]), max(class_index[left], class_index[right])) for patch in cover for left, right in combinations(patch, 2) if class_index[left] != class_index[right]}
    output: set[frozenset[Pair]] = set()
    for partition in python_set_partitions(tuple(range(len(classes)))):
        if any((min(left, right), max(left, right)) in conflicts for block in partition for left, right in combinations(block, 2)):
            continue
        node_block = {node: block_index for block_index, quotient_block in enumerate(partition) for class_id in quotient_block for node in classes[class_id]}
        relation = frozenset((min(left, right), max(left, right)) for left in universe for right in universe if node_block[left] == node_block[right])
        if _exact_restrictions(relation, cover, locals_):
            output.add(relation)
    logger.debug("_quotient_classification exit count=%d", len(output))
    return output
