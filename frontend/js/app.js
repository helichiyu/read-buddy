// ========================================
// Read Buddy - 主逻辑入口
// ========================================

const App = {
  /** 页面初始化 */
  async init() {
    // 加载历史消息
    try {
      const messages = await API.getRecentMessages();
      Chat.renderMessages(messages);
    } catch (e) {
      // 后端未启动，显示提示
      Chat.renderMessages([
        { role: "assistant", content: "你好！我是 Read Buddy，你的阅读伙伴 📚\n\n请先点击右上角 ⚙️ 配置 AI API，然后我们就可以开始聊天了！" },
      ]);
    }

    // 加载待阅读书籍
    await Books.loadPending();

    // 绑定交互
    Chat.init();
    Settings.init();
  },

  /** 重新加载全部界面（导入后使用） */
  async reload() {
    const messages = await API.getRecentMessages();
    Chat.renderMessages(messages);
    await Books.loadPending();
  },
};

// 页面加载完成后初始化
document.addEventListener("DOMContentLoaded", () => {
  App.init();
});
