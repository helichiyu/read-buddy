"""工具注册器 - 自动发现和加载所有工具模块"""

import importlib
import pkgutil
from typing import Dict
from .base import BaseTool

# 工具注册表：name → 实例
_registry: Dict[str, BaseTool] = {}


def _auto_discover():
    """自动发现 tools/ 目录下的所有工具模块"""
    import tools as pkg
    for _, name, _ in pkgutil.iter_modules(pkg.__path__):
        if name.startswith("_") or name == "base":
            continue
        module = importlib.import_module(f"tools.{name}")
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type)
                    and issubclass(attr, BaseTool)
                    and attr is not BaseTool):
                instance = attr()
                _registry[instance.name] = instance


def get_all_tools() -> list[BaseTool]:
    """获取所有已注册的工具实例"""
    if not _registry:
        _auto_discover()
    return list(_registry.values())


def get_tool(name: str) -> BaseTool | None:
    """按名称获取工具"""
    if not _registry:
        _auto_discover()
    return _registry.get(name)


def get_openai_tools() -> list[dict]:
    """获取 OpenAI Function Calling 格式的工具列表"""
    return [t.to_openai_tool() for t in get_all_tools()]
