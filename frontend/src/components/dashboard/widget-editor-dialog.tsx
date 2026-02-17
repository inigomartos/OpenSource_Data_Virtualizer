'use client';

import { useState, useEffect } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { useConnections } from '@/hooks/use-connections';
import type { WidgetWithData, CreateWidgetPayload, UpdateWidgetPayload } from '@/types/dashboard';
import type { ChartConfig } from '@/types/chat';

interface WidgetEditorDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  widget?: WidgetWithData | null;
  onSubmit: (data: CreateWidgetPayload | UpdateWidgetPayload) => Promise<void>;
  initialSql?: string;
  initialConnectionId?: string;
}

const WIDGET_TYPES: { value: WidgetWithData['widget_type']; label: string }[] = [
  { value: 'chart', label: 'Chart' },
  { value: 'table', label: 'Table' },
  { value: 'kpi', label: 'KPI Card' },
  { value: 'text', label: 'Text' },
];

const CHART_TYPES: { value: ChartConfig['chart_type']; label: string }[] = [
  { value: 'bar', label: 'Bar Chart' },
  { value: 'horizontal_bar', label: 'Horizontal Bar' },
  { value: 'line', label: 'Line Chart' },
  { value: 'area', label: 'Area Chart' },
  { value: 'pie', label: 'Pie Chart' },
  { value: 'scatter', label: 'Scatter Plot' },
  { value: 'kpi', label: 'KPI' },
  { value: 'table', label: 'Table' },
];

const REFRESH_INTERVALS = [
  { value: 0, label: 'Manual only' },
  { value: 30, label: 'Every 30 seconds' },
  { value: 60, label: 'Every minute' },
  { value: 300, label: 'Every 5 minutes' },
  { value: 900, label: 'Every 15 minutes' },
  { value: 3600, label: 'Every hour' },
];

