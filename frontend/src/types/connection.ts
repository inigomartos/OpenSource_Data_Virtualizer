export interface Connection {
  id: string;
  name: string;
  type: 'postgresql' | 'mysql' | 'sqlite' | 'csv' | 'excel';
  host?: string;
  port?: number;
  database_name?: string;
  is_active: boolean;
  last_synced_at?: string;
}
