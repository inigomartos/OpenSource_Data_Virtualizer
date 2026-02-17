'use client';

import { useState } from 'react';
import { useChatStore } from '@/stores/chat-store';
import { useConnectionStore } from '@/stores/connection-store';
import ChatInput from './chat-input';
import MessageBubble from './message-bubble';
import SessionSidebar from './session-sidebar';
import SuggestedQuestions from './suggested-questions';

export default function ChatContainer() {
  const { messages, isLoading } = useChatStore();
  const { activeConnectionId } = useConnectionStore();

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
              <SuggestedQuestions />
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
