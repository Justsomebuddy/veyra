"""Diagram, infinity, and nonclaim boundaries for executable P0."""

from __future__ import annotations

import logging

from ..construction.infinity_prefix import (
    PrefixStage, PrefixTowerWindow, prefix_coherence_report,
    prefix_tower_window, snapshot_prefix_stage, snapshot_prefix_window,
)
from ..observer.patch_atlas import (
    LocalObserverSection,
    ObserverPatch,
    ObserverPatchAtlas,
    exact_gluing_criterion,
    pairwise_overlap_rows,
)
from .types import (
    DiagramCoherenceJudgment,
    InfinityJudgment,
    InfinityLevel,
    SilenceBoundaryJudgment,
    SilenceModality,
)
from .validation import (
    PositiveOntologyValidationError,
    snapshot_identifier,
)

logger = logging.getLogger(__name__)


def diagram_coherence_judgment(
    atlas: ObserverPatchAtlas, sections: tuple[LocalObserverSection, ...]
) -> DiagramCoherenceJudgment:
    """Keep pairwise agreement separate from complete declared gluing."""
    logger.debug("diagram_coherence_judgment entry")
    atlas, sections = _snapshot_diagram_source(atlas, sections)
    try:
        overlaps = pairwise_overlap_rows(atlas, sections)
        criterion = exact_gluing_criterion(atlas, sections)
    except ValueError as exc:
        logger.error("diagram_coherence_judgment semantic source rejected")
        raise PositiveOntologyValidationError("invalid-diagram-source") from exc
    result = DiagramCoherenceJudgment(
        all(item.compatible for item in overlaps),
        criterion.exact_gluing_exists,
        criterion.obstruction_count,
    )
    logger.debug(
        "diagram_coherence_judgment exit pairwise=%s global=%s",
        result.pairwise_compatible,
        result.global_coherent,
    )
    return result


def _snapshot_diagram_source(
    atlas: ObserverPatchAtlas, sections: tuple[LocalObserverSection, ...]
) -> tuple[ObserverPatchAtlas, tuple[LocalObserverSection, ...]]:
    logger.debug("_snapshot_diagram_source entry")
    if type(atlas) is not ObserverPatchAtlas or type(sections) is not tuple:
        logger.error("_snapshot_diagram_source exact shell rejected")
        raise PositiveOntologyValidationError("invalid-diagram-source")
    try:
        universe_source, patches_source = atlas.universe, atlas.patches
    except AttributeError as exc:
        logger.error("_snapshot_diagram_source atlas fields missing")
        raise PositiveOntologyValidationError("invalid-diagram-source") from exc
    if (
        type(universe_source) is not tuple
        or not 1 <= len(universe_source) <= 64
        or type(patches_source) is not tuple
        or not 1 <= len(patches_source) <= 64
        or len(sections) > 64
    ):
        logger.error("_snapshot_diagram_source resource shell rejected")
        raise PositiveOntologyValidationError("invalid-diagram-source")
    universe = tuple(snapshot_identifier(item, "diagram-node") for item in universe_source)
    patches: list[ObserverPatch] = []
    for patch in patches_source:
        if type(patch) is not ObserverPatch:
            logger.error("_snapshot_diagram_source patch exact gate rejected")
            raise PositiveOntologyValidationError("invalid-diagram-source")
        try:
            name, nodes_source = patch.name, patch.nodes
        except AttributeError as exc:
            logger.error("_snapshot_diagram_source patch fields missing")
            raise PositiveOntologyValidationError("invalid-diagram-source") from exc
        if type(nodes_source) is not tuple or not 1 <= len(nodes_source) <= 64:
            logger.error("_snapshot_diagram_source patch nodes rejected")
            raise PositiveOntologyValidationError("invalid-diagram-source")
        patches.append(
            ObserverPatch(
                snapshot_identifier(name, "diagram-patch"),
                tuple(snapshot_identifier(item, "diagram-node") for item in nodes_source),
            )
        )
    captured_sections: list[LocalObserverSection] = []
    total_nodes = 0
    for section in sections:
        if type(section) is not LocalObserverSection:
            logger.error("_snapshot_diagram_source section exact gate rejected")
            raise PositiveOntologyValidationError("invalid-diagram-source")
        try:
            patch_name, blocks_source = section.patch_name, section.blocks
        except AttributeError as exc:
            logger.error("_snapshot_diagram_source section fields missing")
            raise PositiveOntologyValidationError("invalid-diagram-source") from exc
        if type(blocks_source) is not tuple or not 1 <= len(blocks_source) <= 64:
            logger.error("_snapshot_diagram_source blocks rejected")
            raise PositiveOntologyValidationError("invalid-diagram-source")
        blocks: list[tuple[str, ...]] = []
        for block in blocks_source:
            if type(block) is not tuple or not 1 <= len(block) <= 64:
                logger.error("_snapshot_diagram_source block rejected")
                raise PositiveOntologyValidationError("invalid-diagram-source")
            total_nodes += len(block)
            if total_nodes > 4096:
                logger.error("_snapshot_diagram_source node limit")
                raise PositiveOntologyValidationError("diagram-source-resource-limit")
            blocks.append(tuple(snapshot_identifier(item, "diagram-node") for item in block))
        captured_sections.append(
            LocalObserverSection(
                snapshot_identifier(patch_name, "diagram-section-patch"), tuple(blocks)
            )
        )
    result = (ObserverPatchAtlas(universe, tuple(patches)), tuple(captured_sections))
    logger.debug("_snapshot_diagram_source exit patches=%d", len(patches))
    return result


