"""FastAPI 应用 - 路由定义"""

import os
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Body
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import database as db

app = FastAPI(title="Read Buddy")


def _today() -> str:
    """返回今天的日期字符串 YYYYMMDD"""
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d")

# 静态文件目录（兼容打包和开发两种模式）
import sys
if getattr(sys, "frozen", False):
    # PyInstaller 打包后，frontend 在 _MEIPASS/frontend
    FRONTEND_DIR = Path(sys._MEIPASS) / "frontend"
else:
    FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


# ========== 启动时初始化数据库 ==========

@app.on_event("startup")
async def startup():
    await db.init_db()


# ========== 书籍 API ==========

@app.get("/api/books/pending")
async def get_pending_books():
    """获取待阅读书籍（侧边栏展示）"""
    books = await db.get_books_by_status("pending")
    return books


@app.get("/api/books/rated")
async def get_rated_books():
    """获取已评价书籍"""
    books = await db.get_books_by_status("rated")
    return books


@app.get("/api/books/not-interested")
async def get_not_interested_books():
    """获取不想看的书籍（含拒绝原因）"""
    books = await db.get_books_by_status("not_interested")
    return books


@app.post("/api/books")
async def add_book(data: dict = Body(...)):
    """添加书籍"""
    book_id = await db.add_book(
        title=data.get("title", ""),
        author=data.get("author", ""),
        reason=data.get("reason", ""),
        status=data.get("status", "suggested"),
    )
    book = await db.get_book(book_id)
    return book


@app.put("/api/books/{book_id}/status")
async def update_book_status(book_id: int, data: dict = Body(...)):
    """更新书籍状态"""
    status = data.get("status", "")
    reject_reason = data.get("reject_reason", "")
    await db.update_book_status(book_id, status, reject_reason)
    # 如果是重新推荐，增加推荐计数
    if status == "suggested":
        await db.increment_recommend_count(book_id)
    book = await db.get_book(book_id)
    return book


@app.post("/api/books/{book_id}/rate")
async def rate_book(book_id: int, data: dict = Body(...)):
    """评价书籍"""
    stars = data.get("stars", 0)
    review = data.get("review", "")
    await db.add_rating(book_id, stars, review)
    await db.update_book_status(book_id, "rated")
    rating = await db.get_ratings_for_book(book_id)
    return {"rating": rating, "book_id": book_id}


# ========== 消息 API ==========

@app.get("/api/messages/recent")
async def get_recent_messages(limit: int = 20):
    """获取最近 N 条对话"""
    messages = await db.get_recent_messages(limit)
    return messages


@app.post("/api/chat")
async def chat(data: dict = Body(...)):
    """
    核心对话接口：
    1. 接收用户消息
    2. 构建上下文（System Prompt + 最近 20 条消息）
    3. 调用 AI（带 Function Calling 工具）
    4. 处理工具调用（评价/推荐/接受/拒绝/聊书）
    5. 返回 AI 回复 + 变更数据
    """
    user_content = data.get("content", "")
    if not user_content:
        return {"error": "消息不能为空"}

    # 检查 AI 配置
    from ai_service import get_ai_service, build_system_prompt, TOOLS
    ai = await get_ai_service()
    if not ai:
        return {
            "reply": "请先在设置中配置 AI 的 API 信息（API Base URL、API Key、模型名称），然后就可以开始聊天了！点击右上角的 ⚙️ 按钮。",
            "tokens": 0,
            "books_changed": [],
        }

    # 存储用户消息
    await db.add_message("user", user_content)

    # 构建上下文
    system_prompt = await build_system_prompt()
    recent_messages = await db.get_recent_messages(limit=20)

    # 构建发送给 AI 的消息列表（不含刚存入的用户消息，因为 recent_messages 已包含）
    chat_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in recent_messages
    ]

    # 调用 AI（可能需要多轮处理工具调用）
    books_changed = []
    total_tokens = 0
    max_rounds = 5  # 最多处理 5 轮工具调用

    for _ in range(max_rounds):
        message, tokens = await ai.chat(chat_messages, system_prompt, tools=TOOLS)
        total_tokens += tokens

        # 如果没有工具调用，直接返回
        if not message.tool_calls:
            break

        # 将 AI 回复加入上下文
        chat_messages.append({"role": "assistant", "content": message.content or "", "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in message.tool_calls
        ]})

        # 处理每个工具调用
        for tc in message.tool_calls:
            import json as _json
            args = _json.loads(tc.function.arguments)
            result = await _handle_tool_call(tc.function.name, args, books_changed)
            # 将工具结果回传给 AI
            chat_messages.append({"role": "tool", "tool_call_id": tc.id, "content": _json.dumps(result, ensure_ascii=False)})

    # 存储 AI 回复
    reply_text = message.content or ""
    await db.add_message("assistant", reply_text, total_tokens)
    await db.add_token_usage(total_tokens)

    return {
        "reply": reply_text,
        "tokens": total_tokens,
        "books_changed": books_changed,
    }


