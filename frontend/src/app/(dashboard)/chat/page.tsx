'use client';

import ChatContainer from '@/components/chat/chat-container';
import { ErrorBoundary } from '@/components/ui/error-boundary';

export default function ChatPage() {
  return (
    <ErrorBoundary>
      <ChatContainer />
    </ErrorBoundary>
  );
}
