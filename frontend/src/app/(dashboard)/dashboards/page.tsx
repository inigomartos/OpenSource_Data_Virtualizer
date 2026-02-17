'use client';

import Link from 'next/link';
import {
  LayoutDashboard,
  Plus,
  Globe,
  Lock,
  LayoutGrid,
  Clock,
} from 'lucide-react';
import { useDashboards } from '@/hooks/use-dashboards';
import { formatDistanceToNow } from 'date-fns';

export default function DashboardsPage() {
  const { dashboards, isLoading, error } = useDashboards();

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-heading font-bold text-text-primary">
            Dashboards
          </h1>
          <p className="text-text-secondary text-sm mt-1">
            Build and share live data dashboards
          </p>
        </div>
        <Link
          href="/dashboards/new"
          className="flex items-center gap-2 px-4 py-2 bg-brand-primary text-white rounded-lg text-sm font-medium hover:opacity-90 shadow-[0_0_20px_rgba(99,102,241,0.3)] transition-all duration-200"
        >
          <Plus className="w-4 h-4" />
          New Dashboard
        </Link>
      </div>

      {/* Loading skeletons */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-48 bg-bg-elevated animate-pulse rounded-xl border border-border-default"
            />
          ))}
        </div>
      ) : dashboards.length === 0 ? (
        /* Empty state */
        <div className="flex flex-col items-center justify-center py-20">
          <div className="w-16 h-16 rounded-2xl bg-brand-primary/10 flex items-center justify-center mb-4">
            <LayoutDashboard className="w-8 h-8 text-brand-primary" />
          </div>
          <h3 className="text-lg font-medium text-text-primary mb-1">
            No dashboards yet
          </h3>
          <p className="text-sm text-text-muted mb-6 text-center max-w-md">
            Create your first dashboard to start visualizing and sharing your
            data insights.
          </p>
          <Link
            href="/dashboards/new"
            className="flex items-center gap-2 px-6 py-3 bg-brand-primary text-white rounded-lg font-medium hover:opacity-90 shadow-[0_0_20px_rgba(99,102,241,0.3)] transition-all duration-200"
          >
            <Plus className="w-5 h-5" />
            Create your first dashboard
          </Link>
        </div>
      ) : (
        /* Dashboard grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {dashboards.map((dash) => {
            const updatedAt = dash.updated_at || dash.created_at;
            const relativeTime = formatDistanceToNow(new Date(updatedAt), {
              addSuffix: true,
            });

            return (
              <Link
                key={dash.id}
                href={`/dashboards/${dash.id}`}
                className="group p-5 backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl hover:border-brand-primary/30 hover:bg-brand-primary/5 transition-all duration-200"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-text-primary group-hover:text-brand-primary transition-colors truncate">
                      {dash.title}
                    </h3>
                    {dash.description && (
                      <p className="text-sm text-text-muted mt-1 line-clamp-2">
                        {dash.description}
                      </p>
                    )}
                  </div>
                  <div className="ml-3 shrink-0">
                    {dash.is_shared ? (
                      <div className="p-1.5 rounded-md bg-brand-accent/10" title="Shared">
                        <Globe className="w-3.5 h-3.5 text-brand-accent" />
                      </div>
                    ) : (
                      <div className="p-1.5 rounded-md bg-white/5" title="Private">
                        <Lock className="w-3.5 h-3.5 text-text-muted" />
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-4 text-xs text-text-muted pt-3 border-t border-white/5">
                  {/* Widget count */}
                  <span className="flex items-center gap-1.5">
                    <LayoutGrid className="w-3.5 h-3.5" />
                    {dash.widget_count != null
                      ? `${dash.widget_count} widget${dash.widget_count !== 1 ? 's' : ''}`
                      : '0 widgets'}
                  </span>

                  {/* Last updated */}
                  <span className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" />
                    {relativeTime}
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
