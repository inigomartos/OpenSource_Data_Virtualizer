'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, LayoutDashboard, Loader2 } from 'lucide-react';
import { createDashboard } from '@/hooks/use-dashboards';

export default function NewDashboardPage() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setSaving(true);
    setError('');

    try {
      const dashboard = await createDashboard({ title, description });
      router.push(`/dashboards/${dashboard.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create dashboard');
      setSaving(false);
    }
  };

  const inputClasses =
    'w-full px-4 py-2.5 bg-bg-elevated border border-border-default rounded-lg text-text-primary focus:outline-none focus:border-brand-primary transition-colors duration-200';

  return (
    <div className="max-w-lg mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <Link
          href="/dashboards"
          className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-white/5 transition-all duration-200"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-heading font-bold text-text-primary">
            New Dashboard
          </h1>
          <p className="text-sm text-text-muted mt-0.5">
            Create a new dashboard to visualize your data
          </p>
        </div>
      </div>

      {/* Form Card */}
      <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-brand-primary/10 flex items-center justify-center">
            <LayoutDashboard className="w-5 h-5 text-brand-primary" />
          </div>
          <p className="text-sm text-text-secondary">
            Give your dashboard a name and optional description.
            You can add widgets after creating it.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-text-secondary mb-1.5">
              Title <span className="text-red-400">*</span>
            </label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Sales Overview, Monthly Metrics"
              className={inputClasses}
              required
              autoFocus
            />
          </div>

          <div>
            <label className="block text-sm text-text-secondary mb-1.5">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What does this dashboard track?"
              className={inputClasses}
              rows={3}
            />
          </div>

          {error && (
            <p className="text-sm text-red-400 bg-red-500/10 px-3 py-2 rounded-lg">
              {error}
            </p>
          )}

          <div className="flex items-center justify-end gap-3 pt-2">
            <Link
              href="/dashboards"
              className="px-4 py-2.5 text-sm text-text-secondary hover:text-text-primary border border-border-default rounded-lg hover:bg-white/5 transition-all duration-200"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={saving || !title.trim()}
              className="flex items-center gap-2 px-6 py-2.5 bg-brand-primary text-white rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50 shadow-[0_0_20px_rgba(99,102,241,0.3)] transition-all duration-200"
            >
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create Dashboard'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
