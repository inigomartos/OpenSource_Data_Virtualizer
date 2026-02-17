'use client';

import { useState } from 'react';
import type { ChatMessage } from '@/types/chat';
import SQLPreview from './sql-preview';
import ChartRenderer from '../charts/chart-renderer';

interface Props {
  message: ChatMessage;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-brand-primary text-white'
            : 'bg-bg-elevated border border-border-default text-text-primary'
        }`}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>

        {!isUser && message.generated_sql && (
          <SQLPreview sql={message.generated_sql} />
        )}

        {!isUser && message.chart_config && message.query_result_preview && (
          <div className="mt-3">
            <ChartRenderer
              config={message.chart_config}
              data={message.query_result_preview}
            />
          </div>
        )}

        {!isUser && message.execution_time_ms && (
          <div className="mt-2 flex items-center gap-3 text-xs text-text-muted">
            <span>Query: {message.execution_time_ms}ms</span>
            {message.full_result_row_count && (
              <span>{message.full_result_row_count.toLocaleString()} rows</span>
            )}
          </div>
        )}

        {message.error_message && (
          <div className="mt-2 text-xs text-brand-danger bg-brand-danger/10 px-2 py-1 rounded">
            {message.error_message}
          </div>
        )}
      </div>
    </div>
  );
}
