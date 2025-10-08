"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AreaChart } from "@/components/ui/area-chart";
import { BarChart } from "@/components/ui/bar-chart";
import { DonutChart } from "@/components/ui/pie-chart";
import { ReactEChartsCore, echarts } from "@/components/ui/echarts-base";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  isDashboardDataPayload,
  type DashboardDataPayload,
  type DashboardMetrics,
} from "@/data/dashboard-data";
import { Dashboard } from "@/types/dashboard";
import { DashboardEditor } from "./DashboardEditor";
import { useDashboardContext } from "@/contexts/DashboardContext";
import { useAgUiAgent } from "../ag-ui/AgUiProvider";

// Re-use types and utilities from dynamic-dashboard page
type ChartBlueprint =
  | {
      kind: "area";
      id: string;
      title: string;
      description?: string;
      data: DashboardDataPayload["salesData"];
      indexKey: string;
      valueKeys: string[];
      formatter: (value: number) => string;
      spanClass: string;
      chartId: string;
      colors: string[];
    }
  | {
      kind: "bar";
      id: string;
      title: string;
      description?: string;
      data: Array<Record<string, unknown>>;
      indexKey: string;
      valueKeys: string[];
      formatter: (value: number) => string;
      spanClass: string;
      chartId: string;
      orientation: "horizontal" | "vertical";
      colors: string[];
      showLegend: boolean;
    }
  | {
      kind: "donut";
      id: string;
      title: string;
      description?: string;
      data: Array<Record<string, unknown>>;
      indexKey: string;
      valueKey: string;
      formatter: (value: number) => string;
      spanClass: string;
      chartId: string;
      colors: string[];
    };

interface DashboardViewEditProps {
  dashboard: Dashboard;
  mode: "view" | "edit";
  onSave: (config: any) => Promise<void>;
}

// Import utility functions from dynamic-dashboard
const CHART_ID_OVERRIDES: Record<string, string> = {
  salesData: "sales-overview",
  productData: "product-performance",
  categoryData: "sales-by-category",
  regionalData: "regional-sales",
  demographicsData: "customer-demographics",
};

const COLOR_PRESETS: Record<string, string[]> = {
  area: ["#3b82f6", "#10b981", "#ef4444"],
  productData: ["#8b5cf6", "#6366f1", "#4f46e5"],
  categoryData: ["#3b82f6", "#64748b", "#10b981", "#f59e0b", "#94a3b8"],
  regionalData: ["#059669", "#10b981", "#34d399", "#6ee7b7", "#a7f3d0"],
  demographicsData: ["#f97316", "#f59e0b", "#eab308", "#facc15", "#fde047"],
};

const DEFAULT_BAR_COLORS = ["#4f46e5", "#6366f1", "#818cf8"];
const DEFAULT_DONUT_COLORS = ["#0ea5e9", "#38bdf8", "#7dd3fc", "#bae6fd"];

function normaliseKeyToTitle(key: string): string {
  return key
    .replace(/Data$/, "")
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/\b([a-z])/g, (match) => match.toUpperCase())
    .trim();
}

function inferFormatter(field: string): (value: number) => string {
  const lower = field.toLowerCase();
  if (/(rate|percentage|share|margin|value)/.test(lower)) {
    return (value) => `${value.toFixed(Math.abs(value) < 1 ? 2 : 1)}%`;
  }
  if (/growth/.test(lower)) {
    return (value) => `${value.toFixed(1)}%`;
  }
  if (/(sales|revenue|profit|spending|expense|order)/.test(lower)) {
    return (value) => `$${value.toLocaleString()}`;
  }
  if (/customers|units/.test(lower)) {
    return (value) => value.toLocaleString();
  }
  return (value) => value.toLocaleString();
}

function prioritiseNumericKeys(keys: string[]): string[] {
  const priorities: Record<string, number> = {
    sales: 0, revenue: 1, profit: 2, expenses: 3, value: 4, spending: 5,
    marketshare: 6, percentage: 7, growth: 8, units: 9, customers: 10,
  };
  return [...keys].sort((a, b) => {
    const aScore = priorities[a.toLowerCase()] ?? 99;
    const bScore = priorities[b.toLowerCase()] ?? 99;
    return aScore - bScore;
  });
}

function chooseSpanClass(kind: ChartBlueprint["kind"]): string {
  if (kind === "area") {
    return "col-span-1 md:col-span-2 lg:col-span-4";
  }
  return "col-span-1 md:col-span-1 lg:col-span-2";
}

