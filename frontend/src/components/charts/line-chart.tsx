'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { CHART_COLORS } from '@/lib/constants';

interface Props {
  data: Record<string, any>[];
  xKey: string;
  yKey: string;
  title: string;
}

export default function LineChartComponent({ data, xKey, yKey, title }: Props) {
  return (
    <div className="bg-bg-surface border border-border-default rounded-xl p-4">
      <h3 className="text-sm font-medium text-text-primary mb-3">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
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
          <Line
            type="monotone"
            dataKey={yKey}
            stroke={CHART_COLORS.categorical[0]}
            strokeWidth={2}
            dot={{ fill: CHART_COLORS.categorical[0], r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
