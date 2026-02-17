export const CHART_COLORS = {
  categorical: [
    '#6366F1', '#22D3EE', '#10B981', '#F59E0B', '#EF4444',
    '#8B5CF6', '#06B6D4', '#34D399', '#F97316', '#EC4899',
  ],
  sequential: ['#C7D2FE', '#A5B4FC', '#818CF8', '#6366F1', '#4F46E5'],
  diverging: ['#EF4444', '#F97316', '#EAB308', '#22C55E', '#10B981'],
  positive: '#10B981',
  negative: '#EF4444',
  neutral: '#94A3B8',
} as const;

export const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
