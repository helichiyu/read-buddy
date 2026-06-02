"""Read Buddy 应用入口 - 启动 FastAPI + pywebview 独立窗口"""

import threading
import webview
import uvicorn


def start_server():
    """在后台线程启动 FastAPI"""
    uvicorn.run("app:app", host="127.0.0.1", port=8742, log_level="warning")


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
