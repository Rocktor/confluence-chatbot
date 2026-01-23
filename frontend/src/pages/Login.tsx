import React, { useEffect, useState, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import api from '../utils/api';
import { useAuthStore } from '../store/authStore';

declare global {
  interface Window {
    DTFrameLogin: (
      config: { id: string; width: number; height: number },
      params: {
        redirect_uri: string;
        client_id: string;
        scope: string;
        response_type: string;
        state: string;
        prompt: string;
      },
      successCallback: (result: { redirectUrl: string; authCode: string; state: string }) => void,
      errorCallback: (errorMsg: string) => void
    ) => void;
  }
}

const Login: React.FC = () => {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const setUser = useAuthStore((state) => state.setUser);
  const [searchParams] = useSearchParams();
  const qrcodeRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');

    if (code && state) {
      handleCallback(code, state);
    } else {
      initQRCode();
    }
  }, []);

  const handleCallback = async (code: string, state: string) => {
    try {
      setLoading(true);
      const response = await api.post('/api/auth/qrcode/callback', null, {
        params: { code, state }
      });

      if (response.data.accessToken) {
        localStorage.setItem('access_token', response.data.accessToken);
        localStorage.setItem('refresh_token', response.data.refreshToken);
        setUser(response.data.user);
        navigate('/chat');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '登录失败');
      initQRCode();
    } finally {
      setLoading(false);
    }
  };

  const initQRCode = async () => {
    try {
      setLoading(true);
      setError('');

      const response = await api.post('/api/auth/qrcode/generate');
      const { state, clientId, redirectUri } = response.data;

      if (window.DTFrameLogin && qrcodeRef.current) {
        window.DTFrameLogin(
          {
            id: 'qrcode-container',
            width: 300,
            height: 300,
          },
          {
            redirect_uri: encodeURIComponent(redirectUri),
            client_id: clientId,
            scope: 'openid',
            response_type: 'code',
            state: state,
            prompt: 'consent',
          },
          (loginResult) => {
            const { authCode, state } = loginResult;
            window.location.href = `${redirectUri}?code=${authCode}&state=${state}`;
          },
          (errorMsg) => {
            console.error('扫码登录失败:', errorMsg);
            setError('扫码失败，请重试');
          }
        );
      }
    } catch (err) {
      setError('初始化登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <div style={{ textAlign: 'center' }}>
        <h1>Confluence Chatbot</h1>
        <p>使用钉钉扫码登录</p>
        <div
          id="qrcode-container"
          ref={qrcodeRef}
          style={{ margin: '20px auto', width: 300, height: 300 }}
        />
        {loading && <p>加载中...</p>}
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button onClick={initQRCode} style={{ marginTop: 10 }}>刷新二维码</button>
      </div>
    </div>
  );
};

export default Login;
