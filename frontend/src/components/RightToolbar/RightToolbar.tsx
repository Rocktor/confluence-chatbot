import React, { useState, useRef, useEffect, useCallback } from 'react';
import ReactDOM from 'react-dom';
import { useChatStore, useModelStore, MODEL_OPTIONS } from '../../store/chatStore';
import styles from './RightToolbar.module.css';

interface RightToolbarProps {
  onSendMessage: (content: string) => void;
}

const Icons = {
  Review: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 11l3 3L22 4" />
      <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
    </svg>
  ),
  Export: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  ),
  Summary: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="17" y1="10" x2="3" y2="10" />
      <line x1="21" y1="6" x2="3" y2="6" />
      <line x1="21" y1="14" x2="3" y2="14" />
      <line x1="17" y1="18" x2="3" y2="18" />
    </svg>
  ),
  ChevronLeft: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="15 18 9 12 15 6" />
    </svg>
  ),
  Model: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2L2 7l10 5 10-5-10-5z" />
      <path d="M2 17l10 5 10-5" />
      <path d="M2 12l10 5 10-5" />
    </svg>
  ),
  Check: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  ),
  ExperimentReview: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 3h6v6l4 8H5l4-8V3z" />
      <line x1="9" y1="3" x2="15" y2="3" />
      <circle cx="12" cy="15" r="1" />
    </svg>
  ),
  ContractReview: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
    </svg>
  ),
  MeetingReview: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <path d="M9 7h6" />
      <path d="M9 11h6" />
      <path d="M9 15l2 2 4-4" />
    </svg>
  ),
};

