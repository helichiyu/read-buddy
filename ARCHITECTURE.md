# 架构设计：Read Buddy

> 本文档基于 v0.1.1 实际代码梳理（2026-06-23）。如代码与本文描述不符，以代码为准并更新本文档。

## 1. 项目概述

### 目标

一个 AI 驱动的书籍阅读记录与智能推荐**桌面应用**。用户通过自然对话录入阅读经历，AI 在对话中追问、评价、推荐，并逐步学习用户偏好。数据完全存于本地，保护隐私。

### 范围

- **做什么**：对话式录入/评价、智能推荐（含系列作品识别、被拒书籍择机重推）、用户偏好自动记忆、本地 SQLite 存储 + JSON 导入导出、Windows 桌面窗口分发。
- **不做什么**：不做账号体系与云端同步；不做社交/书评社区；不绑定特定 AI 供应商；当前仅面向 Windows。

## 2. 技术栈

| 层级 | 技术 | 选型理由 |
|---|---|---|
| 运行时 | Python 3.14 + uv | uv 管理依赖与虚拟环境，速度快 |
| 后端框架 | FastAPI + Uvicorn | 原生 async，路由即函数，轻量 |
| 数据库 | SQLite + aiosqlite | 单文件、零运维、隐私友好；async 接口适配 FastAPI |
| AI 接口 | OpenAI Python SDK（AsyncOpenAI） | 兼容所有 OpenAI 格式供应商（DeepSeek/OpenAI/Claude 等） |
| 书籍数据 | 豆瓣 + Google Books | 中文书优先豆瓣，外文书/兜底用 Google Books |
| 前端 | 原生 HTML / CSS / JavaScript | 无构建步骤、无框架，直接静态托管 |
| 桌面窗口 | pywebview | 用系统 WebView 包裹本地 HTTP 服务，得到独立原生窗口 |
| HTTP 客户端 | httpx | async，用于调用外部书籍 API |
| 打包 | PyInstaller + Inno Setup | 单 EXE + Windows 安装程序 |

## 3. 模块划分

### 进程与启动

`backend/main.py` 是唯一入口：
1. 把 `backend/` 加入 `sys.path`（兼容 PyInstaller 冻结态）。
2. 后台守护线程启动 Uvicorn，监听 `127.0.0.1:8742`。
3. 主线程启动 pywebview 窗口加载该地址。

前端页面由 FastAPI 把 `frontend/` 以 `StaticFiles(html=True)` 挂载到 `/` 提供。

### 后端模块（`backend/`）

| 模块 | 职责 | 关键内容 |
|---|---|---|
| `app.py` | **路由层** | 全部 HTTP 路由；`/api/chat` 委托 `chat_orchestrator`；导出/导入用 tkinter 弹原生对话框；startup 初始化、shutdown 关闭单连接 |
| `chat_orchestrator.py` | **对话编排** | `run_chat()`：构建上下文 + 工具调用循环（最多 5 轮）+ 存回复/累计 token |
| `ai_service.py` | **AI 服务层** | `build_system_prompt()` 动态拼接上下文；`AIService` 封装 AsyncOpenAI；`get_ai_service()` 从配置构造实例 |
| `database.py` | **数据访问层** | async 函数式 API，覆盖 books/ratings/messages/settings/profile 的增删改查与导入导出；**应用级单连接**（`get_db()` 单例，`close_db()` 关闭） |
| `book_service.py` | **外部书籍查询** | `search()`：豆瓣优先、Google Books 兜底，返回封面/简介/ISBN/分类；**进程内缓存**（同书名不重复请求） |
| `preferences.py` | **偏好记忆** | 以 Markdown 文件存储用户偏好，提供读/追加 |
| `paths.py` | **路径工具** | 统一开发/打包路径：`resource_dir()`（只读资源）、`data_dir()`（可写数据） |
| `tools/` | **AI 工具层（Skill 化）** | 自动发现的 `BaseTool` 子类，见下表 |

### 工具模块（`backend/tools/`）

