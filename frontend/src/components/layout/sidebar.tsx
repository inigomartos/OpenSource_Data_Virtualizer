'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { MessageSquare, Database, LayoutDashboard, Search, Bell, Settings, type LucideIcon } from 'lucide-react';
import { useUserStore } from '@/stores/user-store';

const iconMap: Record<string, LucideIcon> = { MessageSquare, Database, LayoutDashboard, Search, Bell, Settings };

const navItems = [
  { href: '/chat', label: 'Chat', icon: 'MessageSquare' },
  { href: '/connections', label: 'Connections', icon: 'Database' },
  { href: '/dashboards', label: 'Dashboards', icon: 'LayoutDashboard' },
  { href: '/explore', label: 'Explore', icon: 'Search' },
  { href: '/alerts', label: 'Alerts', icon: 'Bell' },
  { href: '/settings', label: 'Settings', icon: 'Settings' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const user = useUserStore((s) => s.user);

  const displayName = user?.full_name || 'User';
  const displayEmail = user?.email || 'user@company.com';
  const avatarInitial = displayName.charAt(0).toUpperCase();

  return (
    <aside className="w-64 bg-bg-surface border-r border-border-default flex flex-col">
      <div className="p-6">
        <h1 className="text-xl font-heading font-bold text-text-primary">
          Data<span className="text-brand-primary">Mind</span>
        </h1>
      </div>

      <nav className="flex-1 px-3 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-brand-primary/10 text-brand-primary'
                  : 'text-text-secondary hover:text-text-primary hover:bg-bg-elevated'
              }`}
            >
              {(() => { const Icon = iconMap[item.icon]; return Icon ? <Icon className="w-5 h-5" /> : null; })()}
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-border-default">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-brand-primary/20 flex items-center justify-center text-brand-primary text-sm font-bold">
            {avatarInitial}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-text-primary truncate">{displayName}</p>
            <p className="text-xs text-text-muted truncate">{displayEmail}</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
