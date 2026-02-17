'use client';

import { useState, useRef, useEffect } from 'react';
import { useChatStore } from '@/stores/chat-store';
import { useConnectionStore } from '@/stores/connection-store';
import { apiClient } from '@/lib/api-client';

export default function ChatInput() {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { addMessage, setLoading, isLoading, activeSessionId } = useChatStore();
  const { activeConnectionId, connections } = useConnectionStore();

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !activeConnectionId) return;

    const userMessage = input.trim();
    setInput('');

    addMessage({
      id: crypto.randomUUID(),
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString(),
    });

    setLoading(true);

    try {
      const response = await apiClient('/chat/message', {
        method: 'POST',
        body: JSON.stringify({
          message: userMessage,
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
    <div className="border-t border-border-default p-4">
      <form onSubmit={handleSubmit} className="flex items-end gap-3">
        <select
          value={activeConnectionId || ''}
          onChange={(e) => useConnectionStore.getState().setActiveConnection(e.target.value || null)}
          className="px-3 py-2 bg-bg-elevated border border-border-default rounded-lg text-text-secondary text-sm min-w-[180px]"
        >
          <option value="">Select connection...</option>
          {connections.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name} ({c.type})
            </option>
          ))}
        </select>

        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            placeholder={
              activeConnectionId
                ? 'Ask about your data...'
                : 'Select a connection first...'
            }
            disabled={!activeConnectionId || isLoading}
            rows={1}
            className="w-full px-4 py-3 bg-bg-elevated border border-border-default rounded-xl text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-primary resize-none disabled:opacity-50"
          />
        </div>

        <button
          type="submit"
          disabled={!input.trim() || isLoading || !activeConnectionId}
          className="px-4 py-3 bg-brand-primary text-white rounded-xl font-medium hover:opacity-90 disabled:opacity-50 shadow-[0_0_20px_rgba(99,102,241,0.3)]"
        >
          Send
        </button>
      </form>
    </div>
  );
}
