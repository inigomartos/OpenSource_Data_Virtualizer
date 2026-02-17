'use client';

import type { ChartConfig, QueryResult } from '@/types/chat';
import BarChartComponent from './bar-chart';
import LineChartComponent from './line-chart';
import PieChartComponent from './pie-chart';
import AreaChartComponent from './area-chart';
import KPICard from './kpi-card';
import DataTable from './data-table';

interface Props {
  config: ChartConfig;
  data: QueryResult;
}

export default function ChartRenderer({ config, data }: Props) {
  if (!data || !data.columns || data.rows.length === 0) {
    return (
      <div className="p-4 text-center text-text-muted text-sm">
        No data to display
      </div>
    );
  }

  const chartData = data.rows.map((row) => {
    const obj: Record<string, any> = {};
    data.columns.forEach((col, i) => {
      obj[col] = row[i];
    });
    return obj;
  });

  switch (config.chart_type) {
    case 'bar':
    case 'horizontal_bar':
      return (
        <BarChartComponent
          data={chartData}
          xKey={config.x_column || data.columns[0]}
          yKey={config.y_column || data.columns[1]}
          title={config.title}
          horizontal={config.chart_type === 'horizontal_bar'}
        />
      );
    case 'line':
      return (
        <LineChartComponent
          data={chartData}
          xKey={config.x_column || data.columns[0]}
          yKey={config.y_column || data.columns[1]}
          title={config.title}
        />
      );
    case 'area':
      return (
        <AreaChartComponent
          data={chartData}
          xKey={config.x_column || data.columns[0]}
          yKey={config.y_column || data.columns[1]}
          title={config.title}
        />
      );
    case 'pie':
      return (
        <PieChartComponent
          data={chartData}
          nameKey={config.x_column || data.columns[0]}
          valueKey={config.y_column || data.columns[1]}
          title={config.title}
        />
      );
    case 'kpi':
      return (
        <KPICard
          data={chartData}
          valueKey={config.value_column || data.columns[0]}
          title={config.title}
          format={config.format}
        />
      );
    case 'table':
    default:
      return (
        <DataTable
          columns={data.columns}
          rows={data.rows}
          title={config.title}
        />
      );
  }
}