async def _handle_tool_call(name: str, args: dict, books_changed: list) -> dict:
    """处理单个工具调用，返回结果给 AI"""
    if name == "rate_book":
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
                await db.update_book_details(book_id, series_name=series_name, series_index=series_index)
        else:
            book_id = await db.add_book(title=title, author=author, status="rated", series_name=series_name, series_index=series_index)
        # 尝试从豆瓣获取详情（封面、简介等）
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
        books_changed.append({"action": "rated", **book})
        return {"ok": True, "message": f"已记录《{title}》的评价：{stars}星"} await db.add_book(title=title, author=author, status="rated", series_name=series_name, series_index=series_index)
        await db.add_rating(book_id, stars, review)
        books_changed.append({"action": "rated", "title": title, "stars": stars})
        return {"ok": True, "message": f"已记录《{title}》的评价：{stars}星"}

    elif name == "recommend_books":
        books = args.get("books", [])
        for b in books:
            books_changed.append({
                "action": "recommended",
                "title": b.get("title", ""),
                "author": b.get("author", ""),
                "reason": b.get("reason", ""),
                "series_name": b.get("series_name", ""),
                "series_index": b.get("series_index", 0),
            })
        return {"ok": True, "message": f"已推荐 {len(books)} 本书，等待用户回应"}

    elif name == "accept_book":
        title = args.get("book_title", "")
        author = args.get("author", "")
        reason = args.get("reason", "")
        series_name = args.get("series_name", "")
        series_index = args.get("series_index", 0)
        book_id = await db.add_book(title=title, author=author, reason=reason, status="pending", series_name=series_name, series_index=series_index)
        # 尝试从 Google Books 获取详情（封面、简介等）
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
        book = await db.get_book(book_id)
        books_changed.append({"action": "accepted", **book})
        return {"ok": True, "message": f"《{title}》已加入待阅读列表"}

    elif name == "reject_book":
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
            books_changed.append({"action": "rejected", "title": title})
            return {"ok": True, "message": f"已记录《{title}》的拒绝原因：{reason}"}
        else:
            # 书籍不在数据库中，创建一条记录
            book_id = await db.add_book(title=title, status="not_interested")
            await db.update_book_status(book_id, "not_interested", reason)
            books_changed.append({"action": "rejected", "title": title})
            return {"ok": True, "message": f"已记录《{title}》的拒绝原因：{reason}"}

    elif name == "discuss_book":
        title = args.get("book_title", "")
        topic = args.get("topic", "")
        books_changed.append({"action": "discuss", "title": title, "topic": topic})
        return {"ok": True, "message": f"开始聊《{title}》"}

    elif name == "save_preference":
        category = args.get("category", "其他个性化要求")
        content = args.get("content", "")
        if content:
            from preferences import append_preference
            append_preference(category, content)
            return {"ok": True, "message": f"已保存偏好：{content}"}
        return {"ok": False, "message": "偏好内容为空"}

    return {"ok": False, "message": "未知操作"}


