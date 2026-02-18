'use client';

import { useState, useCallback } from 'react';
import {
  MoreHorizontal,
  RefreshCw,
  Pencil,
  Trash2,
  GripVertical,
  AlertCircle,
  Clock,
} from 'lucide-react';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import ChartRenderer from '@/components/charts/chart-renderer';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import type { WidgetWithData } from '@/types/dashboard';
import { formatDistanceToNow } from 'date-fns';

interface WidgetCardProps {
  widget: WidgetWithData;
  onRefresh: (widgetId: string) => Promise<void>;
  onEdit: (widget: WidgetWithData) => void;
  onDelete: (widgetId: string) => void;
  isEditing: boolean;
}

export default function WidgetCard({
  widget,
  onRefresh,
  onEdit,
  onDelete,
  isEditing,
}: WidgetCardProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await onRefresh(widget.id);
    } finally {
      setIsRefreshing(false);
    }
  }, [onRefresh, widget.id]);

  const hasError = !!widget.last_error;
  const hasData = widget.query_result_preview &&
    widget.query_result_preview.columns.length > 0;

  const relativeTime = widget.last_refreshed_at
    ? formatDistanceToNow(new Date(widget.last_refreshed_at), { addSuffix: true })
    : null;

  return (
    <div
      className={`
        h-full flex flex-col
        backdrop-blur-xl bg-white/5 border rounded-xl
        transition-all duration-200 overflow-hidden
        ${hasError ? 'border-red-500/50' : 'border-white/10'}
        ${isEditing ? 'cursor-grab active:cursor-grabbing' : ''}
      `}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 shrink-0">
        <div className="flex items-center gap-2 min-w-0">
          {isEditing && (
            <div className="drag-handle cursor-grab active:cursor-grabbing text-text-muted hover:text-text-secondary transition-colors">
              <GripVertical className="w-4 h-4" />
            </div>
          )}
          <h3 className="text-sm font-medium text-text-primary truncate">
            {widget.title}
          </h3>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          {relativeTime && (
            <span className="text-[10px] text-text-muted flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {relativeTime}
            </span>
          )}

          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="p-1 rounded-md text-text-muted hover:text-text-secondary hover:bg-white/5 transition-all duration-200 disabled:opacity-50"
            title="Refresh"
          >
            <RefreshCw
              className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`}
            />
          </button>

          <DropdownMenu.Root open={menuOpen} onOpenChange={setMenuOpen}>
            <DropdownMenu.Trigger asChild>
              <button className="p-1 rounded-md text-text-muted hover:text-text-secondary hover:bg-white/5 transition-all duration-200">
                <MoreHorizontal className="w-3.5 h-3.5" />
              </button>
            </DropdownMenu.Trigger>

            <DropdownMenu.Portal>
              <DropdownMenu.Content
                className="min-w-[160px] bg-bg-elevated border border-border-default rounded-lg p-1 shadow-xl z-50"
                sideOffset={5}
                align="end"
              >
                <DropdownMenu.Item
                  className="flex items-center gap-2 px-3 py-2 text-sm text-text-primary rounded-md cursor-pointer hover:bg-white/5 outline-none transition-colors"
                  onSelect={() => onEdit(widget)}
                >
                  <Pencil className="w-3.5 h-3.5" />
                  Edit Widget
                </DropdownMenu.Item>
                <DropdownMenu.Item
                  className="flex items-center gap-2 px-3 py-2 text-sm text-text-primary rounded-md cursor-pointer hover:bg-white/5 outline-none transition-colors"
                  onSelect={handleRefresh}
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Refresh Data
                </DropdownMenu.Item>
                <DropdownMenu.Separator className="h-px bg-border-default my-1" />
                <DropdownMenu.Item
                  className="flex items-center gap-2 px-3 py-2 text-sm text-red-400 rounded-md cursor-pointer hover:bg-red-500/10 outline-none transition-colors"
                  onSelect={() => onDelete(widget.id)}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  Delete Widget
                </DropdownMenu.Item>
              </DropdownMenu.Content>
            </DropdownMenu.Portal>
          </DropdownMenu.Root>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 relative min-h-0 p-2">
        {/* Loading overlay */}
        {isRefreshing && (
          <div className="absolute inset-0 bg-bg-primary/60 backdrop-blur-sm flex items-center justify-center z-10 rounded-b-xl">
            <div className="animate-spin h-6 w-6 border-2 border-brand-primary border-t-transparent rounded-full" />
          </div>
        )}

        {/* Error state */}
        {hasError && (
          <div className="absolute inset-0 bg-red-500/5 flex flex-col items-center justify-center z-5 p-4 rounded-b-xl">
            <AlertCircle className="w-8 h-8 text-red-400 mb-2" />
            <p className="text-xs text-red-400 text-center line-clamp-3">
              {widget.last_error}
            </p>
            <button
              onClick={handleRefresh}
              className="mt-3 px-3 py-1.5 text-xs bg-red-500/20 text-red-300 rounded-md hover:bg-red-500/30 transition-colors"
            >
              Retry
            </button>
          </div>
        )}

        {/* Chart content */}
        {!hasError && hasData && (
          <div className="h-full w-full">
            <ErrorBoundary
              fallback={
                <div className="flex flex-col items-center justify-center h-full p-4 text-center">
                  <AlertCircle className="w-6 h-6 text-brand-danger mb-2" />
                  <p className="text-xs text-text-muted">Chart render error</p>
                  <button
                    onClick={handleRefresh}
                    className="mt-2 text-xs text-brand-primary hover:text-brand-primary/80 transition-colors"
                  >
                    Retry
                  </button>
                </div>
              }
            >
              <ChartRenderer
                config={widget.chart_config}
                data={{
                  columns: widget.query_result_preview!.columns,
                  rows: widget.query_result_preview!.rows,
                  row_count: widget.query_result_preview!.row_count,
                }}
              />
            </ErrorBoundary>
          </div>
        )}

        {/* No data state */}
        {!hasError && !hasData && !isRefreshing && (
          <div className="h-full flex flex-col items-center justify-center text-text-muted">
            <p className="text-sm">No data available</p>
            <button
              onClick={handleRefresh}
              className="mt-2 text-xs text-brand-primary hover:text-brand-primary/80 transition-colors"
            >
              Refresh to load data
            </button>
          </div>
        )}

        {/* Text widget */}
        {widget.widget_type === 'text' && !hasError && (
          <div className="h-full p-3 text-sm text-text-primary whitespace-pre-wrap">
            {widget.chart_config?.content || ''}
          </div>
        )}
      </div>
    </div>
  );
}
