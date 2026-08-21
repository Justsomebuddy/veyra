from __future__ import annotations

from dataclasses import replace
import os

import pytest

from src.core.observer_discovery_v3.dsl.types import ClosedObserverGrammar, ClosedObserverTerm, ClosedWorkerConfig
import src.core.observer_discovery_v3.worker.runtime as worker


class FakeResource:
    RLIM_INFINITY = 2**63 - 1
    RLIMIT_CPU = 1
    RLIMIT_AS = 2
    RLIMIT_RSS = 2
    RLIMIT_FSIZE = 3
    RLIMIT_NOFILE = 4

    def __init__(
        self,
        limits: dict[int, tuple[int, int]],
        *,
        finite_as_error: Exception | None = None,
        all_errors: dict[int, Exception] | None = None,
        ignore_updates: bool = False,
    ) -> None:
        self.limits = dict(limits)
        self.finite_as_error = finite_as_error
        self.all_errors = all_errors or {}
        self.ignore_updates = ignore_updates
        self.set_calls: list[tuple[int, tuple[int, int]]] = []

    def getrlimit(self, kind: int) -> tuple[int, int]:
        return self.limits[kind]

    def setrlimit(self, kind: int, limits: tuple[int, int]) -> None:
        self.set_calls.append((kind, limits))
        if kind in self.all_errors:
            raise self.all_errors[kind]
        if kind == self.RLIMIT_AS and limits != (self.RLIM_INFINITY, self.RLIM_INFINITY):
            if self.finite_as_error is not None:
                raise self.finite_as_error
        if not self.ignore_updates:
            self.limits[kind] = limits


def test_resource_limit_preserves_a_stricter_inherited_limit() -> None:
    resource = FakeResource({FakeResource.RLIMIT_AS: (64, 128)})

    applied = worker._set_resource_limit(resource, resource.RLIMIT_AS, 256)

    assert applied
    assert resource.set_calls == [(resource.RLIMIT_AS, (64, 64))]
    assert resource.getrlimit(resource.RLIMIT_AS) == (64, 64)


def test_resource_limit_rejects_silent_or_unexpected_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    ignored = FakeResource({FakeResource.RLIMIT_AS: (512, 512)}, ignore_updates=True)
    with pytest.raises(worker.ClosedWorkerError, match="resource-limit-not-applied"):
        worker._set_resource_limit(ignored, ignored.RLIMIT_AS, 256)

    monkeypatch.setattr(worker.sys, "platform", "darwin")
    for error in (OSError("unexpected"), ValueError("unexpected")):
        failing = FakeResource(
            {FakeResource.RLIMIT_AS: (512, 512)},
            all_errors={FakeResource.RLIMIT_AS: error},
        )
        with pytest.raises(type(error), match="unexpected"):
            worker._set_resource_limit(
                failing,
                failing.RLIMIT_AS,
                256,
                allow_darwin_as_unavailable=True,
            )


def test_only_confirmed_darwin_rlimit_as_unavailability_is_optional(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(worker.sys, "platform", "darwin")
    infinity = FakeResource.RLIM_INFINITY
    resource = FakeResource(
        {FakeResource.RLIMIT_AS: (infinity, infinity)},
        finite_as_error=ValueError("finite RLIMIT_AS unsupported"),
    )

    applied = worker._set_resource_limit(
        resource,
        resource.RLIMIT_AS,
        256,
        allow_darwin_as_unavailable=True,
    )

    assert not applied
    assert resource.set_calls == [
        (resource.RLIMIT_AS, (256, 256)),
        (resource.RLIMIT_AS, (infinity, infinity)),
    ]
    assert resource.getrlimit(resource.RLIMIT_AS) == (infinity, infinity)


def test_darwin_nonalias_value_error_remains_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(worker.sys, "platform", "darwin")
    infinity = FakeResource.RLIM_INFINITY
    resource = FakeResource(
        {FakeResource.RLIMIT_AS: (infinity, infinity)},
        finite_as_error=ValueError("unexpected nonalias failure"),
    )
    resource.RLIMIT_RSS = 99

    with pytest.raises(ValueError, match="unexpected nonalias failure"):
        worker._set_resource_limit(
            resource,
            resource.RLIMIT_AS,
            256,
            allow_darwin_as_unavailable=True,
        )


def test_darwin_exception_does_not_make_required_limits_optional(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(worker.sys, "platform", "darwin")
    infinity = FakeResource.RLIM_INFINITY
    resource = FakeResource(
        {FakeResource.RLIMIT_CPU: (infinity, infinity)},
        all_errors={FakeResource.RLIMIT_CPU: ValueError("cpu rejected")},
    )

    with pytest.raises(ValueError, match="cpu rejected"):
        worker._set_resource_limit(resource, resource.RLIMIT_CPU, 10)


def test_hard_and_configured_limit_sets_keep_cpu_fsize_and_nofile_mandatory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[int, int, bool]] = []

    def record(_resource: object, kind: int, requested: int, *, allow_darwin_as_unavailable: bool = False) -> bool:
        calls.append((kind, requested, allow_darwin_as_unavailable))
        return kind != FakeResource.RLIMIT_AS

    monkeypatch.setattr(worker, "_set_resource_limit", record)
    fake = FakeResource(
        {
            FakeResource.RLIMIT_CPU: (100, 100),
            FakeResource.RLIMIT_AS: (100, 100),
            FakeResource.RLIMIT_FSIZE: (100, 100),
            FakeResource.RLIMIT_NOFILE: (100, 100),
        }
    )

    worker._apply_hard_limits(fake)
    worker._apply_limits(replace(ClosedWorkerConfig(), memory_limit_mb=128), fake)

    assert calls == [
        (fake.RLIMIT_CPU, 10, False),
        (fake.RLIMIT_AS, 2048 * 1024 * 1024, True),
        (fake.RLIMIT_FSIZE, 16_000_000, False),
        (fake.RLIMIT_NOFILE, 32, False),
        (fake.RLIMIT_CPU, ClosedWorkerConfig().cpu_seconds, False),
        (fake.RLIMIT_AS, 128 * 1024 * 1024, True),
        (fake.RLIMIT_FSIZE, ClosedWorkerConfig().max_response_bytes, False),
        (fake.RLIMIT_NOFILE, 32, False),
    ]


@pytest.mark.skipif(os.name != "posix", reason="closed worker is a POSIX-only logical subprocess")
def test_real_posix_worker_completes_under_host_resource_limits() -> None:
    grammar = ClosedObserverGrammar("resource-limit-host", 2, (0, 1), ("column", "xor"), 2, 1, 3)
    terms = (ClosedObserverTerm("column", (0,)), ClosedObserverTerm("xor", (0, 1)))
    rows = ((0, 0), (0, 1), (1, 0), (1, 1))

    receipt = worker.run_closed_observers_isolated(grammar, terms, rows)

    assert receipt.status == worker.READY
    assert receipt.outputs == ((0, 0, 1, 1), (0, 1, 1, 0))
    assert worker.validate_closed_receipt(receipt)
