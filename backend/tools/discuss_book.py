"""聊书工具"""

from .base import BaseTool


class DiscussBookTool(BaseTool):
    @property
    def name(self) -> str:
        return "discuss_book"

    @property
    def description(self) -> str:
        return "用户想聊某本书（点击了书架卡片或主动提出），进入聊书模式"

    @property
    def parameters(self) -> dict:
        return {
            "book_title": {"type": "string", "description": "书名"},
            "topic": {"type": "string", "description": "聊天话题：background（背景/作者）、reviews（网上评价）、related（相关推荐）等"},
        }

    @property
    def _required_params(self) -> list[str]:
        return ["book_title"]

    async def handle(self, args: dict, context: dict) -> dict:
        title = args.get("book_title", "")
        topic = args.get("topic", "")
        context["books_changed"].append({
            "action": "discuss", "title": title, "topic": topic
        })
        return {"ok": True, "message": f"开始聊《{title}》"}