def bounded_window_judgment(window: PrefixTowerWindow) -> InfinityJudgment:
    """Classify only the supplied finite prefix window."""
    logger.debug("bounded_window_judgment entry")
    window = snapshot_prefix_window(window)
    report = prefix_coherence_report(window)
    result = InfinityJudgment(
        InfinityLevel.BOUNDED_WINDOW,
        report.coherent,
        report.maximum_depth,
        False,
        "finite-window-only" if report.coherent else "finite-window-obstructed",
    )
    logger.debug("bounded_window_judgment exit verified=%s", result.verified)
    return result


def local_extension_judgment(
    window: PrefixTowerWindow, extension: PrefixStage
) -> InfinityJudgment:
    """Check one next stage without promoting to a productive/all-depth claim."""
    logger.debug("local_extension_judgment entry")
    window = snapshot_prefix_window(window)
    extension = snapshot_prefix_stage(extension, window.alphabet)
    expected_depth = len(window.stages)
    if extension.depth != expected_depth:
        logger.error("local_extension_judgment depth mismatch")
        raise PositiveOntologyValidationError("extension-depth-mismatch")
    rows = tuple(item.symbols for item in window.stages) + (extension.symbols,)
    extended = prefix_tower_window(window.alphabet, rows)
    coherent = prefix_coherence_report(extended).coherent
    result = InfinityJudgment(
        InfinityLevel.LOCAL_EXTENSION,
        coherent,
        extension.depth,
        False,
        "one-local-extension-only" if coherent else "local-extension-obstructed",
    )
    logger.debug("local_extension_judgment exit verified=%s", result.verified)
    return result


def nonfinite_infinity_boundary(level: InfinityLevel) -> InfinityJudgment:
    """Represent higher infinity claims without deriving them from finite rows."""
    logger.debug("nonfinite_infinity_boundary entry")
    if type(level) is not InfinityLevel or level not in {
        InfinityLevel.PRODUCTIVE_PROCESS,
        InfinityLevel.ALL_DEPTH_HYPOTHESIS,
        InfinityLevel.COMPLETED_CARRIER,
    }:
        logger.error("nonfinite_infinity_boundary invalid level")
        raise PositiveOntologyValidationError("nonfinite-level-required")
    boundary = {
        InfinityLevel.PRODUCTIVE_PROCESS: "total-next-step-process-must-be-supplied",
        InfinityLevel.ALL_DEPTH_HYPOTHESIS: "all-depth-family-is-an-explicit-hypothesis",
        InfinityLevel.COMPLETED_CARRIER: "completed-carrier-requires-separate-construction",
    }[level]
    result = InfinityJudgment(level, False, 0, False, boundary)
    logger.debug("nonfinite_infinity_boundary exit level=%s", level.value)
    return result


def silence_boundary_judgment(
    modality: SilenceModality, evidence_id: str
) -> SilenceBoundaryJudgment:
    """Record a non-observation modality without pretending it was derived."""
    logger.debug("silence_boundary_judgment entry")
    allowed = {
        SilenceModality.OPERATIONAL_ABSENCE,
        SilenceModality.OBSERVER_BLINDNESS,
        SilenceModality.EPISTEMIC_OPEN,
        SilenceModality.RESOURCE_LIMITED,
        SilenceModality.DIVERGENT,
        SilenceModality.INCONSISTENT,
        SilenceModality.UNRESOLVED_IN_SYSTEM,
    }
    if type(modality) is not SilenceModality or modality not in allowed:
        logger.error("silence_boundary_judgment observation-derived modality rejected")
        raise PositiveOntologyValidationError("explicit-boundary-modality-required")
    evidence = snapshot_identifier(evidence_id, "silence-evidence-id")
    result = SilenceBoundaryJudgment(
        modality, evidence, False, "explicit-evidence-not-observation-derived"
    )
    logger.debug("silence_boundary_judgment exit modality=%s", modality.value)
    return result


def positive_ontology_checklist() -> tuple[str, ...]:
    """Return the bounded P0 acceptance and nonclaim boundary."""
    logger.debug("positive_ontology_checklist entry")
    result = (
        "typed internal observers from the closed R11 codec",
        "separate run, support, persistence, family-extension, and infinity judgments",
        "no absent or nonexistent verdict",
        "path-relative witness-bearing persistence",
        "family extension is ordered prefix pressure, not semantic response translation",
        "pairwise compatibility does not imply global coherence",
        "finite rows never promote productive, all-depth, or completed infinity",
        "metatheory identity is explicit and echo does not reflect token identity",
        "absence, blindness, divergence, inconsistency, and undecidability require explicit evidence",
        "finite operational experiment, not metaphysical proof",
    )
    logger.debug("positive_ontology_checklist exit count=%d", len(result))
    return result
