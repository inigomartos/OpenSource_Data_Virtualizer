'use client';

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { CHART_COLORS } from '@/lib/constants';

interface Props {
  data: Record<string, any>[];
  nameKey: string;
  valueKey: string;
  title: string;
}

export default function PieChartComponent({ data, nameKey, valueKey, title }: Props) {
  return (
    <div className="bg-bg-surface border border-border-default rounded-xl p-4">
      <h3 className="text-sm font-medium text-text-primary mb-3">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            dataKey={valueKey}
            nameKey={nameKey}
            cx="50%"
            cy="50%"
            outerRadius={100}
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
          >
            {data.map((_, index) => (
              <Cell key={index} fill={CHART_COLORS.categorical[index % CHART_COLORS.categorical.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--bg-elevated)',
              border: '1px solid var(--border-default)',
              borderRadius: '8px',
              color: 'var(--text-primary)',
            }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
