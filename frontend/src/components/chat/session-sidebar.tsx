'use client';

import { useChatStore } from '@/stores/chat-store';
import { LoadingSkeleton } from '@/components/ui/loading-skeleton';

export default function SessionSidebar() {
  const { sessions, activeSessionId, setActiveSession, sessionsLoading } = useChatStore();

  return (
    <div className="w-64 bg-bg-surface border-r border-border-default flex flex-col">
      <div className="p-4 border-b border-border-default">
        <button className="w-full px-4 py-2 bg-brand-primary text-white rounded-lg text-sm font-medium hover:opacity-90">
          + New Chat
        </button>
      </div>

      <div className="flex-1 overflow-auto p-2 space-y-1">
        {sessionsLoading ? (
          Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="px-3 py-2.5 space-y-2">
              <LoadingSkeleton width="80%" height="14px" rounded="md" />
              <LoadingSkeleton width="50%" height="10px" rounded="md" />
            </div>
          ))
        ) : sessions.length === 0 ? (
          <p className="text-xs text-text-muted p-3 text-center">
            No conversations yet
          </p>
        ) : (
          sessions.map((session) => (
            <button
              key={session.id}
              onClick={() => setActiveSession(session.id)}
              className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors ${
                activeSessionId === session.id
                  ? 'bg-brand-primary/10 text-brand-primary'
                  : 'text-text-secondary hover:bg-bg-elevated hover:text-text-primary'
              }`}
            >
              <p className="truncate font-medium">{session.title || 'New Chat'}</p>
              <p className="text-xs text-text-muted truncate mt-0.5">
                {new Date(session.created_at).toLocaleDateString()}
              </p>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
