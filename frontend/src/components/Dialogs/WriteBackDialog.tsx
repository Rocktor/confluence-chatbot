import React, { useState } from 'react';
import { useChatStore, useUIStore } from '../../store/chatStore';
import styles from './Dialogs.module.css';

const Icons = {
  X: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  ),
  Upload: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
  ),
  FileText: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  )
};

interface WriteBackDialogProps {
  onWriteBack: (pageId: string, content: string, isNewPage: boolean, title?: string) => Promise<void>;
}

export const WriteBackDialog: React.FC<WriteBackDialogProps> = ({ onWriteBack }) => {
  const { isWritebackDialogOpen, setWritebackDialogOpen } = useUIStore();
  const { selectedConfluencePage, messages } = useChatStore();

  const [mode, setMode] = useState<'update' | 'new'>('update');
  const [newPageTitle, setNewPageTitle] = useState('');
  const [selectedContent, setSelectedContent] = useState('last');
  const [isLoading, setIsLoading] = useState(false);

  if (!isWritebackDialogOpen) return null;

  const getContentToWrite = () => {
    if (selectedContent === 'last') {
      const lastAiMessage = [...messages].reverse().find(m => m.role === 'assistant');
      return lastAiMessage?.content || '';
    }
    return messages
      .filter(m => m.role === 'assistant')
      .map(m => m.content)
      .join('\n\n---\n\n');
  };

  const handleSubmit = async () => {
    setIsLoading(true);
    try {
      const content = getContentToWrite();
      // Use internal database ID for update, not Confluence pageId
      const pageId = mode === 'update' ? String(selectedConfluencePage?.id || '') : '';
      await onWriteBack(pageId, content, mode === 'new', newPageTitle);
      setWritebackDialogOpen(false);
    } catch (error) {
      console.error('Write back failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.overlay} onClick={() => setWritebackDialogOpen(false)}>
      <div className={styles.dialog} onClick={e => e.stopPropagation()}>
        <div className={styles.dialogHeader}>
          <h2>写回 Confluence</h2>
          <button className={styles.closeBtn} onClick={() => setWritebackDialogOpen(false)}>
            <Icons.X />
          </button>
        </div>

        <div className={styles.dialogContent}>
          {/* Mode selection */}
          <div className={styles.modeSelection}>
            <button
              className={`${styles.modeBtn} ${mode === 'update' ? styles.active : ''}`}
              onClick={() => setMode('update')}
              disabled={!selectedConfluencePage}
            >
              <Icons.FileText />
              <span>更新现有页面</span>
            </button>
            <button
              className={`${styles.modeBtn} ${mode === 'new' ? styles.active : ''}`}
              onClick={() => setMode('new')}
            >
              <Icons.Upload />
              <span>创建新页面</span>
            </button>
          </div>

          {/* Update mode info */}
          {mode === 'update' && selectedConfluencePage && (
            <div className={styles.pageInfo}>
              <span className={styles.label}>目标页面</span>
              <span className={styles.value}>{selectedConfluencePage.title}</span>
            </div>
          )}

          {/* New page title */}
          {mode === 'new' && (
            <div className={styles.formGroup}>
              <label className={styles.label}>新页面标题</label>
              <input
                type="text"
                value={newPageTitle}
                onChange={e => setNewPageTitle(e.target.value)}
                placeholder="输入页面标题..."
                className={styles.input}
              />
            </div>
          )}

          {/* Content selection */}
          <div className={styles.formGroup}>
            <label className={styles.label}>写入内容</label>
            <div className={styles.radioGroup}>
              <label className={styles.radio}>
                <input
                  type="radio"
                  name="content"
                  value="last"
                  checked={selectedContent === 'last'}
                  onChange={() => setSelectedContent('last')}
                />
                <span>最后一条 AI 回复</span>
              </label>
              <label className={styles.radio}>
                <input
                  type="radio"
                  name="content"
                  value="all"
                  checked={selectedContent === 'all'}
                  onChange={() => setSelectedContent('all')}
                />
                <span>所有 AI 回复</span>
              </label>
            </div>
          </div>

          {/* Preview */}
          <div className={styles.preview}>
            <span className={styles.label}>内容预览</span>
            <div className={styles.previewContent}>
              {getContentToWrite().slice(0, 500)}
              {getContentToWrite().length > 500 && '...'}
            </div>
          </div>
        </div>

        <div className={styles.dialogFooter}>
          <button className={styles.cancelBtn} onClick={() => setWritebackDialogOpen(false)}>
            取消
          </button>
          <button
            className={styles.submitBtn}
            onClick={handleSubmit}
            disabled={isLoading || (mode === 'new' && !newPageTitle.trim())}
          >
            {isLoading ? '写入中...' : '确认写入'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default WriteBackDialog;
