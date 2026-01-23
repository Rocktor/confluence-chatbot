import React, { useState, useRef, useCallback } from 'react';
import { useChatStore, useUIStore } from '../../store/chatStore';
import styles from './ChatArea.module.css';

const Icons = {
  Send: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  ),
  Stop: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <rect x="6" y="6" width="12" height="12" rx="2" />
    </svg>
  ),
  Paperclip: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
    </svg>
  ),
  Image: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
      <circle cx="8.5" cy="8.5" r="1.5" />
      <polyline points="21 15 16 10 5 21" />
    </svg>
  ),
  X: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  ),
  Confluence: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <path d="M2.73 18.77c-.36.58-.27.85.2 1.2l3.47 2.33c.47.35.74.26 1.1-.32.36-.58 3.1-5.1 8.5-5.1 3.2 0 5.27 1.55 5.27 4.12 0 2.57-2.07 4.12-5.27 4.12H8.5c-.58 0-.85.27-.85.85v3.18c0 .58.27.85.85.85h7.5c5.8 0 10.5-3.7 10.5-9s-4.7-9-10.5-9c-7.9 0-12.4 6.1-12.77 6.77z" transform="scale(0.7) translate(5, 5)" />
    </svg>
  )
};

interface FilePreview {
  file: File;
  preview?: string;
  type: 'image' | 'file';
}

interface MessageInputProps {
  onSendMessage: (content: string, files?: File[]) => void;
  onStop?: () => void;
  isLoading?: boolean;
  disabled?: boolean;
}

export const MessageInput: React.FC<MessageInputProps> = ({ onSendMessage, onStop, isLoading, disabled }) => {
  const [input, setInput] = useState('');
  const [files, setFiles] = useState<FilePreview[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);

  const { selectedConfluencePage } = useChatStore();
  const { setWritebackDialogOpen } = useUIStore();

  const handleFileSelect = useCallback((selectedFiles: FileList | null) => {
    if (!selectedFiles) return;

    const newFiles: FilePreview[] = Array.from(selectedFiles).map(file => {
      const isImage = file.type.startsWith('image/');
      return {
        file,
        preview: isImage ? URL.createObjectURL(file) : undefined,
        type: isImage ? 'image' : 'file'
      };
    });

    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const removeFile = (index: number) => {
    setFiles(prev => {
      const newFiles = [...prev];
      if (newFiles[index].preview) {
        URL.revokeObjectURL(newFiles[index].preview!);
      }
      newFiles.splice(index, 1);
      return newFiles;
    });
  };

  const handlePaste = useCallback((e: React.ClipboardEvent) => {
    const items = e.clipboardData.items;
    const imageItems: File[] = [];

    for (let i = 0; i < items.length; i++) {
      if (items[i].type.startsWith('image/')) {
        const file = items[i].getAsFile();
        if (file) imageItems.push(file);
      }
    }

    if (imageItems.length > 0) {
      e.preventDefault();
      const newFiles: FilePreview[] = imageItems.map(file => ({
        file,
        preview: URL.createObjectURL(file),
        type: 'image'
      }));
      setFiles(prev => [...prev, ...newFiles]);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileSelect(e.dataTransfer.files);
  }, [handleFileSelect]);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if ((!input.trim() && files.length === 0) || disabled) return;

    onSendMessage(input, files.map(f => f.file));
    setInput('');
    files.forEach(f => f.preview && URL.revokeObjectURL(f.preview));
    setFiles([]);

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // Auto-resize
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
  };

  return (
    <div className={styles.inputArea}>
      {/* Context indicator */}
      {selectedConfluencePage && (
        <div className={styles.contextIndicator}>
          <Icons.Confluence />
          <span>正在与文档对话: {selectedConfluencePage.title}</span>
          <button className={styles.writebackBtn} onClick={() => setWritebackDialogOpen(true)}>
            写回 Confluence
          </button>
        </div>
      )}

      {/* File previews */}
      {files.length > 0 && (
        <div className={styles.filePreviews}>
          {files.map((f, idx) => (
            <div key={idx} className={styles.filePreview}>
              {f.type === 'image' && f.preview ? (
                <img src={f.preview} alt={f.file.name} />
              ) : (
                <div className={styles.fileIcon}>📄</div>
              )}
              <span className={styles.fileName}>{f.file.name}</span>
              <button className={styles.removeFile} onClick={() => removeFile(idx)}>
                <Icons.X />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input form */}
      <form
        className={`${styles.inputForm} ${isDragging ? styles.dragging : ''}`}
        onSubmit={handleSubmit}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className={styles.inputWrapper}>
          {/* File buttons */}
          <div className={styles.inputActions}>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.txt,.md"
              onChange={(e) => handleFileSelect(e.target.files)}
              style={{ display: 'none' }}
            />
            <input
              ref={imageInputRef}
              type="file"
              multiple
              accept="image/*"
              onChange={(e) => handleFileSelect(e.target.files)}
              style={{ display: 'none' }}
            />
            <button
              type="button"
              className={styles.actionBtn}
              onClick={() => fileInputRef.current?.click()}
              title="上传文件"
            >
              <Icons.Paperclip />
            </button>
            <button
              type="button"
              className={styles.actionBtn}
              onClick={() => imageInputRef.current?.click()}
              title="上传图片"
            >
              <Icons.Image />
            </button>
          </div>

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            onPaste={handlePaste}
            placeholder={isDragging ? '拖放文件到这里...' : '输入消息，或粘贴图片...'}
            className={styles.textarea}
            rows={1}
            disabled={disabled}
          />

          {/* Send button */}
          <button
            type={isLoading ? "button" : "submit"}
            className={`${styles.sendBtn} ${isLoading ? styles.loading : ''}`}
            onClick={isLoading ? onStop : undefined}
            disabled={!isLoading && (disabled || (!input.trim() && files.length === 0))}
          >
            {isLoading ? <Icons.Stop /> : <Icons.Send />}
          </button>
        </div>

        {/* Drag overlay */}
        {isDragging && (
          <div className={styles.dragOverlay}>
            <Icons.Paperclip />
            <span>拖放文件到这里</span>
          </div>
        )}
      </form>

      <p className={styles.hint}>
        按 Enter 发送，Shift + Enter 换行 · 支持粘贴图片
      </p>
    </div>
  );
};

export default MessageInput;
