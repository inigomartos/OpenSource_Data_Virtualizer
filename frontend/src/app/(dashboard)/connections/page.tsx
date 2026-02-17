'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api-client';
import type { Connection } from '@/types/connection';

export default function ConnectionsPage() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient('/connections')
      .then((data) => setConnections(data.connections || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const connTypeColors: Record<string, string> = {
    postgresql: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    mysql: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
    sqlite: 'bg-green-500/10 text-green-400 border-green-500/20',
    csv: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    excel: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-heading font-bold text-text-primary">Connections</h1>
          <p className="text-text-secondary text-sm mt-1">Manage your data source connections</p>
        </div>
        <Link
          href="/connections/new"
          className="px-4 py-2 bg-brand-primary text-white rounded-lg text-sm font-medium hover:opacity-90 shadow-[0_0_20px_rgba(99,102,241,0.3)]"
        >
          + New Connection
        </Link>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-40 bg-bg-elevated animate-pulse rounded-xl border border-border-default" />
          ))}
        </div>
      ) : connections.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-text-muted text-lg mb-4">No connections yet</p>
          <Link
            href="/connections/new"
            className="px-6 py-3 bg-brand-primary text-white rounded-lg font-medium hover:opacity-90"
          >
            Add your first connection
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {connections.map((conn) => (
            <Link
              key={conn.id}
              href={`/connections/${conn.id}`}
              className="p-5 bg-bg-surface border border-border-default rounded-xl hover:border-border-hover transition-all hover:shadow-lg"
            >
              <div className="flex items-center justify-between mb-3">
                <span className={`px-2 py-1 text-xs rounded-full border ${connTypeColors[conn.type] || 'bg-bg-elevated text-text-muted'}`}>
                  {conn.type}
                </span>
                <span className={`w-2 h-2 rounded-full ${conn.is_active ? 'bg-brand-success' : 'bg-brand-danger'}`} />
              </div>
              <h3 className="font-medium text-text-primary mb-1">{conn.name}</h3>
              {conn.host && (
                <p className="text-sm text-text-muted">{conn.host}:{conn.port}/{conn.database_name}</p>
              )}
              {conn.last_synced_at && (
                <p className="text-xs text-text-muted mt-2">
                  Last synced: {new Date(conn.last_synced_at).toLocaleDateString()}
                </p>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
