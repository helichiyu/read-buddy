"""测试公共配置"""

import os
import sys

# 让测试能导入 backend 下的模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest_asyncio


@pytest_asyncio.fixture
async def fresh_db(tmp_path):
    """每个测试使用独立的临时数据库，互不污染真实 data/。

    单连接改造后，database 用模块级 _db 单例与 DB_PATH 全局；
    这里覆盖 DB_PATH 指向临时目录并重置 _db，测试结束关闭连接。
    """
    import database as db
    db.DB_DIR = str(tmp_path)
    db.DB_PATH = str(tmp_path / "test.db")
    db._db = None
    await db.init_db()
    yield db
    await db.close_db()
    db._db = None
