// ========================================
// Read Buddy - 设置面板模块
// ========================================

const Settings = {
  /** 绑定设置面板交互 */
  init() {
    const overlay = document.getElementById("settings-overlay");
    const btnOpen = document.getElementById("btn-settings");
    const btnClose = document.getElementById("btn-settings-close");
    const btnSave = document.getElementById("btn-settings-save");
    const btnTest = document.getElementById("btn-test-connection");
    const btnExport = document.getElementById("btn-export");
    const btnImport = document.getElementById("btn-import");

    btnOpen.addEventListener("click", () => {
      this.loadFromServer();
      overlay.classList.add("active");
    });

    btnClose.addEventListener("click", () => overlay.classList.remove("active"));

    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) overlay.classList.remove("active");
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && overlay.classList.contains("active")) {
        overlay.classList.remove("active");
      }
    });

    btnSave.addEventListener("click", () => this.saveToServer());

    btnTest.addEventListener("click", () => this.testConnection());

    // 导出
    if (btnExport) {
      btnExport.addEventListener("click", () => this.exportData());
    }
    // 导入
    if (btnImport) {
      btnImport.addEventListener("click", () => this.importData());
    }
  },

  /** 从后端加载配置 */
  async loadFromServer() {
    try {
      const settings = await API.getSettings();
      document.getElementById("setting-api-url").value = settings.api_base_url || "";
      document.getElementById("setting-api-key").value = settings.api_key || "";
      document.getElementById("setting-model").value = settings.model_name || "";

      const profile = await API.getProfile();
      document.getElementById("setting-buddy-name").value = profile.buddy_name || "";
      document.getElementById("setting-user-name").value = profile.user_name || "";
      document.getElementById("setting-greeting").value = profile.greeting || "";

      const usage = await API.getTokenUsage();
      document.getElementById("token-total").textContent = usage.total || 0;
      document.getElementById("token-session").textContent = "0";
    } catch (e) {
      console.error("加载配置失败", e);
    }
  },

  /** 保存配置到后端 */
  async saveToServer() {
    try {
      // 保存 AI 配置（API Key 只有 4 位脱敏时跳过）
      const apiKey = document.getElementById("setting-api-key").value;
      const settingsData = {
        api_base_url: document.getElementById("setting-api-url").value,
        model_name: document.getElementById("setting-model").value,
      };
      // 只有用户真正修改了 key（不是 **** 格式）才发送
      if (apiKey && !apiKey.includes("****")) {
        settingsData.api_key = apiKey;
      }
      await API.updateSettings(settingsData);

      // 保存个性化偏好
      await API.updateProfile({
        buddy_name: document.getElementById("setting-buddy-name").value,
        user_name: document.getElementById("setting-user-name").value,
        greeting: document.getElementById("setting-greeting").value,
      });

      document.getElementById("settings-overlay").classList.remove("active");
    } catch (e) {
      console.error("保存配置失败", e);
    }
  },

  /** 测试连接 */
  async testConnection() {
    const dot = document.getElementById("connection-status");
    const btn = document.getElementById("btn-test-connection");
    dot.className = "status-dot";
    btn.disabled = true;
    btn.textContent = "测试中...";

    try {
      const result = await API.testConnection({
        api_base_url: document.getElementById("setting-api-url").value,
        api_key: document.getElementById("setting-api-key").value,
        model_name: document.getElementById("setting-model").value,
      });
      dot.className = `status-dot ${result.ok ? "ok" : "fail"}`;
    } catch (e) {
      dot.className = "status-dot fail";
    }

    btn.disabled = false;
    btn.textContent = "测试连接";
  },

  /** 更新 Token 显示 */
  updateTokenDisplay(sessionTokens, totalTokens) {
    document.getElementById("token-session").textContent = sessionTokens;
    document.getElementById("token-total").textContent = totalTokens;
  },

  /** 导出数据（调用 Windows 原生保存对话框） */
  async exportData() {
    try {
      const result = await API.request("POST", "/api/export-to-file");
      if (result.ok) {
        alert(`导出成功！\n${result.books} 本书，${result.ratings} 条评价，${result.messages} 条消息\n已保存到：${result.path}`);
      }
    } catch (e) {
      alert("导出失败：" + e.message);
    }
  },

  /** 导入数据（调用 Windows 原生打开对话框） */
  async importData() {
    if (!confirm("导入将覆盖现有数据，确定吗？")) return;
    try {
      const result = await API.request("POST", "/api/import-from-file");
      if (result.ok) {
        alert(`导入成功！\n${result.books || 0} 本书，${result.ratings || 0} 条评价，${result.messages || 0} 条消息`);
        await App.reload();
      } else if (result.message && result.message !== "用户取消") {
        alert("导入失败：" + result.message);
      }
    } catch (e) {
      alert("导入失败：" + e.message);
    }
  },
};
