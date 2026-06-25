// ========================================
// Read Buddy - API 请求封装
// ========================================

const API = {
  /** 通用请求方法 */
  async request(method, path, body = null) {
    const opts = {
      method,
      headers: { "Content-Type": "application/json" },
    };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(path, opts);
    return res.json();
  },

  /** 获取待阅读书籍 */
  async getPendingBooks() {
    return this.request("GET", "/api/books/pending");
  },

  /** 获取最近消息 */
  async getRecentMessages(limit = 20) {
    return this.request("GET", `/api/messages/recent?limit=${limit}`);
  },

  /** 发送聊天消息 */
  async chat(content) {
    return this.request("POST", "/api/chat", { content });
  },

  /** 获取配置 */
  async getSettings() {
    return this.request("GET", "/api/settings");
  },

  /** 更新配置 */
  async updateSettings(data) {
    return this.request("PUT", "/api/settings", data);
  },

  /** 测试连接 */
  async testConnection(data) {
    return this.request("POST", "/api/settings/test", data);
  },

  /** 获取个性化偏好 */
  async getProfile() {
    return this.request("GET", "/api/profile");
  },

  /** 更新个性化偏好 */
  async updateProfile(data) {
    return this.request("PUT", "/api/profile", data);
  },

  /** 获取 Token 统计 */
  async getTokenUsage() {
    return this.request("GET", "/api/token-usage");
  },

  /** 清空数据 */
  async clearData() {
    return this.request("DELETE", "/api/data");
  },
};
