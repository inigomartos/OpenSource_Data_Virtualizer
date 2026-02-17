'use client';

import { useTheme } from '@/hooks/use-theme';

export default function SettingsPage() {
  const { theme, toggle } = useTheme();

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  };

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-heading font-bold text-text-primary mb-6">Settings</h1>

      <div className="space-y-6">
        <div className="p-5 bg-bg-surface border border-border-default rounded-xl">
          <h3 className="font-medium text-text-primary mb-3">Appearance</h3>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-secondary">Theme</p>
              <p className="text-xs text-text-muted">Switch between dark and light mode</p>
            </div>
            <button
              onClick={toggle}
              className="px-4 py-2 bg-bg-elevated border border-border-default rounded-lg text-sm text-text-primary hover:border-border-hover"
            >
              {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
            </button>
          </div>
        </div>

        <div className="p-5 bg-bg-surface border border-border-default rounded-xl">
          <h3 className="font-medium text-text-primary mb-3">Account</h3>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-brand-danger/10 text-brand-danger border border-brand-danger/20 rounded-lg text-sm hover:bg-brand-danger/20"
          >
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}