通过注册器 `_auto_discover()` 自动扫描：凡继承 `BaseTool` 的类即注册，无需手动登记。每个工具通过 `context["books_changed"]` 向对话编排层上报界面变更。

| 工具 | 触发场景 | 主要副作用 |
|---|---|---|
| `recommend_books` | 推荐书籍 | 仅写入 `books_changed`，**不入库**（推荐先在聊天区展示） |
| `accept_book` | 用户接受推荐 | 入库为 `pending`；异步调 `book_service` 回填详情 |
| `rate_book` | 用户做出评价 | 新增或转 `rated`；写 ratings；异步回填详情 |
| `reject_book` | 用户不想看 | 转 `not_interested`，追加拒绝原因与次数 |
| `discuss_book` | 点卡片聊书 | 不产生数据变更 |
| `save_preference` | 记住偏好 | 追加到 `preferences.md` |

### 前端模块（`frontend/js/`）

原生 JS，无框架。五个对象各司其职：

| 模块 | 职责 |
|---|---|
| `app.js` | 入口初始化：加载历史消息 + 书架，绑定各模块 |
| `api.js` | 所有 HTTP 请求的 `fetch` 封装 |
| `chat.js` | 消息渲染、打字机效果、发送、消费 `books_changed` |
| `books.js` | 右侧书架卡片的渲染/增删 |
| `settings.js` | 设置面板（AI 配置、个性化、Token 用量、导出导入按钮） |

## 4. 边界设计

### 依赖方向

```
浏览器(前端)
    │  HTTP (127.0.0.1:8742)
    ▼
app.py  ──────────► ai_service.py ──► database.py ──► SQLite 文件
 (路由/编排)              │               ▲
    │                     ├─► preferences.py (读)
    │                     │
    ├──► tools/*  ────────┤   (工具经 context 由 app.py 分发)
    │       │             │
    │       ├─► database.py
    │       ├─► book_service.py ──► 豆瓣 / Google Books
    │       └─► preferences.py (追加)
    │
    └──► database.py
```

### 边界规则

- **`app.py` 是唯一入口枢纽**：前端只通过 HTTP 与后端交互；所有外部入口收敛到路由层。对话编排委托给 `chat_orchestrator`（同属编排层，依赖 `ai_service`/`tools`/`database`，不被 `tools/*` 反向依赖）。
- **`tools/` 是 AI 的「手脚」**：工具只能向下依赖 `database` / `book_service` / `preferences`，**不得反向依赖 `app.py` 或 `ai_service.py`**。工具之间互不直接调用，协作由 AI 在对话中编排。
- **`ai_service.py` 只负责「说」**：构建 prompt + 调用模型，不执行业务写操作；写操作交给工具。
- **`database.py` 是最底层**：不依赖任何业务模块；所有上层通过它的 async 函数访问数据。
- **`book_service.py` 是纯外部适配**：被 `accept_book` / `rate_book` **延迟导入**调用（避免启动期耦合），结果经 `database.update_book_details` 落库。
- **前端不得绕过后端直连数据库**；前端模块间通过全局对象（`App`/`API`/`Chat`/`Books`/`Settings`）协作。

### 禁止的依赖方向（防耦合）

- `tools/*` → `app.py`、`ai_service.py`（工具不能知道请求上下文与编排细节）
- `database.py` → 任何上层模块
- 前端 → 数据库文件（只能走 HTTP）

## 5. 数据流

### 5.1 对话核心链路

```
用户输入
  → chat.js.handleSend() ──POST /api/chat──► app.py.chat()
      1. 存用户消息 (db.add_message)
      2. build_system_prompt()：注入 已读/待读/拒绝列表 + preferences.md
      3. 取最近 20 条消息作为上下文
      4. 循环（≤5 轮）：
           ai.chat(messages, prompt, tools) → 若有 tool_calls：
             遍历 tool_calls → tools.get_tool(name).handle(args, ctx)
             工具把变更写入 ctx["books_changed"]，结果回传给 AI
           无 tool_calls 则结束
      5. 存 AI 回复 + 累计 Token
      6. 返回 { reply, tokens, books_changed }
  → 前端：
      - 打字机渲染 reply
      - _handleBooksChanged：accepted→加书架卡片；rejected→移除卡片
      - 更新 Token 显示
```

