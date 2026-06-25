"""工具注册器测试 - 验证自动发现与分发"""


def test_get_known_tools():
    """六个内置工具都能被注册器发现"""
    from tools import get_tool
    for name in ("recommend_books", "accept_book", "rate_book",
                 "reject_book", "discuss_book", "save_preference"):
        assert get_tool(name) is not None, f"工具 {name} 未注册"


def test_unknown_tool_returns_none():
    """未知工具返回 None（而非抛异常）"""
    from tools import get_tool
    assert get_tool("nonexistent_tool") is None


def test_all_tools_have_valid_openai_schema():
    """每个工具都能生成合法的 OpenAI Function Calling schema"""
    from tools import get_all_tools
    names = []
    for tool in get_all_tools():
        schema = tool.to_openai_tool()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == tool.name
        assert schema["function"]["description"]
        names.append(tool.name)
    # 工具名唯一（注册器靠 name 索引，重名会互相覆盖）
    assert len(names) == len(set(names)), "存在重名工具"
