"""
设置服务模块 - 获取但不需要配置
"""
import platform
import json
from pathlib import Path
from PySide6.QtCore import QUrl

from PySide6.QtCore import Slot, QObject, Signal
from loguru import logger

from ..integration.classisland import ClassIslandIntegration


class SettingsService(QObject):
    connectivityUpdated = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ciService = ClassIslandIntegration.instance()
        self.ciService.connectivityUpdated.connect(lambda x: self.updateConnectivityStatus("classisland", x))
        # cwService.connectivityUpdated.connect(lambda x: self.updateConnectivityStatus("classwidgets", x))

    @Slot(str, result=bool)
    def getNotifyAvailability(self, option: str) -> bool:
        """获取通知方式的可用性"""
        match option:
            case "randpicker":
                return False
            case "native":
                return True
            case "classisland":
                return True
            case "classwidgets":
                return False
            case _:
                return False

    @Slot(str, result=str)
    def getConnectivityStatus(self, option: str) -> str:
        """获取通知方式的连接状态，供 QML 初始化状态"""
        match option:
            case "classisland":
                return self.ciService.get_connectivity_status()
            case "classwidgets":
                return "NotAvailable"
            case _:
                return "NotAvailable"

    def updateConnectivityStatus(self, method: str, connectivity: str) -> None:
        if method not in ["classisland", "classwidgets"]:
            return
        self.connectivityUpdated.emit(method, connectivity)
        logger.debug(f"触发通知方式 {method} 的连接状态更新: {connectivity}")

    @Slot(result=str)
    def getDotNetDownloadLink(self):
        match platform.system().lower():
            case "windows":
                running_os = "windows"
            case "linux":
                return "https://learn.microsoft.com/dotnet/core/install/linux?WT.mc_id=dotnet-35129-website"
            case "darwin":
                running_os = "macos"
            case _:
                return "https://dotnet.microsoft.com/en-us/download/dotnet/scripts"

        match platform.machine().lower():
            case "amd64" | "x86_64":
                arch = "x64"
            case "arm64" | "aarch64":
                arch = "arm64"
            case _:
                return "https://dotnet.microsoft.com/en-us/download/dotnet/scripts"

        return f"https://dotnet.microsoft.com/en-us/download/dotnet/thank-you/runtime-8.0.23-{running_os}-{arch}-installer"

    @Slot(str, result=bool)
    def exportConfig(self, path):
        try:
            from ..config import StudentsConfig, GroupsConfig, SettingsConfig
            target = Path(QUrl(path).toLocalFile() if str(path).startswith("file:") else path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps({"students": StudentsConfig.instance().getBuffer(), "groups": {"groups": GroupsConfig.instance().get_write_groups()}, "settings": SettingsConfig.instance().config}, ensure_ascii=False, indent=2), encoding="utf-8")
            return True
        except Exception as e:
            logger.exception(f"导出配置失败: {e}"); return False

    @Slot(str, result=bool)
    def importConfig(self, path):
        try:
            from ..config import StudentsConfig, GroupsConfig, SettingsConfig
            source = Path(QUrl(path).toLocalFile() if str(path).startswith("file:") else path)
            data = json.loads(source.read_text(encoding="utf-8"))
            if not all(isinstance(data.get(k), dict) for k in ("students", "groups", "settings")): raise ValueError("配置包缺少必要字段")
            StudentsConfig.instance().config_write = data["students"]; GroupsConfig.instance().config_write = data["groups"]; SettingsConfig.instance().config = data["settings"]
            StudentsConfig.instance().save_config(); GroupsConfig.instance().save_config(); SettingsConfig.instance().save_config(); return True
        except Exception as e:
            logger.exception(f"导入配置失败: {e}"); return False
