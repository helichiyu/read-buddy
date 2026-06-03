"""拒绝推荐工具"""

import database as db
from .base import BaseTool


class RejectBookTool(BaseTool):
    @property
    def name(self) -> str:
        return "reject_book"

    @property
    def description(self) -> str:
        return "用户表示不想看某本推荐的书"

    @property
    def parameters(self) -> dict:
        return {
            "book_title": {"type": "string", "description": "书名"},
            "reason": {"type": "string", "description": "不想看的原因"},
        }

    @property
    def _required_params(self) -> list[str]:
        return ["book_title", "reason"]

    async def handle(self, args: dict, context: dict) -> dict:
        title = args.get("book_title", "")
        reason = args.get("reason", "")

        # 查找这本书
        all_books = await db.get_all_books()
        target = None
        for b in all_books:
            if b["title"] == title:
                target = b
                break

        if target:
            await db.update_book_status(target["id"], "not_interested", reason)
        else:
            # 书籍不在数据库中，创建一条记录
            book_id = await db.add_book(title=title, status="not_interested")
            await db.update_book_status(book_id, "not_interested", reason)

        context["books_changed"].append({"action": "rejected", "title": title})
        return {"ok": True, "message": f"已记录《{title}》的拒绝原因：{reason}"}
