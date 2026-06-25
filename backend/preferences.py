"""用户偏好记忆模块 - 在聊天中自动保存用户偏好到文件"""

import os

from paths import data_dir

PREF_DIR = str(data_dir())
PREF_FILE = os.path.join(PREF_DIR, "preferences.md")

DEFAULT_CONTENT = """# 用户阅读偏好

> 此文件由 AI 在聊天过程中自动维护，记录用户的阅读偏好和个性化要求。

## 阅读偏好

（尚未记录）

## 不喜欢的

（尚未记录）

## 其他个性化要求

（尚未记录）
"""


def get_preferences() -> str:
    """读取用户偏好文件内容，不存在则创建默认文件"""
    os.makedirs(PREF_DIR, exist_ok=True)
    if not os.path.exists(PREF_FILE):
        with open(PREF_FILE, "w", encoding="utf-8") as f:
            f.write(DEFAULT_CONTENT)
    with open(PREF_FILE, "r", encoding="utf-8") as f:
        return f.read()


def append_preference(category: str, content: str):
    """向偏好文件的指定分类下追加一条记录"""
    current = get_preferences()

    # 找到对应分类的段落
    section_header = f"## {category}"
    if section_header not in current:
        # 如果分类不存在，在文件末尾添加
        current = current.rstrip() + f"\n\n## {category}\n\n{content}\n"
    else:
        # 在分类下追加
        lines = current.split("\n")
        insert_idx = None
        for i, line in enumerate(lines):
            if line.strip() == section_header:
                # 找到分类头，找到下一行开始插入
                insert_idx = i + 1
                # 跳过已有的空行和"尚未记录"
                while insert_idx < len(lines) and (
                    lines[insert_idx].strip() == ""
                    or lines[insert_idx].strip() == "（尚未记录）"
                ):
                    insert_idx += 1
                break
        if insert_idx is not None:
            lines.insert(insert_idx, f"- {content}")
            current = "\n".join(lines)

    with open(PREF_FILE, "w", encoding="utf-8") as f:
        f.write(current)
