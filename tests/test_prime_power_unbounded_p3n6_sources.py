"""Focused hostile tests for the unreleased P3-N6 foundation boundary."""

from __future__ import annotations

from dataclasses import fields, replace
import hashlib
import importlib
import logging
import os
from pathlib import Path
import sys
import types

import pytest

logger = logging.getLogger(__name__)


def _isolated_modules():
    """Load candidates without importing the drifting aggregate core API."""
    logger.debug("_isolated_modules entry")
    name = "p3n6_isolated_core"
    package = sys.modules.get(name)
    if package is None:
        package = types.ModuleType(name)
        package.__path__ = [str((Path(__file__).parents[1] / "src/core").resolve())]
        sys.modules[name] = package
    modules = tuple(
        importlib.import_module(f"{name}.{module}")
        for module in (
            "padic_completion",
            "padic_family_introduction",
            "prime_power_unbounded_common",
            "prime_power_unbounded_sources",
            "prime_power_unbounded_requests",
            "prime_power_unbounded_preflight",
        )
    )
    logger.debug("_isolated_modules exit modules=%d", len(modules))
    return modules


def _candidate(name: str):
    """Load one additional isolated candidate module."""
    logger.debug("_candidate entry name=%s", name)
    _isolated_modules()
    result = importlib.import_module(f"p3n6_isolated_core.{name}")
    logger.debug("_candidate exit name=%s", name)
    return result


def _raw_packages(p: int = 5, z: int = 0):
    """Build fresh exact raw PΩ2/N1 packages without prior N6 results."""
    logger.debug("_raw_packages entry p=%d z=%d", p, z)
    completion, family, *_ = _isolated_modules()
    prime = completion.prime_source(p)
    doctrine = completion.padic_tower_doctrine()
    pomega2 = completion.padic_completion_package(
        prime,
        doctrine,
        completion.padic_completion_theorem_source(),
        completion.padic_completion_ledger(),
        completion.padic_completion_policy(),
    )
    n1 = family.n1_introduction_package(
        prime,
        family.integer_source(z),
        doctrine,
        family.n1_theorem_source(),
        family.n1_assumption_ledger(),
        family.n1_policy(),
    )
    logger.debug("_raw_packages exit")
    return n1, pomega2


def test_n6_source_policy_toolchain_and_live_roots() -> None:
    """Pinned descriptors, axiom rows and three live source roots agree."""
    logger.debug("test_n6_source_policy_toolchain_and_live_roots entry")
    _, _, _, sources, _, _ = _isolated_modules()
    source = sources.theorem_source()
    type_module = _candidate("prime_power_unbounded_types")
    w_source = sources.theorem_source(type_module.N6Lane.W_INFORMATION_GROWTH)
    assert sources.snapshot_theorem_source(source) == source
    assert sources.snapshot_policy(sources.policy()) == sources.policy()
    assert source.theorem_axiom_rows == sources.AXIOM_ROWS
    assert source.theorem_ids == sources.E_THEOREM_IDS
    assert w_source.theorem_ids == sources.W_THEOREM_IDS
    assert source.source_digest != w_source.source_digest
    assert set(source.theorem_ids).isdisjoint(w_source.theorem_ids)
    assert tuple(row[0] for row in source.theorem_axiom_rows) == source.theorem_ids
    root = Path(__file__).parents[1]
    for path, expected in (
        (sources.ARTIFACT_PATH, sources.ARTIFACT_SHA256),
        (sources.N1_PATH, sources.N1_SHA),
        (sources.P2_PATH, sources.P2_SHA),
    ):
        assert hashlib.sha256((root / path).read_bytes()).hexdigest() == expected
    logger.debug("test_n6_source_policy_toolchain_and_live_roots exit")


def test_n6_source_and_policy_mutations_fail_closed() -> None:
    """Source, axiom, theorem, TCB and Boolean-bound drift is malformed."""
    logger.debug("test_n6_source_and_policy_mutations_fail_closed entry")
    _, _, common, sources, _, _ = _isolated_modules()
    mutations = (
        replace(sources.theorem_source(), equality_definition_id="alias"),
        replace(sources.theorem_source(), theorem_ids=tuple(reversed(sources.THEOREM_IDS))),
        replace(sources.theorem_source(), theorem_axiom_rows=()),
        replace(sources.theorem_source(), tcb_digest="0" * 64),
    )
    for value in mutations:
        with pytest.raises(common.P3N6ValidationError):
            sources.snapshot_theorem_source(value)
    with pytest.raises(common.P3N6ValidationError, match="integer-invalid"):
        sources.snapshot_policy(replace(sources.policy(), max_ledger_rows=True))
    logger.debug("test_n6_source_and_policy_mutations_fail_closed exit")


