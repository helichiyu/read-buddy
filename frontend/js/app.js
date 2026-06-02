// ========================================
// Read Buddy - 主逻辑入口
// ========================================

// 模拟聊天消息（首次使用场景）
const mockMessages = [
  { role: 'assistant', content: '你好！我是 Read Buddy，你的阅读伙伴 📚\n\n你平时喜欢看什么书呢？' },
  { role: 'user', content: '我最近看了《三体》' },
  { role: 'assistant', content: '很棒！《三体》是刘慈欣的科幻巨作。\n\n你能给它打个分吗？⭐' },
  { role: 'user', content: '5星，非常震撼' },
  { role: 'assistant', content: '已记录！《三体》⭐⭐⭐⭐⭐\n\n根据你的喜好，我推荐你看看这几本书 👇' },
];

// 模拟待阅读书籍
const mockPendingBooks = [
  {
    id: 1, title: '银河帝国：基地', author: '艾萨克·阿西莫夫',
    cover: '', reason: '你喜欢《三体》这样的硬科幻，基地系列是科幻文学的基石',
    description: '银河帝国已有一万两千年的历史，心理史学家哈里·谢顿预言帝国即将覆灭，于是在银河边缘建立基地，保存人类文明的火种...'
  },
  {
    id: 2, title: '沙丘', author: '弗兰克·赫伯特',
    cover: '', reason: '与《三体》类似，涉及文明兴衰与宏大世界观',
    description: '在遥远的未来，人类散布在宇宙各个角落。沙漠星球厄拉科斯是宇宙中最重要的行星，因为它是唯一出产"香料"的地方...'
  },
];

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
  // 加载模拟数据
  Chat.renderMessages(mockMessages);
  Books.renderBooks(mockPendingBooks);

  // 绑定聊天交互
  Chat.init();

  // 绑定设置面板交互
  Settings.init();
});
