"""Direct regressions for the P3-N6 fifth-review repair candidate."""

from __future__ import annotations

import hashlib
import importlib
import logging
from pathlib import Path
import sys
import types

import pytest

logger = logging.getLogger(__name__)


def _repository_root() -> Path:
    """Directory holding `pyproject.toml`, found by walking upward."""
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "pyproject.toml").is_file():
            return candidate
    raise RuntimeError("repository root not found")
P3N6_MANIFEST_ROOT_V1 = "d3082378c6bab81c542d270aba402fa921a6eca95fb6576cdcd7c113c4396cf4"


def _modules() -> dict[str, object]:
    """Load the candidate under one isolated package."""
    logger.debug("_modules entry")
    name = "p3n6_fifth_repair_core"
    if name not in sys.modules:
        package = types.ModuleType(name)
        package.__path__ = [str((_repository_root() / "src/core").resolve())]
        sys.modules[name] = package
    names = (
        "padic.completion.core", "padic.family_introduction.core",
        "prime_power_unbounded_common", "prime_power_unbounded_sources",
        "prime_power_unbounded_types", "prime_power_unbounded_dispatch",
        "prime_power_unbounded_requests", "prime_power_unbounded_failures",
        "prime_power_unbounded_formal_failures",
        "prime_power_unbounded_result_digests",
        "prime_power_unbounded_failure_validation",
    )
    result = {item: importlib.import_module(f"{name}.{item}") for item in names}
    logger.debug("_modules exit count=%d", len(result))
    return result


def _packages(modules: dict[str, object]) -> tuple[object, object]:
    """Construct one fresh exact N1-zero/PΩ2 pair."""
    logger.debug("_packages entry")
    completion = modules["padic.completion.core"]
    family = modules["padic.family_introduction.core"]
    prime = completion.prime_source(5)  # type: ignore[attr-defined]
    doctrine = completion.padic_tower_doctrine()  # type: ignore[attr-defined]
    p2 = completion.padic_completion_package(  # type: ignore[attr-defined]
        prime, doctrine, completion.padic_completion_theorem_source(),
        completion.padic_completion_ledger(), completion.padic_completion_policy(),
    )
    n1 = family.n1_introduction_package(  # type: ignore[attr-defined]
        prime, family.integer_source(0), doctrine, family.n1_theorem_source(),
        family.n1_assumption_ledger(), family.n1_policy(),
    )
    logger.debug("_packages exit")
    return n1, p2


def _some_receipt(modules: dict[str, object], p2: object) -> object:
    """Construct one digest-valid but non-authoritative CI metadata record."""
    logger.debug("_some_receipt entry")
    common = modules["prime_power_unbounded_common"]
    sources = modules["prime_power_unbounded_sources"]
    type_module = modules["prime_power_unbounded_types"]
    lane = type_module.N6Lane.W_INFORMATION_GROWTH  # type: ignore[attr-defined]
    source = sources.theorem_source(lane)  # type: ignore[attr-defined]
    values = (
        p2.doctrine.doctrine_digest, p2.doctrine.index_id,  # type: ignore[attr-defined]
        "candidate-foundation-v1", p2.package_digest, source.source_digest,  # type: ignore[attr-defined]
    )
    receipt_digest = common.digest(  # type: ignore[attr-defined]
        "veyra.p3n6.ci-receipt.v1",
        tuple(
            (label, value.encode())
            for label, value in zip(
                ("doctrine", "index", "foundation", "package", "source"),
                values, strict=True,
            )
        ),
    )
    result = type_module.CompletedInfinityReceiptV1(  # type: ignore[attr-defined]
        *values, receipt_digest
    )
    logger.debug("_some_receipt exit")
    return result


