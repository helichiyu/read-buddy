"""路径工具 - 统一开发态与打包态的路径判断"""

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    """是否运行在 PyInstaller 打包环境"""
    return getattr(sys, "frozen", False)


def resource_dir() -> Path:
    """只读资源目录（打包后为 _MEIPASS，开发态为项目根）"""
    if is_frozen():
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    """可写数据目录（打包后为 %APPDATA%/ReadBuddy，开发态为项目根 data/）"""
    if is_frozen():
        # 安装目录（如 Program Files）普通用户无写权限，
        # 数据放系统标准可写位置 %APPDATA%/ReadBuddy
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / "ReadBuddy"
        return Path.home() / ".readbuddy"  # APPDATA 缺失的极少见兜底
    return resource_dir() / "data"
