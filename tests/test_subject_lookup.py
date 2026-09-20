from types import SimpleNamespace

import pytest

import core.integration.classisland as classisland_module
from core.integration.classisland import ClassIslandIntegration


@pytest.mark.skipif(
    not classisland_module.CSHARP_AVAILABLE,
    reason="ClassIsland IPC assemblies are unavailable on this platform",
)
def test_current_subject_lookup_reads_ipc_subject(monkeypatch):
    class FakeSubject:
        Name = "  语文  "

    class FakeLessonsService:
        CurrentSubject = FakeSubject()

    class GenericProxyFactory:
        def __getitem__(self, interface):
            return lambda provider, peer: FakeLessonsService()

    class FakeFactory:
        CreateIpcProxy = GenericProxyFactory()

    monkeypatch.setattr(classisland_module, "GeneratedIpcFactory", FakeFactory)

    integration = ClassIslandIntegration()
    integration.connectivity_status = "Connected"
    integration.ipcClient = SimpleNamespace(Provider=object(), PeerProxy=object())

    assert integration.get_current_subject() == "语文"


@pytest.mark.skipif(
    not classisland_module.CSHARP_AVAILABLE,
    reason="ClassIsland IPC assemblies are unavailable on this platform",
)
def test_current_subject_lookup_falls_back_when_disconnected():
    integration = ClassIslandIntegration()
    integration.connectivity_status = "NotConnected"
    integration.ipcClient = None

    assert integration.get_current_subject() is None
