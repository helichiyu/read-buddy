"""工具基类 - 所有工具必须继承并实现 schema 和 handler"""

from abc import ABC, abstractmethod


class BaseTool(ABC):
    """工具基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述（AI 看到的说明）"""
        ...

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """JSON Schema 格式的参数定义"""
        ...

    def to_openai_tool(self) -> dict:
        """转换为 OpenAI Function Calling 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": self._required_params,
                },
            },
        }

    @property
    def _required_params(self) -> list[str]:
        """必填参数列表，子类可覆盖"""
        return []

    @abstractmethod
    async def handle(self, args: dict, context: dict) -> dict:
        """
        执行工具逻辑

        Args:
            args: AI 传来的参数（已解析为 dict）
            context: 上下文，包含 books_changed 列表

        Returns:
            dict: 返回给 AI 的结果
        """
        ...
