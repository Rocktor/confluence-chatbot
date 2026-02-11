import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import api from '../utils/api';
import styles from './Admin.module.css';

interface Stats {
  totalUsers: number;
  activeUsers: number;
  totalConversations: number;
  totalMessages: number;
  totalTokens: number;
  usersToday: number;
  messagesToday: number;
}

interface User {
  id: number;
  name: string;
  email: string;
  role: string;
  isActive: boolean;
  lastLoginAt: string;
  createdAt: string;
  totalTokens: number;
  recentTokens: number;
}

interface TokenUsage {
  date: string;
  totalTokens: number;
  requestCount: number;
}

interface TopUser {
  id: number;
  name: string;
  totalTokens: number;
}

const Admin: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'tokens' | 'logs'>('overview');
  const [stats, setStats] = useState<Stats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [tokenUsage, setTokenUsage] = useState<TokenUsage[]>([]);
  const [topUsers, setTopUsers] = useState<TopUser[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [loginLogs, setLoginLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (user?.role !== 'admin') {
      navigate('/chat');
      return;
    }
    loadData();
  }, [user, navigate]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statsRes, usersRes, tokenRes, logsRes] = await Promise.all([
        api.get('/api/admin/stats'),
        api.get('/api/admin/users'),
        api.get('/api/admin/token-usage'),
        api.get('/api/admin/login-logs')
      ]);
      setStats(statsRes.data);
      setUsers(usersRes.data);
      setTokenUsage(tokenRes.data.dailyUsage);
      setTopUsers(tokenRes.data.topUsers || []);
      setLoginLogs(logsRes.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const toggleUserStatus = async (userId: number) => {
    try {
      await api.post(`/api/admin/users/${userId}/toggle`);
      setUsers(users.map(u => u.id === userId ? { ...u, isActive: !u.isActive } : u));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to toggle user status');
    }
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    // 转换为北京时间 (UTC+8)
    return new Date(dateStr).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' });
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString('zh-CN');
  };

  const loadTokenUsage = async (userId?: number | null) => {
    try {
      const url = userId ? `/api/admin/token-usage?user_id=${userId}` : '/api/admin/token-usage';
      const res = await api.get(url);
      setTokenUsage(res.data.dailyUsage);
      setTopUsers(res.data.topUsers || []);
    } catch (err) {
      console.error('Failed to load token usage:', err);
    }
  };

  const handleUserFilter = (userId: number | null) => {
    setSelectedUserId(userId);
    loadTokenUsage(userId);
  };

  if (loading) {
    return <div className={styles.loading}>加载中...</div>;
  }

  if (error) {
    return <div className={styles.error}>{error}</div>;
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>管理后台</h1>
        <button className={styles.backBtn} onClick={() => navigate('/chat')}>
          返回聊天
        </button>
      </header>

      <nav className={styles.tabs}>
        <button
          className={`${styles.tab} ${activeTab === 'overview' ? styles.active : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          概览
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'users' ? styles.active : ''}`}
          onClick={() => setActiveTab('users')}
        >
          用户管理
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'tokens' ? styles.active : ''}`}
          onClick={() => setActiveTab('tokens')}
        >
          Token 消耗
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'logs' ? styles.active : ''}`}
          onClick={() => setActiveTab('logs')}
        >
          登录日志
        </button>
      </nav>

      <main className={styles.content}>
        {activeTab === 'overview' && stats && (
          <div className={styles.overview}>
            <div className={styles.statsGrid}>
              <div className={styles.statCard}>
                <span className={styles.statValue}>{formatNumber(stats.totalUsers)}</span>
                <span className={styles.statLabel}>总用户数</span>
              </div>
              <div className={styles.statCard}>
                <span className={styles.statValue}>{formatNumber(stats.activeUsers)}</span>
                <span className={styles.statLabel}>活跃用户</span>
              </div>
              <div className={styles.statCard}>
                <span className={styles.statValue}>{formatNumber(stats.totalConversations)}</span>
                <span className={styles.statLabel}>总对话数</span>
              </div>
              <div className={styles.statCard}>
                <span className={styles.statValue}>{formatNumber(stats.totalMessages)}</span>
                <span className={styles.statLabel}>总消息数</span>
              </div>
              <div className={styles.statCard}>
                <span className={styles.statValue}>{formatNumber(stats.totalTokens)}</span>
                <span className={styles.statLabel}>总 Token 消耗</span>
              </div>
              <div className={styles.statCard}>
                <span className={styles.statValue}>{formatNumber(stats.usersToday)}</span>
                <span className={styles.statLabel}>今日新用户</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'users' && (
          <div className={styles.users}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>姓名</th>
                  <th>邮箱</th>
                  <th>角色</th>
                  <th>状态</th>
                  <th>7天Token</th>
                  <th>总Token</th>
                  <th>最后登录</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id}>
                    <td>{u.id}</td>
                    <td>{u.name}</td>
                    <td>{u.email || '-'}</td>
                    <td>
                      <span className={`${styles.badge} ${u.role === 'admin' ? styles.admin : ''}`}>
                        {u.role}
                      </span>
                    </td>
                    <td>
                      <span className={`${styles.badge} ${u.isActive ? styles.active : styles.inactive}`}>
                        {u.isActive ? '启用' : '禁用'}
                      </span>
                    </td>
                    <td>{formatNumber(u.recentTokens || 0)}</td>
                    <td>{formatNumber(u.totalTokens || 0)}</td>
                    <td>{formatDate(u.lastLoginAt)}</td>
                    <td>
                      <button
                        className={styles.actionBtn}
                        onClick={() => toggleUserStatus(u.id)}
                        disabled={u.id === user?.id}
                      >
                        {u.isActive ? '禁用' : '启用'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'tokens' && (
          <div className={styles.tokens}>
            <div className={styles.tokenHeader}>
              <h3>最近 30 天 Token 消耗</h3>
              <div className={styles.filterGroup}>
                <select
                  className={styles.select}
                  value={selectedUserId || ''}
                  onChange={(e) => handleUserFilter(e.target.value ? Number(e.target.value) : null)}
                >
                  <option value="">全部用户</option>
                  {users.map(u => (
                    <option key={u.id} value={u.id}>{u.name}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className={styles.tokenGrid}>
              {/* 每日消耗表 */}
              <div className={styles.tokenTable}>
                <h4>每日消耗</h4>
                <table className={styles.table}>
                  <thead>
                    <tr>
                      <th>日期</th>
                      <th>Token 消耗</th>
                      <th>请求次数</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tokenUsage.map((row, idx) => (
                      <tr key={idx}>
                        <td>{row.date}</td>
                        <td>{formatNumber(row.totalTokens)}</td>
                        <td>{formatNumber(row.requestCount)}</td>
                      </tr>
                    ))}
                    {tokenUsage.length === 0 && (
                      <tr><td colSpan={3} style={{textAlign: 'center'}}>暂无数据</td></tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Top 用户 */}
              {!selectedUserId && topUsers.length > 0 && (
                <div className={styles.tokenTable}>
                  <h4>消耗排行 (30天)</h4>
                  <table className={styles.table}>
                    <thead>
                      <tr>
                        <th>排名</th>
                        <th>用户</th>
                        <th>Token 消耗</th>
                      </tr>
                    </thead>
                    <tbody>
                      {topUsers.map((u, idx) => (
                        <tr key={u.id} onClick={() => handleUserFilter(u.id)} style={{cursor: 'pointer'}}>
                          <td>{idx + 1}</td>
                          <td>{u.name}</td>
                          <td>{formatNumber(u.totalTokens)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'logs' && (
          <div className={styles.logs}>
            <h3>登录日志</h3>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>用户</th>
                  <th>登录方式</th>
                  <th>IP 地址</th>
                  <th>时间</th>
                </tr>
              </thead>
              <tbody>
                {loginLogs.map((log, idx) => (
                  <tr key={idx}>
                    <td>{log.userName}</td>
                    <td>{log.loginType}</td>
                    <td>{log.ipAddress || '-'}</td>
                    <td>{formatDate(log.createdAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
};

export default Admin;
