"""书籍状态机测试 - 状态流转、推荐计数、拒绝原因"""

import json


async def test_status_transition(fresh_db):
    """pending → rated 状态流转"""
    bid = await fresh_db.add_book(title="三体", author="刘慈欣", status="pending")
    b = await fresh_db.get_book(bid)
    assert b["status"] == "pending"

    await fresh_db.update_book_status(bid, "rated")
    b = await fresh_db.get_book(bid)
    assert b["status"] == "rated"


async def test_recommend_count_increments(fresh_db):
    """推荐次数递增，返回值正确"""
    bid = await fresh_db.add_book(title="三体", author="刘慈欣", status="suggested")
    n1 = await fresh_db.increment_recommend_count(bid)
    n2 = await fresh_db.increment_recommend_count(bid)
    n3 = await fresh_db.increment_recommend_count(bid)
    assert (n1, n2, n3) == (1, 2, 3)


async def test_reject_reasons_append(fresh_db):
    """拒绝原因以 JSON 数组追加，支持多次记录"""
    bid = await fresh_db.add_book(title="三体", author="刘慈欣", status="pending")
    await fresh_db.update_book_status(bid, "not_interested", "太厚了")
    await fresh_db.update_book_status(bid, "not_interested", "没时间")

    b = await fresh_db.get_book(bid)
    reasons = json.loads(b["reject_reasons"])
    assert [r["reason"] for r in reasons] == ["太厚了", "没时间"]


async def test_rating_added(fresh_db):
    """评价写入并正确关联书籍"""
    bid = await fresh_db.add_book(title="三体", author="刘慈欣", status="rated")
    await fresh_db.add_rating(bid, 5, "震撼")
    rating = await fresh_db.get_ratings_for_book(bid)
    assert rating["stars"] == 5
    assert rating["review"] == "震撼"
