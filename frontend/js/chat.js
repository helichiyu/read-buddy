// ========================================
// Read Buddy - 聊天功能模块
// ========================================

const Chat = {
  /** 渲染消息列表 */
  renderMessages(messages) {
    const container = document.getElementById("chat-messages");
    container.innerHTML = "";
    messages.forEach((msg) => {
      this._appendBubble(msg.role, msg.content);
    });
    this.scrollToBottom();
  },

  /** 添加单条消息气泡 */
  _appendBubble(role, content) {
    const container = document.getElementById("chat-messages");
    const div = document.createElement("div");
    div.className = `message ${role === "assistant" ? "ai" : "user"}`;
    div.textContent = content;
    container.appendChild(div);
  },

  /** AI 回复打字效果 */
  async _typeReply(content) {
    const container = document.getElementById("chat-messages");
    const div = document.createElement("div");
    div.className = "message ai";
    container.appendChild(div);

    for (let i = 0; i < content.length; i++) {
      div.textContent = content.slice(0, i + 1);
      this.scrollToBottom();
      await new Promise((r) => setTimeout(r, 18));
    }
  },

  /** 滚动到底部 */
  scrollToBottom() {
    const container = document.getElementById("chat-messages");
    container.scrollTop = container.scrollHeight;
  },

  /** 绑定交互事件 */
  init() {
    const input = document.getElementById("chat-input");
    const btnSend = document.getElementById("btn-send");

    btnSend.addEventListener("click", () => this.handleSend());
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.handleSend();
      }
    });
  },

  /** 处理发送消息 */
  async handleSend() {
    const input = document.getElementById("chat-input");
    const text = input.value.trim();
    if (!text) return;

    // 立即显示用户消息
    this._appendBubble("user", text);
    input.value = "";
    this.scrollToBottom();

    // 禁用输入
    const btnSend = document.getElementById("btn-send");
    btnSend.disabled = true;
    btnSend.textContent = "思考中...";

    try {
      // 调用后端 API
      const result = await API.chat(text);

      // 显示 AI 回复（带打字效果）
      if (result.reply) {
        await this._typeReply(result.reply);
      }

      // 处理书籍变更
      if (result.books_changed && result.books_changed.length > 0) {
        this._handleBooksChanged(result.books_changed);
      }

      // 更新 Token 显示
      if (result.tokens !== undefined) {
        const total = await API.getTokenUsage();
        Settings.updateTokenDisplay(result.tokens, total.total || 0);
      }
    } catch (err) {
      this._appendBubble("assistant", "网络错误，请检查后端是否正在运行。");
    }

    // 恢复输入
    btnSend.disabled = false;
    btnSend.textContent = "发送";
    this.scrollToBottom();
  },

  /** 处理书籍变更事件 */
  _handleBooksChanged(changes) {
    for (const change of changes) {
      if (change.action === "accepted") {
        // 用户接受了推荐，添加到书架
        Books.addBook(change);
      } else if (change.action === "rejected") {
        // 用户拒绝了，从书架移除
        Books.removeByTitle(change.title);
      }
      // rated / recommended / discuss 不需要操作书架
    }
  },

  /** 通过书架卡片触发聊天（聊某本书） */
  discussBook(title) {
    const input = document.getElementById("chat-input");
    input.value = `我想聊聊《${title}》`;
    this.handleSend();
  },
};
