"""对话编排 - 工具调用循环与上下文构建"""

import json

import database as db
from ai_service import get_ai_service, build_system_prompt
from tools import get_openai_tools, get_tool

# 未配置 AI 时的提示语
_NOT_CONFIGURED_REPLY = "请先在设置中配置 AI 的 API 信息（API Base URL、API Key、模型名称），然后就可以开始聊天了！点击右上角的 ⚙️ 按钮。"

# 单次对话最多处理多少轮工具调用
MAX_TOOL_ROUNDS = 5


async def run_chat(user_content: str) -> dict:
    """
    执行一轮对话，返回 {reply, tokens, books_changed}。

    流程：
    1. 检查 AI 配置
    2. 存储用户消息
    3. 构建上下文（System Prompt + 最近 20 条消息）
    4. 调用 AI，循环处理工具调用（≤ MAX_TOOL_ROUNDS 轮）
    5. 存储 AI 回复、累计 Token
    """
    # 检查 AI 配置
    ai = await get_ai_service()
    if not ai:
        return {"reply": _NOT_CONFIGURED_REPLY, "tokens": 0, "books_changed": []}

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

    # 使用注册器的工具列表
    tools = get_openai_tools()

    # 调用 AI（可能需要多轮处理工具调用）
    books_changed = []
    total_tokens = 0
    message = None

    for _ in range(MAX_TOOL_ROUNDS):
        message, tokens = await ai.chat(chat_messages, system_prompt, tools=tools)
        total_tokens += tokens

        # 如果没有工具调用，直接结束
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

        # 使用注册器分发工具调用
        for tc in message.tool_calls:
            args = json.loads(tc.function.arguments)
            tool = get_tool(tc.function.name)
            if tool:
                result = await tool.handle(args, {"books_changed": books_changed})
            else:
                result = {"ok": False, "message": f"未知工具：{tc.function.name}"}
            # 将工具结果回传给 AI
            chat_messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result, ensure_ascii=False)})

    # 存储 AI 回复
    reply_text = (message.content if message else "") or ""
    await db.add_message("assistant", reply_text, total_tokens)
    await db.add_token_usage(total_tokens)

    return {
        "reply": reply_text,
        "tokens": total_tokens,
        "books_changed": books_changed,
    }
