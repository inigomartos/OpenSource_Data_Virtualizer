'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import type { Dashboard } from '@/types/dashboard';

export default function DashboardsPage() {
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient('/dashboards')
      .then((data) => setDashboards(data.dashboards || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-heading font-bold text-text-primary">Dashboards</h1>
          <p className="text-text-secondary text-sm mt-1">Build and share live data dashboards</p>
        </div>
        <Link
          href="/dashboards/new"
          className="px-4 py-2 bg-brand-primary text-white rounded-lg text-sm font-medium hover:opacity-90 shadow-[0_0_20px_rgba(99,102,241,0.3)]"
        >
          + New Dashboard
        </Link>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-48 bg-bg-elevated animate-pulse rounded-xl border border-border-default" />
          ))}
        </div>
      ) : dashboards.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-text-muted text-lg mb-4">No dashboards yet</p>
          <Link
            href="/dashboards/new"
            className="px-6 py-3 bg-brand-primary text-white rounded-lg font-medium hover:opacity-90"
          >
            Create your first dashboard
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {dashboards.map((dash) => (
            <Link
              key={dash.id}
              href={`/dashboards/${dash.id}`}
              className="p-5 bg-bg-surface border border-border-default rounded-xl hover:border-border-hover transition-all"
            >
              <h3 className="font-medium text-text-primary mb-1">{dash.title}</h3>
              {dash.description && (
                <p className="text-sm text-text-muted mb-3">{dash.description}</p>
              )}
              <div className="flex items-center gap-3 text-xs text-text-muted">
                {dash.is_shared && <span className="text-brand-accent">Shared</span>}
                <span>{new Date(dash.created_at).toLocaleDateString()}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
