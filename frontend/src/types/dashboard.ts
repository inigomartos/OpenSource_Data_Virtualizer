export interface Dashboard {
  id: string;
  title: string;
  description?: string;
  is_shared: boolean;
  layout_config: any[];
  created_at: string;
  updated_at?: string;
  widget_count?: number;
}

export interface Widget {
  id: string;
  title: string;
  widget_type: 'chart' | 'table' | 'kpi' | 'text';
  chart_config: any;
  position: { x: number; y: number; w: number; h: number };
  last_error?: string;
}

export interface WidgetWithData extends Widget {
  query_result_preview?: {
    columns: string[];
    rows: any[][];
    row_count: number;
  };
  connection_id?: string;
  query_sql?: string;
  refresh_interval_seconds?: number;
  last_refreshed_at?: string;
}

export interface DashboardWithWidgets extends Dashboard {
  widgets: WidgetWithData[];
  created_by_id?: string;
}

export interface CreateDashboardPayload {
  title: string;
  description?: string;
}

export interface UpdateDashboardPayload {
  title?: string;
  description?: string;
  is_shared?: boolean;
  layout_config?: any[];
}

export interface CreateWidgetPayload {
  title: string;
  widget_type: 'chart' | 'table' | 'kpi' | 'text';
  chart_config: any;
  position: { x: number; y: number; w: number; h: number };
  connection_id?: string;
  query_sql?: string;
  refresh_interval_seconds?: number;
}

export interface UpdateWidgetPayload {
  title?: string;
  widget_type?: 'chart' | 'table' | 'kpi' | 'text';
  chart_config?: any;
  position?: { x: number; y: number; w: number; h: number };
  connection_id?: string;
  query_sql?: string;
  refresh_interval_seconds?: number;
}
