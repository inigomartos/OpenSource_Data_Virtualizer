import { create } from 'zustand';
import type { ChatMessage, ChatSession } from '@/types/chat';

interface ChatState {
  sessions: ChatSession[];
  activeSessionId: string | null;
  messages: ChatMessage[];
  isLoading: boolean;
  sessionsLoading: boolean;
  streamingContent: string;
  streamingPhase: string;

  setSessions: (sessions: ChatSession[]) => void;
  setActiveSession: (id: string | null) => void;
  setMessages: (messages: ChatMessage[]) => void;
  addMessage: (message: ChatMessage) => void;
  setLoading: (loading: boolean) => void;
  setSessionsLoading: (loading: boolean) => void;
  appendStreamChunk: (chunk: string, phase: string) => void;
  clearStreaming: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  sessions: [],
  activeSessionId: null,
  messages: [],
  isLoading: false,
  sessionsLoading: true,
  streamingContent: '',
  streamingPhase: '',

  setSessions: (sessions) => set({ sessions, sessionsLoading: false }),
  setActiveSession: (id) => set({ activeSessionId: id }),
  setMessages: (messages) => set({ messages }),
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  setLoading: (loading) => set({ isLoading: loading }),
  setSessionsLoading: (loading) => set({ sessionsLoading: loading }),
  appendStreamChunk: (chunk, phase) =>
    set((state) => ({
      streamingContent: state.streamingContent + chunk,
      streamingPhase: phase,
    })),
  clearStreaming: () => set({ streamingContent: '', streamingPhase: '' }),
}));
