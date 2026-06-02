// ========================================
// Read Buddy - 书籍卡片模块
// ========================================

const Books = {
  /** 渲染书籍卡片列表 */
  renderBooks(books) {
    const container = document.getElementById('book-list');
    const countEl = document.getElementById('book-count');
    const emptyEl = document.getElementById('book-empty');

    // 清空旧卡片（保留空状态提示元素）
    container.querySelectorAll('.book-card').forEach(el => el.remove());

    // 更新数量
    countEl.textContent = `${books.length} 本`;

    // 无书籍时显示空状态
    if (books.length === 0) {
      if (!emptyEl) {
        const empty = document.createElement('div');
        empty.className = 'book-empty';
        empty.id = 'book-empty';
        empty.textContent = '暂无推荐书籍，和 AI 聊聊你的阅读经历吧！';
        container.appendChild(empty);
      } else {
        emptyEl.style.display = '';
      }
      return;
    }

    // 隐藏空状态
    if (emptyEl) emptyEl.style.display = 'none';

    // 渲染每张卡片
    books.forEach(book => {
      const card = document.createElement('div');
      card.className = 'book-card';
      card.innerHTML = `
        <div class="book-cover">${book.cover ? `<img src="${book.cover}" alt="${book.title}">` : book.title.charAt(0)}</div>
        <div class="book-info">
          <div class="book-title">${book.title}</div>
          <div class="book-author">${book.author}</div>
          <div class="book-reason">${book.reason}</div>
          <div class="book-detail">${book.description}</div>
        </div>
      `;

      // 点击展开/折叠详情
      card.addEventListener('click', () => {
        card.classList.toggle('expanded');
      });

      container.appendChild(card);
    });
  },

  /** 添加单本书籍卡片 */
  addBook(book) {
    const container = document.getElementById('book-list');
    const emptyEl = document.getElementById('book-empty');

    // 隐藏空状态
    if (emptyEl) emptyEl.style.display = 'none';

    // 更新数量
    const countEl = document.getElementById('book-count');
    const current = parseInt(countEl.textContent) || 0;
    countEl.textContent = `${current + 1} 本`;

    // 创建卡片
    const card = document.createElement('div');
    card.className = 'book-card';
    card.innerHTML = `
      <div class="book-cover">${book.cover ? `<img src="${book.cover}" alt="${book.title}">` : book.title.charAt(0)}</div>
      <div class="book-info">
        <div class="book-title">${book.title}</div>
        <div class="book-author">${book.author}</div>
        <div class="book-reason">${book.reason}</div>
        <div class="book-detail">${book.description || ''}</div>
      </div>
    `;
    card.addEventListener('click', () => card.classList.toggle('expanded'));
    container.appendChild(card);
  },

  /** 移除指定书籍卡片 */
  removeBook(bookId) {
    // 后续对接后端时通过 data-id 定位卡片
    const countEl = document.getElementById('book-count');
    const current = parseInt(countEl.textContent) || 0;
    countEl.textContent = `${Math.max(0, current - 1)} 本`;
  },
};
