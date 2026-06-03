"""保存用户偏好工具"""

from .base import BaseTool


class SavePreferenceTool(BaseTool):
    @property
    def name(self) -> str:
        return "save_preference"

    @property
    def description(self) -> str:
        return (
            "保存用户的阅读偏好或个性化要求（如喜欢的类型、不喜欢的风格、特殊要求等），"
            "后续对话会自动读取"
        )

    @property
    def parameters(self) -> dict:
        return {
            "category": {"type": "string", "description": "偏好分类：阅读偏好 / 不喜欢的 / 其他个性化要求"},
            "content": {"type": "string", "description": "具体的偏好内容"},
        }

    @property
    def _required_params(self) -> list[str]:
        return ["category", "content"]

    async def handle(self, args: dict, context: dict) -> dict:
        category = args.get("category", "其他个性化要求")
        content = args.get("content", "")
        if content:
            from preferences import append_preference
            append_preference(category, content)
            return {"ok": True, "message": f"已保存偏好：{content}"}
        return {"ok": False, "message": "偏好内容为空"}
