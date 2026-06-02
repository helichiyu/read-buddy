"""Read Buddy 打包配置

用法：uv run python build.py
生成的 EXE 在 dist/ReadBuddy/ 目录下
"""

import PyInstaller.__main__
import os

# 项目根目录
ROOT = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    os.path.join(ROOT, "backend", "main.py"),
    "--name=ReadBuddy",
    "--noconfirm",
    "--noconsole",
    "--clean",
    f"--add-data={os.path.join(ROOT, 'frontend')}{os.pathsep}frontend",
    f"--icon={os.path.join(ROOT, 'installer', 'icon.ico')}" if os.path.exists(os.path.join(ROOT, 'installer', 'icon.ico')) else "",
    # 包含 data 目录（空目录需要特殊处理）
    f"--add-data={os.path.join(ROOT, 'data')}{os.pathsep}data" if os.path.exists(os.path.join(ROOT, 'data')) else "",
])
