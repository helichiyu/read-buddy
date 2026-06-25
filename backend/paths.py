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
    """可写数据目录（打包后为 EXE 同级 data/，开发态为项目根 data/）"""
    if is_frozen():
        return Path(os.path.dirname(sys.executable)) / "data"
    return resource_dir() / "data"
