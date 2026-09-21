"""
系统托盘菜单。
"""

import platform
import sys

from PySide6.QtCore import QObject
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon
from loguru import logger

from .config.dirs import ASSETS_DIR


class RPTray(QObject):
    _instance: "RPTray" = None

    @classmethod
    def instance(cls) -> "RPTray":
        return cls._instance

    def __init__(self, parent=None):
        super().__init__()
        RPTray._instance = self
        from .main import RPMain  # 延迟导入，避免循环引用
        self.main = RPMain.instance()

        self.main.themeManager.themeChanged.connect(lambda theme: self.onThemeChanged(theme))

        self.trayIcon = None
        self.menu = None
        self.toggle_action = None
        self._init_tray()

    @staticmethod
    def _is_qt_status_item_unsafe() -> bool:
        """Return whether Qt's Cocoa status-item event path is unsafe.

        Qt 6.11.2 reads ``NSApp.currentEvent.clickCount`` while opening a
        status-item menu. macOS 27 may provide a gesture event there instead
        of a mouse event, which raises an Objective-C assertion and aborts the
        process. Qt has an upstream fix, but it is not present in the wheel
        currently used by RandPicker. This guard should be removed once the
        bundled Qt contains commit 65020b43cdd2 (or an equivalent fix).
        """
        if sys.platform != "darwin":
            return False
        try:
            major = int(platform.mac_ver()[0].split(".", 1)[0])
        except (IndexError, TypeError, ValueError):
            return False
        return major >= 27

    def _init_tray(self):
        if self._is_qt_status_item_unsafe():
            logger.warning(
                "当前 macOS 版本的 Qt 状态栏菜单存在已知崩溃问题，已禁用托盘菜单；"
                "原生通知将改用系统通知。"
            )
            return
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("系统托盘不可用，跳过托盘菜单。")
            return

        icon_path = str(
            ASSETS_DIR / ("icon-light.jpg" if self.main.themeManager.get_theme() == "Light" else "icon-dark.jpg"))
        self.trayIcon = QSystemTrayIcon(QIcon(icon_path), self)
        self.trayIcon.setToolTip("RandPicker")

        self.menu = QMenu()
        self.toggle_action = self.menu.addAction("隐藏窗口", self.toggle_visibility)
        self.menu.addAction("设置", self.open_settings)
        self.menu.addSeparator()
        self.menu.addAction("重启", self.restart_app)
        self.menu.addAction("退出", self.quit_app)

        self.trayIcon.setContextMenu(self.menu)
        self.trayIcon.activated.connect(self._handle_activation)
        self.trayIcon.show()
        self._sync_action_text()

    def _handle_activation(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.toggle_visibility()

    def toggle_visibility(self):
        widget = getattr(self.main, "widget", None)
        if not widget or not getattr(widget, "window", None):
            logger.warning("窗口未初始化，无法切换可见性。")
            return

        if widget.window.isVisible():
            widget.hide()
        else:
            widget.show()
        self._sync_action_text()

    def _sync_action_text(self):
        widget = getattr(self.main, "widget", None)
        if not self.toggle_action or not widget or not getattr(widget, "window", None):
            return
        text = "隐藏窗口" if widget.window.isVisible() else "显示窗口"
        self.toggle_action.setText(text)

    def open_settings(self):
        handler = getattr(self.main, "open_settings", None)
        if callable(handler):
            handler()
            logger.info("打开设置")
            return
        logger.error("打开设置失败")

    def restart_app(self):
        handler = getattr(self.main, "restart", None)
        if callable(handler):
            handler()
            return
        logger.error("重新启动失败")

    def quit_app(self):
        handler = getattr(self.main, "quit", None)
        if callable(handler):
            handler()
            return
        logger.error("退出应用失败")

    def onThemeChanged(self, theme):
        if not self.trayIcon:
            return
        icon_path = str(ASSETS_DIR / ("icon-light.jpg" if theme == "Light" else "icon-dark.jpg"))
        self.trayIcon.setIcon(QIcon(icon_path))
