"""SQLite 数据库操作"""

import os
import json
from datetime import datetime
from typing import Optional

import aiosqlite

# 数据库文件路径
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "readbuddy.db")


async def get_db() -> aiosqlite.Connection:
    """获取数据库连接（确保目录和表已初始化）"""
    os.makedirs(DB_DIR, exist_ok=True)
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    """初始化数据库，创建所有表"""
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT DEFAULT '',
                cover_url TEXT DEFAULT '',
                description TEXT DEFAULT '',
                isbn TEXT DEFAULT '',
                categories TEXT DEFAULT '',
                status TEXT DEFAULT 'suggested',
                recommend_reason TEXT DEFAULT '',
                reject_reasons TEXT DEFAULT '[]',
                recommend_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                stars INTEGER DEFAULT 0,
                review TEXT DEFAULT '',
                created_at TEXT DEFAULT '',
                FOREIGN KEY (book_id) REFERENCES books(id)
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT DEFAULT '',
                tokens INTEGER DEFAULT 0,
                created_at TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY DEFAULT 1,
                api_base_url TEXT DEFAULT '',
                api_key TEXT DEFAULT '',
                model_name TEXT DEFAULT '',
                total_tokens_used INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY DEFAULT 1,
                buddy_name TEXT DEFAULT 'Read Buddy',
                greeting TEXT DEFAULT '',
                user_name TEXT DEFAULT ''
            );

            -- 确保 settings 和 profile 各有一条记录
            INSERT OR IGNORE INTO settings (id) VALUES (1);
            INSERT OR IGNORE INTO profile (id) VALUES (1);
        """)
        await db.commit()
    finally:
        await db.close()


def _now() -> str:
    """当前时间字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _row_to_dict(row: aiosqlite.Row) -> dict:
    """将 Row 转为 dict"""
    return dict(row) if row else None


# ========== 书籍操作 ==========

async def get_books_by_status(status: str) -> list[dict]:
    """按状态查询书籍"""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM books WHERE status = ? ORDER BY created_at DESC", (status,))
        rows = await cursor.fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        await db.close()


async def get_all_books() -> list[dict]:
    """查询所有书籍"""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM books ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        await db.close()


async def get_book(book_id: int) -> Optional[dict]:
    """查询单本书籍"""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        row = await cursor.fetchone()
        return _row_to_dict(row)
    finally:
        await db.close()


async def add_book(title: str, author: str = "", reason: str = "", status: str = "suggested") -> int:
    """添加书籍，返回 ID"""
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO books (title, author, recommend_reason, status, created_at) VALUES (?, ?, ?, ?, ?)",
            (title, author, reason, status, _now()),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def update_book_status(book_id: int, status: str, reject_reason: str = "") -> bool:
    """更新书籍状态。如有拒绝原因，追加到 reject_reasons 列表"""
    db = await get_db()
    try:
        if reject_reason:
            # 读取现有原因列表并追加
            cursor = await db.execute("SELECT reject_reasons FROM books WHERE id = ?", (book_id,))
            row = await cursor.fetchone()
            reasons = json.loads(row["reject_reasons"]) if row else []
            reasons.append({"reason": reject_reason, "date": _now()})
            await db.execute(
                "UPDATE books SET status = ?, reject_reasons = ? WHERE id = ?",
                (status, json.dumps(reasons, ensure_ascii=False), book_id),
            )
        else:
            await db.execute("UPDATE books SET status = ? WHERE id = ?", (status, book_id))
        await db.commit()
        return True
    finally:
        await db.close()


async def increment_recommend_count(book_id: int) -> int:
    """增加推荐次数，返回更新后的次数"""
    db = await get_db()
    try:
        await db.execute(
            "UPDATE books SET recommend_count = recommend_count + 1 WHERE id = ?",
            (book_id,),
        )
        await db.commit()
        cursor = await db.execute("SELECT recommend_count FROM books WHERE id = ?", (book_id,))
        row = await cursor.fetchone()
        return row["recommend_count"] if row else 0
    finally:
        await db.close()


async def update_book_details(book_id: int, **kwargs) -> bool:
    """更新书籍详情（cover_url, description, isbn, categories 等）"""
    db = await get_db()
    try:
        sets = []
        values = []
        for key in ("cover_url", "description", "isbn", "categories", "author"):
            if key in kwargs:
                sets.append(f"{key} = ?")
                values.append(kwargs[key])
        if not sets:
            return False
        values.append(book_id)
        await db.execute(f"UPDATE books SET {', '.join(sets)} WHERE id = ?", values)
        await db.commit()
        return True
    finally:
        await db.close()


# ========== 评价操作 ==========

async def add_rating(book_id: int, stars: int, review: str = "") -> int:
    """添加评价"""
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO ratings (book_id, stars, review, created_at) VALUES (?, ?, ?, ?)",
            (book_id, stars, review, _now()),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def get_ratings_for_book(book_id: int) -> Optional[dict]:
    """获取某本书的评价"""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM ratings WHERE book_id = ?", (book_id,))
        row = await cursor.fetchone()
        return _row_to_dict(row)
    finally:
        await db.close()


async def get_all_ratings() -> list[dict]:
    """获取所有评价"""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM ratings ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        await db.close()


# ========== 消息操作 ==========

async def add_message(role: str, content: str, tokens: int = 0) -> int:
    """添加消息"""
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO messages (role, content, tokens, created_at) VALUES (?, ?, ?, ?)",
            (role, content, tokens, _now()),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def get_recent_messages(limit: int = 20) -> list[dict]:
    """获取最近 N 条消息"""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM messages ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()
        # 按时间正序返回（最旧在前）
        return [_row_to_dict(r) for r in reversed(rows)]
    finally:
        await db.close()


