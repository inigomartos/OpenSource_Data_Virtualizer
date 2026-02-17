'use client';

import { useEffect, useState, useCallback } from 'react';
import { apiClient } from '@/lib/api-client';
import { formatDistanceToNow } from 'date-fns';
import {
  Plus,
  Trash2,
  AlertTriangle,
  Bell,
  BellOff,
  ChevronDown,
  Activity,
  Clock,
  Loader2,
} from 'lucide-react';
import * as Switch from '@radix-ui/react-switch';
import { CreateAlertDialog } from '@/components/alerts/create-alert-dialog';
import { AlertEventsPanel } from '@/components/alerts/alert-events-panel';
import { SkeletonList } from '@/components/ui/loading-skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import { ErrorMessage } from '@/components/ui/error-boundary';

interface Alert {
  id: string;
  name: string;
  description?: string;
  condition_type: 'above' | 'below' | 'change_pct' | 'anomaly';
  threshold: number;
  is_active: boolean;
  last_checked_at?: string;
  last_value?: number;
  consecutive_failures: number;
  check_interval_minutes: number;
  created_at: string;
}

type FilterMode = 'all' | 'active' | 'triggered';

const conditionLabels: Record<string, { label: string; color: string }> = {
  above: { label: 'Above', color: 'bg-brand-warning/10 text-brand-warning' },
  below: { label: 'Below', color: 'bg-brand-accent/10 text-brand-accent' },
  change_pct: { label: 'Change %', color: 'bg-brand-primary/10 text-brand-primary' },
  anomaly: { label: 'Anomaly', color: 'bg-brand-danger/10 text-brand-danger' },
};

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterMode>('all');
  const [createOpen, setCreateOpen] = useState(false);
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
  const [togglingIds, setTogglingIds] = useState<Set<string>>(new Set());
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const fetchAlerts = useCallback(async () => {
    try {
      setError(null);
      const data = await apiClient('/alerts');
      setAlerts(data.alerts || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load alerts');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  const handleToggle = async (alertId: string) => {
    setTogglingIds((prev) => new Set(prev).add(alertId));
    try {
      await apiClient(`/alerts/${alertId}/toggle`, { method: 'POST' });
      setAlerts((prev) =>
        prev.map((a) =>
          a.id === alertId ? { ...a, is_active: !a.is_active } : a
        )
      );
    } catch {
      // Failed silently, state remains unchanged
    } finally {
      setTogglingIds((prev) => {
        const next = new Set(prev);
        next.delete(alertId);
        return next;
      });
    }
  };

  const handleDelete = async (alertId: string) => {
    setDeletingId(alertId);
    try {
      await apiClient(`/alerts/${alertId}`, { method: 'DELETE' });
      setAlerts((prev) => prev.filter((a) => a.id !== alertId));
      if (selectedAlertId === alertId) {
        setSelectedAlertId(null);
      }
    } catch {
      // Failed silently
    } finally {
      setDeletingId(null);
      setConfirmDeleteId(null);
    }
  };

  const filteredAlerts = alerts.filter((alert) => {
    if (filter === 'active') return alert.is_active;
    if (filter === 'triggered') return alert.consecutive_failures > 0;
    return true;
  });

  const selectedAlert = alerts.find((a) => a.id === selectedAlertId);

  const activeCount = alerts.filter((a) => a.is_active).length;
  const triggeredCount = alerts.filter((a) => a.consecutive_failures > 0).length;

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-heading font-bold text-text-primary">Alerts</h1>
          <p className="text-text-secondary text-sm mt-1">
            Monitor your data with automated alerts
          </p>
        </div>
        <button
          onClick={() => setCreateOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-brand-primary text-white rounded-lg text-sm font-medium hover:opacity-90 transition-opacity shadow-[0_0_20px_rgba(99,102,241,0.3)]"
        >
          <Plus className="w-4 h-4" />
          New Alert
        </button>
      </div>

      {/* Filter tabs */}
      <div className="flex items-center gap-1 p-1 bg-bg-surface border border-border-default rounded-xl mb-6 w-fit">
        {([
          { key: 'all', label: 'All', count: alerts.length },
          { key: 'active', label: 'Active', count: activeCount },
          { key: 'triggered', label: 'Triggered', count: triggeredCount },
        ] as const).map(({ key, label, count }) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
              filter === key
                ? 'bg-bg-elevated text-text-primary'
                : 'text-text-muted hover:text-text-secondary'
            }`}
          >
            {label}
            <span className={`ml-1.5 text-xs ${filter === key ? 'text-text-secondary' : 'text-text-muted'}`}>
              {count}
            </span>
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <SkeletonList count={3} />
      ) : error ? (
        <ErrorMessage message={error} onRetry={fetchAlerts} />
      ) : filteredAlerts.length === 0 ? (
        filter === 'all' ? (
          <EmptyState
            icon={Bell}
            title="No alerts configured"
            description="Set up alerts to get notified when your data meets certain conditions."
            actionLabel="Create your first alert"
            onAction={() => setCreateOpen(true)}
          />
        ) : (
          <EmptyState
            icon={Bell}
            title={`No ${filter} alerts`}
            description={
              filter === 'active'
                ? 'No alerts are currently active.'
                : 'No alerts have been triggered recently.'
            }
          />
        )
      ) : (
        <div className="space-y-3">
          {filteredAlerts.map((alert) => {
            const condition = conditionLabels[alert.condition_type] || {
              label: alert.condition_type,
              color: 'bg-bg-elevated text-text-muted',
            };

            return (
              <div
                key={alert.id}
                className={`p-4 bg-bg-surface border rounded-xl transition-colors ${
                  selectedAlertId === alert.id
                    ? 'border-brand-primary/50'
                    : 'border-border-default hover:border-border-hover'
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  {/* Left side - Alert info */}
                  <button
                    onClick={() =>
                      setSelectedAlertId(
                        selectedAlertId === alert.id ? null : alert.id
                      )
                    }
                    className="flex-1 min-w-0 text-left"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium text-text-primary truncate">
                        {alert.name}
                      </h3>
                      <span
                        className={`px-2 py-0.5 text-xs font-medium rounded-full shrink-0 ${condition.color}`}
                      >
                        {condition.label}
                        {alert.condition_type !== 'anomaly' && (
                          <> {alert.threshold}</>
                        )}
                      </span>
                      {alert.consecutive_failures > 0 && (
                        <span className="flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full bg-brand-warning/10 text-brand-warning shrink-0">
                          <AlertTriangle className="w-3 h-3" />
                          {alert.consecutive_failures} failure{alert.consecutive_failures !== 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                    {alert.description && (
                      <p className="text-sm text-text-muted mb-2 truncate">
                        {alert.description}
                      </p>
                    )}
                    <div className="flex items-center gap-4 text-xs text-text-muted">
                      {alert.last_checked_at && (
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          Checked{' '}
                          {formatDistanceToNow(new Date(alert.last_checked_at), {
                            addSuffix: true,
                          })}
                        </span>
                      )}
                      {alert.last_value !== undefined && alert.last_value !== null && (
                        <span className="flex items-center gap-1">
                          <Activity className="w-3 h-3" />
                          Last value: {alert.last_value}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        Every {alert.check_interval_minutes}m
                      </span>
                    </div>
                  </button>

                  {/* Right side - Controls */}
                  <div className="flex items-center gap-3 shrink-0">
                    {/* Status toggle */}
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-text-muted">
                        {alert.is_active ? (
                          <Bell className="w-3.5 h-3.5 text-brand-success" />
                        ) : (
                          <BellOff className="w-3.5 h-3.5" />
                        )}
                      </span>
                      <Switch.Root
                        checked={alert.is_active}
                        onCheckedChange={() => handleToggle(alert.id)}
                        disabled={togglingIds.has(alert.id)}
                        className="w-9 h-5 bg-bg-elevated rounded-full relative data-[state=checked]:bg-brand-success transition-colors border border-border-default disabled:opacity-50"
                      >
                        <Switch.Thumb className="block w-3.5 h-3.5 bg-white rounded-full transition-transform translate-x-0.5 data-[state=checked]:translate-x-[18px]" />
                      </Switch.Root>
                    </div>

                    {/* Delete button */}
                    {confirmDeleteId === alert.id ? (
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleDelete(alert.id)}
                          disabled={deletingId === alert.id}
                          className="px-2 py-1 text-xs font-medium text-white bg-brand-danger rounded-md hover:opacity-90 disabled:opacity-50"
                        >
                          {deletingId === alert.id ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                          ) : (
                            'Confirm'
                          )}
                        </button>
                        <button
                          onClick={() => setConfirmDeleteId(null)}
                          className="px-2 py-1 text-xs font-medium text-text-secondary bg-bg-elevated rounded-md hover:text-text-primary"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setConfirmDeleteId(alert.id)}
                        className="p-1.5 rounded-lg text-text-muted hover:text-brand-danger hover:bg-brand-danger/10 transition-colors"
                        title="Delete alert"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}

                    {/* Expand arrow */}
                    <ChevronDown
                      className={`w-4 h-4 text-text-muted transition-transform ${
                        selectedAlertId === alert.id ? 'rotate-180' : ''
                      }`}
                    />
                  </div>
                </div>

                {/* Expanded events panel */}
                {selectedAlertId === alert.id && (
                  <div className="mt-4 pt-4 border-t border-border-default">
                    <AlertEventsPanel
                      alertId={alert.id}
                      alertName={alert.name}
                      onClose={() => setSelectedAlertId(null)}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Create dialog */}
      <CreateAlertDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        onCreated={fetchAlerts}
      />
    </div>
  );
}