### 5.2 书籍状态机

```
        (对话推荐，不入库)
            suggested*  ──accept_book──►  pending  ──rate_book──►  rated
                  │                          │
                  └──reject_book──►  not_interested  ◄──reject_book──┘
                                       (含原因+次数)
```

- `suggested*`：推荐阶段的书只活在对话与 `books_changed`，**不写库**。
- `pending`：接受后入库（`accept_book`），同时懒加载书籍详情。
- `rated`：评价后写入 ratings 并转状态（`rate_book`，可从 pending 转入或新建）。
- `not_interested`：拒绝后记录原因（JSON 数组，可多次追加）与推荐次数。
- **重新推荐**：`PUT /api/books/{id}/status` 传 `suggested` 时触发 `increment_recommend_count`；同一本书「最多 3 次」由 System Prompt 软约束（非代码强制）。

### 5.3 书籍详情懒加载

`recommend_books` **不**查询豆瓣/Google；只有 `accept_book` / `rate_book` 执行时才调 `book_service.search` 回填 `cover_url/description/isbn/categories`。这样推荐即时、外部 API 调用最少。

## 6. 目录结构

```
read-buddy/
├── backend/
│   ├── main.py            # 入口：启动 FastAPI + pywebview
│   ├── app.py             # 路由层
│   ├── chat_orchestrator.py  # 对话编排（工具调用循环）
│   ├── ai_service.py      # AI 服务 + System Prompt
│   ├── database.py        # SQLite 数据访问（单连接）
│   ├── book_service.py    # 豆瓣 + Google Books 查询（内存缓存）
│   ├── paths.py           # 路径工具（开发/打包统一）
│   ├── preferences.py     # 用户偏好（Markdown）
│   └── tools/             # AI 工具（自动发现）
│       ├── __init__.py    #   注册器
│       ├── base.py        #   BaseTool 基类
│       ├── rate_book.py / recommend_books.py
│       ├── accept_book.py / reject_book.py
│       └── discuss_book.py / save_preference.py
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/{app,api,chat,books,settings}.js
├── tests/                 # 单元测试（pytest）
├── installer/setup.iss    # Inno Setup 安装程序配置
├── data/                  # 运行时数据（已 .gitignore）
│   ├── readbuddy.db
│   └── preferences.md
├── build.py               # PyInstaller 打包脚本
├── pyproject.toml
├── CLAUDE.md
└── ARCHITECTURE.md
```

## 7. 关键设计决策

| 决策 | 理由 | 权衡 |
|---|---|---|
| FastAPI 跑本地端口 + pywebview 包窗口 | 用 Web 技术栈做 UI，又能得到独立原生窗口、避开浏览器 | 多一个本地 HTTP 层；窗口与端口绑定 |
| 全 OpenAI 兼容接口（用户自配 base_url/key/model） | 不绑供应商、无需后端密钥、用户数据与花费自管 | 质量依赖用户所选模型；不同模型对 Function Calling 支持不一 |
| 工具自动发现（Skill 化） | 加新工具零配置，符合「单一职责、可扩展」 | 注册顺序不可控；命名冲突需自律 |
| System Prompt 自检表（「说什么→调什么工具」） | 用表格强约束工具调用，降低漏调概率，保障数据落库 | 依赖模型遵循指令，非强制 |
| 书籍详情懒加载 | 推荐即时、外部 API 调用最少 | 推荐阶段卡片无封面，需接受后才补全 |
| System Prompt 动态注入全量书籍列表 | 让 AI 每轮都掌握完整状态，推荐更准、不重复 | 随数据增长 prompt 膨胀（见可优化点） |
| 本地优先（SQLite + Markdown + 导出脱敏） | 隐私、离线可用、可迁移 | 无多端同步 |
| 打包双路径模式（`sys.frozen` 区分） | 兼容开发态与 PyInstaller 冻结态，数据写可写目录、资源读只读 `_MEIPASS` | 已由 `paths.py` 统一（`main.py` 因引导阶段保留内联） |