def test_source_identities_ignore_replaceable_module_bindings(monkeypatch) -> None:
    """Mutable display bindings cannot alter source capture or theorem identity."""
    logger.debug("test_source_identities_ignore_replaceable_module_bindings entry")
    modules = _modules()
    sources = modules["prime_power_unbounded_sources"]
    dispatcher = modules["prime_power_unbounded_dispatch"]
    requests = modules["prime_power_unbounded_requests"]
    n1, p2 = _packages(modules)
    expected = sources.theorem_source()  # type: ignore[attr-defined]
    assert not hasattr(dispatcher, "_SOURCE_SPECS")
    for name, value in (
        ("ARTIFACT_PATH", "attacker.lean"),
        ("ARTIFACT_SHA256", "0" * 64),
        ("E_THEOREM_IDS", ("ATTACKER_THEOREM",)),
        ("E_AXIOM_ROWS", (("ATTACKER_THEOREM", ("choice",)),)),
        ("TCB_DIGEST", "1" * 64),
        ("HARD_CAPTURED_BYTES", 1),
    ):
        monkeypatch.setattr(sources, name, value)
    request = requests.e_request(n1, p2)  # type: ignore[attr-defined]
    assert request.theorem == expected
    assert request.policy.max_captured_bytes == 3 * 1024 * 1024
    logger.debug("test_source_identities_ignore_replaceable_module_bindings exit")


def test_w_specific_malformed_fields_reject_before_source_capture(monkeypatch) -> None:
    """Receipt, theorem and policy shape checks precede every source open."""
    logger.debug("test_w_specific_malformed_fields_reject_before_source_capture entry")
    modules = _modules()
    common = modules["prime_power_unbounded_common"]
    dispatcher = modules["prime_power_unbounded_dispatch"]
    requests = modules["prime_power_unbounded_requests"]
    n1, p2 = _packages(modules)

    def bomb(_fd: int) -> tuple[object, ...]:
        raise AssertionError("source-capture-ran-before-w-specific-preflight")

    monkeypatch.setattr(dispatcher, "_capture_all", bomb)
    for arguments in (
        (object(), None, None),
        (None, object(), None),
        (None, None, object()),
    ):
        with pytest.raises(common.P3N6ValidationError):  # type: ignore[attr-defined]
            requests.w_request(  # type: ignore[attr-defined]
                n1, p2, arguments[0], arguments[1], arguments[2]
            )
    logger.debug("test_w_specific_malformed_fields_reject_before_source_capture exit")


def test_w_result_arm_is_dependent_on_none_or_some_request() -> None:
    """NONE accepts only OPEN and SOME only dependency-replay FORMAL_FAILURE."""
    logger.debug("test_w_result_arm_is_dependent_on_none_or_some_request entry")
    modules = _modules()
    common = modules["prime_power_unbounded_common"]
    types_module = modules["prime_power_unbounded_types"]
    requests = modules["prime_power_unbounded_requests"]
    failures = modules["prime_power_unbounded_failures"]
    digests = modules["prime_power_unbounded_result_digests"]
    validation = modules["prime_power_unbounded_failure_validation"]
    n1, p2 = _packages(modules)
    none_request = requests.w_request(n1, p2)  # type: ignore[attr-defined]
    some_request = requests.w_request(  # type: ignore[attr-defined]
        n1, p2, _some_receipt(modules, p2)
    )
    open_for_some = failures.N6WOpenV1(  # type: ignore[attr-defined]
        types_module.N6Status.OPEN,  # type: ignore[attr-defined]
        types_module.N6WOpenReason.MISSING_COMPLETED_INFINITY_ADMISSION,  # type: ignore[attr-defined]
        types_module.N6GoalID.COMPLETED_INFINITY_ADMISSION,  # type: ignore[attr-defined]
        some_request.request_digest,
        digests.open_result_digest(  # type: ignore[attr-defined]
            types_module.N6Lane.W_INFORMATION_GROWTH,  # type: ignore[attr-defined]
            "missing-completed-infinity-admission",
            types_module.N6GoalID.COMPLETED_INFINITY_ADMISSION,  # type: ignore[attr-defined]
            some_request.request_digest,
        ),
    )
    formal_for_some = requests.w_result(some_request)  # type: ignore[attr-defined]
    with pytest.raises(common.P3N6ValidationError, match="alternative-arm"):  # type: ignore[attr-defined]
        validation.validate_w_result(open_for_some, some_request)  # type: ignore[attr-defined]
    with pytest.raises(common.P3N6ValidationError, match="alternative-arm"):  # type: ignore[attr-defined]
        validation.validate_w_result(formal_for_some, none_request)  # type: ignore[attr-defined]
    assert validation.validate_w_result(  # type: ignore[attr-defined]
        requests.w_result(none_request), none_request  # type: ignore[attr-defined]
    )
    assert validation.validate_w_result(  # type: ignore[attr-defined]
        formal_for_some, some_request
    )
    logger.debug("test_w_result_arm_is_dependent_on_none_or_some_request exit")


