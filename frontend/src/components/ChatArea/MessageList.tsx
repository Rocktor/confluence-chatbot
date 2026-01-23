import React, { useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useChatStore, Message } from '../../store/chatStore';
import { useAuthStore } from '../../store/authStore';
import styles from './ChatArea.module.css';

const Icons = {
  Bot: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <rect x="3" y="11" width="18" height="10" rx="2" />
      <circle cx="12" cy="5" r="2" />
      <path d="M12 7v4" />
      <line x1="8" y1="16" x2="8" y2="16" />
      <line x1="16" y1="16" x2="16" y2="16" />
    </svg>
  ),
  Copy: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
  ),
  Check: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  ),
  Tool: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
    </svg>
  ),
  Spinner: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={styles.spinner}>
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  )
};

interface MessageItemProps {
  message: Message;
}

const MessageItem: React.FC<MessageItemProps> = ({ message }) => {
  const { user } = useAuthStore();
  const [copied, setCopied] = React.useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isUser = message.role === 'user';

  // Tool call message
  if (message.toolCall) {
    return (
      <div className={`${styles.messageWrapper} ${styles.assistant}`}>
        <div className={styles.messageContainer}>
          <div className={styles.avatar}>
            <Icons.Bot />
          </div>
          <div className={styles.messageContent}>
            <div className={styles.messageHeader}>
              <span className={styles.roleName}>AI 助手</span>
            </div>
            <div className={`${styles.messageBubble} ${styles.aiBubble} ${styles.toolCallBubble}`}>
              <div className={styles.toolCallStatus}>
                {message.toolCall.status === 'executing' ? (
                  <>
                    <Icons.Spinner />
                    <span>正在{message.toolCall.displayName}...</span>
                    <span className={styles.toolHint}>AI 正在处理您的请求</span>
                  </>
                ) : (
                  <>
                    <Icons.Check />
                    <span>{message.toolCall.displayName}完成</span>
                  </>
                )}
              </div>
              {message.toolCall.result && message.toolCall.result.success && (
                <div className={styles.toolCallResult}>
                  {message.toolCall.name === 'read_confluence_page' && message.toolCall.result.title && (
                    <a href={message.toolCall.result.url} target="_blank" rel="noopener noreferrer">
                      {message.toolCall.result.title}
                    </a>
                  )}
                  {message.toolCall.name === 'search_confluence' && message.toolCall.result.results && (
                    <span>找到 {message.toolCall.result.count} 个结果</span>
                  )}
                  {message.toolCall.name === 'create_confluence_page' && message.toolCall.result.url && (
                    <a href={message.toolCall.result.url} target="_blank" rel="noopener noreferrer">
                      查看新页面: {message.toolCall.result.title}
                    </a>
                  )}
                  {message.toolCall.name === 'update_confluence_page' && message.toolCall.result.url && (
                    <a href={message.toolCall.result.url} target="_blank" rel="noopener noreferrer">
                      查看更新: {message.toolCall.result.title}
                    </a>
                  )}
                </div>
              )}
              {message.toolCall.result && !message.toolCall.result.success && (
                <div className={styles.toolCallError}>
                  {message.toolCall.result.error}
                </div>
              )}
              {/* Show AI response content if present */}
              {message.content && (
                <div className={`markdown-content ${styles.textContent}`}>
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`${styles.messageWrapper} ${isUser ? styles.user : styles.assistant}`}>
      <div className={styles.messageContainer}>
        {/* Avatar */}
        <div className={styles.avatar}>
          {isUser ? (
            user?.avatar_url ? (
              <img src={user.avatar_url} alt={user.name} />
            ) : (
              <span>{user?.name?.charAt(0) || 'U'}</span>
            )
          ) : (
            <Icons.Bot />
          )}
        </div>

        {/* Content */}
        <div className={styles.messageContent}>
          <div className={styles.messageHeader}>
            <span className={styles.roleName}>{isUser ? user?.name || '你' : 'AI 助手'}</span>
            {message.createdAt && (
              <span className={styles.timestamp}>
                {new Date(message.createdAt).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
          </div>

          <div className={`${styles.messageBubble} ${isUser ? styles.userBubble : styles.aiBubble}`}>
            {/* File attachments */}
            {message.fileUrls && message.fileUrls.length > 0 && (
              <div className={styles.attachments}>
                {message.fileUrls.map((url, idx) => (
                  <a key={idx} href={url} target="_blank" rel="noopener noreferrer" className={styles.attachment}>
                    📎 附件 {idx + 1}
                  </a>
                ))}
              </div>
            )}

            {/* Image */}
            {message.imageUrl && (
              <div className={styles.imageContainer}>
                <img src={message.imageUrl} alt="上传的图片" className={styles.messageImage} />
              </div>
            )}

            {/* Text content */}
            <div className={`markdown-content ${styles.textContent}`}>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  a: ({ href, children }) => (
                    <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>
                  )
                }}
              >{message.content}</ReactMarkdown>
            </div>

            {/* Copy button for AI messages */}
            {!isUser && message.content && (
              <button className={styles.copyBtn} onClick={handleCopy} title="复制">
                {copied ? <Icons.Check /> : <Icons.Copy />}
                <span>{copied ? '已复制' : '复制'}</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Typing indicator
const TypingIndicator: React.FC = () => (
  <div className={`${styles.messageWrapper} ${styles.assistant}`}>
    <div className={styles.messageContainer}>
      <div className={styles.avatar}>
        <Icons.Bot />
      </div>
      <div className={styles.messageContent}>
        <div className={styles.messageHeader}>
          <span className={styles.roleName}>AI 助手</span>
        </div>
        <div className={`${styles.messageBubble} ${styles.aiBubble}`}>
          <div className={styles.typingIndicator}>
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    </div>
  </div>
);

export const MessageList: React.FC = () => {
  const { messages, isLoading, isStreaming } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className={styles.emptyState}>
        <div className={styles.emptyIcon}>◈</div>
        <h2 className={styles.emptyTitle}>开始新对话</h2>
        <p className={styles.emptyDescription}>
          直接粘贴 Confluence 链接，AI 会自动读取并帮你总结、分析或修改文档
        </p>
      </div>
    );
  }

  return (
    <div className={styles.messageList}>
      {messages.map((msg, idx) => (
        <MessageItem key={idx} message={msg} />
      ))}
      {isLoading && !isStreaming && <TypingIndicator />}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;
