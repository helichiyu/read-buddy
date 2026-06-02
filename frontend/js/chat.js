// ========================================
// Read Buddy - 聊天功能模块
// ========================================

const Chat = {
  /** 渲染消息列表 */
  renderMessages(messages) {
    const container = document.getElementById('chat-messages');
    container.innerHTML = '';
    messages.forEach(msg => {
      const div = document.createElement('div');
      div.className = `message ${msg.role === 'assistant' ? 'ai' : 'user'}`;
      div.textContent = msg.content;
      container.appendChild(div);
    });
    this.scrollToBottom();
  },

  /** 添加单条消息并滚动到底部 */
  addMessage(role, content) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `message ${role === 'assistant' ? 'ai' : 'user'}`;
    div.textContent = content;
    container.appendChild(div);
    this.scrollToBottom();
  },

  /** AI 回复打字效果 */
  async addMessageWithTyping(content) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'message ai';
    container.appendChild(div);

    // 逐字显示
    for (let i = 0; i < content.length; i++) {
      div.textContent = content.slice(0, i + 1);
      this.scrollToBottom();
      await new Promise(r => setTimeout(r, 20));
    }
  },

  /** 滚动到底部 */
  scrollToBottom() {
    const container = document.getElementById('chat-messages');
    container.scrollTop = container.scrollHeight;
  },

  /** 绑定交互事件 */
  init() {
    const input = document.getElementById('chat-input');
    const btnSend = document.getElementById('btn-send');

    // 发送按钮
    btnSend.addEventListener('click', () => this.handleSend());

    // 回车发送
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.handleSend();
      }
    });
  },

  /** 处理发送消息（当前为模拟回复，后续对接后端 API） */
  handleSend() {
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text) return;

    // 显示用户消息
    this.addMessage('user', text);
    input.value = '';

    // 模拟 AI 回复（后续替换为 POST /api/chat）
    setTimeout(() => {
      const replies = [
        '收到！让我想想...',
        '这个问题很好，我来帮你分析一下。',
        '有趣的阅读体验！还有别的想分享的吗？',
        '已记录！你觉得这本书最吸引你的是什么？',
        '好的，我来看看有没有适合你的推荐 📚',
      ];
      const reply = replies[Math.floor(Math.random() * replies.length)];
      this.addMessageWithTyping(reply);
    }, 500);
  },
};
