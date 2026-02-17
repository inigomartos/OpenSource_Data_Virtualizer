'use client';

import { usePathname } from 'next/navigation';

const pageTitles: Record<string, string> = {
  '/chat': 'Chat',
  '/connections': 'Connections',
  '/dashboards': 'Dashboards',
  '/explore': 'Explore',
  '/alerts': 'Alerts',
  '/settings': 'Settings',
};

export default function Topbar() {
  const pathname = usePathname();
  const title = Object.entries(pageTitles).find(([path]) =>
    pathname.startsWith(path)
  )?.[1] || 'DataMind';

  return (
    <header className="h-14 bg-bg-surface border-b border-border-default flex items-center justify-between px-6">
      <h2 className="text-lg font-heading font-semibold text-text-primary">
        {title}
      </h2>
      <div className="flex items-center gap-4">
        <button className="px-3 py-1.5 text-sm text-text-secondary bg-bg-elevated rounded-lg border border-border-default hover:border-border-hover">
          Cmd+K
        </button>
      </div>
    </header>
  );
}
