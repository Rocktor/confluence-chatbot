import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Message {
  id?: number;
  role: 'user' | 'assistant';
  content: string;
  imageUrl?: string;
  fileUrls?: string[];
  createdAt?: string;
  toolCall?: {
    name: string;
    displayName: string;
    status: 'executing' | 'completed' | 'error';
    result?: any;
  };
}

export interface Conversation {
  id: number;
  title: string;
  confluencePageId?: number;
  contextType: 'general' | 'confluence';
  createdAt: string;
  updatedAt: string;
}

export interface ConfluencePage {
  id: number;
  pageId: string;
  title: string;
  spaceKey: string;
  contentMarkdown?: string;
}

interface ChatState {
  conversations: Conversation[];
  currentConversationId: number | null;
  messages: Message[];
  isLoading: boolean;
  isStreaming: boolean;
  selectedConfluencePage: ConfluencePage | null;
  currentToolCall: { name: string; displayName: string } | null;

  setConversations: (conversations: Conversation[]) => void;
  addConversation: (conversation: Conversation) => void;
  removeConversation: (id: number) => void;
  updateConversationTitle: (id: number, title: string) => void;
  setCurrentConversationId: (id: number | null) => void;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  updateLastMessage: (content: string) => void;
  removeLastEmptyMessage: () => void;
  addToolCallMessage: (toolName: string, displayName: string) => void;
  updateToolCallResult: (toolName: string, result: any) => void;
  setIsLoading: (loading: boolean) => void;
  setIsStreaming: (streaming: boolean) => void;
  setSelectedConfluencePage: (page: ConfluencePage | null) => void;
  setCurrentToolCall: (toolCall: { name: string; displayName: string } | null) => void;
  clearChat: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  conversations: [],
  currentConversationId: null,
  messages: [],
  isLoading: false,
  isStreaming: false,
  selectedConfluencePage: null,
  currentToolCall: null,

  setConversations: (conversations) => set({ conversations }),

  addConversation: (conversation) => set((state) => ({
    conversations: [conversation, ...state.conversations]
  })),

  removeConversation: (id) => set((state) => ({
    conversations: state.conversations.filter(conv => conv.id !== id),
    currentConversationId: state.currentConversationId === id ? null : state.currentConversationId,
    messages: state.currentConversationId === id ? [] : state.messages
  })),

  updateConversationTitle: (id, title) => set((state) => ({
    conversations: state.conversations.map(conv =>
      conv.id === id ? { ...conv, title } : conv
    )
  })),

  setCurrentConversationId: (id) => set({ currentConversationId: id }),

  setMessages: (messages) => set({ messages }),

  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),

  updateLastMessage: (content) => set((state) => {
    const messages = [...state.messages];
    const lastMessage = messages[messages.length - 1];
    if (lastMessage && lastMessage.role === 'assistant') {
      lastMessage.content += content;
    }
    return { messages };
  }),

  removeLastEmptyMessage: () => set((state) => {
    const messages = [...state.messages];
    const lastMessage = messages[messages.length - 1];
    if (lastMessage?.role === 'assistant' && !lastMessage.content?.trim() && !lastMessage.toolCall) {
      messages.pop();
    }
    return { messages };
  }),

  addToolCallMessage: (toolName, displayName) => set((state) => ({
    messages: [...state.messages, {
      role: 'assistant' as const,
      content: '',
      toolCall: { name: toolName, displayName, status: 'executing' as const }
    }]
  })),

  updateToolCallResult: (toolName, result) => set((state) => {
    const messages = [...state.messages];
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].toolCall?.name === toolName && messages[i].toolCall?.status === 'executing') {
        messages[i] = {
          ...messages[i],
          toolCall: { ...messages[i].toolCall!, status: 'completed', result }
        };
        break;
      }
    }
    return { messages };
  }),

  setIsLoading: (isLoading) => set({ isLoading }),

  setIsStreaming: (isStreaming) => set({ isStreaming }),

  setSelectedConfluencePage: (page) => set({ selectedConfluencePage: page }),

  setCurrentToolCall: (toolCall) => set({ currentToolCall: toolCall }),

  clearChat: () => set({ messages: [], currentConversationId: null, selectedConfluencePage: null, currentToolCall: null })
}));

// Theme Store
type Theme = 'light' | 'dark';

interface ThemeState {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: 'light',
      setTheme: (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        set({ theme });
      },
      toggleTheme: () => set((state) => {
        const newTheme = state.theme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        return { theme: newTheme };
      })
    }),
    {
      name: 'theme-storage',
      onRehydrateStorage: () => (state) => {
        if (state) {
          document.documentElement.setAttribute('data-theme', state.theme);
        }
      }
    }
  )
);

// UI State Store
interface UIState {
  isSidebarOpen: boolean;
  isSettingsOpen: boolean;
  isWritebackDialogOpen: boolean;
  toggleSidebar: () => void;
  setSettingsOpen: (open: boolean) => void;
  setWritebackDialogOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  isSidebarOpen: true,
  isSettingsOpen: false,
  isWritebackDialogOpen: false,
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  setSettingsOpen: (open) => set({ isSettingsOpen: open }),
  setWritebackDialogOpen: (open) => set({ isWritebackDialogOpen: open })
}));
