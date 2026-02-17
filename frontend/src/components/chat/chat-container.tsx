'use client';

import { useChatStore } from '@/stores/chat-store';
import { useConnectionStore } from '@/stores/connection-store';
import { apiClient } from '@/lib/api-client';
import ChatInput from './chat-input';
import MessageBubble from './message-bubble';
import SessionSidebar from './session-sidebar';
import SuggestedQuestions from './suggested-questions';

export default function ChatContainer() {
  const { messages, isLoading, addMessage, setLoading, activeSessionId } = useChatStore();
  const { activeConnectionId } = useConnectionStore();

  const handleSend = async (text: string) => {
    if (!text.trim() || isLoading || !activeConnectionId) return;

    addMessage({
      id: crypto.randomUUID(),
      role: 'user',
      content: text.trim(),
      created_at: new Date().toISOString(),
    });

    setLoading(true);

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
  };

  return (
    <div className="h-full flex">
      <SessionSidebar />
      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-auto p-4 space-y-4">
          {messages.length === 0 && (
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

        <ChatInput />
      </div>
    </div>
  );
}
