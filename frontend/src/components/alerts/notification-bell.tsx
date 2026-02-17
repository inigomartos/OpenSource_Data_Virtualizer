'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Bell, X, AlertTriangle, Check } from 'lucide-react';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { apiClient } from '@/lib/api-client';
import { formatDistanceToNow } from 'date-fns';

interface UnreadEvent {
  id: string;
  alert_id: string;
  alert_name: string;
  triggered_value: number;
  message: string;
  is_read: boolean;
  created_at: string;
}

const POLL_INTERVAL = 30000; // 30 seconds

export function NotificationBell() {
  const router = useRouter();
  const [events, setEvents] = useState<UnreadEvent[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [open, setOpen] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchUnread = useCallback(async () => {
    try {
      const data = await apiClient('/alerts/events/unread');
      const unreadEvents: UnreadEvent[] = data?.data || [];
      setEvents(unreadEvents);
      setUnreadCount(unreadEvents.length);
    } catch {
      // Silently fail - don't disrupt the UI for notification polling
    }
  }, []);

  useEffect(() => {
    fetchUnread();
    intervalRef.current = setInterval(fetchUnread, POLL_INTERVAL);
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchUnread]);

  const handleEventClick = async (event: UnreadEvent) => {
    // Mark as read
    try {
      await apiClient(`/alerts/events/${event.id}/read`, { method: 'POST' });
      setEvents((prev) => prev.filter((e) => e.id !== event.id));
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch {
      // ignore
    }
    setOpen(false);
    router.push('/alerts');
  };

  const handleMarkAllRead = async () => {
    try {
      await apiClient('/alerts/events/read-all', { method: 'POST' });
      setEvents([]);
      setUnreadCount(0);
    } catch {
      // ignore
    }
  };

  return (
    <DropdownMenu.Root open={open} onOpenChange={setOpen}>
      <DropdownMenu.Trigger asChild>
        <button className="relative p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-elevated transition-colors">
          <Bell className="w-5 h-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] flex items-center justify-center px-1 text-[10px] font-bold text-white bg-brand-danger rounded-full">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </button>
      </DropdownMenu.Trigger>

      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="end"
          sideOffset={8}
          className="w-80 max-h-96 overflow-hidden bg-bg-surface border border-border-default rounded-xl shadow-2xl z-50 flex flex-col"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-border-default">
            <h3 className="text-sm font-heading font-semibold text-text-primary">
              Notifications
            </h3>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="flex items-center gap-1 text-xs text-text-muted hover:text-text-secondary transition-colors"
              >
                <Check className="w-3 h-3" />
                Mark all read
              </button>
            )}
          </div>

          {/* Events */}
          <div className="overflow-y-auto flex-1">
            {events.length === 0 ? (
              <div className="flex flex-col items-center py-8 px-4">
                <Bell className="w-8 h-8 text-text-muted/50 mb-2" />
                <p className="text-sm text-text-muted">No new notifications</p>
              </div>
            ) : (
              <div>
                {events.slice(0, 20).map((event) => (
                  <DropdownMenu.Item
                    key={event.id}
                    onSelect={() => handleEventClick(event)}
                    className="px-4 py-3 hover:bg-bg-elevated cursor-pointer border-b border-border-default/50 last:border-b-0 outline-none focus:bg-bg-elevated"
                  >
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5 shrink-0">
                        <div className="w-7 h-7 rounded-full bg-brand-warning/10 flex items-center justify-center">
                          <AlertTriangle className="w-3.5 h-3.5 text-brand-warning" />
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-text-primary truncate">
                          {event.alert_name}
                        </p>
                        <p className="text-xs text-text-secondary mt-0.5 line-clamp-2">
                          {event.message}
                        </p>
                        <p className="text-xs text-text-muted mt-1">
                          {formatDistanceToNow(new Date(event.created_at), {
                            addSuffix: true,
                          })}
                        </p>
                      </div>
                      <div className="mt-1.5 shrink-0">
                        <div className="w-2 h-2 rounded-full bg-brand-primary" />
                      </div>
                    </div>
                  </DropdownMenu.Item>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          {events.length > 0 && (
            <div className="px-4 py-2.5 border-t border-border-default">
              <button
                onClick={() => {
                  setOpen(false);
                  router.push('/alerts');
                }}
                className="text-xs text-brand-primary hover:text-brand-primary/80 font-medium transition-colors w-full text-center"
              >
                View all alerts
              </button>
            </div>
          )}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