def test_n6_zero_request_precharged_dispatch_roundtrip() -> None:
    """Every deep E construction stays inside the precharged transaction."""
    logger.debug("test_n6_zero_request_precharged_dispatch_roundtrip entry")
    _, _, _, _, requests, _ = _isolated_modules()
    n1, pomega2 = _raw_packages()
    request = requests.e_request(n1, pomega2)
    assert requests.snapshot_e_request(request) == request
    logger.debug("test_n6_zero_request_precharged_dispatch_roundtrip exit")


def test_n6_request_rejects_nonzero_digest_and_nested_drift() -> None:
    """Nonzero, replayed digest and malformed nested errors stay N6-owned."""
    logger.debug("test_n6_request_rejects_nonzero_digest_and_nested_drift entry")
    _, _, common, _, requests, _ = _isolated_modules()
    nonzero, pomega2 = _raw_packages(z=1)
    with pytest.raises(common.P3N6ValidationError, match="n1-zero-required"):
        requests.e_request(nonzero, pomega2)
    zero, pomega2 = _raw_packages()
    request = requests.e_request(zero, pomega2)
    with pytest.raises(common.P3N6ValidationError, match="request-drift"):
        requests.snapshot_e_request(replace(request, request_digest="0" * 64))
    bad_p2 = replace(pomega2, package_digest="0" * 64)
    with pytest.raises(common.P3N6ValidationError, match="nested-validation"):
        requests.snapshot_e_request(replace(request, pomega2=bad_p2))
    bad_n1 = replace(zero, package_digest="0" * 64)
    with pytest.raises(common.P3N6ValidationError, match="nested-validation"):
        requests.snapshot_e_request(replace(request, n1_zero=bad_n1))
    logger.debug("test_n6_request_rejects_nonzero_digest_and_nested_drift exit")


def test_n6_preflight_charges_and_caps_graph_before_recursive_walk(monkeypatch) -> None:
    """Exact graph caps fire before declared-byte traversal or deep snapshot."""
    logger.debug("test_n6_preflight_charges_and_caps_graph_before_recursive_walk entry")
    _, _, common, sources, requests, preflight = _isolated_modules()
    n1, pomega2 = _raw_packages()
    raw = requests.raw_e_request(n1, pomega2, sources.theorem_source(), sources.policy())
    charge = preflight.preflight_e_request(raw)
    assert charge.ledger_rows == len(n1.ledger.ordered_rows) + len(pomega2.ledger.rows)
    oversized = replace(n1, ledger=replace(n1.ledger, ordered_rows=("x",) * 257))
    oversized_raw = replace(raw, n1_zero=oversized)

    with pytest.raises(common.P3N6ValidationError, match="n1-rows-hard-cap"):
        preflight.preflight_e_request(oversized_raw)
    dispatcher = _candidate("prime_power_unbounded_dispatch")

    def bomb(*_args, **_kwargs):
        raise AssertionError("source-open-or-hash-ran-before-graph-cap")

    monkeypatch.setattr(dispatcher.os, "open", bomb)
    with pytest.raises(common.P3N6ValidationError, match="n1-rows-hard-cap"):
        requests.e_request(oversized, pomega2, sources.theorem_source(), sources.policy())
    damaged = replace(n1)
    object.__delattr__(damaged, "ledger")
    with pytest.raises(common.P3N6ValidationError, match="field-names|fields-missing"):
        preflight.preflight_e_request(replace(raw, n1_zero=damaged))
    logger.debug("test_n6_preflight_charges_and_caps_graph_before_recursive_walk exit")


def test_n6_capability_and_materializer_are_not_module_attributes() -> None:
    """Only the precharged dispatcher can reach nested materialization."""
    logger.debug("test_n6_capability_and_materializer_are_not_module_attributes entry")
    _, _, _, _, requests, _ = _isolated_modules()
    capability_module = _candidate("prime_power_unbounded_capability")
    preflight = _candidate("prime_power_unbounded_preflight")
    n1, pomega2 = _raw_packages()
    assert requests.e_request(n1, pomega2).n1_zero.integer.z == 0
    assert not hasattr(capability_module, "_issue_capability")
    assert not hasattr(capability_module, "_N6EPrechargeCapability")
    assert not hasattr(capability_module, "_create_handle")
    assert not hasattr(capability_module, "_open_fixed_source")
    assert not hasattr(capability_module, "_SOURCE_SPECS")
    assert not hasattr(preflight, "_precharged_dispatch")
    assert not hasattr(requests, "_materialize_e_request")
    logger.debug("test_n6_capability_and_materializer_are_not_module_attributes exit")


