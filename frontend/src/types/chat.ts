export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  generated_sql?: string;
  query_result_preview?: QueryResult;
  full_result_row_count?: number;
  chart_config?: ChartConfig;
  execution_time_ms?: number;
  error_message?: string;
  created_at: string;
}

export interface QueryResult {
  columns: string[];
  rows: any[][];
  row_count: number;
  truncated?: boolean;
}

export interface ChartConfig {
  chart_type: 'bar' | 'horizontal_bar' | 'line' | 'area' | 'pie' | 'scatter' | 'kpi' | 'table';
  x_column?: string;
  y_column?: string;
  title: string;
  color_column?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  value_column?: string;
  format?: string;
  highlight_columns?: string[];
}

export interface ChatSession {
  id: string;
  title?: string;
  connection_id?: string;
  is_pinned: boolean;
  created_at: string;
}
