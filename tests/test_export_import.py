"""导入导出往返测试"""

import pytest


async def test_export_structure_and_desensitize(fresh_db):
    """导出结构正确，且 api_key 被脱敏（不包含在导出数据中）"""
    bid = await fresh_db.add_book(title="三体", author="刘慈欣", status="rated")
    await fresh_db.add_rating(bid, 5, "震撼")

    exported = await fresh_db.export_all()
    assert exported["version"] == "1.0"
    assert len(exported["books"]) == 1
    # 安全关键：导出数据不得包含 api_key
    assert "api_key" not in exported["settings"]


async def test_import_roundtrip(fresh_db):
    """导出 → 清空 → 导入，books/ratings/messages 数量与内容一致"""
    bid = await fresh_db.add_book(title="三体", author="刘慈欣", status="rated")
    await fresh_db.add_rating(bid, 5, "震撼")
    await fresh_db.add_message("user", "我读了三体")

    exported = await fresh_db.export_all()

    # 清空后确认库为空
    await fresh_db.clear_all()
    assert len(await fresh_db.get_all_books()) == 0

    # 重新导入
    result = await fresh_db.import_all(exported)
    assert result["books"] == 1
    assert result["ratings"] == 1
    assert result["messages"] == 1

    # 内容一致
    books = await fresh_db.get_all_books()
    assert books[0]["title"] == "三体"
    assert books[0]["status"] == "rated"


async def test_import_failure_rolls_back_partial_changes(fresh_db):
    """导入中途失败时，不留下清空表或部分插入的未提交事务"""
    original_id = await fresh_db.add_book(title="Original", author="Author", status="rated")

    broken_data = {
        "books": [
            {"id": original_id + 1, "title": "Imported"},
            {"id": original_id + 2, "title": None},
        ],
        "ratings": [],
        "messages": [],
        "settings": {},
        "profile": {},
    }

    with pytest.raises(Exception):
        await fresh_db.import_all(broken_data)

    # A later commit should not accidentally persist the failed import transaction.
    await fresh_db.add_message("user", "after failed import")
    books = await fresh_db.get_all_books()
    assert [book["title"] for book in books] == ["Original"]


async def test_message_auto_cleanup_threshold(fresh_db):
    """消息数超过 200 时触发清理，保留最近 100 条（清理在 cnt>200 的那次插入时执行一次）"""
    for i in range(201):
        await fresh_db.add_message("user", f"消息 {i}")
    # 第 201 条触发清理：201 → 100
    msgs = await fresh_db.get_recent_messages(limit=9999)
    assert len(msgs) == 100
    # 保留的是最近 100 条（消息 101~200），更早的已被清理
    contents = [m["content"] for m in msgs]
    assert "消息 200" in contents
    assert "消息 100" not in contents
