import React, { useState, useRef, useCallback, useEffect } from 'react';
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
  ),
  Check: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  ),
  Warning: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  )
};

interface FilePreview {
  file: File;
  preview?: string;
  type: 'image' | 'file';
}

interface ToastMessage {
  id: number;
  text: string;
  type: 'success' | 'info' | 'error';
}

const MAX_IMAGES = 5;

interface MessageInputProps {
  onSendMessage: (content: string, files?: File[]) => void;
  onStop?: () => void;
  isLoading?: boolean;
  isUploading?: boolean;
  disabled?: boolean;
}

export const MessageInput: React.FC<MessageInputProps> = ({ onSendMessage, onStop, isLoading, isUploading, disabled }) => {
  const [input, setInput] = useState('');
  const [files, setFiles] = useState<FilePreview[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const toastIdRef = useRef(0);

  const { selectedConfluencePage } = useChatStore();
  const { setWritebackDialogOpen } = useUIStore();

  const showToast = useCallback((text: string, type: 'success' | 'info' | 'error' = 'success') => {
    const id = ++toastIdRef.current;
    setToasts(prev => [...prev, { id, text, type }]);
    // Error toasts show longer
    const duration = type === 'error' ? 4000 : 2500;
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, duration);
  }, []);

  const handleFileSelect = useCallback((selectedFiles: FileList | null) => {
    if (!selectedFiles) return;

    // Block adding files while uploading
    if (isUploading) {
      showToast('正在上传中，请稍候...', 'error');
      return;
    }

    // Check image count limit
    const currentImageCount = files.filter(f => f.type === 'image').length;
    const newImageFiles = Array.from(selectedFiles).filter(f => f.type.startsWith('image/'));
    const newImageCount = newImageFiles.length;

    if (currentImageCount + newImageCount > MAX_IMAGES) {
      const remaining = MAX_IMAGES - currentImageCount;
      if (remaining <= 0) {
        showToast(`最多只能上传 ${MAX_IMAGES} 张图片`, 'error');
      } else {
        showToast(`还能上传 ${remaining} 张图片，已忽略多余的图片`, 'error');
      }
      // Only take allowed images
      if (remaining <= 0) return;
    }

    const newFiles: FilePreview[] = Array.from(selectedFiles).map(file => {
      const isImage = file.type.startsWith('image/');
      return {
        file,
        preview: isImage ? URL.createObjectURL(file) : undefined,
        type: isImage ? 'image' : 'file'
      };
    });

    // Filter images to respect limit
    const imagesToAdd = newFiles.filter(f => f.type === 'image').slice(0, MAX_IMAGES - currentImageCount);
    const filesToAdd = newFiles.filter(f => f.type === 'file');
    const finalFiles = [...imagesToAdd, ...filesToAdd];

    if (finalFiles.length === 0) return;

    setFiles(prev => [...prev, ...finalFiles]);

    const addedImageCount = imagesToAdd.length;
    const addedFileCount = filesToAdd.length;
    if (addedImageCount > 0) {
      showToast(`已添加 ${addedImageCount} 张图片`, 'success');
    }
    if (addedFileCount > 0) {
      showToast(`已添加 ${addedFileCount} 个文件`, 'success');
    }
  }, [showToast, files, isUploading]);

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

      // Block pasting while uploading
      if (isUploading) {
        showToast('正在上传中，请稍候...', 'error');
        return;
      }

      // Check image count limit
      const currentImageCount = files.filter(f => f.type === 'image').length;
      const remaining = MAX_IMAGES - currentImageCount;

      if (remaining <= 0) {
        showToast(`最多只能上传 ${MAX_IMAGES} 张图片`, 'error');
        return;
      }

      // Only take allowed images
      const imagesToPaste = imageItems.slice(0, remaining);
      if (imagesToPaste.length < imageItems.length) {
        showToast(`还能上传 ${remaining} 张图片，已忽略多余的图片`, 'error');
      }

      const newFiles: FilePreview[] = imagesToPaste.map(file => ({
        file,
        preview: URL.createObjectURL(file),
        type: 'image'
      }));
      setFiles(prev => [...prev, ...newFiles]);
      showToast(`已粘贴 ${imagesToPaste.length} 张图片`, 'success');
    }
  }, [showToast, files, isUploading]);

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

    // Block dropping while uploading
    if (isUploading) {
      showToast('正在上传中，请稍候...', 'error');
      return;
    }

    handleFileSelect(e.dataTransfer.files);
  }, [handleFileSelect, isUploading, showToast]);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if ((!input.trim() && files.length === 0) || disabled || isUploading) return;

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

  // Clean up previews on unmount
  useEffect(() => {
    return () => {
      files.forEach(f => f.preview && URL.revokeObjectURL(f.preview));
    };
  }, []);

  return (
    <div className={styles.inputArea}>
      {/* Toast notifications */}
      <div className={styles.toastContainer}>
        {toasts.map(toast => (
          <div key={toast.id} className={`${styles.toast} ${styles[toast.type]}`}>
            {toast.type === 'error' ? <Icons.Warning /> : <Icons.Check />}
            <span>{toast.text}</span>
          </div>
        ))}
      </div>

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

      {/* File previews with upload overlay */}
      {files.length > 0 && (
        <div className={`${styles.filePreviews} ${isUploading ? styles.filePreviewsUploading : ''}`}>
          {isUploading && (
            <div className={styles.uploadOverlay}>
              <span className={styles.uploadSpinner} />
              <span>正在上传...</span>
            </div>
          )}
          {files.map((f, idx) => (
            <div key={idx} className={styles.filePreview}>
              {f.type === 'image' && f.preview ? (
                <img src={f.preview} alt={f.file.name} />
              ) : (
                <div className={styles.fileIcon}>📄</div>
              )}
              <span className={styles.fileName}>{f.file.name}</span>
              <button
                className={styles.removeFile}
                onClick={() => removeFile(idx)}
                disabled={isUploading}
              >
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
              className={`${styles.actionBtn} ${isUploading ? styles.actionBtnDisabled : ''}`}
              onClick={() => !isUploading && fileInputRef.current?.click()}
              title={isUploading ? '正在上传中...' : '上传文件'}
              disabled={isUploading}
            >
              <Icons.Paperclip />
            </button>
            <button
              type="button"
              className={`${styles.actionBtn} ${isUploading ? styles.actionBtnDisabled : ''}`}
              onClick={() => !isUploading && imageInputRef.current?.click()}
              title={isUploading ? '正在上传中...' : '上传图片'}
              disabled={isUploading}
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
            className={`${styles.sendBtn} ${isLoading ? styles.loading : ''} ${isUploading ? styles.uploading : ''}`}
            onClick={isLoading ? onStop : undefined}
            disabled={isUploading || (!isLoading && (disabled || (!input.trim() && files.length === 0)))}
          >
            {isUploading ? (
              <span className={styles.uploadingSpinner} />
            ) : isLoading ? (
              <Icons.Stop />
            ) : (
              <Icons.Send />
            )}
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
        Enter 发送 · Shift+Enter 换行 · Ctrl/Cmd+V 粘贴图片
      </p>
    </div>
  );
};

export default MessageInput;
