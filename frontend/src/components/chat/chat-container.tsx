'use client';

import { useCallback } from 'react';
import { useChatStore } from '@/stores/chat-store';
import { useConnectionStore } from '@/stores/connection-store';
import { useWebSocket } from '@/hooks/use-websocket';
import { apiClient } from '@/lib/api-client';
import ChatInput from './chat-input';
import MessageBubble from './message-bubble';
import SessionSidebar from './session-sidebar';
import SuggestedQuestions from './suggested-questions';
import StreamingText from './streaming-text';
import { ErrorBoundary } from '@/components/ui/error-boundary';

export default function ChatContainer() {
  const {
    messages,
    isLoading,
    addMessage,
    setLoading,
    activeSessionId,
    streamingContent,
    streamingPhase,
    appendStreamChunk,
    clearStreaming,
  } = useChatStore();
  const { activeConnectionId } = useConnectionStore();

  const handleWsMessage = useCallback(
    (data: any) => {
      if (data.type === 'stream') {
        appendStreamChunk(data.chunk, data.phase);
      } else if (data.type === 'stream_start') {
        clearStreaming();
      } else if (data.type === 'chat_response') {
        clearStreaming();
        addMessage({
          id: data.message_id || crypto.randomUUID(),
          role: 'assistant',
          content: data.content,
          generated_sql: data.generated_sql,
          query_result_preview: data.query_result_preview,
          full_result_row_count: data.full_result_row_count,
          chart_config: data.chart_config,
          execution_time_ms: data.execution_time_ms,
          error_message: data.error_message,
          created_at: new Date().toISOString(),
        });
        setLoading(false);
      } else if (data.type === 'error') {
        clearStreaming();
        addMessage({
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.content || 'An error occurred.',
          error_message: data.content,
          created_at: new Date().toISOString(),
        });
        setLoading(false);
      }
    },
    [addMessage, setLoading, appendStreamChunk, clearStreaming],
  );

  const { send, isConnected } = useWebSocket({
    onMessage: handleWsMessage,
  });

  const handleSend = async (text: string) => {
    if (!text.trim() || isLoading || !activeConnectionId) return;

    addMessage({
      id: crypto.randomUUID(),
      role: 'user',
      content: text.trim(),
      created_at: new Date().toISOString(),
    });

    setLoading(true);
    clearStreaming();

    // Use WebSocket if connected, otherwise fall back to REST
    if (isConnected) {
      send({
        type: 'chat_message',
        message: text.trim(),
        connection_id: activeConnectionId,
        session_id: activeSessionId,
      });
    } else {
      try {
        const response = await apiClient('/chat/message', {
          method: 'POST',
          body: JSON.stringify({
            message: text.trim(),
            connection_id: activeConnectionId,
            session_id: activeSessionId,
          }),
        });

        addMessage({
          id: response.message_id || crypto.randomUUID(),
          role: 'assistant',
          content: response.content,
          generated_sql: response.generated_sql,
          query_result_preview: response.query_result_preview,
          full_result_row_count: response.full_result_row_count,
          chart_config: response.chart_config,
          execution_time_ms: response.execution_time_ms,
          error_message: response.error_message,
          created_at: new Date().toISOString(),
        });
      } catch (err: any) {
        addMessage({
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `Sorry, something went wrong: ${err.message}`,
          error_message: err.message,
          created_at: new Date().toISOString(),
        });
      } finally {
        setLoading(false);
      }
    }
  };

  const phaseLabel =
    streamingPhase === 'generating_sql'
      ? 'Generating SQL...'
      : streamingPhase === 'analyzing'
        ? 'Analyzing results...'
        : 'Thinking...';

  return (
    <div className="h-full flex">
      <SessionSidebar />
      <div className="flex-1 flex flex-col">
        <ErrorBoundary>
        <div className="flex-1 overflow-auto p-4 space-y-4">
          {messages.length === 0 && !isLoading && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <h2 className="text-2xl font-heading font-bold text-text-primary mb-2">
                Ask anything about your data
              </h2>
              <p className="text-text-secondary mb-8">
                I&apos;ll generate SQL, run it, and visualize the results for you.
              </p>
              <SuggestedQuestions onSelect={(question) => handleSend(question)} />
            </div>
          )}

          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {isLoading && (
            <div className="bg-bg-secondary rounded-lg p-4">
              {streamingContent ? (
                <div className="text-text-primary">
                  <div className="text-xs text-text-muted mb-2">{phaseLabel}</div>
                  <StreamingText content={streamingContent} isStreaming />
                </div>
              ) : (
                <div className="flex items-center gap-2 text-text-muted">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-brand-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-brand-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-brand-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                  <span className="text-sm">Analyzing your data...</span>
                </div>
              )}
            </div>
          )}
        </div>
        </ErrorBoundary>

        <ChatInput />
      </div>
    </div>
  );
}