## 8. 可优化点

> 本节记录历史梳理出的优化点及其当前状态。2026-06-23 的清理重构（见 `todos/todo_0623_1.md`）已处理其中多数项。

1. ✅ **`models.py` 定义了但运行时未使用** → **已删除**。全后端无引用，`app.py` 用裸 `dict = Body(...)`、`database.py` 返回 dict，删除以免文档误导。
2. ✅ **`database.py` 无连接复用** → **已改为应用级单连接**。`get_db()` 返回模块级单例（首次建库建表），`close_db()` 在应用 shutdown 时关闭；业务函数不再逐次 `connect`/`close`。
3. ✅ **`app.py` 的 `/api/chat` 编排较重** → **已抽 `chat_orchestrator.py`**。`run_chat()` 承担工具调用循环与上下文构建，`/api/chat` 路由瘦身为委托调用。
4. ⏸ **System Prompt 随数据膨胀** → **暂不处理（待评估）**。当前个人使用数据量小，书籍列表全量注入尚不构成压力；待书籍上百后再评估截断/摘要/检索式注入。
5. ⏸ **部分状态约束靠 Prompt 软约束**（同一本最多推荐 3 次、不重复推荐已读）→ **暂不加代码兜底（待评估）**。继续信任 prompt；待观察到实际推荐重复率偏高后再在 `recommend_books` 加代码校验。
6. ✅ **导出/导入存在冗余实现** → **已清理**。删除后端未调用的 `/api/export`、`/api/import` 路由及 `api.js` 中无人调用的 `exportData`/`importData`，统一为 `-to-file`/`-from-file` 版本。
7. ✅ **`book_service` 无缓存** → **已加进程内内存缓存**。`search()` 按完整归一化 query 缓存命中结果（失败不缓存），同书名不重复请求外部 API，且避免英文书名同首词串缓存；重启失效。正则抓豆瓣详情页的脆弱性问题仍在（未改）。
8. ❌ **推荐阶段无封面/详情** → **经核实不成立，已取消**。核实前端 `chat.js` 发现：推荐（`recommended`）阶段**不渲染卡片**（注释明确「recommended 不操作书架」），推荐书只通过 AI 文字展示，仅 `accept_book` 后才以卡片入书架（此时已同步回填封面）。因此「推荐卡片无封面」前提不成立，预取封面无目标。
9. ✅ **多处 `except Exception: pass` 静默吞错** → **已改为日志**。`book_service`/`accept_book`/`rate_book` 的静默 except 改为 `logger.warning`，`main.py` 配置 `basicConfig`。注：`app.py`/`ai_service.py` 中 `except Exception as e: return {...}` 已正确返回错误，非静默吞错，未改。
10. ✅ **缺少自动化测试** → **已补**。引入 `pytest` + `pytest-asyncio`，覆盖工具注册器分发、书籍状态机、导入导出往返、导入失败回滚、消息清理、书籍搜索缓存（`tests/`，单连接下用临时库隔离）。
11. ✅ **`sys.frozen` 路径判断散落 4 处** → **已抽 `paths.py`**。`resource_dir()`（只读资源）/`data_dir()`（可写数据）统一 `app.py`/`database.py`/`preferences.py` 三处；`main.py` 因处于 sys.path 引导阶段，保留内联判断（无法 import 工具，鸡生蛋）。

## 9. 演进与待细化项

- 多端同步 / 账号体系（当前明确不做，待需求明确再评估）。
- 跨平台支持（macOS/Linux）：pywebview + tkinter 对话框需替换为各平台原生方案。
- 推荐质量评估：是否引入显式的「推荐命中率」统计，反哺推荐策略。
- 长上下文治理：随对话与书籍增长，消息已做「>200 条保留最近 100 条」的清理，书籍列表注入策略待随数据规模细化。
