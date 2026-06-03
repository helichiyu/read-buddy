"""接受推荐工具"""

import database as db
from .base import BaseTool


class AcceptBookTool(BaseTool):
    @property
    def name(self) -> str:
        return "accept_book"

    @property
    def description(self) -> str:
        return "用户接受了推荐，愿意把这本书加入待阅读列表"

    @property
    def parameters(self) -> dict:
        return {
            "book_title": {"type": "string", "description": "书名"},
            "author": {"type": "string", "description": "作者"},
            "reason": {"type": "string", "description": "推荐原因"},
            "series_name": {"type": "string", "description": "系列名称，单本不填"},
            "series_index": {"type": "integer", "description": "系列序号，单本不填"},
        }

    @property
    def _required_params(self) -> list[str]:
        return ["book_title", "author"]

    async def handle(self, args: dict, context: dict) -> dict:
        title = args.get("book_title", "")
        author = args.get("author", "")
        reason = args.get("reason", "")
        series_name = args.get("series_name", "")
        series_index = args.get("series_index", 0)

        book_id = await db.add_book(
            title=title, author=author, reason=reason, status="pending",
            series_name=series_name, series_index=series_index,
        )

        # 尝试获取书籍详情
        try:
            from book_service import search as search_book
            query = f"{title} {author}".strip()
            book_info = await search_book(query)
            if book_info:
                await db.update_book_details(
                    book_id,
                    cover_url=book_info.get("cover_url", ""),
                    description=book_info.get("description", ""),
                    isbn=book_info.get("isbn", ""),
                    categories=book_info.get("categories", ""),
                    author=book_info.get("author", "") or author,
                )
        except Exception:
            pass

        book = await db.get_book(book_id)
        context["books_changed"].append({"action": "accepted", **book})
        return {"ok": True, "message": f"《{title}》已加入待阅读列表"}
