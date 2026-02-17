import useSWR from 'swr';
import { apiClient } from '@/lib/api-client';
import { ListResponse } from '@/types/common';
import type { ChatSession, ChatMessage } from '@/types/chat';

export function useChatSessions() {
  const { data, error, mutate } = useSWR<ListResponse<ChatSession>>(
    '/chat/sessions',
    apiClient
  );

  return {
    sessions: data?.data || [],
    isLoading: !error && !data,
    error,
    refresh: mutate,
  };
}

export function useChatHistory(sessionId: string | null) {
  const { data, error, mutate } = useSWR<ListResponse<ChatMessage>>(
    sessionId ? `/chat/history/${sessionId}` : null,
    apiClient
  );

  return {
    messages: data?.data || [],
    isLoading: !error && !data,
    error,
    refresh: mutate,
  };
}