function getRuntimeBaseUrl(): string {
  const runtimeUrl = process.env.NEXT_PUBLIC_AG_UI_RUNTIME_URL ?? "http://localhost:8004/ag-ui/run";
  return runtimeUrl.replace(/\/run\/?$/, "");
}

function formatMetricValue(key: string, value: number | string): string {
  if (typeof value === "string") {
    return value;
  }
  const lower = key.toLowerCase();
  if (/(revenue|profit|spending|sales|expense|order)/.test(lower)) {
    return `$${value.toLocaleString()}`;
  }
  if (/(rate|margin|percentage)/.test(lower)) {
    return `${value}%`;
  }
  return value.toLocaleString();
}

function normaliseHeading(line: string): string {
  return line
    .trim()
    .replace(/^#+\s*/, "")
    .replace(/^[>*\-\s]+/, "")
    .replace(/[*_`]/g, "")
    .replace(/:$/, "")
    .trim()
    .toLowerCase();
}

type CommentarySection = {
  id: string;
  label: string;
  content: string;
};

function parseStrategicCommentary(markdown: string): CommentarySection[] {
  if (!markdown) return [];

  const sections: Record<string, string[]> = {
    risks: [], opportunities: [], recommendations: [], other: [],
  };

  let current: keyof typeof sections | null = null;

  markdown.split(/\r?\n/).forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed) {
      if (current) sections[current].push("");
      return;
    }

    const heading = normaliseHeading(trimmed);
    if (["risks", "risk"].includes(heading)) {
      current = "risks";
      return;
    }
    if (["opportunities", "opportunity"].includes(heading)) {
      current = "opportunities";
      return;
    }
    if (["recommendations", "recommendation"].includes(heading)) {
      current = "recommendations";
      return;
    }

    if (current) {
      sections[current].push(line);
    } else {
      sections.other.push(line);
    }
  });

  return [
    { id: "risks", label: "Risks", content: sections.risks.join("\n").trim() },
    { id: "opportunities", label: "Opportunities", content: sections.opportunities.join("\n").trim() },
    { id: "recommendations", label: "Recommendations", content: sections.recommendations.join("\n").trim() },
  ].filter((section) => section.content.length > 0);
}

export function DashboardViewEdit({ dashboard, mode, onSave }: DashboardViewEditProps) {
  const [currentConfig, setCurrentConfig] = useState(dashboard.layout_config);
  const [currentName, setCurrentName] = useState(dashboard.name);
  const [currentDescription, setCurrentDescription] = useState(dashboard.description || "");
  const [hasChanges, setHasChanges] = useState(false);
  const [saving, setSaving] = useState(false);

  // Sync local state with dashboard prop changes (e.g., from context updates)
  useEffect(() => {
    setCurrentConfig(dashboard.layout_config);
    setCurrentName(dashboard.name);
    setCurrentDescription(dashboard.description || "");
  }, [dashboard.layout_config, dashboard.name, dashboard.description]);

  // Use dashboard context for managing active section and save/reset handlers
  const { setOnSave, setOnReset, setOnNameChange, setOnDescriptionChange, setHasChanges: setContextHasChanges, setSaving: setContextSaving, setActiveSection, setSelectedItemId, activeSection } = useDashboardContext();
  const { sendDirectUIUpdate } = useAgUiAgent();

  // Set default active section when entering edit mode (only if no section is already active)
  useEffect(() => {
    if (mode === "edit") {
      // Only set default if no section is currently active
      if (!activeSection) {
        setActiveSection("dashboard-preview"); // Default to showing Add Items and Dashboard Settings
      }
    } else {
      setActiveSection(null); // Clear active section in view mode
      setSelectedItemId(null); // Clear selected item in view mode
    }
  }, [mode, setActiveSection, setSelectedItemId, activeSection]);

  // Sync local state with context for Data Assistant panel
  useEffect(() => {
    setContextHasChanges(hasChanges);
  }, [hasChanges, setContextHasChanges]);

  useEffect(() => {
    setContextSaving(saving);
  }, [saving, setContextSaving]);

  // Define save and reset handlers
  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      await onSave({
        name: currentName,
        description: currentDescription,
        layout_config: currentConfig,
        metadata: dashboard.metadata,
      });
      setHasChanges(false);
    } catch (error) {
      console.error("Save failed:", error);
    } finally {
      setSaving(false);
    }
  }, [onSave, currentName, currentDescription, currentConfig, dashboard.metadata]);

  const handleReset = useCallback(() => {
    setCurrentConfig(dashboard.layout_config);
    setCurrentName(dashboard.name);
    setCurrentDescription(dashboard.description || "");
    setHasChanges(false);
  }, [dashboard.layout_config, dashboard.name, dashboard.description]);

  const handleNameChange = useCallback((newName: string) => {
    setCurrentName(newName);
    checkForChanges(newName, currentDescription, currentConfig);
  }, [currentDescription, currentConfig, dashboard.name, dashboard.description]);

  const handleDescriptionChange = useCallback((newDescription: string) => {
    setCurrentDescription(newDescription);
    checkForChanges(currentName, newDescription, currentConfig);
  }, [currentName, currentConfig, dashboard.name, dashboard.description]);

  const checkForChanges = useCallback((name: string, description: string, config: any) => {
    const nameChanged = name !== dashboard.name;
    const descriptionChanged = description !== (dashboard.description || "");
    const configChanged = JSON.stringify(config) !== JSON.stringify(dashboard.layout_config);
    setHasChanges(nameChanged || descriptionChanged || configChanged);
  }, [dashboard.name, dashboard.description, dashboard.layout_config]);

  const handleConfigChange = useCallback((newConfig: any) => {
    setCurrentConfig(newConfig);
    checkForChanges(currentName, currentDescription, newConfig);

    if (mode === "edit") {
      setSaving(true);
      (async () => {
        try {
          await onSave({
            name: currentName,
            description: currentDescription,
            layout_config: newConfig,
            metadata: dashboard.metadata,
          });
          setHasChanges(false);
        } catch (error) {
          console.error("Auto-save layout failed:", error);
          setHasChanges(true);
        } finally {
          setSaving(false);
        }
      })();
    }
  }, [currentName, currentDescription, checkForChanges, mode, onSave, dashboard.metadata]);

  // Handle dashboard item clicks in edit mode
  const handleItemClick = useCallback((itemId: string, itemTitle: string, event?: React.MouseEvent) => {
    console.log('🔍 handleItemClick called:', { itemId, itemTitle, mode, hasSendDirectUIUpdate: !!sendDirectUIUpdate });

    if (mode === "edit") {
      // Prevent event bubbling to dashboard wrapper
      event?.stopPropagation();

      console.log('🔵 Sending DirectUIUpdate for item properties:', itemId);
      // Use DirectUIUpdate message over AgUI protocol for immediate UI navigation (No LLM)
      sendDirectUIUpdate(`Show item properties for "${itemTitle}" (${itemId}) in Data Assistant panel`);

      console.log(`✅ Dashboard item clicked: ${itemTitle} (${itemId}) - Data Assistant showing item properties`);
    } else {
      console.log('⚠️ Item click ignored - not in edit mode. Current mode:', mode);
    }
  }, [mode, sendDirectUIUpdate]);

  // Set up save and reset handlers in context
  useEffect(() => {
    setOnSave(handleSave);
    setOnReset(handleReset);
  }, [setOnSave, setOnReset, handleSave, handleReset]);

  // Set up name and description change handlers in context
  useEffect(() => {
    setOnNameChange(handleNameChange);
    setOnDescriptionChange(handleDescriptionChange);
  }, [setOnNameChange, setOnDescriptionChange, handleNameChange, handleDescriptionChange]);

  // Dashboard data state (similar to dynamic-dashboard page)
  const baseUrl = useMemo(() => getRuntimeBaseUrl(), []);
  const dashboardEndpoint = useMemo(() => `${baseUrl}/dashboard-data`, [baseUrl]);
  const commentaryEndpoint = useMemo(() => `${baseUrl}/action/generateStrategicCommentary`, [baseUrl]);

  const [data, setData] = useState<DashboardDataPayload | null>(null);
  const [dataLoading, setDataLoading] = useState(true);
  const [dataError, setDataError] = useState<string | null>(null);

  const [commentary, setCommentary] = useState("");
  const [commentaryLoading, setCommentaryLoading] = useState(false);
  const [commentaryError, setCommentaryError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string | undefined>(undefined);

  // Load dashboard data (reuse logic from dynamic-dashboard)
  useEffect(() => {
    let cancelled = false;
    let source: EventSource | null = null;

    const close = () => {
      if (source) {
        source.close();
        source = null;
      }
    };

    const hydrate = () => {
      setDataLoading(true);
      setDataError(null);
      setData(null);
      try {
        source = new EventSource(dashboardEndpoint, { withCredentials: true });
      } catch (error) {
        if (!cancelled) {
          setDataError("Unable to initialise dashboard data stream.");
          setDataLoading(false);
        }
        return;
      }

      source.onmessage = (event) => {
        if (cancelled) return;
        try {
          const parsed = JSON.parse(event.data);
          if (isDashboardDataPayload(parsed)) {
            setData(parsed);
            setDataError(null);
          } else {
            throw new Error("Invalid payload");
          }
        } catch (error) {
          setDataError("Received malformed dashboard payload.");
        } finally {
          setDataLoading(false);
          close();
        }
      };

      source.onerror = () => {
        if (!cancelled) {
          setDataError("Unable to load dashboard data.");
          setDataLoading(false);
        }
        close();
      };
    };

    hydrate();
    return () => {
      cancelled = true;
      close();
    };
  }, [dashboardEndpoint]);

  // Load commentary
  useEffect(() => {
    let cancelled = false;

    const fetchCommentary = async () => {
      setCommentaryLoading(true);
      setCommentaryError(null);
      try {
        const response = await fetch(commentaryEndpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          cache: "no-store",
          body: JSON.stringify({}),
        });
        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }
        const body = (await response.json()) as { commentary?: string };
        if (!cancelled) {
          setCommentary(body.commentary?.trim() ?? "");
        }
      } catch (error) {
        if (!cancelled) {
          setCommentaryError("Unable to load strategic commentary.");
        }
      } finally {
        if (!cancelled) {
          setCommentaryLoading(false);
        }
      }
    };

    fetchCommentary();
    return () => {
      cancelled = true;
    };
  }, [commentaryEndpoint]);

  // Move all useMemo hooks before the early return to maintain consistent hook order
  const chartBlueprints = useMemo(() => {
    if (!data) return [];
    // Use existing chart blueprint logic
    const entries: Array<[keyof DashboardDataPayload, unknown]> = Object.entries(data) as Array<
      [keyof DashboardDataPayload, unknown]
    >;
    const charts: ChartBlueprint[] = [];
    for (const [key, value] of entries) {
      if (Array.isArray(value)) {
        // Reuse chart inference logic from dynamic-dashboard
        const blueprint = inferChartBlueprint(key as string, value as Array<Record<string, unknown>>);
        if (blueprint) {
          charts.push(blueprint);
        }
      }
    }
    return charts;
  }, [data]);

  const metrics = useMemo(() => {
    if (!data?.metrics) return [];
    const entries = Object.entries(data.metrics as DashboardMetrics);
    return entries.map(([key, value]) => ({
      label: normaliseKeyToTitle(key),
      value: formatMetricValue(key, value),
    }));
  }, [data]);

  const commentarySections = useMemo(() => parseStrategicCommentary(commentary), [commentary]);

  // Get configured dashboard items - use currentConfig to reflect any changes
  const dashboardItems = useMemo(() => {
    const items = currentConfig?.items || [];
    // Sort items by their grid position (row first, then column) for proper rendering order
    return items.sort((a, b) => {
      const rowA = a.position?.row || 0;
      const rowB = b.position?.row || 0;
      if (rowA !== rowB) {
        return rowA - rowB;
      }
      const colA = a.position?.col || 0;
      const colB = b.position?.col || 0;
      return colA - colB;
    });
  }, [currentConfig]);

  const hasDashboardItems = dashboardItems.length > 0;

  // Generate layout class for view mode - uses CSS Grid without visible grid lines
  const getViewLayoutClass = (cols: number) => {
    const colsMap: Record<number, string> = {
      2: "grid-cols-1 md:grid-cols-2",
      3: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
      4: "grid-cols-1 md:grid-cols-2 lg:grid-cols-4",
      6: "grid-cols-2 md:grid-cols-3 lg:grid-cols-6",
    };
    return `grid w-full gap-4 ${colsMap[cols] || "grid-cols-1 md:grid-cols-2 lg:grid-cols-4"}`;
  };

  // Helper function to convert item position to CSS Grid positioning for view mode
  const getItemGridStyle = (item: any, cols: number) => {
    if (!item.position || (!item.position.row && !item.position.col)) {
      // If no position data, let CSS Grid auto-place the item
      return {};
    }

    // Parse span to get width from the drag-and-drop resizing
    const spanMatch = item.span?.match(/col-span-(\d+)/);
    const width = spanMatch ? parseInt(spanMatch[1]) : 1;

    // Calculate grid position (convert from 0-based position to 1-based CSS Grid)
    const startCol = Math.max(1, Math.min((item.position.col || 0) + 1, cols));
    const endCol = Math.max(2, Math.min(startCol + width, cols + 1));
    const startRow = Math.max(1, (item.position.row || 1));

    return {
      gridColumnStart: startCol,
      gridColumnEnd: endCol,
      gridRowStart: startRow,
      gridRowEnd: startRow + 1, // Single row height for now
    };
  };

  if (mode === "edit") {
    return (
      <div className="space-y-4">


        <div
          className="cursor-pointer hover:shadow-md transition-shadow rounded-lg"
          onClick={() => {
            // Direct context update - no LLM involved
            setActiveSection("dashboard-preview");
          }}
        >
          <DashboardEditor
            config={currentConfig}
            onChange={handleConfigChange}
            data={data}
            dataLoading={dataLoading}
          />
        </div>
      </div>
    );
  }

  // View mode - render the configured dashboard items
  if (!hasDashboardItems) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Card>
          <CardContent className="py-8 text-center">
            <h3 className="text-lg font-semibold">No Dashboard Items</h3>
            <p className="mt-2 text-muted-foreground">
              This dashboard is empty. Switch to edit mode to add visualizations and components.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const gridCols = currentConfig?.grid?.cols || 4;
  const layoutClass = getViewLayoutClass(gridCols);

  return (
    <div className={layoutClass}>
      {dashboardItems.map((item) => {
        const itemStyle = getItemGridStyle(item, gridCols);
        // Use explicit grid positioning if available, otherwise fall back to span classes
        const hasPosition = item.position && (item.position.row || item.position.col);
        const itemClassName = hasPosition ? "" : item.span;
        // Handle metric items (including Base Layout metrics)
        if (item.type === "metric") {
          if (item.config?.type === "metrics") {
            // Base Layout metrics - render the dynamic metrics
            return (
              <div key={item.id} className={itemClassName} style={itemStyle}>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
                  {metrics.length === 0 && dataLoading ? (
                    Array.from({ length: 6 }).map((_, index) => (
                      <Card key={`metric-skeleton-${index}`} className="gap-2 py-4">
                        <CardHeader className="px-4 py-0">
                          <div className="h-2.5 w-16 animate-pulse rounded bg-muted" />
                        </CardHeader>
                        <CardContent className="px-4 py-0">
                          <div className="h-4 w-20 animate-pulse rounded bg-muted" />
                        </CardContent>
                      </Card>
                    ))
                  ) : (
                    metrics.map((metric) => (
                      <Card key={metric.label} className="gap-2 py-4">
                        <CardHeader className="px-4 py-0">
                          <CardDescription className="text-xs text-muted-foreground">
                            {metric.label}
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="px-4 py-0">
                          <CardTitle className="text-xl text-card-foreground">{metric.value}</CardTitle>
                        </CardContent>
                      </Card>
                    ))
                  )}
                </div>
              </div>
            );
          } else {
            // Custom metric item
            return (
              <Card
                key={item.id}
                className={`${itemClassName} ${mode === "edit" ? "cursor-pointer hover:shadow-md transition-shadow" : ""}`}
                style={itemStyle}
                onClick={(e) => handleItemClick(item.id, item.title, e)}
              >
                <CardHeader className="pb-1 pt-3">
                  <CardTitle className="text-base font-medium">{item.title}</CardTitle>
                  {item.description && (
                    <CardDescription className="text-xs">{item.description}</CardDescription>
                  )}
                </CardHeader>
                <CardContent className="p-3">
                  <div className="text-2xl font-bold">
                    {item.config?.value || "No Data"}
                  </div>
                </CardContent>
              </Card>
            );
          }
        }

        // Handle chart items
        if (item.type === "chart") {
          // LIDA chart with embedded ECharts config
          if (item.config?.echarts_config) {
            const echartsOption = parseEchartsOption(
              item.config.echarts_config,
              (item.config as Record<string, unknown>)?.["echar_code"],
            );
            return (
              <Card
                key={item.id}
                className={`${itemClassName} ${mode === "edit" ? "cursor-pointer hover:shadow-md transition-shadow" : ""}`}
                style={itemStyle}
                data-chart-id={item.id}
                onClick={(e) => handleItemClick(item.id, item.title, e)}
              >
                <CardHeader className="pb-1 pt-3">
                  <CardTitle className="text-base font-medium">{item.title}</CardTitle>
                  {item.description && (
                    <CardDescription className="text-xs">{item.description}</CardDescription>
                  )}
                </CardHeader>
                <CardContent className="p-3">
                  <div className="h-60">
                    <ReactEChartsCore
                      echarts={echarts}
                      option={echartsOption ?? {}}
                      style={{ width: '100%', height: '100%' }}
                      notMerge={true}
                      lazyUpdate={true}
                    />
                  </div>
                </CardContent>
              </Card>
            );
          }
          // Base Layout chart with data source reference
          else if (item.config?.data_source) {
            const chart = chartBlueprints.find(c => c.id === item.config.data_source);
            if (chart) {
              if (chart.kind === "area") {
                return (
                  <Card
                    key={item.id}
                    className={`${itemClassName} ${mode === "edit" ? "cursor-pointer hover:shadow-md transition-shadow" : ""}`}
                    style={itemStyle}
                    data-chart-id={chart.chartId}
                    onClick={(e) => handleItemClick(item.id, item.title, e)}
                  >
                    <CardHeader className="pb-1 pt-3">
                      <CardTitle className="text-base font-medium">{item.title}</CardTitle>
                      {item.description && (
                        <CardDescription className="text-xs">{item.description}</CardDescription>
                      )}
                    </CardHeader>
                    <CardContent className="p-3">
                      <div className="h-60">
                        <AreaChart
                          data={chart.data}
                          index={chart.indexKey}
                          categories={chart.valueKeys}
                          chartId={chart.chartId}
                          colors={chart.colors}
                          valueFormatter={chart.formatter}
                          showLegend={true}
                          showGrid={true}
                          showXAxis={true}
                          showYAxis={true}
                        />
                      </div>
                    </CardContent>
                  </Card>
                );
              }
              if (chart.kind === "bar") {
                return (
                  <Card
                    key={item.id}
                    className={`${itemClassName} ${mode === "edit" ? "cursor-pointer hover:shadow-md transition-shadow" : ""}`}
                    style={itemStyle}
                    data-chart-id={chart.chartId}
                    onClick={(e) => handleItemClick(item.id, item.title, e)}
                  >
                    <CardHeader className="pb-1 pt-3">
                      <CardTitle className="text-base font-medium">{item.title}</CardTitle>
                      {item.description && (
                        <CardDescription className="text-xs">{item.description}</CardDescription>
                      )}
                    </CardHeader>
                    <CardContent className="p-3">
                      <div className="h-60">
                        <BarChart
                          data={chart.data}
                          index={chart.indexKey}
                          categories={chart.valueKeys}
                          chartId={chart.chartId}
                          colors={chart.colors}
                          valueFormatter={chart.formatter}
                          showLegend={chart.showLegend}
                          showGrid={true}
                          layout={chart.orientation}
                        />
                      </div>
                    </CardContent>
                  </Card>
                );
              }
              if (chart.kind === "donut") {
                return (
                  <Card
                    key={item.id}
                    className={`${itemClassName} ${mode === "edit" ? "cursor-pointer hover:shadow-md transition-shadow" : ""}`}
                    style={itemStyle}
                    data-chart-id={chart.chartId}
                    onClick={(e) => handleItemClick(item.id, item.title, e)}
                  >
                    <CardHeader className="pb-1 pt-3">
                      <CardTitle className="text-base font-medium">{item.title}</CardTitle>
                      {item.description && (
                        <CardDescription className="text-xs">{item.description}</CardDescription>
                      )}
                    </CardHeader>
                    <CardContent className="p-3">
                      <div className="h-60">
                        <DonutChart
                          data={chart.data}
                          index={chart.indexKey}
                          category={chart.valueKey}
                          chartId={chart.chartId}
                          valueFormatter={chart.formatter}
                          colors={chart.colors}
                          centerText={item.title}
                          paddingAngle={0}
                          showLegend={true}
                          showLabel={false}
                          innerRadius={45}
                          outerRadius="85%"
                        />
                      </div>
                    </CardContent>
                  </Card>
                );
              }
            }
            // Fallback if data source not found
            return (
              <Card
                key={item.id}
                className={`${itemClassName} ${mode === "edit" ? "cursor-pointer hover:shadow-md transition-shadow" : ""}`}
                style={itemStyle}
                onClick={(e) => handleItemClick(item.id, item.title, e)}
              >
                <CardHeader className="pb-1 pt-3">
                  <CardTitle className="text-base font-medium">{item.title}</CardTitle>
                  {item.description && (
                    <CardDescription className="text-xs">{item.description}</CardDescription>
                  )}
                </CardHeader>
                <CardContent className="p-3">
                  <div className="flex h-60 items-center justify-center text-muted-foreground">
                    {dataLoading ? "Loading chart data..." : "Chart data not available"}
                  </div>
                </CardContent>
              </Card>
            );
          }
        }

        // Handle commentary items
        if (item.type === "commentary") {
          if (item.config?.type === "ai_commentary") {
            // Base Layout commentary - render the AI commentary
            return (
              <Card
                key={item.id}
                className={`${itemClassName} ${mode === "edit" ? "cursor-pointer hover:shadow-md transition-shadow" : ""}`}
                style={itemStyle}
                data-chart-id="strategic-commentary"
                onClick={(e) => handleItemClick(item.id, item.title, e)}
              >
                <CardHeader className="pb-1 pt-3">
                  <CardTitle className="text-base font-medium">{item.title}</CardTitle>
                  {item.description && (
                    <CardDescription className="text-xs">{item.description}</CardDescription>
                  )}
                </CardHeader>
                <CardContent className="p-3">
                  <div className="min-h-[8rem]">
                    {commentaryLoading ? (
                      <div className="space-y-2">
                        <div className="h-3 w-3/4 animate-pulse rounded bg-muted" />
                        <div className="h-3 w-5/6 animate-pulse rounded bg-muted" />
                        <div className="h-3 w-2/3 animate-pulse rounded bg-muted" />
                      </div>
                    ) : commentaryError ? (
                      <p className="text-sm text-destructive">{commentaryError}</p>
                    ) : commentarySections.length > 0 ? (
                      <Tabs value={activeTab ?? commentarySections[0]?.id} onValueChange={setActiveTab} className="w-full">
                        <TabsList className="grid w-full grid-cols-1 gap-2 sm:grid-cols-3">
                          {commentarySections.map((section) => (
                            <TabsTrigger key={section.id} value={section.id}>
                              {section.label}
                            </TabsTrigger>
                          ))}
                        </TabsList>
                        {commentarySections.map((section) => (
                          <TabsContent key={section.id} value={section.id}>
                            <div className="prose prose-sm text-muted-foreground dark:prose-invert">
                              <ReactMarkdown remarkPlugins={[remarkGfm]}>{section.content}</ReactMarkdown>
                            </div>
                          </TabsContent>
                        ))}
                      </Tabs>
                    ) : commentary ? (
                      <div className="prose prose-sm text-muted-foreground dark:prose-invert">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{commentary}</ReactMarkdown>
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">Strategic commentary is not available yet.</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          } else {
            // Custom commentary item
            return (
              <Card
                key={item.id}
                className={`${itemClassName} ${mode === "edit" ? "cursor-pointer hover:shadow-md transition-shadow" : ""}`}
                style={itemStyle}
                onClick={(e) => handleItemClick(item.id, item.title, e)}
              >
                <CardHeader className="pb-1 pt-3">
                  <CardTitle className="text-base font-medium">{item.title}</CardTitle>
                  {item.description && (
                    <CardDescription className="text-xs">{item.description}</CardDescription>
                  )}
                </CardHeader>
                <CardContent className="p-3">
                  <div className="prose prose-sm text-muted-foreground dark:prose-invert">
                    {item.config?.insights ? (
                      <ul>
                        {item.config.insights.map((insight: string, index: number) => (
                          <li key={index}>{insight}</li>
                        ))}
                      </ul>
                    ) : (
                      <p>No insights available</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          }
        }

        // Handle text items
        if (item.type === "text") {
          return (
            <Card
              key={item.id}
              className={`${itemClassName} ${mode === "edit" ? "cursor-pointer hover:shadow-md transition-shadow" : ""}`}
              style={itemStyle}
              onClick={() => handleItemClick(item.id, item.title)}
            >
              <CardHeader className="pb-1 pt-3">
                <CardTitle className="text-base font-medium">{item.title}</CardTitle>
                {item.description && (
                  <CardDescription className="text-xs">{item.description}</CardDescription>
                )}
              </CardHeader>
              <CardContent className="p-3">
                <div className="prose prose-sm dark:prose-invert">
                  {item.config?.content || "No content"}
                </div>
              </CardContent>
            </Card>
          );
        }

        // Default fallback for unknown item types
        return (
          <Card
            key={item.id}
            className={`${itemClassName} ${mode === "edit" ? "cursor-pointer hover:shadow-md transition-shadow" : ""}`}
            style={itemStyle}
            onClick={() => handleItemClick(item.id, item.title)}
          >
            <CardHeader className="pb-1 pt-3">
              <CardTitle className="text-base font-medium">{item.title}</CardTitle>
              {item.description && (
                <CardDescription className="text-xs">{item.description}</CardDescription>
              )}
            </CardHeader>
            <CardContent className="p-3">
              <div className="flex h-32 items-center justify-center text-muted-foreground">
                Unknown item type: {item.type}
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

// Utility function for chart blueprint inference (reused from dynamic-dashboard)
function inferChartBlueprint(key: string, records: Array<Record<string, unknown>>): ChartBlueprint | null {
  if (!records || records.length === 0) return null;

  const chartId = CHART_ID_OVERRIDES[key] ?? key.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
  const title = (() => {
    switch (key) {
      case "salesData": return "Sales Overview";
      case "productData": return "Product Performance";
      case "categoryData": return "Sales by Category";
      case "regionalData": return "Regional Sales";
      case "demographicsData": return "Customer Demographics";
      default: return normaliseKeyToTitle(key);
    }
  })();
  const defaultDescription = "Auto-generated view based on dashboard dataset.";

  const first = records[0];
  const stringKeys = Object.keys(first).filter((field) => typeof first[field as keyof typeof first] === "string");
  const numericKeys = Object.keys(first).filter((field) => typeof first[field as keyof typeof first] === "number");

  if ("date" in first) {
    const sortedNumeric = prioritiseNumericKeys(numericKeys);
    const formatter = inferFormatter(sortedNumeric[0] ?? "value");
    const colors = COLOR_PRESETS.area;
    return {
      kind: "area",
      id: key,
      title,
      description: "Monthly performance across revenue, profit, and expense lines.",
      data: records as DashboardDataPayload["salesData"],
      indexKey: "date",
      valueKeys: sortedNumeric,
      formatter,
      spanClass: chooseSpanClass("area"),
      chartId,
      colors,
    };
  }

  const [categoryKey] = stringKeys;
  const sortedNumeric = prioritiseNumericKeys(numericKeys);
  if (!categoryKey || sortedNumeric.length === 0) return null;

  const primaryKey = sortedNumeric[0];
  if (!primaryKey) return null;

  const values = records
    .map((entry) => (typeof entry[primaryKey] === "number" ? (entry[primaryKey] as number) : 0))
    .filter((value) => Number.isFinite(value))
    .map((value) => Math.abs(value));
  const total = values.reduce((acc, value) => acc + value, 0);
  const primaryKeyLower = primaryKey.toLowerCase();
  const looksLikeShare =
    primaryKeyLower.includes("share") ||
    primaryKeyLower.includes("percentage") ||
    primaryKeyLower.includes("value");
  const shouldUseDonut = looksLikeShare || (total > 0 && total <= 105 && values.length >= 3);

  if (shouldUseDonut) {
    const baseColors = COLOR_PRESETS[key] ?? DEFAULT_DONUT_COLORS;
    return {
      kind: "donut",
      id: key,
      title,
      description: "Proportional contribution by segment.",
      data: records,
      indexKey: categoryKey,
      valueKey: primaryKey,
      formatter: inferFormatter(primaryKey),
      spanClass: chooseSpanClass("bar"),
      chartId,
      colors: baseColors,
    };
  }

  const baseColors = COLOR_PRESETS[key] ?? DEFAULT_BAR_COLORS;
  const formatter = inferFormatter(primaryKey);
  return {
    kind: "bar",
    id: key,
    title,
    description: defaultDescription,
    data: records,
    indexKey: categoryKey,
    valueKeys: sortedNumeric,
    formatter,
    spanClass: chooseSpanClass("bar"),
    chartId,
    orientation: "horizontal",
    colors: baseColors,
    showLegend: sortedNumeric.length > 1,
  };
}
const parseEchartsOption = (rawOption: unknown, fallback?: unknown): Record<string, unknown> | undefined => {
  const tryParse = (source: unknown): Record<string, unknown> | undefined => {
    if (!source) return undefined;
    if (typeof source === "string") {
      try {
        const parsed = JSON.parse(source);
        return parsed && typeof parsed === "object" ? (parsed as Record<string, unknown>) : undefined;
      } catch {
        return undefined;
      }
    }
    if (typeof source === "object") {
      return source as Record<string, unknown>;
    }
    return undefined;
  };

  return tryParse(rawOption) ?? tryParse(fallback);
};
