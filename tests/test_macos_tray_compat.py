# Import the application graph first; the current package has legacy imports
# between ``core.config`` and ``core.integration``.
import core.choice  # noqa: F401
import core.tray as tray_module
import core.integration.native as native_module
from core.integration.native import NativeNotifier


def test_macos_27_disables_qt_status_item(monkeypatch):
    monkeypatch.setattr(tray_module.sys, "platform", "darwin")
    monkeypatch.setattr(tray_module.platform, "mac_ver", lambda: ("27.0", ("", "", ""), ""))

    assert tray_module.RPTray._is_qt_status_item_unsafe()


def test_older_macos_keeps_qt_status_item(monkeypatch):
    monkeypatch.setattr(tray_module.sys, "platform", "darwin")
    monkeypatch.setattr(tray_module.platform, "mac_ver", lambda: ("26.6", ("", "", ""), ""))

    assert not tray_module.RPTray._is_qt_status_item_unsafe()


def test_native_notifier_uses_osascript_without_status_item(monkeypatch):
    calls = []

    class FakeTray:
        trayIcon = None

    notifier = object.__new__(NativeNotifier)
    notifier.tray = FakeTray()
    monkeypatch.setattr(native_module.sys, "platform", "darwin")
    monkeypatch.setattr(
        native_module.subprocess,
        "run",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    notifier._send("标题", "正文")

    assert calls
    args, kwargs = calls[0]
    command = args[0]
    assert command[:2] == ["osascript", "-e"]
    assert "display notification" in command[2]
    assert "标题" in command[2]
    assert "正文" in command[2]
    assert kwargs["check"] is True
