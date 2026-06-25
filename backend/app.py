"""FastAPI 应用 - 路由定义"""

import os

from fastapi import FastAPI, Body
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import database as db

app = FastAPI(title="Read Buddy")


def _today() -> str:
    """返回今天的日期字符串 YYYYMMDD"""
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d")

from paths import resource_dir

# 静态文件目录（兼容打包和开发两种模式）
FRONTEND_DIR = resource_dir() / "frontend"


# ========== 启动时初始化数据库 ==========

@app.on_event("startup")
async def startup():
    await db.init_db()


@app.on_event("shutdown")
async def shutdown():
    await db.close_db()


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
    """核心对话接口：委托 chat_orchestrator 完成工具调用循环"""
    from chat_orchestrator import run_chat
    user_content = data.get("content", "")
    if not user_content:
        return {"error": "消息不能为空"}
    return await run_chat(user_content)


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


@app.delete("/api/data")
async def clear_data():
    """清空所有数据"""
    await db.clear_all()
    return {"ok": True}


# ========== 静态文件（前端）==========

if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
