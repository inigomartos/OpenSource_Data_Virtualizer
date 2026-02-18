# DataMind Frontend

Next.js 14 (App Router) single-page application for the DataMind BI platform.

## Tech Stack
- Next.js 14 (App Router), React 18, TypeScript
- Tailwind CSS + shadcn/ui components
- Zustand (client state), SWR (server data fetching)
- Recharts (charts), react-grid-layout (dashboard builder)
- cmdk (command palette)

## Directory Structure
```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/                 # Route group: login, register (centered card layout)
│   ├── (dashboard)/            # Route group: chat, connections, dashboards, alerts, explore, settings
│   ├── layout.tsx              # Root layout (fonts, theme, metadata)
│   └── globals.css             # Tailwind base + custom styles
│
├── components/             # React components
│   ├── chat/                   # ChatContainer, ChatMessages, ChatInput, SuggestedQuestions
│   ├── dashboard/              # DashboardGrid, AddWidgetDialog, WidgetCard
│   ├── charts/                 # ChartRenderer (switch → bar/line/area/pie/scatter/kpi/table)
│   ├── alerts/                 # AlertsList, CreateAlertDialog, NotificationBell, AlertEventsPanel
│   ├── layout/                 # Sidebar (Lucide iconMap), Topbar, CommandPalette
│   └── ui/                     # shadcn primitives (Button, Dialog, Input, etc.)
│
├── hooks/                  # Data fetching (SWR)
│   ├── use-connections.ts      # ListResponse<Connection>, data?.data pattern
│   ├── use-dashboards.ts       # ListResponse<Dashboard>, globalMutate on create/update/delete
│   ├── use-chat.ts             # Sessions + history hooks
│   └── use-websocket.ts        # WebSocket with useRef for callback stability (fixed infinite loop)
│
├── stores/                 # Client state (Zustand)
│   ├── chat-store.ts           # sessions, activeSessionId, messages, isLoading
│   ├── connection-store.ts     # connections, activeConnection
│   └── ui-store.ts             # sidebarOpen, commandPaletteOpen, theme
│
├── lib/                    # Utilities
│   ├── api-client.ts           # fetchWithAuth: Bearer token from localStorage, 401 → redirect to login
│   ├── constants.ts            # API_BASE_URL, WS_URL
│   └── utils.ts                # cn() for Tailwind class merging
│
└── types/                  # TypeScript interfaces
    ├── common.ts               # ListResponse<T> { data: T[], count: number }
    ├── connection.ts, dashboard.ts, chat.ts, alert.ts, query.ts
```

## Key Patterns
- **ListResponse<T>**: All list hooks expect `{ data: T[], count: number }` from backend
- **SWR + Zustand split**: SWR for server data (cached, auto-revalidated), Zustand for UI state (synchronous)
- **data?.data access**: SWR returns `{ data: ListResponse }`, so actual array is `data?.data`
- **globalMutate**: After mutations, revalidate SWR cache keys for immediate UI updates
- **Optimistic updates**: Chat messages appear immediately before API response

## Known Issues
- ⚠️ No automatic token refresh — 401 redirects to login (users get kicked every 60 min)
- ⚠️ JWT stored in localStorage (XSS vulnerable) — should be HttpOnly cookies
- ⚠️ Sidebar shows hardcoded "User" / "user@company.com" — no user context from login
- ⚠️ No error boundaries — single component error crashes entire page
- ⚠️ Zero tests (vitest + Playwright configured but no test files)
- ⚠️ No accessibility (no aria labels, no focus traps, no color contrast verification)

## Running
```bash
npm install
npm run dev    # http://localhost:3000
npm run build  # Production build (standalone output)
```

## Environment Variables (build-time)
```
NEXT_PUBLIC_API_URL=/api/v1      # API base URL (inlined at build time)
NEXT_PUBLIC_WS_URL=/ws           # WebSocket URL (inlined at build time)
```
