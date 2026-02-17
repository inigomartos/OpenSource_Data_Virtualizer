export interface Dashboard {
  id: string;
  title: string;
  description?: string;
  is_shared: boolean;
  layout_config: any[];
  created_at: string;
}

export interface Widget {
  id: string;
  title: string;
  widget_type: 'chart' | 'table' | 'kpi' | 'text';
  chart_config: any;
  position: { x: number; y: number; w: number; h: number };
  last_error?: string;
}
