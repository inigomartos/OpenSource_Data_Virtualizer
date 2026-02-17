'use client';

import { usePathname } from 'next/navigation';
import { Sun, Moon, Search, User, LogOut } from 'lucide-react';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { useUIStore } from '@/stores/ui-store';
import { NotificationBell } from '@/components/alerts/notification-bell';
import { useRouter } from 'next/navigation';

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
  const router = useRouter();
  const { theme, setTheme, toggleCommandPalette } = useUIStore();

  const title = Object.entries(pageTitles).find(([path]) =>
    pathname.startsWith(path)
  )?.[1] || 'DataMind';

  const handleToggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    router.push('/login');
  };

  return (
    <header className="h-14 bg-bg-surface border-b border-border-default flex items-center justify-between px-6">
      <h2 className="text-lg font-heading font-semibold text-text-primary">
        {title}
      </h2>

      <div className="flex items-center gap-2">
        {/* Command palette trigger */}
        <button
          onClick={toggleCommandPalette}
          className="flex items-center gap-2 px-3 py-1.5 text-sm text-text-secondary bg-bg-elevated rounded-lg border border-border-default hover:border-border-hover transition-colors"
        >
          <Search className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Search...</span>
          <kbd className="hidden sm:inline text-[10px] font-mono text-text-muted bg-bg-surface px-1.5 py-0.5 rounded border border-border-default ml-2">
            {typeof navigator !== 'undefined' && /Mac|iPod|iPhone|iPad/.test(navigator.platform || '')
              ? '\u2318K'
              : 'Ctrl+K'}
          </kbd>
        </button>

        {/* Theme toggle */}
        <button
          onClick={handleToggleTheme}
          className="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-elevated transition-colors"
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? (
            <Sun className="w-5 h-5" />
          ) : (
            <Moon className="w-5 h-5" />
          )}
        </button>

        {/* Notification bell */}
        <NotificationBell />

        {/* User menu */}
        <DropdownMenu.Root>
          <DropdownMenu.Trigger asChild>
            <button className="w-8 h-8 rounded-full bg-brand-primary/20 flex items-center justify-center text-brand-primary text-sm font-bold hover:bg-brand-primary/30 transition-colors">
              U
            </button>
          </DropdownMenu.Trigger>

          <DropdownMenu.Portal>
            <DropdownMenu.Content
              align="end"
              sideOffset={8}
              className="w-48 bg-bg-surface border border-border-default rounded-xl shadow-2xl z-50 p-1"
            >
              <DropdownMenu.Item
                onSelect={() => router.push('/settings')}
                className="flex items-center gap-2 px-3 py-2 text-sm text-text-secondary rounded-lg cursor-pointer outline-none hover:bg-bg-elevated hover:text-text-primary focus:bg-bg-elevated"
              >
                <User className="w-4 h-4" />
                Profile & Settings
              </DropdownMenu.Item>
              <DropdownMenu.Separator className="h-px bg-border-default my-1" />
              <DropdownMenu.Item
                onSelect={handleLogout}
                className="flex items-center gap-2 px-3 py-2 text-sm text-brand-danger rounded-lg cursor-pointer outline-none hover:bg-brand-danger/10 focus:bg-brand-danger/10"
              >
                <LogOut className="w-4 h-4" />
                Sign Out
              </DropdownMenu.Item>
            </DropdownMenu.Content>
          </DropdownMenu.Portal>
        </DropdownMenu.Root>
      </div>
    </header>
  );
}
