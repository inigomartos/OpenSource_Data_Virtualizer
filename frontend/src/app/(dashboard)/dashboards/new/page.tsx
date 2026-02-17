'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';

export default function NewDashboardPage() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await apiClient('/dashboards', {
        method: 'POST',
        body: JSON.stringify({ title, description }),
      });
      router.push('/dashboards');
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto">
      <h1 className="text-2xl font-heading font-bold text-text-primary mb-6">New Dashboard</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm text-text-secondary mb-1">Title</label>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-4 py-2.5 bg-bg-elevated border border-border-default rounded-lg text-text-primary focus:outline-none focus:border-brand-primary"
            required
          />
        </div>
        <div>
          <label className="block text-sm text-text-secondary mb-1">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-4 py-2.5 bg-bg-elevated border border-border-default rounded-lg text-text-primary focus:outline-none focus:border-brand-primary"
            rows={3}
          />
        </div>
        <button
          type="submit"
          disabled={saving}
          className="px-6 py-2.5 bg-brand-primary text-white rounded-lg font-medium hover:opacity-90 disabled:opacity-50"
        >
          {saving ? 'Creating...' : 'Create Dashboard'}
        </button>
      </form>
    </div>
  );
}
