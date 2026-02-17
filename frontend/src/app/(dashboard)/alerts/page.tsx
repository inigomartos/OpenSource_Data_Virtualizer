'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';

interface Alert {
  id: string;
  name: string;
  condition_type: string;
  is_active: boolean;
  last_checked_at?: string;
  last_value?: number;
  consecutive_failures: number;
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient('/alerts')
      .then((data) => setAlerts(data.alerts || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-heading font-bold text-text-primary">Alerts</h1>
          <p className="text-text-secondary text-sm mt-1">Monitor your data with automated alerts</p>
        </div>
        <button className="px-4 py-2 bg-brand-primary text-white rounded-lg text-sm font-medium hover:opacity-90 shadow-[0_0_20px_rgba(99,102,241,0.3)]">
          + New Alert
        </button>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-bg-elevated animate-pulse rounded-xl border border-border-default" />
          ))}
        </div>
      ) : alerts.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-text-muted text-lg mb-4">No alerts configured</p>
          <p className="text-sm text-text-muted">Set up alerts to get notified when your data meets certain conditions.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className="p-4 bg-bg-surface border border-border-default rounded-xl flex items-center justify-between"
            >
              <div>
                <h3 className="font-medium text-text-primary">{alert.name}</h3>
                <p className="text-sm text-text-muted mt-0.5">
                  Condition: {alert.condition_type} | Last value: {alert.last_value ?? 'N/A'}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span className={`px-2 py-1 text-xs rounded-full ${alert.is_active ? 'bg-brand-success/10 text-brand-success' : 'bg-bg-elevated text-text-muted'}`}>
                  {alert.is_active ? 'Active' : 'Paused'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