export default function WidgetEditorDialog({
  open,
  onOpenChange,
  widget,
  onSubmit,
  initialSql = '',
  initialConnectionId = '',
}: WidgetEditorDialogProps) {
  const { connections } = useConnections();
  const isEditing = !!widget;

  const [title, setTitle] = useState('');
  const [widgetType, setWidgetType] = useState<WidgetWithData['widget_type']>('chart');
  const [chartType, setChartType] = useState<ChartConfig['chart_type']>('bar');
  const [querySql, setQuerySql] = useState('');
  const [connectionId, setConnectionId] = useState('');
  const [xColumn, setXColumn] = useState('');
  const [yColumn, setYColumn] = useState('');
  const [valueColumn, setValueColumn] = useState('');
  const [format, setFormat] = useState('');
  const [textContent, setTextContent] = useState('');
  const [refreshInterval, setRefreshInterval] = useState(0);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  // Reset form when widget changes or dialog opens
  useEffect(() => {
    if (open) {
      if (widget) {
        setTitle(widget.title);
        setWidgetType(widget.widget_type);
        setChartType(widget.chart_config?.chart_type || 'bar');
        setQuerySql(widget.query_sql || '');
        setConnectionId(widget.connection_id || '');
        setXColumn(widget.chart_config?.x_column || '');
        setYColumn(widget.chart_config?.y_column || '');
        setValueColumn(widget.chart_config?.value_column || '');
        setFormat(widget.chart_config?.format || '');
        setTextContent(widget.chart_config?.content || '');
        setRefreshInterval(widget.refresh_interval_seconds || 0);
      } else {
        setTitle('');
        setWidgetType('chart');
        setChartType('bar');
        setQuerySql(initialSql);
        setConnectionId(initialConnectionId || (connections[0]?.id || ''));
        setXColumn('');
        setYColumn('');
        setValueColumn('');
        setFormat('');
        setTextContent('');
        setRefreshInterval(0);
      }
      setError('');
    }
  }, [open, widget, initialSql, initialConnectionId, connections]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!title.trim()) {
      setError('Title is required');
      return;
    }

    if (widgetType !== 'text' && !querySql.trim()) {
      setError('SQL query is required');
      return;
    }

    if (widgetType !== 'text' && !connectionId) {
      setError('Please select a connection');
      return;
    }

    setSaving(true);

    try {
      const chartConfig: any = {
        title,
        chart_type: widgetType === 'chart' ? chartType : widgetType,
      };

      if (widgetType === 'chart') {
        if (xColumn) chartConfig.x_column = xColumn;
        if (yColumn) chartConfig.y_column = yColumn;
      }

      if (widgetType === 'kpi') {
        chartConfig.chart_type = 'kpi';
        if (valueColumn) chartConfig.value_column = valueColumn;
        if (format) chartConfig.format = format;
      }

      if (widgetType === 'table') {
        chartConfig.chart_type = 'table';
      }

      if (widgetType === 'text') {
        chartConfig.content = textContent;
      }

      const payload: CreateWidgetPayload | UpdateWidgetPayload = {
        title,
        widget_type: widgetType,
        chart_config: chartConfig,
        ...(widgetType !== 'text' && {
          connection_id: connectionId,
          query_sql: querySql,
        }),
        refresh_interval_seconds: refreshInterval,
        ...(!isEditing && {
          position: { x: 0, y: Infinity, w: widgetType === 'kpi' ? 3 : 6, h: widgetType === 'kpi' ? 2 : 4 },
        }),
      };

      await onSubmit(payload);
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save widget');
    } finally {
      setSaving(false);
    }
  };

  const inputClasses =
    'w-full px-4 py-2.5 bg-bg-elevated border border-border-default rounded-lg text-text-primary text-sm focus:outline-none focus:border-brand-primary transition-colors duration-200';
  const labelClasses = 'block text-sm text-text-secondary mb-1.5';
  const selectClasses =
    'w-full px-4 py-2.5 bg-bg-elevated border border-border-default rounded-lg text-text-primary text-sm focus:outline-none focus:border-brand-primary appearance-none cursor-pointer transition-colors duration-200';

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-xl max-h-[85vh] overflow-y-auto bg-bg-surface border border-border-default rounded-2xl shadow-2xl z-50 p-6">
          <div className="flex items-center justify-between mb-6">
            <Dialog.Title className="text-lg font-heading font-bold text-text-primary">
              {isEditing ? 'Edit Widget' : 'Configure Widget'}
            </Dialog.Title>
            <Dialog.Close asChild>
              <button className="p-1.5 rounded-md text-text-muted hover:text-text-primary hover:bg-white/5 transition-all duration-200">
                <X className="w-5 h-5" />
              </button>
            </Dialog.Close>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Title */}
            <div>
              <label className={labelClasses}>Title</label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Widget title"
                className={inputClasses}
                required
              />
            </div>

            {/* Widget Type */}
            <div>
              <label className={labelClasses}>Widget Type</label>
              <select
                value={widgetType}
                onChange={(e) => setWidgetType(e.target.value as WidgetWithData['widget_type'])}
                className={selectClasses}
              >
                {WIDGET_TYPES.map((wt) => (
                  <option key={wt.value} value={wt.value}>
                    {wt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Chart Type (only for chart widgets) */}
            {widgetType === 'chart' && (
              <div>
                <label className={labelClasses}>Chart Type</label>
                <select
                  value={chartType}
                  onChange={(e) => setChartType(e.target.value as ChartConfig['chart_type'])}
                  className={selectClasses}
                >
                  {CHART_TYPES.map((ct) => (
                    <option key={ct.value} value={ct.value}>
                      {ct.label}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Chart column mapping (for chart widgets) */}
            {widgetType === 'chart' && (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className={labelClasses}>X Column</label>
                  <input
                    value={xColumn}
                    onChange={(e) => setXColumn(e.target.value)}
                    placeholder="Auto-detect"
                    className={inputClasses}
                  />
                </div>
                <div>
                  <label className={labelClasses}>Y Column</label>
                  <input
                    value={yColumn}
                    onChange={(e) => setYColumn(e.target.value)}
                    placeholder="Auto-detect"
                    className={inputClasses}
                  />
                </div>
              </div>
            )}

            {/* KPI-specific fields */}
            {widgetType === 'kpi' && (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className={labelClasses}>Value Column</label>
                  <input
                    value={valueColumn}
                    onChange={(e) => setValueColumn(e.target.value)}
                    placeholder="Auto-detect"
                    className={inputClasses}
                  />
                </div>
                <div>
                  <label className={labelClasses}>Format</label>
                  <select
                    value={format}
                    onChange={(e) => setFormat(e.target.value)}
                    className={selectClasses}
                  >
                    <option value="">Number</option>
                    <option value="currency">Currency</option>
                    <option value="percent">Percentage</option>
                  </select>
                </div>
              </div>
            )}

            {/* Text content (for text widgets) */}
            {widgetType === 'text' && (
              <div>
                <label className={labelClasses}>Content</label>
                <textarea
                  value={textContent}
                  onChange={(e) => setTextContent(e.target.value)}
                  placeholder="Enter text content..."
                  rows={4}
                  className={inputClasses}
                />
              </div>
            )}

            {/* Connection selector (not for text widgets) */}
            {widgetType !== 'text' && (
              <div>
                <label className={labelClasses}>Connection</label>
                <select
                  value={connectionId}
                  onChange={(e) => setConnectionId(e.target.value)}
                  className={selectClasses}
                  required
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
            )}

            {/* SQL Query (not for text widgets) */}
            {widgetType !== 'text' && (
              <div>
                <label className={labelClasses}>SQL Query</label>
                <textarea
                  value={querySql}
                  onChange={(e) => setQuerySql(e.target.value)}
                  placeholder="SELECT * FROM ..."
                  rows={5}
                  className={`${inputClasses} font-mono text-xs`}
                  required
                />
              </div>
            )}

            {/* Refresh Interval */}
            {widgetType !== 'text' && (
              <div>
                <label className={labelClasses}>Auto Refresh</label>
                <select
                  value={refreshInterval}
                  onChange={(e) => setRefreshInterval(Number(e.target.value))}
                  className={selectClasses}
                >
                  {REFRESH_INTERVALS.map((ri) => (
                    <option key={ri.value} value={ri.value}>
                      {ri.label}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Error message */}
            {error && (
              <p className="text-sm text-red-400 bg-red-500/10 px-3 py-2 rounded-lg">
                {error}
              </p>
            )}

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-2">
              <Dialog.Close asChild>
                <button
                  type="button"
                  className="px-4 py-2.5 text-sm text-text-secondary hover:text-text-primary border border-border-default rounded-lg hover:bg-white/5 transition-all duration-200"
                >
                  Cancel
                </button>
              </Dialog.Close>
              <button
                type="submit"
                disabled={saving}
                className="px-6 py-2.5 bg-brand-primary text-white rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50 shadow-[0_0_20px_rgba(99,102,241,0.3)] transition-all duration-200"
              >
                {saving ? 'Saving...' : isEditing ? 'Update Widget' : 'Add Widget'}
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
