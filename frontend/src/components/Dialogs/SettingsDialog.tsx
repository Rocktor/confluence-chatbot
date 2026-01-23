import React, { useState, useEffect } from 'react';
import { useUIStore } from '../../store/chatStore';
import api from '../../utils/api';
import styles from './Dialogs.module.css';

const Icons = {
  X: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  ),
  Check: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  ),
  AlertCircle: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  )
};

interface ConfluenceConfig {
  id?: number;
  baseUrl: string;
  email: string;
  apiToken: string;
  spaceKey: string;
}

export const SettingsDialog: React.FC = () => {
  const { isSettingsOpen, setSettingsOpen } = useUIStore();
  const [config, setConfig] = useState<ConfluenceConfig>({
    baseUrl: 'https://docs.matrixback.com',
    email: '',
    apiToken: '',
    spaceKey: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<'success' | 'error' | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isSettingsOpen) {
      loadConfig();
    }
  }, [isSettingsOpen]);

  const loadConfig = async () => {
    try {
      const response = await api.get('/api/confluence/configs');
      if (response.data.length > 0) {
        const existingConfig = response.data[0];
        setConfig({
          id: existingConfig.id,
          baseUrl: 'https://docs.matrixback.com',
          email: existingConfig.email || '',
          apiToken: '', // Don't show existing token
          spaceKey: existingConfig.spaceKey || ''
        });
      } else {
        // No existing config, use defaults
        setConfig({
          baseUrl: 'https://docs.matrixback.com',
          email: '',
          apiToken: '',
          spaceKey: ''
        });
      }
    } catch (err) {
      console.error('Failed to load config:', err);
    }
  };

  const handleSave = async () => {
    // Validate required fields (use || '' to handle undefined)
    if (!(config.baseUrl || '').trim()) {
      setError('请填写 Confluence URL');
      return;
    }
    if (!(config.email || '').trim()) {
      setError('请填写邮箱');
      return;
    }
    if (!config.id && !(config.apiToken || '').trim()) {
      setError('请填写 API Token');
      return;
    }

    setIsLoading(true);
    setError('');
    try {
      const payload = {
        base_url: config.baseUrl,
        email: config.email,
        api_token: config.apiToken,
        space_key: config.spaceKey || null
      };
      if (config.id) {
        await api.put(`/api/confluence/configs/${config.id}`, payload);
      } else {
        await api.post('/api/confluence/configs', payload);
      }
      setSettingsOpen(false);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      // Handle validation error array or string
      if (Array.isArray(detail)) {
        setError(detail.map((d: any) => d.msg || d).join(', '));
      } else if (typeof detail === 'object') {
        setError(JSON.stringify(detail));
      } else {
        setError(detail || '保存失败');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleTest = async () => {
    // Validate required fields (use || '' to handle undefined)
    // 如果已有配置，允许 apiToken 为空（使用已保存的 token）
    if (!(config.baseUrl || '').trim() || !(config.email || '').trim()) {
      setError('请填写 URL 和用户名后再测试');
      return;
    }
    if (!config.id && !(config.apiToken || '').trim()) {
      setError('请填写 API Token 后再测试');
      return;
    }

    setIsTesting(true);
    setTestResult(null);
    setError('');
    try {
      await api.post('/api/confluence/test', {
        base_url: config.baseUrl,
        email: config.email,
        api_token: config.apiToken || null,
        space_key: config.spaceKey || null,
        config_id: config.id || null
      });
      setTestResult('success');
    } catch (err) {
      setTestResult('error');
    } finally {
      setIsTesting(false);
    }
  };

  if (!isSettingsOpen) return null;

  return (
    <div className={styles.overlay} onClick={() => setSettingsOpen(false)}>
      <div className={styles.dialog} onClick={e => e.stopPropagation()}>
        <div className={styles.dialogHeader}>
          <h2>Confluence 配置</h2>
          <button className={styles.closeBtn} onClick={() => setSettingsOpen(false)}>
            <Icons.X />
          </button>
        </div>

        <div className={styles.dialogContent}>
          <p className={styles.description}>
            配置您的 Confluence 连接信息，以便搜索和同步文档。
          </p>

          <div className={styles.formGroup}>
            <label className={styles.label}>Confluence URL</label>
            <input
              type="url"
              value={config.baseUrl}
              disabled
              className={`${styles.input} ${styles.inputDisabled}`}
            />
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label}>Confluence 用户名</label>
            <input
              type="text"
              value={config.email}
              onChange={e => setConfig({ ...config, email: e.target.value })}
              placeholder="例如: rongtao.wang"
              className={styles.input}
            />
            <span className={styles.hint}>
              Confluence 登录用户名（不是邮箱），通常是姓名拼音
            </span>
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label}>API Token</label>
            <input
              type="password"
              value={config.apiToken}
              onChange={e => setConfig({ ...config, apiToken: e.target.value })}
              placeholder={config.id ? '留空保持不变' : '输入 API Token'}
              className={styles.input}
            />
            <span className={styles.hint}>
              在 <a href="https://id.atlassian.com/manage-profile/security/api-tokens" target="_blank" rel="noopener noreferrer">Atlassian 账户设置</a> 中创建 API Token
            </span>
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label}>默认空间 Key（可选）</label>
            <input
              type="text"
              value={config.spaceKey}
              onChange={e => setConfig({ ...config, spaceKey: e.target.value })}
              placeholder="例如: DOCS"
              className={styles.input}
            />
          </div>

          {/* Test result */}
          {testResult && (
            <div className={`${styles.testResult} ${styles[testResult]}`}>
              {testResult === 'success' ? <Icons.Check /> : <Icons.AlertCircle />}
              <span>{testResult === 'success' ? '连接成功' : '连接失败，请检查配置'}</span>
            </div>
          )}

          {error && (
            <div className={`${styles.testResult} ${styles.error}`}>
              <Icons.AlertCircle />
              <span>{error}</span>
            </div>
          )}
        </div>

        <div className={styles.dialogFooter}>
          <button className={styles.testBtn} onClick={handleTest} disabled={isTesting}>
            {isTesting ? '测试中...' : '测试连接'}
          </button>
          <div className={styles.footerRight}>
            <button className={styles.cancelBtn} onClick={() => setSettingsOpen(false)}>
              取消
            </button>
            <button className={styles.submitBtn} onClick={handleSave} disabled={isLoading}>
              {isLoading ? '保存中...' : '保存'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsDialog;
