export type ChartType = 'bar' | 'horizontal_bar' | 'line' | 'area' | 'pie' | 'scatter' | 'kpi' | 'table';

export interface ChartData {
  columns: string[];
  rows: any[][];
}