async def get_message_count() -> int:
    """获取消息总数"""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM messages")
        row = await cursor.fetchone()
        return row["cnt"] if row else 0
    finally:
        await db.close()


# ========== 配置操作 ==========

async def get_settings() -> dict:
    """获取配置"""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM settings WHERE id = 1")
        row = await cursor.fetchone()
        return _row_to_dict(row)
    finally:
        await db.close()


async def update_settings(**kwargs) -> bool:
    """更新配置"""
    db = await get_db()
    try:
        sets = []
        values = []
        for key in ("api_base_url", "api_key", "model_name"):
            if key in kwargs:
                sets.append(f"{key} = ?")
                values.append(kwargs[key])
        if not sets:
            return False
        values.append(1)
        await db.execute(f"UPDATE settings SET {', '.join(sets)} WHERE id = ?", values)
        await db.commit()
        return True
    finally:
        await db.close()


async def add_token_usage(tokens: int):
    """累加 Token 用量"""
    db = await get_db()
    try:
        await db.execute("UPDATE settings SET total_tokens_used = total_tokens_used + ? WHERE id = 1", (tokens,))
        await db.commit()
    finally:
        await db.close()


# ========== 个性化偏好操作 ==========

async def get_profile() -> dict:
    """获取个性化偏好"""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM profile WHERE id = 1")
        row = await cursor.fetchone()
        return _row_to_dict(row)
    finally:
        await db.close()


async def update_profile(**kwargs) -> bool:
    """更新个性化偏好"""
    db = await get_db()
    try:
        sets = []
        values = []
        for key in ("buddy_name", "greeting", "user_name"):
            if key in kwargs:
                sets.append(f"{key} = ?")
                values.append(kwargs[key])
        if not sets:
            return False
        values.append(1)
        await db.execute(f"UPDATE profile SET {', '.join(sets)} WHERE id = ?", values)
        await db.commit()
        return True
    finally:
        await db.close()


# ========== 导出/导入 ==========

async def export_all() -> dict:
    """导出全部数据（不含 API Key）"""
    settings = await get_settings()
    # 脱敏：移除 api_key
    safe_settings = {k: v for k, v in settings.items() if k != "api_key"}
    return {
        "version": "1.0",
        "export_date": _now(),
        "books": await get_all_books(),
        "ratings": await get_all_ratings(),
        "messages": await get_recent_messages(limit=9999),
        "settings": safe_settings,
        "profile": await get_profile(),
    }


async def import_all(data: dict) -> dict:
    """导入数据（覆盖），返回统计"""
    db = await get_db()
    try:
        # 清空所有表
        for table in ("ratings", "messages", "books"):
            await db.execute(f"DELETE FROM {table}")

        imported = {"books": 0, "ratings": 0, "messages": 0}

        # 导入书籍
        for book in data.get("books", []):
            await db.execute(
                """INSERT INTO books (id, title, author, cover_url, description, isbn,
                   categories, status, recommend_reason, reject_reasons, recommend_count, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (book.get("id"), book.get("title", ""), book.get("author", ""),
                 book.get("cover_url", ""), book.get("description", ""), book.get("isbn", ""),
                 book.get("categories", ""), book.get("status", "suggested"),
                 book.get("recommend_reason", ""), book.get("reject_reasons", "[]"),
                 book.get("recommend_count", 0), book.get("created_at", "")),
            )
            imported["books"] += 1

        # 导入评价
        for rating in data.get("ratings", []):
            await db.execute(
                "INSERT INTO ratings (id, book_id, stars, review, created_at) VALUES (?, ?, ?, ?, ?)",
                (rating.get("id"), rating.get("book_id"), rating.get("stars", 0),
                 rating.get("review", ""), rating.get("created_at", "")),
            )
            imported["ratings"] += 1

        # 导入消息
        for msg in data.get("messages", []):
            await db.execute(
                "INSERT INTO messages (id, role, content, tokens, created_at) VALUES (?, ?, ?, ?, ?)",
                (msg.get("id"), msg.get("role"), msg.get("content", ""),
                 msg.get("tokens", 0), msg.get("created_at", "")),
            )
            imported["messages"] += 1

        # 导入配置（不含 api_key）
        settings = data.get("settings", {})
        if settings:
            await db.execute(
                "UPDATE settings SET api_base_url = ?, model_name = ?, total_tokens_used = ? WHERE id = 1",
                (settings.get("api_base_url", ""), settings.get("model_name", ""),
                 settings.get("total_tokens_used", 0)),
            )

        # 导入个性化偏好
        profile = data.get("profile", {})
        if profile:
            await db.execute(
                "UPDATE profile SET buddy_name = ?, greeting = ?, user_name = ? WHERE id = 1",
                (profile.get("buddy_name", "Read Buddy"), profile.get("greeting", ""),
                 profile.get("user_name", "")),
            )

        await db.commit()
        return imported
    finally:
        await db.close()


async def clear_all():
    """清空所有数据（保留表结构和 settings/profile 的默认行）"""
    db = await get_db()
    try:
        for table in ("ratings", "messages", "books"):
            await db.execute(f"DELETE FROM {table}")
        await db.execute("UPDATE settings SET total_tokens_used = 0 WHERE id = 1")
        await db.commit()
    finally:
        await db.close()
