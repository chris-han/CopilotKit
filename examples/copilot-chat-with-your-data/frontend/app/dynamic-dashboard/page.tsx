"use client";

import { useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { AreaChart } from "../../components/ui/area-chart";
import { BarChart } from "../../components/ui/bar-chart";
import { DonutChart } from "../../components/ui/pie-chart";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import {
  STRATEGIC_COMMENTARY_TAB_EVENT,
  type StrategicCommentaryTabEventDetail,
} from "../../lib/chart-highlighting";
import {
  isDashboardDataPayload,
  type DashboardDataPayload,
  type DashboardMetrics,
} from "../../data/dashboard-data";

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
    sales: 0,
    revenue: 1,
    profit: 2,
    expenses: 3,
    value: 4,
    spending: 5,
    marketshare: 6,
    percentage: 7,
    growth: 8,
    units: 9,
    customers: 10,
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

function inferChartBlueprint(key: string, records: Array<Record<string, unknown>>): ChartBlueprint | null {
  if (!records || records.length === 0) {
    return null;
  }

  const chartId = CHART_ID_OVERRIDES[key] ?? key.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
  const title = (() => {
    switch (key) {
      case "salesData":
        return "Sales Overview";
      case "productData":
        return "Product Performance";
      case "categoryData":
        return "Sales by Category";
      case "regionalData":
        return "Regional Sales";
      case "demographicsData":
        return "Customer Demographics";
      default:
        return normaliseKeyToTitle(key);
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
  if (!categoryKey || sortedNumeric.length === 0) {
    return null;
  }

  const primaryKey = sortedNumeric[0];
  if (!primaryKey) {
    return null;
  }

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

function deriveChartBlueprints(data: DashboardDataPayload): ChartBlueprint[] {
  const entries: Array<[keyof DashboardDataPayload, unknown]> = Object.entries(data) as Array<
    [keyof DashboardDataPayload, unknown]
  >;
  const charts: ChartBlueprint[] = [];
  for (const [key, value] of entries) {
    if (Array.isArray(value)) {
      const blueprint = inferChartBlueprint(key as string, value as Array<Record<string, unknown>>);
      if (blueprint) {
        charts.push(blueprint);
      }
    }
  }
  return charts;
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
  if (!markdown) {
    return [];
  }

  const sections: Record<string, string[]> = {
    risks: [],
    opportunities: [],
    recommendations: [],
    other: [],
  };

  let current: keyof typeof sections | null = null;

  markdown.split(/\r?\n/).forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed) {
      if (current) {
        sections[current].push("");
      }
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
    {
      id: "recommendations",
      label: "Recommendations",
      content: sections.recommendations.join("\n").trim(),
    },
  ].filter((section) => section.content.length > 0);
}

function getRuntimeBaseUrl(): string {
  const runtimeUrl = process.env.NEXT_PUBLIC_AG_UI_RUNTIME_URL ?? "http://localhost:8004/ag-ui/run";
  return runtimeUrl.replace(/\/run\/?$/, "");
}

export default function DynamicDashboardPage() {
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
        if (cancelled) {
          return;
        }
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

  const chartBlueprints = useMemo(() => (data ? deriveChartBlueprints(data) : []), [data]);

  const metrics = useMemo(() => {
    if (!data?.metrics) {
      return [];
    }
    const entries = Object.entries(data.metrics as DashboardMetrics);
    return entries.map(([key, value]) => ({
      label: normaliseKeyToTitle(key),
      value: formatMetricValue(key, value),
    }));
  }, [data]);

  const commentarySections = useMemo(() => parseStrategicCommentary(commentary), [commentary]);

  useEffect(() => {
    if (!commentarySections.length) {
      setActiveTab(undefined);
      return;
    }
    setActiveTab((previous) => {
      if (previous && commentarySections.some((section) => section.id === previous)) {
        return previous;
      }
      return commentarySections[0]?.id;
    });
  }, [commentarySections]);

  useEffect(() => {
    const handler = (event: CustomEvent<StrategicCommentaryTabEventDetail>) => {
      const tabId = event.detail?.tab;
      if (tabId && commentarySections.some((section) => section.id === tabId)) {
        setActiveTab(tabId);
      }
    };

    const wrapped = handler as EventListener;
    window.addEventListener(STRATEGIC_COMMENTARY_TAB_EVENT, wrapped);
    return () => window.removeEventListener(STRATEGIC_COMMENTARY_TAB_EVENT, wrapped);
  }, [commentarySections]);

  return (
    <div className="grid w-full grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      {dataError ? (
        <div className="col-span-1 md:col-span-2 lg:col-span-4">
          <div className="rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {dataError}
          </div>
        </div>
      ) : null}

      <div className="col-span-1 md:col-span-2 lg:col-span-4">
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

      {chartBlueprints.map((chart) => {
        if (chart.kind === "area") {
          return (
            <Card key={chart.id} className={chart.spanClass} data-chart-id={chart.chartId}>
              <CardHeader className="pb-1 pt-3">
                <CardTitle className="text-base font-medium">{chart.title}</CardTitle>
                {chart.description ? (
                  <CardDescription className="text-xs">{chart.description}</CardDescription>
                ) : null}
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
            <Card key={chart.id} className={chart.spanClass} data-chart-id={chart.chartId}>
              <CardHeader className="pb-1 pt-3">
                <CardTitle className="text-base font-medium">{chart.title}</CardTitle>
                {chart.description ? (
                  <CardDescription className="text-xs">{chart.description}</CardDescription>
                ) : null}
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

        return (
          <Card key={chart.id} className={chart.spanClass} data-chart-id={chart.chartId}>
            <CardHeader className="pb-1 pt-3">
              <CardTitle className="text-base font-medium">{chart.title}</CardTitle>
              {chart.description ? (
                <CardDescription className="text-xs">{chart.description}</CardDescription>
              ) : null}
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
                  centerText={chart.title}
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
      })}

      <Card className="col-span-1 md:col-span-2 lg:col-span-4" data-chart-id="strategic-commentary">
        <CardHeader className="pb-1 pt-3">
          <CardTitle className="text-base font-medium">Strategic Commentary</CardTitle>
          <CardDescription className="text-xs">
            AI-authored risks, opportunities, and recommendations
          </CardDescription>
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
    </div>
  );
}
