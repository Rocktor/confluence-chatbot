import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useChatStore, useThemeStore, useUIStore } from '../../store/chatStore';
import { useAuthStore } from '../../store/authStore';
import api from '../../utils/api';
import styles from './LeftPanel.module.css';

// Icons as inline SVGs for better control
const Icons = {
  Plus: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="12" y1="5" x2="12" y2="19" />
      <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  ),
  Search: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  ),
  Trash: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    </svg>
  ),
  Close: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  ),
  Link: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
    </svg>
  ),
  Settings: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  ),
  Moon: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  ),
  Sun: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <circle cx="12" cy="12" r="5" />
      <line x1="12" y1="1" x2="12" y2="3" />
      <line x1="12" y1="21" x2="12" y2="23" />
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
      <line x1="1" y1="12" x2="3" y2="12" />
      <line x1="21" y1="12" x2="23" y2="12" />
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
    </svg>
  ),
  Message: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  ),
  Confluence: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <path d="M2.73 18.77c-.36.58-.27.85.2 1.2l3.47 2.33c.47.35.74.26 1.1-.32.36-.58 3.1-5.1 8.5-5.1 3.2 0 5.27 1.55 5.27 4.12 0 2.57-2.07 4.12-5.27 4.12H8.5c-.58 0-.85.27-.85.85v3.18c0 .58.27.85.85.85h7.5c5.8 0 10.5-3.7 10.5-9s-4.7-9-10.5-9c-7.9 0-12.4 6.1-12.77 6.77z" transform="scale(0.8) translate(3, 3)" />
    </svg>
  ),
  Logout: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  ),
  ChevronLeft: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <polyline points="15 18 9 12 15 6" />
    </svg>
  ),
  Shield: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  )
};

interface LeftPanelProps {
  onNewChat: () => void;
  onSelectConversation: (id: number) => void;
}

export const LeftPanel: React.FC<LeftPanelProps> = ({
  onNewChat,
  onSelectConversation,
}) => {
  const navigate = useNavigate();
  const { conversations, currentConversationId, removeConversation } = useChatStore();
  const { theme, toggleTheme } = useThemeStore();
  const { isSidebarOpen, toggleSidebar, setSettingsOpen } = useUIStore();
  const { user, logout } = useAuthStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return '今天';
    if (days === 1) return '昨天';
    if (days < 7) return `${days}天前`;
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
  };

  const handleDelete = async (e: React.MouseEvent, convId: number) => {
    e.stopPropagation();
    if (deleteConfirm === convId) {
      try {
        await api.delete(`/api/chat/conversations/${convId}`);
        removeConversation(convId);
      } catch (error) {
        console.error('Failed to delete conversation:', error);
      }
      setDeleteConfirm(null);
    } else {
      setDeleteConfirm(convId);
      setTimeout(() => setDeleteConfirm(null), 3000);
    }
  };

  const filteredConversations = searchQuery
    ? conversations.filter(conv => conv.title?.toLowerCase().includes(searchQuery.toLowerCase()))
    : conversations;

  return (
    <aside className={`${styles.sidebar} ${!isSidebarOpen ? styles.collapsed : ''}`}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.logo}>
          <span className={styles.logoIcon}>◈</span>
          <span className={styles.logoText}>Confluence</span>
        </div>
        <button className={styles.collapseBtn} onClick={toggleSidebar} title="收起侧边栏">
          <Icons.ChevronLeft />
        </button>
      </div>

      {/* New Chat Button */}
      <button className={styles.newChatBtn} onClick={onNewChat}>
        <Icons.Plus />
        <span>新对话</span>
      </button>

      {/* Search Box */}
      {conversations.length > 0 && (
        <div className={styles.searchBox}>
          <Icons.Search />
          <input
            type="text"
            placeholder="搜索对话..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={styles.searchInput}
          />
          {searchQuery && (
            <button className={styles.clearSearch} onClick={() => setSearchQuery('')}>
              <Icons.Close />
            </button>
          )}
        </div>
      )}

      {/* Content Area - Conversations only */}
      <div className={styles.content}>
        <div className={styles.conversationList}>
          {filteredConversations.length === 0 ? (
            <div className={styles.emptyState}>
              <p>{searchQuery ? '未找到匹配的对话' : '暂无对话'}</p>
              <p className={styles.emptyHint}>{searchQuery ? '尝试其他关键词' : '点击上方按钮开始新对话'}</p>
            </div>
          ) : (
            filteredConversations.map((conv, index) => (
              <button
                key={conv.id}
                className={`${styles.conversationItem} ${conv.id === currentConversationId ? styles.active : ''}`}
                onClick={() => onSelectConversation(conv.id)}
                style={{ animationDelay: `${index * 30}ms` }}
              >
                <div className={styles.convIcon}>
                  {conv.contextType === 'confluence' ? <Icons.Confluence /> : <Icons.Message />}
                </div>
                <div className={styles.convContent}>
                  <span className={styles.convTitle}>{conv.title || '新对话'}</span>
                  <span className={styles.convDate}>{formatDate(conv.updatedAt)}</span>
                </div>
                <button
                  className={`${styles.deleteBtn} ${deleteConfirm === conv.id ? styles.confirm : ''}`}
                  onClick={(e) => handleDelete(e, conv.id)}
                  title={deleteConfirm === conv.id ? '再次点击确认删除' : '删除对话'}
                >
                  <Icons.Trash />
                </button>
              </button>
            ))
          )}
          <p className={styles.hint}>提示：直接在聊天中粘贴 Confluence 链接即可</p>
        </div>
      </div>

      {/* Footer */}
      <div className={styles.footer}>
        {/* User Info */}
        <div className={styles.userInfo}>
          {user?.avatar_url ? (
            <img src={user.avatar_url} alt={user.name} className={styles.avatar} />
          ) : (
            <div className={styles.avatarPlaceholder}>
              {user?.name?.charAt(0) || 'U'}
            </div>
          )}
          <span className={styles.userName}>{user?.name || '用户'}</span>
        </div>

        {/* Actions */}
        <div className={styles.actions}>
          {user?.role === 'admin' && (
            <button className={styles.actionBtn} onClick={() => navigate('/admin')} title="管理后台">
              <Icons.Shield />
            </button>
          )}
          <button className={styles.actionBtn} onClick={toggleTheme} title={theme === 'light' ? '切换深色模式' : '切换浅色模式'}>
            {theme === 'light' ? <Icons.Moon /> : <Icons.Sun />}
          </button>
          <button className={styles.actionBtn} onClick={() => setSettingsOpen(true)} title="设置">
            <Icons.Settings />
          </button>
          <button className={styles.actionBtn} onClick={logout} title="退出登录">
            <Icons.Logout />
          </button>
        </div>
      </div>

      {/* Version */}
      <div className={styles.version}>v2.1.0</div>
    </aside>
  );
};

export default LeftPanel;
