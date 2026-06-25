"""Read Buddy 应用入口 - 启动 FastAPI + pywebview 独立窗口"""

import sys
import os
import logging
import threading

# 日志配置（桌面应用输出到控制台即可）
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# PyInstaller 打包后需要把项目根目录加入搜索路径
if getattr(sys, "frozen", False):
    # 打包后，_MEIPASS 是临时解压目录
    BASE_DIR = sys._MEIPASS
    sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

import uvicorn
import webview
from app import app


def start_server():
    """在后台线程启动 FastAPI"""
    uvicorn.run(app, host="127.0.0.1", port=8742, log_level="warning")


if __name__ == "__main__":
    # 后台启动 FastAPI 服务
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # 创建 pywebview 独立窗口
    webview.create_window(
        title="Read Buddy",
        url="http://127.0.0.1:8742",
        width=1200,
        height=800,
        min_size=(900, 600),
    )
    webview.start()