# ========== 配置 API ==========

@app.get("/api/settings")
async def get_settings():
    """获取配置（API Key 脱敏）"""
    settings = await db.get_settings()
    # 脱敏：只显示 key 的前 4 位
    if settings.get("api_key"):
        key = settings["api_key"]
        settings["api_key"] = key[:4] + "****" if len(key) > 4 else "****"
    return settings


@app.put("/api/settings")
async def update_settings(data: dict = Body(...)):
    """更新配置"""
    await db.update_settings(**data)
    return {"ok": True}


@app.post("/api/settings/test")
async def test_connection(data: dict = Body(...)):
    """测试 AI API 连接"""
    api_url = data.get("api_base_url", "")
    api_key = data.get("api_key", "")
    model = data.get("model_name", "")
    if not api_url or not api_key or not model:
        return {"ok": False, "error": "请填写完整的 API 配置"}
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(base_url=api_url, api_key=api_key)
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "你好"}],
            max_tokens=10,
        )
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ========== 个性化偏好 API ==========

@app.get("/api/profile")
async def get_profile():
    """获取个性化偏好"""
    profile = await db.get_profile()
    return profile


@app.put("/api/profile")
async def update_profile(data: dict = Body(...)):
    """更新个性化偏好"""
    await db.update_profile(**data)
    return {"ok": True}


# ========== Token 统计 ==========

@app.get("/api/token-usage")
async def get_token_usage():
    """获取 Token 使用统计"""
    settings = await db.get_settings()
    return {"total": settings.get("total_tokens_used", 0)}


# ========== 存档 API ==========

@app.get("/api/export")
async def export_data():
    """导出全部数据为 JSON（返回数据，前端下载用）"""
    data = await db.export_all()
    return data


@app.post("/api/export-to-file")
async def export_to_file():
    """弹出 Windows 原生保存对话框，导出数据到用户选择的路径"""
    import tkinter as tk
    from tkinter import filedialog
    import json

    data = await db.export_all()
    json_str = json.dumps(data, ensure_ascii=False, indent=2)

    # 在主线程外弹对话框（用临时隐藏窗口）
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    filepath = filedialog.asksaveasfilename(
        parent=root,
        title="导出 Read Buddy 存档",
        defaultextension=".json",
        filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
        initialfile=f"readbuddy_backup_{_today()}.json",
    )
    root.destroy()

    if not filepath:
        return {"ok": False, "message": "用户取消"}

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(json_str)

    return {
        "ok": True,
        "message": f"已导出到 {filepath}",
        "path": filepath,
        "books": len(data.get("books", [])),
        "ratings": len(data.get("ratings", [])),
        "messages": len(data.get("messages", [])),
    }


@app.post("/api/import-from-file")
async def import_from_file():
    """弹出 Windows 原生打开对话框，从用户选择的文件导入"""
    import tkinter as tk
    from tkinter import filedialog
    import json

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    filepath = filedialog.askopenfilename(
        parent=root,
        title="导入 Read Buddy 存档",
        filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
    )
    root.destroy()

    if not filepath:
        return {"ok": False, "message": "用户取消"}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        data = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return {"ok": False, "message": f"文件读取失败：{e}"}

    if "version" not in data:
        return {"ok": False, "message": "无效的备份文件格式（缺少 version 字段）"}

    result = await db.import_all(data)
    result["ok"] = True
    result["path"] = filepath
    return result


@app.post("/api/import")
async def import_data(file: UploadFile = File(...)):
    """从 JSON 文件导入数据"""
    import json
    content = await file.read()
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return {"error": "无效的 JSON 文件"}
    if "version" not in data:
        return {"error": "无效的备份文件格式"}
    result = await db.import_all(data)
    return result


@app.delete("/api/data")
async def clear_data():
    """清空所有数据"""
    await db.clear_all()
    return {"ok": True}


# ========== 静态文件（前端）==========

if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
