'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    org_name: '',
    org_slug: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    if (name === 'org_name') {
      setForm((prev) => ({
        ...prev,
        org_slug: value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''),
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/auth/register`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(form),
        }
      );

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Registration failed');
      }

      router.push('/login');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-xl font-heading font-semibold text-text-primary">
        Create your account
      </h2>

      {error && (
        <div className="p-3 bg-brand-danger/10 border border-brand-danger/20 rounded-lg text-brand-danger text-sm">
          {error}
        </div>
      )}

      <div>
        <label className="block text-sm text-text-secondary mb-1">Full Name</label>
        <input
          type="text"
          name="full_name"
          value={form.full_name}
          onChange={handleChange}
          className="w-full px-4 py-2.5 bg-bg-elevated border border-border-default rounded-lg text-text-primary focus:outline-none focus:border-brand-primary"
          required
        />
      </div>

      <div>
        <label className="block text-sm text-text-secondary mb-1">Email</label>
        <input
          type="email"
          name="email"
          value={form.email}
          onChange={handleChange}
          className="w-full px-4 py-2.5 bg-bg-elevated border border-border-default rounded-lg text-text-primary focus:outline-none focus:border-brand-primary"
          required
        />
      </div>

      <div>
        <label className="block text-sm text-text-secondary mb-1">Password</label>
        <input
          type="password"
          name="password"
          value={form.password}
          onChange={handleChange}
          className="w-full px-4 py-2.5 bg-bg-elevated border border-border-default rounded-lg text-text-primary focus:outline-none focus:border-brand-primary"
          minLength={8}
          required
        />
      </div>

      <div>
        <label className="block text-sm text-text-secondary mb-1">Organization Name</label>
        <input
          type="text"
          name="org_name"
          value={form.org_name}
          onChange={handleChange}
          className="w-full px-4 py-2.5 bg-bg-elevated border border-border-default rounded-lg text-text-primary focus:outline-none focus:border-brand-primary"
          required
        />
      </div>

      <div>
        <label className="block text-sm text-text-secondary mb-1">
          Organization Slug
        </label>
        <input
          type="text"
          name="org_slug"
          value={form.org_slug}
          onChange={handleChange}
          className="w-full px-4 py-2.5 bg-bg-elevated border border-border-default rounded-lg text-text-primary focus:outline-none focus:border-brand-primary"
          pattern="^[a-z0-9-]+$"
          required
        />
        <p className="text-xs text-text-muted mt-1">URL-safe identifier (lowercase, hyphens)</p>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full py-2.5 bg-brand-primary text-white rounded-lg font-medium hover:opacity-90 disabled:opacity-50 shadow-[0_0_20px_rgba(99,102,241,0.3)]"
      >
        {loading ? 'Creating account...' : 'Create Account'}
      </button>

      <p className="text-center text-sm text-text-muted">
        Already have an account?{' '}
        <Link href="/login" className="text-brand-primary hover:underline">
          Sign in
        </Link>
      </p>
    </form>
  );
}
