'use client';

import { useState, useCallback, useMemo, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Responsive, WidthProvider, Layout } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import {
  ArrowLeft,
  Pencil,
  Plus,
  Lock,
  Globe,
  Loader2,
  LayoutGrid,
  Eye,
} from 'lucide-react';
import {
  useDashboard,
  updateDashboard,
  addWidget,
  updateWidget,
  deleteWidget,
  refreshWidget,
} from '@/hooks/use-dashboards';
import WidgetCard from '@/components/dashboard/widget-card';
import WidgetEditorDialog from '@/components/dashboard/widget-editor-dialog';
import AddWidgetDialog from '@/components/dashboard/add-widget-dialog';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import type {
  WidgetWithData,
  CreateWidgetPayload,
  UpdateWidgetPayload,
} from '@/types/dashboard';

const ResponsiveGridLayout = WidthProvider(Responsive);

export default function DashboardDetailPage() {
  const params = useParams();
  const dashboardId = params.id as string;
  const { dashboard, isLoading, error, refresh } = useDashboard(dashboardId);

  const [isEditing, setIsEditing] = useState(false);
  const [isSharing, setIsSharing] = useState(false);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [editorDialogOpen, setEditorDialogOpen] = useState(false);
  const [editingWidget, setEditingWidget] = useState<WidgetWithData | null>(null);
  const [pendingSql, setPendingSql] = useState('');
  const [pendingConnectionId, setPendingConnectionId] = useState('');
  const [refreshingWidgets, setRefreshingWidgets] = useState<Set<string>>(new Set());

  // Auto-refresh timers
  useEffect(() => {
    if (!dashboard?.widgets) return;

    const timers: NodeJS.Timeout[] = [];

    dashboard.widgets.forEach((widget) => {
      if (widget.refresh_interval_seconds && widget.refresh_interval_seconds > 0) {
        const timer = setInterval(() => {
          handleRefreshWidget(widget.id);
        }, widget.refresh_interval_seconds * 1000);
        timers.push(timer);
      }
    });

    return () => {
      timers.forEach(clearInterval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dashboard?.widgets?.map((w) => `${w.id}-${w.refresh_interval_seconds}`).join(',')]);

  // Separate KPI widgets from grid widgets
  const { kpiWidgets, gridWidgets } = useMemo(() => {
    if (!dashboard?.widgets) return { kpiWidgets: [], gridWidgets: [] };

    const kpis: WidgetWithData[] = [];
    const grids: WidgetWithData[] = [];

    dashboard.widgets.forEach((w) => {
      if (w.widget_type === 'kpi') {
        kpis.push(w);
      } else {
        grids.push(w);
      }
    });

    return { kpiWidgets: kpis, gridWidgets: grids };
  }, [dashboard?.widgets]);

  // Build layout from widget positions
  const layouts = useMemo(() => {
    const lg: Layout[] = gridWidgets.map((w) => ({
      i: w.id,
      x: w.position.x,
      y: w.position.y,
      w: w.position.w,
      h: w.position.h,
      minW: 2,
      minH: 2,
      static: !isEditing,
    }));

    return { lg, md: lg, sm: lg.map((l) => ({ ...l, w: Math.min(l.w, 6), x: 0 })) };
  }, [gridWidgets, isEditing]);

  const handleLayoutChange = useCallback(
    async (layout: Layout[]) => {
      if (!isEditing || !dashboard) return;

      // Build new layout config
      const updatedPositions = layout.map((l) => ({
        widgetId: l.i,
        position: { x: l.x, y: l.y, w: l.w, h: l.h },
      }));

      try {
        await updateDashboard(dashboard.id, {
          layout_config: updatedPositions,
        });

        // Also update individual widget positions
        for (const item of updatedPositions) {
          const widget = dashboard.widgets.find((w) => w.id === item.widgetId);
          if (
            widget &&
            (widget.position.x !== item.position.x ||
              widget.position.y !== item.position.y ||
              widget.position.w !== item.position.w ||
              widget.position.h !== item.position.h)
          ) {
            await updateWidget(dashboard.id, item.widgetId, {
              position: item.position,
            });
          }
        }

        refresh();
      } catch (err) {
        console.error('Failed to save layout:', err);
      }
    },
    [isEditing, dashboard, refresh]
  );

  const handleRefreshWidget = useCallback(
    async (widgetId: string) => {
      if (!dashboard) return;
      setRefreshingWidgets((prev) => new Set(prev).add(widgetId));
      try {
        await refreshWidget(dashboard.id, widgetId);
        await refresh();
      } catch (err) {
        console.error('Failed to refresh widget:', err);
      } finally {
        setRefreshingWidgets((prev) => {
          const next = new Set(prev);
          next.delete(widgetId);
          return next;
        });
      }
    },
    [dashboard, refresh]
  );

  const handleEditWidget = useCallback((widget: WidgetWithData) => {
    setEditingWidget(widget);
    setPendingSql('');
    setPendingConnectionId('');
    setEditorDialogOpen(true);
  }, []);

  const handleDeleteWidget = useCallback(
    async (widgetId: string) => {
      if (!dashboard) return;
      if (!window.confirm('Delete this widget? This cannot be undone.')) return;

      try {
        await deleteWidget(dashboard.id, widgetId);
        await refresh();
      } catch (err) {
        console.error('Failed to delete widget:', err);
      }
    },
    [dashboard, refresh]
  );

  const handleToggleShare = useCallback(async () => {
    if (!dashboard) return;
    setIsSharing(true);
    try {
      await updateDashboard(dashboard.id, { is_shared: !dashboard.is_shared });
      await refresh();
    } catch (err) {
      console.error('Failed to toggle sharing:', err);
    } finally {
      setIsSharing(false);
    }
  }, [dashboard, refresh]);

  // Called from AddWidgetDialog: user selected a query
  const handleAddWidgetFromQuery = useCallback(
    (sql: string, connectionId: string) => {
      setPendingSql(sql);
      setPendingConnectionId(connectionId);
      setEditingWidget(null);
      setEditorDialogOpen(true);
    },
    []
  );

  // Called from WidgetEditorDialog: submit new or edit widget
  const handleWidgetEditorSubmit = useCallback(
    async (data: CreateWidgetPayload | UpdateWidgetPayload) => {
      if (!dashboard) return;

      if (editingWidget) {
        await updateWidget(dashboard.id, editingWidget.id, data as UpdateWidgetPayload);
      } else {
        await addWidget(dashboard.id, data as CreateWidgetPayload);
      }

      await refresh();
      setEditingWidget(null);
    },
    [dashboard, editingWidget, refresh]
  );

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 text-brand-primary animate-spin" />
          <p className="text-sm text-text-muted">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !dashboard) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-center">
          <p className="text-lg text-text-primary mb-2">Dashboard not found</p>
          <p className="text-sm text-text-muted mb-4">
            The dashboard may have been deleted or you lack access.
          </p>
          <Link
            href="/dashboards"
            className="px-4 py-2 bg-brand-primary text-white rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
          >
            Back to Dashboards
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-full">
      {/* Top Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <Link
            href="/dashboards"
            className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-white/5 transition-all duration-200"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-xl font-heading font-bold text-text-primary">
              {dashboard.title}
            </h1>
            {dashboard.description && (
              <p className="text-sm text-text-muted mt-0.5">{dashboard.description}</p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Share toggle */}
          <button
            onClick={handleToggleShare}
            disabled={isSharing}
            className={`
              flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium
              transition-all duration-200 border
              ${
                dashboard.is_shared
                  ? 'border-brand-accent/30 text-brand-accent bg-brand-accent/10 hover:bg-brand-accent/20'
                  : 'border-border-default text-text-secondary hover:text-text-primary hover:bg-white/5'
              }
            `}
          >
            {isSharing ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : dashboard.is_shared ? (
              <Globe className="w-4 h-4" />
            ) : (
              <Lock className="w-4 h-4" />
            )}
            {dashboard.is_shared ? 'Shared' : 'Private'}
          </button>

          {/* Edit mode toggle */}
          <button
            onClick={() => setIsEditing(!isEditing)}
            className={`
              flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium
              transition-all duration-200 border
              ${
                isEditing
                  ? 'border-brand-primary/30 text-brand-primary bg-brand-primary/10 hover:bg-brand-primary/20'
                  : 'border-border-default text-text-secondary hover:text-text-primary hover:bg-white/5'
              }
            `}
          >
            {isEditing ? (
              <>
                <Eye className="w-4 h-4" />
                Done Editing
              </>
            ) : (
              <>
                <Pencil className="w-4 h-4" />
                Edit
              </>
            )}
          </button>

          {/* Add widget */}
          <button
            onClick={() => setAddDialogOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-brand-primary text-white rounded-lg text-sm font-medium hover:opacity-90 shadow-[0_0_20px_rgba(99,102,241,0.3)] transition-all duration-200"
          >
            <Plus className="w-4 h-4" />
            Add Widget
          </button>
        </div>
      </div>

      {/* KPI Row */}
      {kpiWidgets.length > 0 && (
        <ErrorBoundary>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-6">
            {kpiWidgets.map((kpi) => (
              <div key={kpi.id} className="h-[120px]">
                <WidgetCard
                  widget={kpi}
                  onRefresh={handleRefreshWidget}
                  onEdit={handleEditWidget}
                  onDelete={handleDeleteWidget}
                  isEditing={isEditing}
                />
              </div>
            ))}
          </div>
        </ErrorBoundary>
      )}

      {/* Grid Widgets */}
      {gridWidgets.length > 0 ? (
        <ErrorBoundary>
        <ResponsiveGridLayout
          className="layout"
          layouts={layouts}
          breakpoints={{ lg: 1200, md: 768, sm: 480 }}
          cols={{ lg: 12, md: 6, sm: 1 }}
          rowHeight={80}
          isDraggable={isEditing}
          isResizable={isEditing}
          draggableHandle=".drag-handle"
          onLayoutChange={(layout) => handleLayoutChange(layout)}
          compactType="vertical"
          margin={[16, 16]}
        >
          {gridWidgets.map((widget) => (
            <div key={widget.id}>
              <WidgetCard
                widget={widget}
                onRefresh={handleRefreshWidget}
                onEdit={handleEditWidget}
                onDelete={handleDeleteWidget}
                isEditing={isEditing}
              />
            </div>
          ))}
        </ResponsiveGridLayout>
        </ErrorBoundary>
      ) : kpiWidgets.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="w-16 h-16 rounded-2xl bg-brand-primary/10 flex items-center justify-center mb-4">
            <LayoutGrid className="w-8 h-8 text-brand-primary" />
          </div>
          <h3 className="text-lg font-medium text-text-primary mb-1">
            No widgets yet
          </h3>
          <p className="text-sm text-text-muted mb-6 text-center max-w-md">
            Add your first widget to start building this dashboard. Choose from
            saved queries or write custom SQL.
          </p>
          <button
            onClick={() => setAddDialogOpen(true)}
            className="flex items-center gap-2 px-6 py-3 bg-brand-primary text-white rounded-lg font-medium hover:opacity-90 shadow-[0_0_20px_rgba(99,102,241,0.3)] transition-all duration-200"
          >
            <Plus className="w-5 h-5" />
            Add Your First Widget
          </button>
        </div>
      ) : null}

      {/* Dialogs */}
      <AddWidgetDialog
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
        onSelect={handleAddWidgetFromQuery}
      />

      <WidgetEditorDialog
        open={editorDialogOpen}
        onOpenChange={setEditorDialogOpen}
        widget={editingWidget}
        onSubmit={handleWidgetEditorSubmit}
        initialSql={pendingSql}
        initialConnectionId={pendingConnectionId}
      />
    </div>
  );
}
