import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Message {
  id?: string;  // Unique ID for React key (generated automatically by addMessage)
  dbId?: number;  // Database ID (from server)
  role: 'user' | 'assistant';
  content: string;
  imageUrl?: string;
  fileUrls?: string[];
  createdAt?: string;
  thinkingContent?: string;  // Gemini thinking model output
  toolCall?: {
    name: string;
    displayName: string;
    status: 'executing' | 'completed' | 'error';
    result?: any;
  };
}

// Generate unique message ID
const generateMessageId = (): string =>
  `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

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
  isUploading: boolean;
  isThinking: boolean;
  thinkingBuffer: string;
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
  setIsUploading: (uploading: boolean) => void;
  setIsThinking: (thinking: boolean) => void;
  appendThinkingBuffer: (content: string) => void;
  clearThinkingBuffer: () => void;
  setSelectedConfluencePage: (page: ConfluencePage | null) => void;
  setCurrentToolCall: (toolCall: { name: string; displayName: string } | null) => void;
  clearChat: () => void;
  updateLastUserMessage: (imageUrl?: string, fileUrls?: string[]) => void;
  removeLastMessage: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  conversations: [],
  currentConversationId: null,
  messages: [],
  isLoading: false,
  isStreaming: false,
  isUploading: false,
  isThinking: false,
  thinkingBuffer: '',
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

  setMessages: (messages) => set({
    messages: messages.map(msg => ({
      ...msg,
      id: msg.id || generateMessageId()  // Ensure all messages have id
    }))
  }),

  addMessage: (message) => set((state) => ({
    messages: [...state.messages, { ...message, id: message.id || generateMessageId() }]
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
      id: generateMessageId(),
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

  setIsUploading: (isUploading) => set({ isUploading }),

  setIsThinking: (isThinking) => set({ isThinking }),

  appendThinkingBuffer: (content) => set((state) => ({
    thinkingBuffer: state.thinkingBuffer + content
  })),

  clearThinkingBuffer: () => set({ thinkingBuffer: '' }),

  setSelectedConfluencePage: (page) => set({ selectedConfluencePage: page }),

  setCurrentToolCall: (toolCall) => set({ currentToolCall: toolCall }),

  clearChat: () => set({ messages: [], currentConversationId: null, selectedConfluencePage: null, currentToolCall: null }),

  updateLastUserMessage: (imageUrl?: string, fileUrls?: string[]) => set((state) => {
    const messages = [...state.messages];
    // Find the last user message from the end
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === 'user') {
        messages[i] = { ...messages[i], imageUrl, fileUrls };
        break;
      }
    }
    return { messages };
  }),

  removeLastMessage: () => set((state) => {
    const messages = [...state.messages];
    if (messages.length > 0) {
      messages.pop();
    }
    return { messages };
  })
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

// Model Store
export type ModelId = 'gpt-5.1' | 'gpt-5.2' | 'gemini-3-pro';

export interface ModelOption {
  id: ModelId;
  name: string;
  provider: string;
}

export const MODEL_OPTIONS: ModelOption[] = [
  { id: 'gpt-5.1', name: 'GPT-5.1', provider: 'Azure' },
  { id: 'gpt-5.2', name: 'GPT-5.2', provider: 'Azure' },
  { id: 'gemini-3-pro', name: 'Gemini 3 Pro', provider: 'Google' },
];

interface ModelState {
  currentModel: ModelId;
  setCurrentModel: (model: ModelId) => void;
}

export const useModelStore = create<ModelState>()(
  persist(
    (set) => ({
      currentModel: 'gpt-5.1' as ModelId,
      setCurrentModel: (model) => set({ currentModel: model }),
    }),
    { name: 'model-storage' }
  )
);

export const useUIStore = create<UIState>((set) => ({
  isSidebarOpen: true,
  isSettingsOpen: false,
  isWritebackDialogOpen: false,
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  setSettingsOpen: (open) => set({ isSettingsOpen: open }),
  setWritebackDialogOpen: (open) => set({ isWritebackDialogOpen: open })
}));

// Review Prompt Store
export type ReviewToolId = 'review' | 'experiment-review' | 'sla-review' | 'meeting-submission-review';

export const DEFAULT_REVIEW_PROMPTS: Record<ReviewToolId, { empty: string; review: string }> = {
  'review': {
    empty: '请帮我审核会议材料。\n\n（请先发送 Confluence 页面链接，或直接粘贴/上传待审阅的文档内容）',
    review: '请根据营销服会议材料审稿标准，对上面讨论的文档内容进行完整审稿评分。',
  },
  'experiment-review': {
    empty: '请帮我审核实验复盘文档。\n\n（请先发送 Confluence 页面链接，或直接粘贴/上传待审阅的实验复盘内容）',
    review: '请根据运策实验复盘审稿标准，对上面讨论的文档内容进行完整审稿评分。',
  },
  'sla-review': {
    empty: '请帮我审核SLA合同。\n\n（请先发送 Confluence 页面链接，或直接粘贴/上传待审阅的SLA合同内容）',
    review: '请根据SLA合同审稿标准，对上面讨论的合同内容进行完整审稿评分。',
  },
  'meeting-submission-review': {
    empty: '请帮我审核营销服会材料。\n\n（请先发送 Confluence 页面链接，或直接粘贴/上传待审核的议题材料内容）',
    review: '请根据营销服会材料审核规范（Gate+Score模式），对上面的议题材料进行完整的10分制结构化评分审核。底线层4项逐项检查，上限层4项评级，结合CEO判定模式预判风险，给出三态结论和具体修改建议。',
  },
};

interface ReviewPromptState {
  customPrompts: Partial<Record<ReviewToolId, string>>;
  setCustomPrompt: (toolId: ReviewToolId, prompt: string) => void;
  resetPrompt: (toolId: ReviewToolId) => void;
}

export const useReviewPromptStore = create<ReviewPromptState>()(
  persist(
    (set) => ({
      customPrompts: {},
      setCustomPrompt: (toolId, prompt) => set((state) => ({
        customPrompts: { ...state.customPrompts, [toolId]: prompt }
      })),
      resetPrompt: (toolId) => set((state) => {
        const { [toolId]: _, ...rest } = state.customPrompts;
        return { customPrompts: rest };
      }),
    }),
    { name: 'review-prompt-storage' }
  )
);
