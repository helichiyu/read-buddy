"""推荐书籍工具"""

from .base import BaseTool


class RecommendBooksTool(BaseTool):
    @property
    def name(self) -> str:
        return "recommend_books"

    @property
    def description(self) -> str:
        return "向用户推荐书籍（推荐先在聊天区展示，用户接受后才入库）"

    @property
    def parameters(self) -> dict:
        return {
            "books": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "书名"},
                        "author": {"type": "string", "description": "作者"},
                        "reason": {"type": "string", "description": "推荐原因（不剧透）"},
                        "series_name": {"type": "string", "description": "系列名称，单本不填"},
                        "series_index": {"type": "integer", "description": "系列序号，单本不填"},
                    },
                    "required": ["title", "author", "reason"],
                },
            },
        }

    @property
    def _required_params(self) -> list[str]:
        return ["books"]

    async def handle(self, args: dict, context: dict) -> dict:
        books = args.get("books", [])
        for b in books:
            context["books_changed"].append({
                "action": "recommended",
                "title": b.get("title", ""),
                "author": b.get("author", ""),
                "reason": b.get("reason", ""),
                "series_name": b.get("series_name", ""),
                "series_index": b.get("series_index", 0),
            })
        return {"ok": True, "message": f"已推荐 {len(books)} 本书，等待用户回应"}
