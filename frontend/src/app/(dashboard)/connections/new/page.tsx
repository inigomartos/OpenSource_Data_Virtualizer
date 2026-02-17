'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';

export default function NewConnectionPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    name: '',
    type: 'postgresql',
    host: '',
    port: 5432,
    database_name: '',
    username: '',
    password: '',
    ssl_mode: 'prefer',
  });
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: name === 'port' ? parseInt(value) || 0 : value }));
  };

  const isFileType = form.type === 'csv' || form.type === 'excel' || form.type === 'sqlite';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await apiClient('/connections', {
        method: 'POST',
        body: JSON.stringify(form),
      });
      router.push('/connections');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-heading font-bold text-text-primary mb-6">New Connection</h1>

      <form onSubmit={handleSubmit} className="space-y-5">
        {error && (
          <div className="p-3 bg-brand-danger/10 border border-brand-danger/20 rounded-lg text-brand-danger text-sm">
            {error}
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-text-secondary mb-1">Connection Name</label>
            <input
              name="name"
              value={form.name}
              onChange={handleChange}
              className="w-full px-4 py-2.5 bg-bg-elevated border border-border-default rounded-lg text-text-primary focus:outline-none focus:border-brand-primary"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-text-secondary mb-1">Type</label>
            <select
              name="type"
              value={form.type}
              onChange={handleChange}
              className="w-full px-4 py-2.5 bg-bg-elevated border border-border-default rounded-lg text-text-primary focus:outline-none focus:border-brand-primary"
            >
              <option value="postgresql">PostgreSQL</option>
              <option value="mysql">MySQL</option>
              <option value="sqlite">SQLite</option>
              <option value="csv">CSV File</option>
              <option value="excel">Excel File</option>
            </select>
          </div>
        </div>

        {!isFileType && (
          <>
            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-2">
                <label className="block text-sm text-text-secondary mb-1">Host</label>
                <input name="host" value={form.host} onChange={handleChange} className="w-full px-4 py-2.5 bg-bg-elevated border border-border-default rounded-lg text-text-primary focus:outline-none focus:border-brand-primary" />
              </div>
              <div>
                <label className="block text-sm text-text-secondary mb-1">Port</label>
                <input name="port" type="number" value={form.port} onChange={handleChange} className="w-full px-4 py-2.5 bg-bg-elevated border border-border-default rounded-lg text-text-primary focus:outline-none focus:border-brand-primary" />
              </div>
            </div>
            <div>
              <label className="block text-sm text-text-secondary mb-1">Database Name</label>
              <input name="database_name" value={form.database_name} onChange={handleChange} className="w-full px-4 py-2.5 bg-bg-elevated border border-border-default rounded-lg text-text-primary focus:outline-none focus:border-brand-primary" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-text-secondary mb-1">Username</label>
                <input name="username" value={form.username} onChange={handleChange} className="w-full px-4 py-2.5 bg-bg-elevated border border-border-default rounded-lg text-text-primary focus:outline-none focus:border-brand-primary" />
              </div>
              <div>
                <label className="block text-sm text-text-secondary mb-1">Password</label>
                <input name="password" type="password" value={form.password} onChange={handleChange} className="w-full px-4 py-2.5 bg-bg-elevated border border-border-default rounded-lg text-text-primary focus:outline-none focus:border-brand-primary" />
              </div>
            </div>
          </>
        )}

        <div className="flex gap-3 pt-4">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 bg-brand-primary text-white rounded-lg font-medium hover:opacity-90 disabled:opacity-50"
          >
            {saving ? 'Creating...' : 'Create Connection'}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="px-6 py-2.5 bg-bg-elevated text-text-primary rounded-lg font-medium border border-border-default hover:border-border-hover"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
