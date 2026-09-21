import asyncio

import pytest

# Import through the application module first so the package's existing
# integration/config singleton initialization completes before direct access.
import core.choice  # noqa: F401
import core.integration.classisland as classisland_module
from core.integration.classisland import ClassIslandIntegration


@pytest.mark.skipif(
    not classisland_module.CSHARP_AVAILABLE,
    reason="ClassIsland IPC assemblies are unavailable on this platform",
)
def test_start_sets_running_before_thread_starts(monkeypatch):
    observed = []

    class FakeThread:
        def __init__(self, target, daemon):
            self.target = target
            self.daemon = daemon

        def start(self):
            observed.append(integration.is_running)

    integration = ClassIslandIntegration.__new__(ClassIslandIntegration)
    integration.is_running = False
    integration.is_available = True
    integration.client_thread = None
    integration._set_connectivity = lambda status: None
    monkeypatch.setattr(classisland_module.threading, "Thread", FakeThread)

    integration.start()

    assert observed == [True]


@pytest.mark.skipif(
    not classisland_module.CSHARP_AVAILABLE,
    reason="ClassIsland IPC assemblies are unavailable on this platform",
)
def test_connect_failure_does_not_prevent_retry():
    class FakeClient:
        def __init__(self):
            self.attempts = 0

        def Connect(self):
            self.attempts += 1
            if self.attempts == 1:
                raise RuntimeError("ClassIsland is not running")
            return object()

    integration = ClassIslandIntegration.__new__(ClassIslandIntegration)
    integration.ipcClient = FakeClient()
    awaited = []

    async def fake_await_dotnet_task(task):
        awaited.append(task)

    integration._await_dotnet_task = fake_await_dotnet_task

    assert asyncio.run(integration._try_connect()) is False
    assert asyncio.run(integration._try_connect()) is True
    assert integration.ipcClient.attempts == 2
    assert len(awaited) == 1
