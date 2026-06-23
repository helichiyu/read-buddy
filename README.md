# Read Buddy

![](https://img.shields.io/badge/Python-3.14-blue) ![](https://img.shields.io/badge/Version-0.1.0-green) ![](https://img.shields.io/badge/Platform-Windows-informational)

AI 驱动的书籍阅读记录与智能推荐桌面应用。通过自然对话录入你的阅读经历，AI 会深入了解你的偏好，为你推荐真正感兴趣的书。

数据完全存储在本地，保护你的隐私。

## 下载安装

👉 [**下载 ReadBuddy_Setup_v0.1.0.zip**](https://github.com/helichiyu/read-buddy/releases/download/v0.1.0/ReadBuddy_Setup_v0.1.0.zip)，解压后双击安装即可。

> 安装后首次打开，点击右上角 ⚙️ 配置你的 AI API 信息（支持 DeepSeek、OpenAI、Claude 等所有 OpenAI 兼容接口）。

所有版本见 [Releases 页面](https://github.com/helichiyu/read-buddy/releases)。

---

## 功能特性

- **对话式阅读录入** — 告诉 AI 你读过什么书、感觉如何，AI 会通过追问引导你给出详细评价
- **智能书籍推荐** — 基于你的阅读历史和偏好，推荐你可能喜欢的书；被拒绝的书如果理由是临时原因，AI 会择机重新推荐
- **系列作品识别** — 自动识别系列作品（如《三体》三部曲），区分每一部，推荐时建议从第一部开始
- **书籍状态管理** — 推荐中 → 待阅读 → 已评价 / 不想看，完整的状态流转
- **用户偏好记忆** — AI 在对话中自动学习你的偏好（喜欢的类型、风格、特殊要求），后续对话自动应用
- **禁止剧透** — 推荐和聊书时绝不透露剧情，除非你明确要求
- **全 API 兼容** — 支持 DeepSeek、OpenAI、Claude 等所有 OpenAI 格式的 API，只需填入地址和 Key
- **本地数据存储** — SQLite 数据库，支持 JSON 导出/导入备份
- **Token 用量追踪** — 实时显示每次对话和累计的 Token 消耗
- **原生桌面窗口** — 不在浏览器中运行，使用独立窗口，苹果风格界面

---

## 技术栈

| 层级 | 技术 |
|---|---|
| 后端框架 | Python 3.14 + FastAPI + Uvicorn |
| 数据库 | SQLite (aiosqlite) |
| AI 接口 | OpenAI Python SDK（兼容所有供应商） |
| 书籍数据 | 豆瓣 API + Google Books API |
| 前端 | 原生 HTML / CSS / JavaScript |
| 桌面窗口 | pywebview |
| HTTP 客户端 | httpx |
| 打包 | PyInstaller + Inno Setup |

---

## 快速开始

### 环境要求

- Python >= 3.14
- [uv](https://docs.astral.sh/uv/)（Python 包管理器）

### 安装与启动

```bash
# 克隆项目
git clone <仓库地址>
cd read-buddy

# 安装依赖
uv sync

# 启动应用
uv run python backend/main.py
```

首次启动后会弹出独立窗口。点击右上角 ⚙️ 按钮进入设置，填入你的 AI API 信息：

| 配置项 | 说明 | 示例 |
|---|---|---|
| API Base URL | API 服务地址 | `https://api.deepseek.com/v1` |
| API Key | 你的 API 密钥 | `sk-...` |
| 模型名称 | 要使用的模型 | `deepseek-chat` |

填写完成后点击"测试连接"，看到绿色指示灯即可开始对话。

---

## 使用指南

### 首次使用

1. 启动应用，配置 AI API（见上方）
2. AI 会主动打招呼，询问你的阅读经历
3. 告诉它你读过的书——可以直接说书名，也可以描述内容让 AI 猜
4. AI 会通过追问了解你的详细感受，然后请你打分
5. 评价完成后，AI 根据你的偏好推荐新书

### 日常使用

1. 打开应用，AI 会问候并询问上次推荐的书看了没有
2. 回答"看了" → 进入评价流程
3. 回答"还没看" → 保留在待阅读列表，下次再问
4. 回答"不想看了" → AI 询问原因并记录

### 存档管理

- **导出**：点击右侧底部"导出存档"按钮，选择保存位置
- **导入**：点击"导入存档"按钮，选择之前的备份文件
- 导出文件为 JSON 格式，不包含 API Key

---

## 项目结构

```
read-buddy/
├── backend/                  # 后端
│   ├── main.py               # 应用入口（启动 FastAPI + pywebview）
│   ├── app.py                # FastAPI 路由定义
│   ├── database.py           # SQLite 数据库操作
│   ├── ai_service.py         # AI 服务封装 + System Prompt
│   ├── book_service.py       # 书籍信息查询（豆瓣 + Google Books）
│   ├── models.py             # Pydantic 数据模型
│   ├── preferences.py        # 用户偏好记忆（Markdown 文件）
│   └── tools/                # AI 工具模块（Function Calling）
│       ├── __init__.py       #   工具注册器（自动发现）
│       ├── base.py           #   工具基类
│       ├── rate_book.py      #   评价书籍
│       ├── recommend_books.py#   推荐书籍
│       ├── accept_book.py    #   接受推荐
│       ├── reject_book.py    #   拒绝推荐
│       ├── discuss_book.py   #   讨论书籍
│       └── save_preference.py#   保存偏好
├── frontend/                 # 前端
│   ├── index.html            # 主页面
│   ├── css/style.css         # 苹果风格样式
│   └── js/
│       ├── app.js            #   应用初始化
│       ├── api.js            #   API 请求封装
│       ├── chat.js           #   聊天功能
│       ├── books.js          #   书籍卡片管理
│       └── settings.js       #   设置面板
├── installer/
│   └── setup.iss             # Inno Setup 安装程序配置
├── data/                     # 运行时数据（Git 忽略）
│   ├── readbuddy.db          #   SQLite 数据库
│   └── preferences.md        #   用户偏好文件
├── build.py                  # 打包脚本
├── pyproject.toml            # 项目依赖
├── CLAUDE.md                 # AI 编码准则
└── ARCHITECTURE.md           # 架构设计文档
```

---

## 打包发布

### 生成 EXE

```bash
# 安装打包依赖（如果还没装）
uv add --dev pyinstaller

# 打包
uv run python build.py
```

生成的文件在 `dist/ReadBuddy/` 目录下。

### 生成安装程序

使用 [Inno Setup](https://jrsoftware.org/isinfo.php) 打开 `installer/setup.iss`，点击 Build。生成的安装程序在 `installer_output/` 目录下。

安装程序功能：
- 安装到 `Program Files\Read Buddy`
- 可选创建桌面快捷方式
- 安装完成提示"立即运行"
- 卸载时可选清理数据

---

## 开发说明

### 扩展 AI 工具

工具模块采用自动发现机制。要添加新工具，在 `backend/tools/` 下创建文件：

```python
# backend/tools/my_tool.py
from .base import BaseTool

class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def description(self) -> str:
        return "工具描述（AI 会看到这段文字）"

    @property
    def parameters(self) -> dict:
        return {
            "param1": {"type": "string", "description": "参数说明"},
        }

    @property
    def _required_params(self) -> list[str]:
        return ["param1"]

    async def handle(self, args: dict, context: dict) -> dict:
        # 执行工具逻辑
        return {"ok": True, "message": "执行结果"}
```

重启应用后，注册器会自动加载新工具。

### API 路由一览

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/books/pending` | 获取待阅读书籍 |
| `GET` | `/api/books/rated` | 获取已评价书籍 |
| `POST` | `/api/books` | 添加书籍 |
| `PUT` | `/api/books/{id}/status` | 更新书籍状态 |
| `POST` | `/api/books/{id}/rate` | 评价书籍 |
| `GET` | `/api/messages/recent` | 获取最近对话 |
| `POST` | `/api/chat` | 核心对话接口 |
| `GET` | `/api/settings` | 获取配置 |
| `PUT` | `/api/settings` | 更新配置 |
| `POST` | `/api/settings/test` | 测试 API 连接 |
| `GET` | `/api/profile` | 获取个性化偏好 |
| `PUT` | `/api/profile` | 更新个性化偏好 |
| `GET` | `/api/token-usage` | Token 用量统计 |
| `GET` | `/api/export` | 导出数据 |
| `POST` | `/api/export-to-file` | 导出至文件 |
| `POST` | `/api/import-from-file` | 从文件导入 |
| `DELETE` | `/api/data` | 清空所有数据 |

---

## 更新日志

### v0.1.0 (2026-06-03)

首次发布，包含以下核心功能：

- AI 对话式阅读录入与评价
- 智能书籍推荐（含重新推荐机制）
- 工具模块化架构（Skill 化），支持自动发现和注册新工具
- Prompt 自检机制，确保 AI 正确调用工具
- 豆瓣 + Google Books 双数据源获取书籍封面和详情
- 用户偏好自动记忆
- SQLite 本地存储 + JSON 导出/导入备份
- PyInstaller 打包 + Inno Setup 7 安装程序

---

## 许可证

MIT
