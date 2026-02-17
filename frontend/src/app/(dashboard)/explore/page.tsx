'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { useConnectionStore } from '@/stores/connection-store';

export default function ExplorePage() {
  const { connections, activeConnectionId, setActiveConnection } = useConnectionStore();
  const [schema, setSchema] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (activeConnectionId) {
      setLoading(true);
      apiClient(`/schema/${activeConnectionId}`)
        .then((data) => setSchema(data.tables || []))
        .catch(() => setSchema([]))
        .finally(() => setLoading(false));
    }
  }, [activeConnectionId]);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-heading font-bold text-text-primary">Schema Explorer</h1>
          <p className="text-text-secondary text-sm mt-1">Browse your database structure</p>
        </div>
        <select
          value={activeConnectionId || ''}
          onChange={(e) => setActiveConnection(e.target.value || null)}
          className="px-4 py-2 bg-bg-elevated border border-border-default rounded-lg text-text-primary text-sm"
        >
          <option value="">Select connection...</option>
          {connections.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      {!activeConnectionId ? (
        <div className="text-center py-16 text-text-muted">
          Select a connection to explore its schema
        </div>
      ) : loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-16 bg-bg-elevated animate-pulse rounded-xl border border-border-default" />
          ))}
        </div>
      ) : schema.length === 0 ? (
        <div className="text-center py-16 text-text-muted">
          No tables found. Try refreshing the schema.
        </div>
      ) : (
        <div className="space-y-3">
          {schema.map((table: any) => (
            <details
              key={table.table_name}
              className="bg-bg-surface border border-border-default rounded-xl overflow-hidden"
            >
              <summary className="px-5 py-3 cursor-pointer hover:bg-bg-elevated flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-brand-primary font-mono text-sm">{table.table_name}</span>
                  {table.ai_description && (
                    <span className="text-xs text-text-muted">— {table.ai_description}</span>
                  )}
                </div>
                {table.row_count != null && (
                  <span className="text-xs text-text-muted">{table.row_count.toLocaleString()} rows</span>
                )}
              </summary>
              <div className="px-5 py-3 border-t border-border-default">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-xs text-text-muted">
                      <th className="text-left py-1">Column</th>
                      <th className="text-left py-1">Type</th>
                      <th className="text-left py-1">Keys</th>
                      <th className="text-left py-1">Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(table.columns || []).map((col: any) => (
                      <tr key={col.column_name} className="border-t border-border-default/50">
                        <td className="py-1.5 font-mono text-text-primary">{col.column_name}</td>
                        <td className="py-1.5 text-text-muted">{col.data_type}</td>
                        <td className="py-1.5">
                          {col.is_primary_key && <span className="text-brand-warning text-xs">PK</span>}
                          {col.is_foreign_key && <span className="text-brand-accent text-xs ml-1">FK</span>}
                        </td>
                        <td className="py-1.5 text-text-muted text-xs">{col.ai_description || col.ai_business_term || ''}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          ))}
        </div>
      )}
    </div>
  );
}
