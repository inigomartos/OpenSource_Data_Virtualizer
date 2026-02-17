'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Command } from 'cmdk';
import {
  MessageSquare,
  LayoutDashboard,
  Database,
  Search,
  Bell,
  Settings,
  Plus,
  Sun,
  Moon,
  Clock,
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { useUIStore } from '@/stores/ui-store';

interface RecentSession {
  id: string;
  title?: string;
  created_at: string;
}

export function CommandPalette() {
  const router = useRouter();
  const { commandPaletteOpen, toggleCommandPalette, theme, setTheme } = useUIStore();
  const [search, setSearch] = useState('');
  const [recentSessions, setRecentSessions] = useState<RecentSession[]>([]);

  // Keyboard shortcut: Cmd+K / Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        toggleCommandPalette();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [toggleCommandPalette]);

  // Fetch recent sessions when opening
  useEffect(() => {
    if (commandPaletteOpen) {
      setSearch('');
      apiClient('/chat/sessions?limit=5')
        .then((data) => setRecentSessions(data.sessions || []))
        .catch(() => setRecentSessions([]));
    }
  }, [commandPaletteOpen]);

  const runAction = useCallback(
    (callback: () => void) => {
      callback();
      toggleCommandPalette();
    },
    [toggleCommandPalette]
  );

  const navigateTo = useCallback(
    (path: string) => {
      runAction(() => router.push(path));
    },
    [router, runAction]
  );

  const handleToggleTheme = useCallback(() => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  }, [theme, setTheme]);

  if (!commandPaletteOpen) return null;

  return (
    <div className="fixed inset-0 z-50">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={toggleCommandPalette}
      />

      {/* Command palette */}
      <div className="absolute top-[20%] left-1/2 -translate-x-1/2 w-full max-w-lg">
        <Command
          className="bg-bg-surface border border-border-default rounded-2xl shadow-2xl overflow-hidden"
          onKeyDown={(e: React.KeyboardEvent) => {
            if (e.key === 'Escape') {
              toggleCommandPalette();
            }
          }}
        >
          {/* Search input */}
          <div className="flex items-center gap-3 px-4 border-b border-border-default">
            <Search className="w-4 h-4 text-text-muted shrink-0" />
            <Command.Input
              value={search}
              onValueChange={setSearch}
              placeholder="Type a command or search..."
              className="flex-1 h-12 bg-transparent text-sm text-text-primary placeholder:text-text-muted outline-none"
            />
            <kbd className="hidden sm:inline-flex items-center px-1.5 py-0.5 text-[10px] font-mono text-text-muted bg-bg-elevated border border-border-default rounded">
              ESC
            </kbd>
          </div>

          {/* Results */}
          <Command.List className="max-h-80 overflow-y-auto p-2">
            <Command.Empty className="py-8 text-center text-sm text-text-muted">
              No results found.
            </Command.Empty>

            {/* Pages group */}
            <Command.Group
              heading="Pages"
              className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-text-muted"
            >
              <CommandItem
                icon={<MessageSquare className="w-4 h-4" />}
                label="Chat"
                shortcut="G C"
                onSelect={() => navigateTo('/chat')}
              />
              <CommandItem
                icon={<LayoutDashboard className="w-4 h-4" />}
                label="Dashboards"
                shortcut="G D"
                onSelect={() => navigateTo('/dashboards')}
              />
              <CommandItem
                icon={<Database className="w-4 h-4" />}
                label="Connections"
                shortcut="G N"
                onSelect={() => navigateTo('/connections')}
              />
              <CommandItem
                icon={<Bell className="w-4 h-4" />}
                label="Alerts"
                shortcut="G A"
                onSelect={() => navigateTo('/alerts')}
              />
              <CommandItem
                icon={<Search className="w-4 h-4" />}
                label="Explore"
                shortcut="G E"
                onSelect={() => navigateTo('/explore')}
              />
              <CommandItem
                icon={<Settings className="w-4 h-4" />}
                label="Settings"
                shortcut="G S"
                onSelect={() => navigateTo('/settings')}
              />
            </Command.Group>

            {/* Actions group */}
            <Command.Group
              heading="Actions"
              className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-text-muted"
            >
              <CommandItem
                icon={<Plus className="w-4 h-4" />}
                label="New Dashboard"
                onSelect={() => navigateTo('/dashboards?new=1')}
              />
              <CommandItem
                icon={<Plus className="w-4 h-4" />}
                label="New Connection"
                onSelect={() => navigateTo('/connections?new=1')}
              />
              <CommandItem
                icon={<Plus className="w-4 h-4" />}
                label="New Alert"
                onSelect={() => navigateTo('/alerts?new=1')}
              />
              <CommandItem
                icon={theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                label={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
                onSelect={() => runAction(handleToggleTheme)}
              />
            </Command.Group>

            {/* Recent sessions */}
            {recentSessions.length > 0 && (
              <Command.Group
                heading="Recent"
                className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-text-muted"
              >
                {recentSessions.map((session) => (
                  <CommandItem
                    key={session.id}
                    icon={<Clock className="w-4 h-4" />}
                    label={session.title || 'Untitled Session'}
                    onSelect={() => navigateTo(`/chat?session=${session.id}`)}
                  />
                ))}
              </Command.Group>
            )}
          </Command.List>
        </Command>
      </div>
    </div>
  );
}

function CommandItem({
  icon,
  label,
  shortcut,
  onSelect,
}: {
  icon: React.ReactNode;
  label: string;
  shortcut?: string;
  onSelect: () => void;
}) {
  return (
    <Command.Item
      value={label}
      onSelect={onSelect}
      className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-text-secondary cursor-pointer data-[selected=true]:bg-bg-elevated data-[selected=true]:text-text-primary transition-colors"
    >
      <span className="text-text-muted shrink-0">{icon}</span>
      <span className="flex-1">{label}</span>
      {shortcut && (
        <kbd className="hidden sm:inline text-[10px] font-mono text-text-muted bg-bg-elevated px-1.5 py-0.5 rounded border border-border-default">
          {shortcut}
        </kbd>
      )}
    </Command.Item>
  );
}
