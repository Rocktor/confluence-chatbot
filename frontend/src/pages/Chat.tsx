import React, { useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useChatStore, useUIStore, useThemeStore, Conversation, Message } from '../store/chatStore';
import { LeftPanel } from '../components/LeftPanel';
import { MessageList, MessageInput } from '../components/ChatArea';
import { WriteBackDialog, SettingsDialog } from '../components/Dialogs';
import api from '../utils/api';
import styles from './Chat.module.css';

const Icons = {
  Menu: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="6" x2="21" y2="6" />
      <line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  )
};

const Chat: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const {
    conversations,
    currentConversationId,
    isLoading,
    setConversations,
    addConversation,
    updateConversationTitle,
    setCurrentConversationId,
    setMessages,
    addMessage,
    updateLastMessage,
    addToolCallMessage,
    updateToolCallResult,
    setIsLoading,
    setIsStreaming,
    setSelectedConfluencePage,
    setCurrentToolCall,
    clearChat
  } = useChatStore();
  const { isSidebarOpen, toggleSidebar } = useUIStore();
  const { theme } = useThemeStore();

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  // Initialize theme
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Check authentication
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

  // Load conversations
  useEffect(() => {
    loadConversations();
  }, []);

  // WebSocket connection
  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  const loadConversations = async () => {
    try {
      const response = await api.get('/api/chat/conversations');
      setConversations(response.data);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const loadMessages = async (conversationId: number) => {
    try {
      const response = await api.get(`/api/chat/conversations/${conversationId}/messages`);
      setMessages(response.data);
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  };

  const connectWebSocket = useCallback(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    // Use VITE_WS_URL if set, otherwise construct from current host
    const wsUrl = import.meta.env.VITE_WS_URL
      ? `${import.meta.env.VITE_WS_URL}?token=${token}`
      : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/chat/ws?token=${token}`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
      reconnectAttempts.current = 0; // Reset on successful connection
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'conversation_created':
          const newConv: Conversation = {
            id: data.conversation_id,
            title: data.title || '新对话',
            contextType: 'general',
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
          };
          addConversation(newConv);
          setCurrentConversationId(data.conversation_id);
          break;

        case 'title_updated':
          updateConversationTitle(data.conversation_id, data.title);
          break;

        case 'stream_start':
          setIsStreaming(true);
          // 不在这里创建空消息，等 stream_chunk 时按需创建
          break;

        case 'stream_chunk':
          // 检查最后一条消息是否是可追加的 assistant 消息
          const messages = useChatStore.getState().messages;
          const lastMsg = messages[messages.length - 1];
          const canAppend = lastMsg?.role === 'assistant' && !lastMsg.toolCall;

          if (!canAppend) {
            // 没有可追加的消息，先创建一个
            addMessage({ role: 'assistant', content: data.content });
          } else {
            updateLastMessage(data.content);
          }
          break;

        case 'stream_end':
          setIsStreaming(false);
          setIsLoading(false);
          setCurrentToolCall(null);
          break;

        case 'tool_call':
          setCurrentToolCall({ name: data.tool_name, displayName: data.display_name });
          addToolCallMessage(data.tool_name, data.display_name);
          break;

        case 'tool_result':
          updateToolCallResult(data.tool_name, data.result);
          setCurrentToolCall(null);
          break;

        case 'error':
          console.error('WebSocket error:', data.message);
          setIsLoading(false);
          setIsStreaming(false);
          break;
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Exponential backoff reconnect with max attempts
      if (reconnectAttempts.current < maxReconnectAttempts) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectAttempts.current++;
        console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current}/${maxReconnectAttempts})`);
        reconnectTimeoutRef.current = setTimeout(connectWebSocket, delay);
      } else {
        console.log('Max reconnect attempts reached');
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    wsRef.current = ws;
  }, []);

  const handleNewChat = () => {
    clearChat();
  };

  const handleStopGeneration = () => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    setIsLoading(false);
    setIsStreaming(false);
    setCurrentToolCall(null);
    reconnectAttempts.current = 0;
    connectWebSocket();
  };

  const handleSelectConversation = async (id: number) => {
    setCurrentConversationId(id);
    await loadMessages(id);

    // Check if conversation has confluence page
    const conv = conversations.find(c => c.id === id);
    if (conv?.confluencePageId) {
      try {
        const response = await api.get(`/api/confluence/pages/${conv.confluencePageId}`);
        setSelectedConfluencePage(response.data);
      } catch (error) {
        console.error('Failed to load confluence page:', error);
      }
    } else {
      setSelectedConfluencePage(null);
    }
  };

  const handleSendMessage = async (content: string, files?: File[]) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected');
      return;
    }

    // Upload files first if any
    let fileUrls: string[] = [];
    let imageUrl: string | undefined;

    if (files && files.length > 0) {
      try {
        const formData = new FormData();
        files.forEach(file => formData.append('files', file));

        const response = await api.post('/api/chat/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        fileUrls = response.data.urls || [];
        // Use first image as imageUrl for backward compatibility
        const imageFile = files.find(f => f.type.startsWith('image/'));
        if (imageFile) {
          imageUrl = fileUrls.find(url => url.includes(imageFile.name));
        }
      } catch (error) {
        console.error('Failed to upload files:', error);
      }
    }

    // Add user message to UI
    const userMessage: Message = {
      role: 'user',
      content,
      imageUrl,
      fileUrls
    };
    addMessage(userMessage);
    setIsLoading(true);

    // Send to WebSocket
    wsRef.current.send(JSON.stringify({
      conversation_id: currentConversationId,
      content,
      image_url: imageUrl,
      file_urls: fileUrls
    }));
  };

  const handleWriteBack = async (pageId: string, content: string, isNewPage: boolean, title?: string) => {
    try {
      if (isNewPage) {
        await api.post('/api/confluence/writeback/new', {
          title,
          content
        });
      } else {
        // pageId here is the internal database ID
        await api.post(`/api/confluence/writeback/${pageId}`, { content });
      }
    } catch (error) {
      console.error('Failed to write back:', error);
      throw error;
    }
  };

  return (
    <div className={styles.container}>
      {/* Left Panel */}
      <LeftPanel
        onNewChat={handleNewChat}
        onSelectConversation={handleSelectConversation}
      />

      {/* Main Chat Area */}
      <main className={styles.main}>
        {/* Header */}
        <header className={styles.header}>
          {!isSidebarOpen && (
            <button className={styles.menuBtn} onClick={toggleSidebar}>
              <Icons.Menu />
            </button>
          )}
          <div className={styles.headerTitle}>
            <h1>Confluence Chat</h1>
          </div>
        </header>

        {/* Messages */}
        <div className={styles.messagesContainer}>
          <MessageList />
        </div>

        {/* Input */}
        <MessageInput
          onSendMessage={handleSendMessage}
          onStop={handleStopGeneration}
          isLoading={isLoading}
        />
      </main>

      {/* Dialogs */}
      <WriteBackDialog onWriteBack={handleWriteBack} />
      <SettingsDialog />
    </div>
  );
};

export default Chat;
