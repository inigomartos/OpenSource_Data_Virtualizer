'use client';

import { useEffect, useState, useCallback } from 'react';
import { X, CheckCheck, Clock, AlertTriangle, Loader2 } from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { formatDistanceToNow } from 'date-fns';

interface AlertEvent {
  id: string;
  alert_id: string;
  triggered_value: number;
  message: string;
  is_read: boolean;
  created_at: string;
}

interface AlertEventsProps {
  alertId: string;
  alertName: string;
  onClose: () => void;
}

export function AlertEventsPanel({ alertId, alertName, onClose }: AlertEventsProps) {
  const [events, setEvents] = useState<AlertEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [markingAll, setMarkingAll] = useState(false);

  const fetchEvents = useCallback(async () => {
    try {
      const data = await apiClient(`/alerts/${alertId}/events`);
      setEvents(data?.data || []);
    } catch {
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }, [alertId]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  const handleMarkAllRead = async () => {
    setMarkingAll(true);
    try {
      await apiClient(`/alerts/${alertId}/events/read`, {
        method: 'POST',
      });
      setEvents((prev) => prev.map((e) => ({ ...e, is_read: true })));
    } catch {
      // silently fail
    } finally {
      setMarkingAll(false);
    }
  };

  const unreadCount = events.filter((e) => !e.is_read).length;

  return (
    <div className="bg-bg-surface border border-border-default rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border-default">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-heading font-semibold text-text-primary">
            Events for &ldquo;{alertName}&rdquo;
          </h3>
          {unreadCount > 0 && (
            <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-brand-primary/10 text-brand-primary">
              {unreadCount} unread
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              disabled={markingAll}
              className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-text-secondary bg-bg-elevated border border-border-default rounded-lg hover:border-border-hover transition-colors disabled:opacity-50"
            >
              {markingAll ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <CheckCheck className="w-3.5 h-3.5" />
              )}
              Mark all read
            </button>
          )}
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-elevated transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Events list */}
      <div className="max-h-80 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-5 h-5 animate-spin text-text-muted" />
          </div>
        ) : events.length === 0 ? (
          <div className="flex flex-col items-center py-12 text-text-muted">
            <Clock className="w-8 h-8 mb-2 opacity-50" />
            <p className="text-sm">No events yet</p>
            <p className="text-xs mt-1">Events will appear here when the alert triggers</p>
          </div>
        ) : (
          <div className="divide-y divide-border-default">
            {events.map((event) => (
              <div
                key={event.id}
                className={`px-4 py-3 hover:bg-bg-elevated/50 transition-colors ${
                  !event.is_read ? 'bg-brand-primary/[0.03]' : ''
                }`}
              >
                <div className="flex items-start gap-3">
                  {/* Unread indicator */}
                  <div className="mt-1.5 shrink-0">
                    {!event.is_read ? (
                      <div className="w-2 h-2 rounded-full bg-brand-primary" />
                    ) : (
                      <div className="w-2 h-2 rounded-full bg-transparent" />
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <AlertTriangle className="w-3.5 h-3.5 text-brand-warning shrink-0" />
                      <span className="text-sm font-medium text-text-primary">
                        Value: {event.triggered_value}
                      </span>
                    </div>
                    <p className="text-sm text-text-secondary">{event.message}</p>
                    <p className="text-xs text-text-muted mt-1">
                      {formatDistanceToNow(new Date(event.created_at), { addSuffix: true })}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
