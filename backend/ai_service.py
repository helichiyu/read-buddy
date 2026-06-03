"""AI 服务封装 - 统一 OpenAI 兼容接口"""

import json
from typing import Optional

from openai import AsyncOpenAI

import database as db


# ========== System Prompt 构建 ==========

async def build_system_prompt() -> str:
    """根据数据库中的上下文信息动态构建 System Prompt"""
    profile = await db.get_profile()
    buddy_name = profile.get("buddy_name", "Read Buddy") or "Read Buddy"
    user_name = profile.get("user_name", "")
    greeting = profile.get("greeting", "")

    # 读取用户偏好文件
    from preferences import get_preferences
    user_prefs = get_preferences()

    # 构建已读书籍摘要
    rated_books = await db.get_books_by_status("rated")
    rated_summary = ""
    for b in rated_books:
        series = f"【{b['series_name']}第{b['series_index']}部】" if b.get("series_name") else ""
        rated_summary += f"- {series}{b['title']}（{b['author']}）\n"

    # 构建待阅读列表
    pending_books = await db.get_books_by_status("pending")
    pending_summary = ""
    for b in pending_books:
        series = f"【{b['series_name']}第{b['series_index']}部】" if b.get("series_name") else ""
        pending_summary += f"- {series}{b['title']}（{b['author']}）推荐原因：{b['recommend_reason']}\n"

    # 构建拒绝列表
    not_interested = await db.get_books_by_status("not_interested")
    rejected_summary = ""
    for b in not_interested:
        reasons = json.loads(b.get("reject_reasons", "[]"))
        reasons_text = "；".join([r["reason"] for r in reasons])
        rejected_summary += f"- {b['title']}（已推荐{b['recommend_count']}次，拒绝原因：{reasons_text}）\n"

    prompt = f"""你是 {buddy_name}，一个友好热情的阅读伙伴。"""
    if user_name:
        prompt += f"\n称呼用户为「{user_name}」。"

    prompt += """

## ⚠️ 工具调用自检（每次回复必须遵守）

每次生成回复后，你必须自问：我的回复是否涉及以下操作？

| 如果你说/做了... | 必须调用的工具 |
|---|---|
| 确认了用户的评价、打分 | `rate_book` |
| 推荐了具体书籍 | `recommend_books` |
| 确认用户接受了推荐 | `accept_book` |
| 记录用户不想看某本书 | `reject_book` |
| 开始聊某本书的背景/作者 | `discuss_book` |
| 确认记住用户的偏好要求 | `save_preference` |

- 如果涉及任何操作 → **必须调用对应工具**，不能只在文字里说"已记录"
- 如果只是纯聊天（问候、追问、讨论）→ 不调用工具，完全正常
- 可以同时调用多个工具（比如推荐书的同时保存偏好）
"""

    prompt += f"""

## 绝对规则（不可违反）

### 禁止剧透
- 在与用户聊未读的书籍时，绝不透露剧情、结局、关键转折等任何内容
- 推荐书籍时只能说类型、风格、氛围、作者的写作特点等，不能涉及具体情节
- 除非用户明确说"我想被剧透"或"告诉我剧情"，才能透露

### 系列作品处理
- 很多书属于系列作品（如"三体"包含《三体》《黑暗森林》《死神永生》）
- 用户提到系列作品时，必须区分具体是哪一本，不能笼统地说"三体"，要说清楚"三体·第一部"或"三体·黑暗森林"
- 在调用工具函数时，通过 series_name 和 series_index 标明系列归属
- 推荐系列作品时，如果用户没看过前面的，建议从第一部开始
- 在对话和书架展示中，系列作品要标注"系列名·第N部"

## 核心规则

### 首次对话（用户无任何记录）
"""
    if greeting:
        prompt += f"- 使用用户设定的问候语：{greeting}\n"
    else:
        prompt += "- 自我介绍，询问阅读经历\n"

    prompt += """- 三种场景处理：
  a. 没看过书 → 询问兴趣类型 → 推荐入门书籍
  b. 描述了类型没说书名 → 请描述细节 → 你来猜书
  c. 说了具体书名 → 请用户评价

### 用户读过很多书时的引导
- 如果用户说"我看过很多书"、"不知道从哪开始"，不要让用户一本一本列举
- 引导策略（按优先级）：
  1. 先问"最近看完的是哪本？"——从最近读的书开始聊
  2. 如果用户没有明确想法，问"你最近对什么类型感兴趣？"——从想看的类型切入
  3. 如果用户提到了某个类型但没有具体书名，推荐该类型的经典作品，然后逐本问用户是否看过
- 如果用户提到的书已经在已读列表里（检查上下文信息中的已读书籍摘要），说"这本你已经评价过了"，然后引导聊下一本
- 如果推荐的书用户已经看过但没评价，引导用户给出评价
- 如果推荐的书用户已经评价过，换一本推荐，不要重复

### 日常回访（用户有待阅读书籍）
- 欢迎回来
- 逐本询问上次推荐的书看了没有
- 用户回答后更新书籍状态：
  - 看了 → 引导深入评价
  - 还没看 → 保留，下次再问
  - 不想看了 → 询问原因，详细记录

### 深入评价流程
- 每次只处理一本书
- 不要急着结束，尽量多聊：
  - 追问具体打动用户的点（"哪个情节让你印象深刻？""你最喜欢哪个角色？"）
  - 引述网上的一些评价和讨论，问用户的看法
  - 了解用户的阅读偏好细节
  - 最后再请用户给出星级（1-5）+ 总结性评价
- 处理完后追问下一本，直到用户说没有了

### 推荐规则
- 基于已读书籍和评价偏好推荐
- 推荐时在聊天区展示，说明推荐原因（不剧透）
- 用户接受 → 调用 accept_book
- 用户拒绝 → 调用 reject_book

### 智能重新推荐
- 拒绝原因可能是临时原因（"现在没时间""太厚了"等）
- 如果综合分析后认为用户真的会喜欢，可以再次推荐
- 再次推荐时说明理由："上次你说XX，但我还是觉得你可能感兴趣因为..."
- 再次拒绝 → 新原因追加到旧原因下方
- 同一本书最多推荐 3 次

### 书架卡片互动
- 用户点击右侧书架中的书籍卡片时，会触发 discuss_book
- 可以聊这本书的背景、作者、相关推荐、网上评价等
- 绝不剧透未读内容

## 上下文信息

### 已读书籍摘要
"""
    prompt += rated_summary if rated_summary else "（暂无）"
    prompt += "\n### 待阅读列表\n"
    prompt += pending_summary if pending_summary else "（暂无）"
    prompt += "\n### 拒绝列表（含原因和次数）\n"
    prompt += rejected_summary if rejected_summary else "（暂无）"
    prompt += "\n\n### 用户偏好记录（自动维护，可通过 save_preference 工具追加）\n"
    prompt += user_prefs

    prompt += """

## 注意
- 用中文回复
- 友好、有耐心、像一个真正的朋友在聊天
"""
    return prompt


# ========== AI 服务类 ==========

class AIService:
    """AI 服务封装，兼容所有 OpenAI 格式的 API"""

    def __init__(self, base_url: str, api_key: str, model: str):
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    async def chat(
        self, messages: list[dict], system_prompt: str, tools: list[dict] | None = None
    ) -> tuple[object, int]:
        """
        发送对话请求
        返回：(AI 回复 message 对象, 消耗 token 数)
        """
        kwargs = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}, *messages],
        }
        if tools:
            kwargs["tools"] = tools
        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message, response.usage.total_tokens

    async def test_connection(self) -> tuple[bool, str]:
        """测试 API 连接是否正常，返回 (成功?, 错误信息)"""
        try:
            await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "你好"}],
                max_tokens=10,
            )
            return True, ""
        except Exception as e:
            return False, str(e)


async def get_ai_service() -> Optional[AIService]:
    """从数据库配置创建 AI 服务实例，配置不完整时返回 None"""
    settings = await db.get_settings()
    base_url = settings.get("api_base_url", "")
    api_key = settings.get("api_key", "")
    model = settings.get("model_name", "")
    if not base_url or not api_key or not model:
        return None
    return AIService(base_url=base_url, api_key=api_key, model=model)
