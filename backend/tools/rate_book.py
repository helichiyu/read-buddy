"""评价书籍工具"""

import database as db
from .base import BaseTool


class RateBookTool(BaseTool):
    @property
    def name(self) -> str:
        return "rate_book"

    @property
    def description(self) -> str:
        return "用户对一本书做出了评价（包含星级和/或文字评价）"

    @property
    def parameters(self) -> dict:
        return {
            "book_title": {"type": "string", "description": "书名"},
            "author": {"type": "string", "description": "作者"},
            "stars": {"type": "integer", "description": "星级评分 1-5"},
            "review": {"type": "string", "description": "用户的文字评价"},
            "series_name": {"type": "string", "description": "系列名称，单本不填"},
            "series_index": {"type": "integer", "description": "系列序号，单本不填"},
        }

    @property
    def _required_params(self) -> list[str]:
        return ["book_title", "stars"]

    async def handle(self, args: dict, context: dict) -> dict:
        title = args.get("book_title", "")
        stars = args.get("stars", 0)
        review = args.get("review", "")
        author = args.get("author", "")
        series_name = args.get("series_name", "")
        series_index = args.get("series_index", 0)

        # 查找是否已有同名书籍
        all_books = await db.get_all_books()
        existing = None
        for b in all_books:
            if b["title"] == title and b.get("series_index", 0) == series_index:
                existing = b
                break

        if existing:
            # 已存在，更新状态为 rated 并添加评价
            book_id = existing["id"]
            await db.update_book_status(book_id, "rated")
            if author and not existing.get("author"):
                await db.update_book_details(book_id, author=author)
            if series_name and not existing.get("series_name"):
                await db.update_book_details(
                    book_id, series_name=series_name, series_index=series_index
                )
        else:
            book_id = await db.add_book(
                title=title, author=author, status="rated",
                series_name=series_name, series_index=series_index,
            )

        # 尝试获取书籍详情（封面、简介等）
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
            pass  # API 失败不影响主流程

        await db.add_rating(book_id, stars, review)
        book = await db.get_book(book_id)
        context["books_changed"].append({"action": "rated", **book})
        return {"ok": True, "message": f"已记录《{title}》的评价：{stars}星"}
