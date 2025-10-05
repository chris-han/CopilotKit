// Unified Dashboard interfaces and utilities

export interface DashboardItem {
  id: string;
  type: "chart" | "metric" | "text" | "commentary";
  chartType?: "area" | "bar" | "donut";
  title: string;
  description?: string;
  span: string;
  position: { row: number; col?: number };
  config?: any;
}

export interface DashboardConfig {
  grid: { cols: number; rows: string };
  items: DashboardItem[];
}

export interface Dashboard {
  id: string;
  name: string;
  description?: string;
  layout_config?: DashboardConfig;
  metadata?: any;
  is_public?: boolean;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

// Helper function to get item count consistently
export function getDashboardItemCount(dashboard: Dashboard): number {
  return dashboard.layout_config?.items?.length || 0;
}

// Helper function to get item label based on count
export function getDashboardItemLabel(dashboard: Dashboard): string {
  const count = getDashboardItemCount(dashboard);
  return count !== 1 ? "items" : "item";
}