export const RightToolbar: React.FC<RightToolbarProps> = ({ onSendMessage }) => {
  const [expanded, setExpanded] = useState(false);
  const [modelMenuOpen, setModelMenuOpen] = useState(false);
  const [menuPos, setMenuPos] = useState({ top: 0, right: 0 });
  const { messages, isLoading } = useChatStore();
  const { currentModel, setCurrentModel } = useModelStore();
  const modelBtnRef = useRef<HTMLButtonElement>(null);
  const modelMenuRef = useRef<HTMLDivElement>(null);

  // Close model menu on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        modelMenuRef.current && !modelMenuRef.current.contains(e.target as Node) &&
        modelBtnRef.current && !modelBtnRef.current.contains(e.target as Node)
      ) {
        setModelMenuOpen(false);
      }
    };
    if (modelMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [modelMenuOpen]);

  const toggleModelMenu = useCallback(() => {
    if (!modelMenuOpen && modelBtnRef.current) {
      const rect = modelBtnRef.current.getBoundingClientRect();
      setMenuPos({
        top: rect.top,
        right: window.innerWidth - rect.left + 8,
      });
    }
    setModelMenuOpen(prev => !prev);
  }, [modelMenuOpen]);

  const handleReview = () => {
    if (isLoading) return;

    if (messages.length === 0) {
      onSendMessage("请帮我审核会议材料。\n\n（请先发送 Confluence 页面链接，或直接粘贴/上传待审阅的文档内容）");
    } else {
      onSendMessage("请根据营销服会议材料审稿标准，对上面讨论的文档内容进行完整审稿评分。");
    }
  };

  const handleExperimentReview = () => {
    if (isLoading) return;

    if (messages.length === 0) {
      onSendMessage("请帮我审核实验复盘文档。\n\n（请先发送 Confluence 页面链接，或直接粘贴/上传待审阅的实验复盘内容）");
    } else {
      onSendMessage("请根据运策实验复盘审稿标准，对上面讨论的文档内容进行完整审稿评分。");
    }
  };

  const handleSlaReview = () => {
    if (isLoading) return;

    if (messages.length === 0) {
      onSendMessage("请帮我审核SLA合同。\n\n（请先发送 Confluence 页面链接，或直接粘贴/上传待审阅的SLA合同内容）");
    } else {
      onSendMessage("请根据SLA合同审稿标准，对上面讨论的合同内容进行完整审稿评分。");
    }
  };

  const handleMeetingSubmissionReview = () => {
    if (isLoading) return;

    if (messages.length === 0) {
      onSendMessage("请帮我审核上会材料。\n\n（请先发送 Confluence 页面链接，或直接粘贴/上传待审阅的上会材料内容）");
    } else {
      onSendMessage("请根据营销服会上会材料审核规范，对上面讨论的材料进行完整结构化审核。");
    }
  };

  const currentModelOption = MODEL_OPTIONS.find(m => m.id === currentModel) || MODEL_OPTIONS[0];

  const tools = [
    { id: 'review', label: '审稿', icon: <Icons.Review />, onClick: handleReview, disabled: false },
    { id: 'experiment-review', label: '复盘审稿', icon: <Icons.ExperimentReview />, onClick: handleExperimentReview, disabled: false },
    { id: 'sla-review', label: 'SLA审稿', icon: <Icons.ContractReview />, onClick: handleSlaReview, disabled: false },
    { id: 'meeting-submission-review', label: '婷简单', icon: <Icons.MeetingReview />, onClick: handleMeetingSubmissionReview, disabled: false },
    { id: 'export', label: '导出', icon: <Icons.Export />, onClick: () => {}, disabled: true, tooltip: '即将推出' },
    { id: 'summary', label: '摘要', icon: <Icons.Summary />, onClick: () => {}, disabled: true, tooltip: '即将推出' },
  ];

  const modelMenu = modelMenuOpen
    ? ReactDOM.createPortal(
        <div
          ref={modelMenuRef}
          className={styles.modelMenu}
          style={{ top: menuPos.top, right: menuPos.right }}
        >
          {MODEL_OPTIONS.map((option) => (
            <button
              key={option.id}
              className={`${styles.modelMenuItem} ${option.id === currentModel ? styles.active : ''}`}
              onClick={() => {
                setCurrentModel(option.id);
                setModelMenuOpen(false);
              }}
            >
              <div className={styles.modelInfo}>
                <span className={styles.modelName}>{option.name}</span>
                <span className={styles.modelProvider}>{option.provider}</span>
              </div>
              {option.id === currentModel && (
                <span className={styles.checkIcon}><Icons.Check /></span>
              )}
            </button>
          ))}
        </div>,
        document.body
      )
    : null;

  return (
    <div className={`${styles.toolbar} ${expanded ? styles.expanded : ''}`}>
      <div className={styles.toolList}>
        {/* Model Selector */}
        <div className={styles.modelSelector}>
          <button
            ref={modelBtnRef}
            className={styles.toolBtn}
            onClick={toggleModelMenu}
            title={expanded ? undefined : currentModelOption.name}
          >
            <span className={styles.toolIcon}><Icons.Model /></span>
            <span className={styles.toolLabel}>{currentModelOption.name}</span>
            {!expanded && (
              <span className={styles.tooltip}>{currentModelOption.name}</span>
            )}
          </button>
        </div>

        <div className={styles.divider} />

        {/* Tool buttons */}
        {tools.map((tool) => (
          <button
            key={tool.id}
            className={`${styles.toolBtn} ${tool.disabled ? styles.disabled : ''}`}
            onClick={tool.disabled ? undefined : tool.onClick}
            title={expanded ? undefined : (tool.tooltip || tool.label)}
          >
            <span className={styles.toolIcon}>{tool.icon}</span>
            <span className={styles.toolLabel}>{tool.label}</span>
            {!expanded && (
              <span className={styles.tooltip}>{tool.tooltip || tool.label}</span>
            )}
          </button>
        ))}
      </div>

      <button className={styles.toggleBtn} onClick={() => setExpanded(!expanded)}>
        <span className={`${styles.toggleIcon} ${expanded ? styles.rotated : ''}`}>
          <Icons.ChevronLeft />
        </span>
      </button>

      {/* Model menu rendered via portal to avoid overflow:hidden clipping */}
      {modelMenu}
    </div>
  );
};

export default RightToolbar;
