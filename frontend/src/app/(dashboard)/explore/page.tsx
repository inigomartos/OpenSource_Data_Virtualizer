'use client';

import { useEffect, useState, useMemo, useCallback } from 'react';
import { apiClient } from '@/lib/api-client';
import { useConnectionStore } from '@/stores/connection-store';
import {
  Search,
  Table2,
  ChevronRight,
  ChevronDown,
  Key,
  Link2,
  Hash,
  Type,
  Sparkles,
  Database,
  RefreshCw,
  Loader2,
  Columns3,
  Eye,
} from 'lucide-react';
import { SkeletonList } from '@/components/ui/loading-skeleton';
import { EmptyState } from '@/components/ui/empty-state';

interface Column {
  column_name: string;
  data_type: string;
  is_nullable: boolean;
  is_primary_key: boolean;
  is_foreign_key: boolean;
  foreign_key_ref?: string;
  ai_description?: string;
  ai_business_term?: string;
  sample_values?: string[];
}

interface TableSchema {
  table_name: string;
  schema_name?: string;
  row_count?: number;
  ai_description?: string;
  columns: Column[];
}

export default function ExplorePage() {
  const { connections, activeConnectionId, setActiveConnection } = useConnectionStore();
  const [schema, setSchema] = useState<TableSchema[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedTables, setExpandedTables] = useState<Set<string>>(new Set());
  const [selectedColumn, setSelectedColumn] = useState<{
    table: string;
    column: Column;
  } | null>(null);

  const fetchSchema = useCallback(
    async (showRefreshIndicator = false) => {
      if (!activeConnectionId) return;

      if (showRefreshIndicator) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      try {
        const data = await apiClient(`/schema/${activeConnectionId}`);
        setSchema(data.tables || []);
      } catch {
        setSchema([]);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [activeConnectionId]
  );

  useEffect(() => {
    if (activeConnectionId) {
      fetchSchema();
      setExpandedTables(new Set());
      setSelectedColumn(null);
      setSearchQuery('');
    } else {
      setSchema([]);
    }
  }, [activeConnectionId, fetchSchema]);

  // Load connections if not yet loaded
  useEffect(() => {
    if (connections.length === 0) {
      apiClient('/connections')
        .then((data) => {
          const { setConnections } = useConnectionStore.getState();
          setConnections(data.connections || []);
        })
        .catch(() => {});
    }
  }, [connections.length]);

  const toggleTable = (tableName: string) => {
    setExpandedTables((prev) => {
      const next = new Set(prev);
      if (next.has(tableName)) {
        next.delete(tableName);
      } else {
        next.add(tableName);
      }
      return next;
    });
  };

  const filteredSchema = useMemo(() => {
    if (!searchQuery.trim()) return schema;

    const query = searchQuery.toLowerCase();
    return schema.filter((table) => {
      // Match table name
      if (table.table_name.toLowerCase().includes(query)) return true;
      // Match AI description
      if (table.ai_description?.toLowerCase().includes(query)) return true;
      // Match column names
      if (
        table.columns.some(
          (col) =>
            col.column_name.toLowerCase().includes(query) ||
            col.ai_description?.toLowerCase().includes(query) ||
            col.ai_business_term?.toLowerCase().includes(query)
        )
      )
        return true;
      return false;
    });
  }, [schema, searchQuery]);

  const getDataTypeIcon = (dataType: string) => {
    const type = dataType.toLowerCase();
    if (
      type.includes('int') ||
      type.includes('numeric') ||
      type.includes('decimal') ||
      type.includes('float') ||
      type.includes('double')
    ) {
      return <Hash className="w-3 h-3 text-brand-accent" />;
    }
    if (
      type.includes('char') ||
      type.includes('text') ||
      type.includes('string') ||
      type.includes('varchar')
    ) {
      return <Type className="w-3 h-3 text-brand-warning" />;
    }
    return <Columns3 className="w-3 h-3 text-text-muted" />;
  };

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-heading font-bold text-text-primary">
            Schema Explorer
          </h1>
          <p className="text-text-secondary text-sm mt-1">
            Browse your database structure
          </p>
        </div>
        <div className="flex items-center gap-3">
          {activeConnectionId && (
            <button
              onClick={() => fetchSchema(true)}
              disabled={refreshing}
              className="flex items-center gap-2 px-3 py-2 text-sm text-text-secondary bg-bg-elevated border border-border-default rounded-lg hover:border-border-hover transition-colors disabled:opacity-50"
            >
              {refreshing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
              Refresh
            </button>
          )}
          <select
            value={activeConnectionId || ''}
            onChange={(e) => setActiveConnection(e.target.value || null)}
            className="px-4 py-2 bg-bg-elevated border border-border-default rounded-lg text-text-primary text-sm focus:outline-none focus:border-brand-primary"
          >
            <option value="">Select connection...</option>
            {connections.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* No connection selected */}
      {!activeConnectionId ? (
        <EmptyState
          icon={Database}
          title="Select a connection"
          description="Choose a database connection to explore its schema, tables, and columns."
        />
      ) : loading ? (
        <SkeletonList count={4} />
      ) : schema.length === 0 ? (
        <EmptyState
          icon={Table2}
          title="No tables found"
          description="No tables were found in this database. Try refreshing the schema."
          actionLabel="Refresh Schema"
          onAction={() => fetchSchema(true)}
        />
      ) : (
        <div className="flex gap-6">
          {/* Left: Table tree */}
          <div className="flex-1 min-w-0">
            {/* Search bar */}
            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search tables, columns, descriptions..."
                className="w-full pl-10 pr-4 py-2.5 bg-bg-surface border border-border-default rounded-xl text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand-primary"
              />
              {searchQuery && (
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-text-muted">
                  {filteredSchema.length} table{filteredSchema.length !== 1 ? 's' : ''}
                </span>
              )}
            </div>

            {/* Summary stats */}
            <div className="flex items-center gap-4 mb-4 text-xs text-text-muted">
              <span className="flex items-center gap-1">
                <Table2 className="w-3 h-3" />
                {schema.length} table{schema.length !== 1 ? 's' : ''}
              </span>
              <span className="flex items-center gap-1">
                <Columns3 className="w-3 h-3" />
                {schema.reduce((sum, t) => sum + (t.columns?.length || 0), 0)} columns
              </span>
            </div>

            {/* Table list */}
            {filteredSchema.length === 0 ? (
              <div className="text-center py-12 text-text-muted">
                <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No tables match &ldquo;{searchQuery}&rdquo;</p>
              </div>
            ) : (
              <div className="space-y-2">
                {filteredSchema.map((table) => {
                  const isExpanded = expandedTables.has(table.table_name);

                  return (
                    <div
                      key={table.table_name}
                      className="bg-bg-surface border border-border-default rounded-xl overflow-hidden"
                    >
                      {/* Table header */}
                      <button
                        onClick={() => toggleTable(table.table_name)}
                        className="w-full px-4 py-3 flex items-center gap-3 hover:bg-bg-elevated/50 transition-colors text-left"
                      >
                        <span className="shrink-0">
                          {isExpanded ? (
                            <ChevronDown className="w-4 h-4 text-text-muted" />
                          ) : (
                            <ChevronRight className="w-4 h-4 text-text-muted" />
                          )}
                        </span>
                        <Table2 className="w-4 h-4 text-brand-primary shrink-0" />
                        <span className="font-mono text-sm font-medium text-text-primary">
                          {table.schema_name ? `${table.schema_name}.` : ''}
                          {table.table_name}
                        </span>
                        {table.ai_description && (
                          <span className="text-xs text-text-muted truncate flex items-center gap-1">
                            <Sparkles className="w-3 h-3 text-brand-accent shrink-0" />
                            {table.ai_description}
                          </span>
                        )}
                        <div className="ml-auto flex items-center gap-3 shrink-0">
                          <span className="text-xs text-text-muted">
                            {table.columns?.length || 0} col{(table.columns?.length || 0) !== 1 ? 's' : ''}
                          </span>
                          {table.row_count != null && (
                            <span className="text-xs text-text-muted">
                              {table.row_count.toLocaleString()} rows
                            </span>
                          )}
                        </div>
                      </button>

                      {/* Columns */}
                      {isExpanded && (
                        <div className="border-t border-border-default">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="text-xs text-text-muted bg-bg-elevated/30">
                                <th className="text-left px-4 py-2 font-medium">Column</th>
                                <th className="text-left px-4 py-2 font-medium">Type</th>
                                <th className="text-left px-4 py-2 font-medium">Keys</th>
                                <th className="text-left px-4 py-2 font-medium">Description</th>
                                <th className="text-right px-4 py-2 font-medium w-10"></th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-border-default/50">
                              {(table.columns || []).map((col) => (
                                <tr
                                  key={col.column_name}
                                  className={`hover:bg-bg-elevated/30 transition-colors ${
                                    selectedColumn?.table === table.table_name &&
                                    selectedColumn?.column.column_name === col.column_name
                                      ? 'bg-brand-primary/5'
                                      : ''
                                  }`}
                                >
                                  <td className="px-4 py-2">
                                    <div className="flex items-center gap-2">
                                      {getDataTypeIcon(col.data_type)}
                                      <span className="font-mono text-text-primary">
                                        {col.column_name}
                                      </span>
                                      {col.is_nullable && (
                                        <span className="text-[10px] text-text-muted">NULL</span>
                                      )}
                                    </div>
                                  </td>
                                  <td className="px-4 py-2">
                                    <span className="text-text-muted font-mono text-xs">
                                      {col.data_type}
                                    </span>
                                  </td>
                                  <td className="px-4 py-2">
                                    <div className="flex items-center gap-1">
                                      {col.is_primary_key && (
                                        <span className="flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-medium rounded bg-brand-warning/10 text-brand-warning">
                                          <Key className="w-2.5 h-2.5" />
                                          PK
                                        </span>
                                      )}
                                      {col.is_foreign_key && (
                                        <span className="flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-medium rounded bg-brand-accent/10 text-brand-accent">
                                          <Link2 className="w-2.5 h-2.5" />
                                          FK
                                        </span>
                                      )}
                                    </div>
                                  </td>
                                  <td className="px-4 py-2">
                                    {col.ai_description ? (
                                      <span className="text-xs text-text-secondary flex items-center gap-1">
                                        <Sparkles className="w-3 h-3 text-brand-accent shrink-0" />
                                        {col.ai_description}
                                      </span>
                                    ) : col.ai_business_term ? (
                                      <span className="text-xs text-text-muted">
                                        {col.ai_business_term}
                                      </span>
                                    ) : (
                                      <span className="text-xs text-text-muted/50">--</span>
                                    )}
                                  </td>
                                  <td className="px-4 py-2 text-right">
                                    <button
                                      onClick={() =>
                                        setSelectedColumn(
                                          selectedColumn?.table === table.table_name &&
                                            selectedColumn?.column.column_name === col.column_name
                                            ? null
                                            : { table: table.table_name, column: col }
                                        )
                                      }
                                      className="p-1 rounded text-text-muted hover:text-text-primary hover:bg-bg-elevated transition-colors"
                                      title="View column details"
                                    >
                                      <Eye className="w-3.5 h-3.5" />
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Right: Column detail panel */}
          {selectedColumn && (
            <div className="w-80 shrink-0">
              <div className="sticky top-0 bg-bg-surface border border-border-default rounded-xl p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-heading font-semibold text-text-primary">
                    Column Details
                  </h3>
                  <button
                    onClick={() => setSelectedColumn(null)}
                    className="text-xs text-text-muted hover:text-text-secondary transition-colors"
                  >
                    Close
                  </button>
                </div>

                {/* Column name */}
                <div className="mb-4">
                  <p className="text-xs text-text-muted mb-1">Column</p>
                  <p className="font-mono text-sm font-medium text-text-primary">
                    {selectedColumn.column.column_name}
                  </p>
                </div>

                {/* Table */}
                <div className="mb-4">
                  <p className="text-xs text-text-muted mb-1">Table</p>
                  <p className="font-mono text-sm text-text-secondary">
                    {selectedColumn.table}
                  </p>
                </div>

                {/* Data type */}
                <div className="mb-4">
                  <p className="text-xs text-text-muted mb-1">Data Type</p>
                  <p className="font-mono text-sm text-text-secondary">
                    {selectedColumn.column.data_type}
                  </p>
                </div>

                {/* Nullable */}
                <div className="mb-4">
                  <p className="text-xs text-text-muted mb-1">Nullable</p>
                  <p className="text-sm text-text-secondary">
                    {selectedColumn.column.is_nullable ? 'Yes' : 'No'}
                  </p>
                </div>

                {/* Keys */}
                {(selectedColumn.column.is_primary_key ||
                  selectedColumn.column.is_foreign_key) && (
                  <div className="mb-4">
                    <p className="text-xs text-text-muted mb-1">Keys</p>
                    <div className="flex items-center gap-2">
                      {selectedColumn.column.is_primary_key && (
                        <span className="flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-md bg-brand-warning/10 text-brand-warning">
                          <Key className="w-3 h-3" />
                          Primary Key
                        </span>
                      )}
                      {selectedColumn.column.is_foreign_key && (
                        <span className="flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-md bg-brand-accent/10 text-brand-accent">
                          <Link2 className="w-3 h-3" />
                          Foreign Key
                        </span>
                      )}
                    </div>
                    {selectedColumn.column.foreign_key_ref && (
                      <p className="text-xs text-text-muted mt-1.5 font-mono">
                        References: {selectedColumn.column.foreign_key_ref}
                      </p>
                    )}
                  </div>
                )}

                {/* AI Description */}
                {selectedColumn.column.ai_description && (
                  <div className="mb-4">
                    <p className="text-xs text-text-muted mb-1 flex items-center gap-1">
                      <Sparkles className="w-3 h-3 text-brand-accent" />
                      AI Description
                    </p>
                    <p className="text-sm text-text-secondary">
                      {selectedColumn.column.ai_description}
                    </p>
                  </div>
                )}

                {/* Business Term */}
                {selectedColumn.column.ai_business_term && (
                  <div className="mb-4">
                    <p className="text-xs text-text-muted mb-1">Business Term</p>
                    <span className="inline-block px-2 py-1 text-xs font-medium rounded-md bg-brand-primary/10 text-brand-primary">
                      {selectedColumn.column.ai_business_term}
                    </span>
                  </div>
                )}

                {/* Sample Values */}
                {selectedColumn.column.sample_values &&
                  selectedColumn.column.sample_values.length > 0 && (
                    <div>
                      <p className="text-xs text-text-muted mb-1.5">Sample Values</p>
                      <div className="space-y-1">
                        {selectedColumn.column.sample_values.slice(0, 8).map((val, i) => (
                          <div
                            key={i}
                            className="px-2 py-1 bg-bg-elevated rounded text-xs font-mono text-text-secondary truncate"
                          >
                            {val}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
