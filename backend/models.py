"""数据模型定义"""

from pydantic import BaseModel


class Book(BaseModel):
    """书籍记录"""
    id: int = 0
    title: str = ""
    author: str = ""
    cover_url: str = ""
    description: str = ""
    isbn: str = ""
    categories: str = ""
    series_name: str = ""   # 系列名称（如"三体"、"哈利·波特"）
    series_index: int = 0   # 系列中的序号（1=第一部，2=第二部）
    # 状态：suggested（推荐中）| pending（待阅读）| rated（已评价）| not_interested（不想看）
    status: str = "suggested"
    recommend_reason: str = ""
    # 拒绝原因列表（JSON 数组，支持多次追加）
    # 格式：[{"reason": "太厚了", "date": "2026-06-02"}, ...]
    reject_reasons: str = "[]"
    recommend_count: int = 0  # 已推荐次数（同一本书，上限 3 次）
    created_at: str = ""


class Rating(BaseModel):
    """评价记录"""
    id: int = 0
    book_id: int = 0
    stars: int = 0       # 1-5 星
    review: str = ""     # 文字评价
    created_at: str = ""


class Message(BaseModel):
    """对话消息"""
    id: int = 0
    role: str = ""       # 'user' | 'assistant'
    content: str = ""
    tokens: int = 0      # 本次消耗 token（仅 assistant 消息记录）
    created_at: str = ""


class Settings(BaseModel):
    """用户配置"""
    id: int = 1
    api_base_url: str = ""
    api_key: str = ""
    model_name: str = ""
    total_tokens_used: int = 0


class Profile(BaseModel):
    """用户个性化偏好"""
    id: int = 1
    buddy_name: str = "Read Buddy"
    greeting: str = ""
    user_name: str = ""
