// ========================================
// Read Buddy - 设置面板模块
// ========================================

const Settings = {
  /** 绑定设置面板交互 */
  init() {
    const overlay = document.getElementById('settings-overlay');
    const btnOpen = document.getElementById('btn-settings');
    const btnClose = document.getElementById('btn-settings-close');
    const btnSave = document.getElementById('btn-settings-save');
    const btnTest = document.getElementById('btn-test-connection');

    // 打开设置
    btnOpen.addEventListener('click', () => {
      this.loadFromStorage();
      overlay.classList.add('active');
    });

    // 关闭设置
    btnClose.addEventListener('click', () => overlay.classList.remove('active'));

    // 点击遮罩关闭
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) overlay.classList.remove('active');
    });

    // ESC 关闭
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && overlay.classList.contains('active')) {
        overlay.classList.remove('active');
      }
    });

    // 保存设置
    btnSave.addEventListener('click', () => {
      this.saveToStorage();
      overlay.classList.remove('active');
    });

    // 测试连接（模拟，后续对接后端 API）
    btnTest.addEventListener('click', () => this.testConnection());
  },

  /** 从 localStorage 读取配置填充表单 */
  loadFromStorage() {
    const fields = [
      { id: 'setting-api-url', key: 'api_url' },
      { id: 'setting-api-key', key: 'api_key' },
      { id: 'setting-model', key: 'model' },
      { id: 'setting-buddy-name', key: 'buddy_name' },
      { id: 'setting-user-name', key: 'user_name' },
      { id: 'setting-greeting', key: 'greeting' },
    ];
    fields.forEach(({ id, key }) => {
      const el = document.getElementById(id);
      if (el) el.value = localStorage.getItem(`readbuddy_${key}`) || '';
    });

    // 恢复 Token 显示
    const sessionToken = localStorage.getItem('readbuddy_token_session') || '0';
    const totalToken = localStorage.getItem('readbuddy_token_total') || '0';
    document.getElementById('token-session').textContent = sessionToken;
    document.getElementById('token-total').textContent = totalToken;
  },

  /** 保存配置到 localStorage */
  saveToStorage() {
    const fields = [
      { id: 'setting-api-url', key: 'api_url' },
      { id: 'setting-api-key', key: 'api_key' },
      { id: 'setting-model', key: 'model' },
      { id: 'setting-buddy-name', key: 'buddy_name' },
      { id: 'setting-user-name', key: 'user_name' },
      { id: 'setting-greeting', key: 'greeting' },
    ];
    fields.forEach(({ id, key }) => {
      const el = document.getElementById(id);
      if (el) localStorage.setItem(`readbuddy_${key}`, el.value);
    });
  },

  /** 测试连接（模拟，后续对接 POST /api/settings/test） */
  async testConnection() {
    const dot = document.getElementById('connection-status');
    const btn = document.getElementById('btn-test-connection');
    dot.className = 'status-dot';
    btn.disabled = true;
    btn.textContent = '测试中...';

    // 模拟延迟
    await new Promise(r => setTimeout(r, 1000));

    // 模拟成功（后续改为真实 API 调用）
    const apiUrl = document.getElementById('setting-api-url').value;
    const apiKey = document.getElementById('setting-api-key').value;
    if (apiUrl && apiKey) {
      dot.className = 'status-dot ok';
    } else {
      dot.className = 'status-dot fail';
    }

    btn.disabled = false;
    btn.textContent = '测试连接';
  },

  /** 更新 Token 显示 */
  updateTokenDisplay(sessionTokens, totalTokens) {
    document.getElementById('token-session').textContent = sessionTokens;
    document.getElementById('token-total').textContent = totalTokens;
    localStorage.setItem('readbuddy_token_session', sessionTokens);
    localStorage.setItem('readbuddy_token_total', totalTokens);
  },
};