def test_production_root_acquisition_is_resolve_free_and_no_follow() -> None:
    """Dispatch uses the shared lexical dirfd root; production never canonicalizes."""
    logger.debug("test_production_root_acquisition_is_resolve_free_and_no_follow entry")
    core = _repository_root() / "src/core"
    paths = tuple(sorted(core.glob("prime_power_unbounded_*.py")))
    assert paths
    assert all(b".resolve(" not in path.read_bytes() for path in paths)
    dispatch = (core / "prime_power_unbounded_dispatch.py").read_text()
    capture = (core / "prime_power_unbounded_capture.py").read_text()
    assert "root_fd, _ = _open_project_root()" in dispatch
    assert "module_path = Path(__file__)" in capture
    assert "os.O_NOFOLLOW" in capture
    logger.debug("test_production_root_acquisition_is_resolve_free_and_no_follow exit")


def test_canonical_manifest_root_is_reproducible() -> None:
    """The self-contained public code/tests/spec manifest root reproduces."""
    logger.debug("test_canonical_manifest_root_is_reproducible entry")
    root = _repository_root()
    spec = root / "docs/reference/proofs.md"
    heading = "## P3-N6 public interface boundary\n"
    text = spec.read_text()
    section = text.split(heading, 1)[1].split("\n## ", 1)[0]
    spec_bytes = (heading + section).encode()
    test_path = Path(__file__).relative_to(root).as_posix()
    marker = 'P3N6_MANIFEST_ROOT_V1 = "'
    test_bytes = Path(__file__).read_bytes()
    normalized_test = test_bytes.replace(
        (marker + P3N6_MANIFEST_ROOT_V1).encode(),
        (marker + "0" * 64).encode(),
        1,
    )
    paths = (
        "proofs/lean/VeyraPrimePowerUnbounded.lean",
        "src/core/prime_power_unbounded_capability.py",
        "src/core/prime_power_unbounded_capture.py",
        "src/core/prime_power_unbounded_common.py",
        "src/core/prime_power_unbounded_dispatch.py",
        "src/core/prime_power_unbounded_execution_continuity.py",
        "src/core/prime_power_unbounded_failure_validation.py",
        "src/core/prime_power_unbounded_failures.py",
        "src/core/prime_power_unbounded_formal.py",
        "src/core/prime_power_unbounded_formal_failures.py",
        "src/core/prime_power_unbounded_ledger.py",
        "src/core/prime_power_unbounded_preflight.py",
        "src/core/prime_power_unbounded_requests.py",
        "src/core/prime_power_unbounded_result_digests.py",
        "src/core/prime_power_unbounded_results.py",
        "src/core/prime_power_unbounded_runtime.py",
        "src/core/prime_power_unbounded_sources.py",
        "src/core/prime_power_unbounded_types.py",
        "docs/reference/proofs.md",
        "tests/prime_power/test_prime_power_unbounded_p3n6_fifth_repair.py",
        "tests/prime_power/test_prime_power_unbounded_p3n6_hardening.py",
        "tests/prime_power/test_prime_power_unbounded_p3n6_positive.py",
        "tests/prime_power/test_prime_power_unbounded_p3n6_sources.py",
    )
    rows = []
    for path in paths:
        if path == spec.relative_to(root).as_posix():
            payload = spec_bytes
        elif path == test_path:
            payload = normalized_test
        else:
            payload = (root / path).read_bytes()
        row = len(path.encode()).to_bytes(8, "big") + path.encode() + hashlib.sha256(payload).digest()
        rows.append(len(row).to_bytes(8, "big") + row)
    manifest = b"P3N6-MANIFEST-V1\0" + len(rows).to_bytes(8, "big") + b"".join(rows)
    assert hashlib.sha256(manifest).hexdigest() == P3N6_MANIFEST_ROOT_V1
    logger.debug("test_canonical_manifest_root_is_reproducible exit")
