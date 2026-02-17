'use client';

import { formatCurrency, formatNumber } from '@/lib/utils';

interface Props {
  data: Record<string, any>[];
  valueKey: string;
  title: string;
  format?: string;
}

export default function KPICard({ data, valueKey, title, format }: Props) {
  const value = data[0]?.[valueKey] ?? 0;

  const formatted =
    format === 'currency'
      ? formatCurrency(Number(value))
      : format === 'percent'
      ? `${Number(value).toFixed(1)}%`
      : formatNumber(Number(value));

  return (
    <div className="bg-bg-surface border border-border-default rounded-xl p-6 text-center">
      <p className="text-sm text-text-muted mb-1">{title}</p>
      <p className="text-4xl font-heading font-bold text-text-primary">{formatted}</p>
    </div>
  );
}
