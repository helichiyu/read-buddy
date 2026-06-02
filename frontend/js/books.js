// ========================================
// Read Buddy - 书籍卡片模块
// ========================================

const Books = {
  /** 从后端加载并渲染待阅读书籍 */
  async loadPending() {
    try {
      const books = await API.getPendingBooks();
      this.renderBooks(books);
    } catch (e) {
      console.error("加载书架失败", e);
    }
  },

  /** 渲染书籍卡片列表 */
  renderBooks(books) {
    const container = document.getElementById("book-list");
    const countEl = document.getElementById("book-count");
    const emptyEl = document.getElementById("book-empty");

    // 清空旧卡片
    container.querySelectorAll(".book-card").forEach((el) => el.remove());

    countEl.textContent = `${books.length} 本`;

    if (books.length === 0) {
      if (!emptyEl) {
        const empty = document.createElement("div");
        empty.className = "book-empty";
        empty.id = "book-empty";
        empty.textContent = "暂无推荐书籍，和 AI 聊聊你的阅读经历吧！";
        container.appendChild(empty);
      } else {
        emptyEl.style.display = "";
      }
      return;
    }

    if (emptyEl) emptyEl.style.display = "none";

    books.forEach((book) => this._createCard(book, container));
  },

  /** 添加单本书籍卡片 */
  addBook(book) {
    const container = document.getElementById("book-list");
    const emptyEl = document.getElementById("book-empty");
    if (emptyEl) emptyEl.style.display = "none";

    const countEl = document.getElementById("book-count");
    const current = parseInt(countEl.textContent) || 0;
    countEl.textContent = `${current + 1} 本`;

    this._createCard(book, container);
  },

  /** 按标题移除卡片 */
  removeByTitle(title) {
    const container = document.getElementById("book-list");
    const cards = container.querySelectorAll(".book-card");
    for (const card of cards) {
      const titleEl = card.querySelector(".book-title");
      if (titleEl && titleEl.textContent === title) {
        card.remove();
        // 更新数量
        const countEl = document.getElementById("book-count");
        const remaining = container.querySelectorAll(".book-card").length;
        countEl.textContent = `${remaining} 本`;
        // 如果没有卡片了，显示空状态
        if (remaining === 0) {
          const emptyEl = document.getElementById("book-empty");
          if (emptyEl) emptyEl.style.display = "";
        }
        break;
      }
    }
  },

  /** 创建单张卡片 */
  _createCard(book, container) {
    const card = document.createElement("div");
    card.className = "book-card";
    if (book.id) card.dataset.id = book.id;

    card.innerHTML = `
      <div class="book-cover">${
        book.cover_url ? `<img src="${book.cover_url}" alt="${book.title}">` : (book.title || "?").charAt(0)
      }</div>
      <div class="book-info">
        <div class="book-title">${book.title}</div>
        <div class="book-author">${book.author || ""}</div>
        <div class="book-reason">${book.recommend_reason || book.reason || ""}</div>
        <div class="book-detail">${book.description || ""}</div>
      </div>
    `;

    // 点击展开/折叠详情
    card.addEventListener("click", () => {
      card.classList.toggle("expanded");
      // 如果只是展开详情，不触发聊天（双击或长按可以聊）
    });

    // 双击触发聊书
    card.addEventListener("dblclick", (e) => {
      e.preventDefault();
      if (book.title) {
        Chat.discussBook(book.title);
      }
    });

    container.appendChild(card);
  },
};
