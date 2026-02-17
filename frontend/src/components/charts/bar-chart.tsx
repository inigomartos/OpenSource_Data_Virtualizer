'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { CHART_COLORS } from '@/lib/constants';

interface Props {
  data: Record<string, any>[];
  xKey: string;
  yKey: string;
  title: string;
  horizontal?: boolean;
}

export default function BarChartComponent({ data, xKey, yKey, title, horizontal }: Props) {
  return (
    <div className="bg-bg-surface border border-border-default rounded-xl p-4">
      <h3 className="text-sm font-medium text-text-primary mb-3">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        {horizontal ? (
          <BarChart data={data} layout="vertical" margin={{ left: 80 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-default)" />
            <XAxis type="number" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
            <YAxis dataKey={xKey} type="category" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} width={80} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--bg-elevated)',
                border: '1px solid var(--border-default)',
                borderRadius: '8px',
                color: 'var(--text-primary)',
              }}
            />
            <Bar dataKey={yKey} fill={CHART_COLORS.categorical[0]} radius={[0, 4, 4, 0]} />
          </BarChart>
        ) : (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-default)" />
            <XAxis dataKey={xKey} tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
            <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--bg-elevated)',
                border: '1px solid var(--border-default)',
                borderRadius: '8px',
                color: 'var(--text-primary)',
              }}
            />
            <Bar dataKey={yKey} fill={CHART_COLORS.categorical[0]} radius={[4, 4, 0, 0]} />
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
