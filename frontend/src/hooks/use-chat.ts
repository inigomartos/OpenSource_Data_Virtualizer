import useSWR from 'swr';
import { apiClient } from '@/lib/api-client';
import { useChatStore } from '@/stores/chat-store';
import type { ChatSession } from '@/types/chat';

export function useChatSessions() {
  const { data, error, mutate } = useSWR<{ sessions: ChatSession[] }>(
    '/chat/sessions',
    apiClient
  );

  return {
    sessions: data?.sessions || [],
    isLoading: !error && !data,
    error,
    refresh: mutate,
  };
}

export function useChatHistory(sessionId: string | null) {
  const { data, error, mutate } = useSWR(
    sessionId ? `/chat/history/${sessionId}` : null,
    apiClient
  );

  return {
    messages: data?.messages || [],
    isLoading: !error && !data,
    error,
    refresh: mutate,
  };
}