def test_n6_source_transaction_closes_every_fd_on_nested_rejection(monkeypatch) -> None:
    """The sole dispatcher closes all pinned sources on a semantic rejection."""
    logger.debug("test_n6_source_open_rejects_symlink_ancestors_and_detects_fd_drift entry")
    _, _, common, _, requests, _ = _isolated_modules()
    nonzero, pomega2 = _raw_packages(z=1)
    before = len(os.listdir("/proc/self/fd"))
    with pytest.raises(common.P3N6ValidationError, match="n1-zero-required"):
        requests.e_request(nonzero, pomega2)
    assert len(os.listdir("/proc/self/fd")) == before
    dispatcher = _candidate("prime_power_unbounded_dispatch")
    original_signature = dispatcher._signature
    calls = 0

    def fail_after_acquisition(fd):
        nonlocal calls
        calls += 1
        if calls == 2:
            common.reject("n6-test-post-acquisition-failure")
        return original_signature(fd)

    monkeypatch.setattr(dispatcher, "_signature", fail_after_acquisition)
    zero, pomega2 = _raw_packages()
    with pytest.raises(common.P3N6ValidationError, match="post-acquisition"):
        requests.e_request(zero, pomega2)
    assert len(os.listdir("/proc/self/fd")) == before
    logger.debug("test_n6_source_open_rejects_symlink_ancestors_and_detects_fd_drift exit")


def test_n6_hostile_values_are_validated_before_logging_or_len() -> None:
    """Hostile __len__/__str__ hooks never run before exact-type rejection."""
    logger.debug("test_n6_hostile_values_are_validated_before_logging_or_len entry")
    _, _, common, _, _, _ = _isolated_modules()

    class Bomb:
        def __len__(self):
            raise AssertionError("hostile-len-ran")

        def __str__(self):
            raise AssertionError("hostile-str-ran")

    with pytest.raises(common.P3N6ValidationError, match="exact-bytes"):
        common.sha(Bomb())
    with pytest.raises(common.P3N6ValidationError, match="exact-text"):
        common.digest(Bomb(), ())
    with pytest.raises(common.P3N6ValidationError, match="internal-contract"):
        common.exact_text("safe", Bomb())
    logger.debug("test_n6_hostile_values_are_validated_before_logging_or_len exit")


def test_n6_lane_closure_owned_positive_and_bounded_failures() -> None:
    """E/W reasons are disjoint, raw positives do not establish, payloads are bounded."""
    logger.debug("test_n6_lane_closure_owned_positive_and_bounded_failures entry")
    _, _, common, _, _, _ = _isolated_modules()
    type_module = _candidate("prime_power_unbounded_types")
    results = _candidate("prime_power_unbounded_results")
    failures = _candidate("prime_power_unbounded_failures")
    assert tuple(type_module.N6EOpenReason) == (type_module.N6EOpenReason.MISSING_EXACT_EQUALITY_ADAPTER,)
    assert tuple(type_module.N6WOpenReason) == (type_module.N6WOpenReason.MISSING_COMPLETED_INFINITY_ADMISSION,)
    assert "status" not in {field.name for field in fields(results.PowerInjectionJudgmentRawV1)}
    with pytest.raises(common.P3N6ValidationError, match="constructor-forbidden"):
        results.PowerInjectionEvidenceV1(object())
    with pytest.raises(common.P3N6ValidationError, match="e-open-lane"):
        failures.N6EOpenV1(
            type_module.N6Status.OPEN,
            type_module.N6WOpenReason.MISSING_COMPLETED_INFINITY_ADMISSION,
            type_module.N6GoalID.EXACT_EQUALITY_ADAPTER,
            "0" * 64,
            "1" * 64,
        )
    assert not hasattr(failures, "N6CounterexampleV1")
    assert not hasattr(failures, "N6ERefutedV1")
    assert not hasattr(failures, "N6EResourceLimitV1")
    with pytest.raises(common.P3N6ValidationError, match="code-exact-enum"):
        failures.N6SanitizedDiagnosticV1("timeout", "0" * 64)
    logger.debug("test_n6_lane_closure_owned_positive_and_bounded_failures exit")
