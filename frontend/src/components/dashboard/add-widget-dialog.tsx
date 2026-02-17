'use client';

import { useState, useEffect } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import * as Tabs from '@radix-ui/react-tabs';
import { X, Search, Database, Code2, FileText } from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { useConnections } from '@/hooks/use-connections';

interface SavedQuery {
  id: string;
  title: string;
  sql: string;
  connection_id: string;
  connection_name?: string;
  created_at: string;
}

interface AddWidgetDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (sql: string, connectionId: string) => void;
}

export default function AddWidgetDialog({
  open,
  onOpenChange,
  onSelect,
}: AddWidgetDialogProps) {
  const { connections } = useConnections();
  const [savedQueries, setSavedQueries] = useState<SavedQuery[]>([]);
  const [loadingQueries, setLoadingQueries] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [freeformSql, setFreeformSql] = useState('');
  const [selectedConnectionId, setSelectedConnectionId] = useState('');

  // Fetch saved queries when dialog opens
  useEffect(() => {
    if (open) {
      setLoadingQueries(true);
      setSearchTerm('');
      setFreeformSql('');
      setSelectedConnectionId(connections[0]?.id || '');

      apiClient<{ data: SavedQuery[] }>('/query/saved')
        .then((data) => setSavedQueries(data?.data || []))
        .catch(() => setSavedQueries([]))
        .finally(() => setLoadingQueries(false));
    }
  }, [open, connections]);

  const filteredQueries = savedQueries.filter((q) =>
    q.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    q.sql.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSelectSavedQuery = (query: SavedQuery) => {
    onSelect(query.sql, query.connection_id);
    onOpenChange(false);
  };

  const handleSubmitFreeform = () => {
    if (!freeformSql.trim() || !selectedConnectionId) return;
    onSelect(freeformSql, selectedConnectionId);
    onOpenChange(false);
  };

  const inputClasses =
    'w-full px-4 py-2.5 bg-bg-elevated border border-border-default rounded-lg text-text-primary text-sm focus:outline-none focus:border-brand-primary transition-colors duration-200';

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl max-h-[85vh] overflow-hidden bg-bg-surface border border-border-default rounded-2xl shadow-2xl z-50 flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-6 pb-0">
            <Dialog.Title className="text-lg font-heading font-bold text-text-primary">
              Add Widget
            </Dialog.Title>
            <Dialog.Close asChild>
              <button className="p-1.5 rounded-md text-text-muted hover:text-text-primary hover:bg-white/5 transition-all duration-200">
                <X className="w-5 h-5" />
              </button>
            </Dialog.Close>
          </div>

          <Tabs.Root defaultValue="saved" className="flex flex-col flex-1 overflow-hidden">
            {/* Tab triggers */}
            <Tabs.List className="flex gap-1 px-6 pt-4 border-b border-border-default">
              <Tabs.Trigger
                value="saved"
                className="px-4 py-2.5 text-sm text-text-muted data-[state=active]:text-brand-primary data-[state=active]:border-b-2 data-[state=active]:border-brand-primary transition-all duration-200 flex items-center gap-2 -mb-px"
              >
                <FileText className="w-4 h-4" />
                From Saved Queries
              </Tabs.Trigger>
              <Tabs.Trigger
                value="sql"
                className="px-4 py-2.5 text-sm text-text-muted data-[state=active]:text-brand-primary data-[state=active]:border-b-2 data-[state=active]:border-brand-primary transition-all duration-200 flex items-center gap-2 -mb-px"
              >
                <Code2 className="w-4 h-4" />
                Write SQL
              </Tabs.Trigger>
            </Tabs.List>

            {/* Tab: Saved Queries */}
            <Tabs.Content value="saved" className="flex-1 overflow-hidden flex flex-col p-6">
              {/* Search */}
              <div className="relative mb-4">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                <input
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search saved queries..."
                  className={`${inputClasses} pl-10`}
                />
              </div>

              {/* Query list */}
              <div className="flex-1 overflow-y-auto space-y-2 min-h-0">
                {loadingQueries ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin h-6 w-6 border-2 border-brand-primary border-t-transparent rounded-full" />
                  </div>
                ) : filteredQueries.length === 0 ? (
                  <div className="text-center py-8">
                    <Database className="w-10 h-10 text-text-muted mx-auto mb-3 opacity-50" />
                    <p className="text-sm text-text-muted">
                      {savedQueries.length === 0
                        ? 'No saved queries found'
                        : 'No queries match your search'}
                    </p>
                    <p className="text-xs text-text-muted mt-1">
                      Save queries from the SQL editor to use them here
                    </p>
                  </div>
                ) : (
                  filteredQueries.map((query) => (
                    <button
                      key={query.id}
                      onClick={() => handleSelectSavedQuery(query)}
                      className="w-full text-left p-4 bg-bg-elevated border border-border-default rounded-xl hover:border-brand-primary/50 hover:bg-brand-primary/5 transition-all duration-200 group"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <h4 className="text-sm font-medium text-text-primary group-hover:text-brand-primary transition-colors">
                          {query.title}
                        </h4>
                        {query.connection_name && (
                          <span className="text-[10px] px-2 py-0.5 bg-white/5 rounded-full text-text-muted">
                            {query.connection_name}
                          </span>
                        )}
                      </div>
                      <pre className="text-xs text-text-muted font-mono line-clamp-2 whitespace-pre-wrap">
                        {query.sql}
                      </pre>
                    </button>
                  ))
                )}
              </div>
            </Tabs.Content>

            {/* Tab: Write SQL */}
            <Tabs.Content value="sql" className="flex-1 overflow-hidden flex flex-col p-6">
              <div className="space-y-4 flex-1 flex flex-col">
                {/* Connection selector */}
                <div>
                  <label className="block text-sm text-text-secondary mb-1.5">Connection</label>
                  <select
                    value={selectedConnectionId}
                    onChange={(e) => setSelectedConnectionId(e.target.value)}
                    className={`${inputClasses} appearance-none cursor-pointer`}
                  >
                    <option value="">Select a connection</option>
                    {connections
                      .filter((c) => c.is_active)
                      .map((conn) => (
                        <option key={conn.id} value={conn.id}>
                          {conn.name} ({conn.type})
                        </option>
                      ))}
                  </select>
                </div>

                {/* SQL textarea */}
                <div className="flex-1 flex flex-col">
                  <label className="block text-sm text-text-secondary mb-1.5">SQL Query</label>
                  <textarea
                    value={freeformSql}
                    onChange={(e) => setFreeformSql(e.target.value)}
                    placeholder="SELECT * FROM your_table LIMIT 100"
                    className={`${inputClasses} font-mono text-xs flex-1 min-h-[200px] resize-none`}
                  />
                </div>

                {/* Submit */}
                <div className="flex justify-end">
                  <button
                    onClick={handleSubmitFreeform}
                    disabled={!freeformSql.trim() || !selectedConnectionId}
                    className="px-6 py-2.5 bg-brand-primary text-white rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50 shadow-[0_0_20px_rgba(99,102,241,0.3)] transition-all duration-200"
                  >
                    Continue to Configure
                  </button>
                </div>
              </div>
            </Tabs.Content>
          </Tabs.Root>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
