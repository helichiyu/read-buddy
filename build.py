"""Read Buddy 打包配置

用法：uv run python build.py
生成的 EXE 在 dist/ReadBuddy/ 目录下
"""

import PyInstaller.__main__
import os

# 项目根目录
ROOT = os.path.dirname(os.path.abspath(__file__))

# 动态导入的模块，PyInstaller 无法自动发现，必须手动列出
HIDDEN_IMPORTS = [
    # 后端模块
    "database",
    "ai_service",
    "app",
    "chat_orchestrator",
    "book_service",
    "paths",
    "preferences",
    # 工具模块（使用 importlib 动态加载）
    "tools",
    "tools.base",
    "tools.rate_book",
    "tools.recommend_books",
    "tools.accept_book",
    "tools.reject_book",
    "tools.discuss_book",
    "tools.save_preference",
]

args = [
    os.path.join(ROOT, "backend", "main.py"),
    "--name=ReadBuddy",
    "--noconfirm",
    "--noconsole",
    "--clean",
    f"--add-data={os.path.join(ROOT, 'frontend')}{os.pathsep}frontend",
]

# 图标（如果存在）
icon_path = os.path.join(ROOT, "installer", "icon.ico")
if os.path.exists(icon_path):
    args.append(f"--icon={icon_path}")

# data 目录（如果存在）
data_dir = os.path.join(ROOT, "data")
if os.path.exists(data_dir):
    args.append(f"--add-data={data_dir}{os.pathsep}data")

# hidden-imports
for mod in HIDDEN_IMPORTS:
    args.append(f"--hidden-import={mod}")

PyInstaller.__main__.run(args)
