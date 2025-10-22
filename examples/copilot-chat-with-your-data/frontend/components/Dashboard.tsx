"use client";

import { useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { AreaChart } from "./ui/area-chart";
import { BarChart } from "./ui/bar-chart";
import { DonutChart } from "./ui/pie-chart";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import {
  STRATEGIC_COMMENTARY_TAB_EVENT,
  type StrategicCommentaryTabEventDetail,
} from "../lib/chart-highlighting";
import { isDashboardDataPayload, type DashboardDataPayload } from "../data/dashboard-data";
import { useDashboardContext } from "../contexts/DashboardContext";

export function Dashboard() {
  const { setIsDynamicDashboard } = useDashboardContext();
  const [strategicCommentary, setStrategicCommentary] = useState<string>("");
  const [commentaryLoading, setCommentaryLoading] = useState<boolean>(false);
  const [commentaryError, setCommentaryError] = useState<string | null>(null);
  const [activeCommentaryTab, setActiveCommentaryTab] = useState<string | undefined>(undefined);

  const [dashboardData, setDashboardData] = useState<DashboardDataPayload | null>(null);
  const [dashboardLoading, setDashboardLoading] = useState<boolean>(true);
  const [dashboardError, setDashboardError] = useState<string | null>(null);

  const baseRuntimeUrl = useMemo(() => {
    const runtimeUrl = process.env.NEXT_PUBLIC_AG_UI_RUNTIME_URL ?? "http://localhost:8004/ag-ui/run";
    return runtimeUrl.replace(/\/run\/?$/, "");
  }, []);

  const strategicCommentaryEndpoint = useMemo(
    () => `${baseRuntimeUrl}/action/generateStrategicCommentary`,
    [baseRuntimeUrl],
  );

  const dashboardDataEndpoint = useMemo(
    () => `${baseRuntimeUrl}/dashboard-data`,
    [baseRuntimeUrl],
  );

  useEffect(() => {
    setIsDynamicDashboard(true);
    return () => setIsDynamicDashboard(false);
  }, [setIsDynamicDashboard]);

  useEffect(() => {
    let cancelled = false;
    let source: EventSource | null = null;

    const closeSource = () => {
      if (source) {
        source.close();
        source = null;
      }
    };

    const initialise = () => {
      setDashboardLoading(true);
      setDashboardError(null);
      setDashboardData(null);

      try {
        source = new EventSource(dashboardDataEndpoint, { withCredentials: true });
      } catch {
        if (!cancelled) {
          setDashboardError("Unable to load dashboard data.");
          setDashboardLoading(false);
        }
        return;
      }

      source.onmessage = (event) => {
        if (cancelled) {
          return;
        }

        try {
          const parsed = JSON.parse(event.data);
          if (!isDashboardDataPayload(parsed)) {
            throw new Error("Invalid dashboard payload");
          }
          setDashboardData(parsed);
          setDashboardError(null);
        } catch {
          setDashboardError("Received malformed dashboard data.");
        } finally {
          setDashboardLoading(false);
          closeSource();
        }
      };

      source.onerror = () => {
        if (cancelled) {
          return;
        }

        setDashboardError("Unable to load dashboard data.");
        setDashboardLoading(false);
        closeSource();
      };
    };

    initialise();

    return () => {
      cancelled = true;
      closeSource();
    };
  }, [dashboardDataEndpoint]);

  useEffect(() => {
    let cancelled = false;

    const fetchCommentary = async () => {
      setCommentaryLoading(true);
      setCommentaryError(null);
      try {
        const response = await fetch(strategicCommentaryEndpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          cache: "no-store",
          body: JSON.stringify({}),
        });
        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }
        const data = (await response.json()) as { commentary?: string };
        if (!cancelled) {
          setStrategicCommentary(data.commentary?.trim() ?? "");
        }
      } catch {
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
  }, [strategicCommentaryEndpoint]);

  const commentarySections = useMemo(() => {
    if (!strategicCommentary) {
      return null;
    }

    const sections = {
      risks: [] as string[],
      opportunities: [] as string[],
      recommendations: [] as string[],
      other: [] as string[],
    };

    let current: keyof typeof sections | null = null;

    const normaliseHeading = (line: string) =>
      line
        .trim()
        .replace(/^#+\s*/, "")
        .replace(/^[>*\-\s]+/, "")
        .replace(/[*_`]/g, "")
        .replace(/:$/, "")
        .trim()
        .toLowerCase();

    strategicCommentary.split(/\r?\n/).forEach((line) => {
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

    const ordered = [
      { id: "risks", label: "Risks", content: sections.risks.join("\n").trim() },
      {
        id: "opportunities",
        label: "Opportunities",
        content: sections.opportunities.join("\n").trim(),
      },
      {
        id: "recommendations",
        label: "Recommendations",
        content: sections.recommendations.join("\n").trim(),
      },
    ].filter((section) => section.content.length > 0);

    if (ordered.length === 0) {
      return null;
    }

    return ordered;
  }, [strategicCommentary]);

  useEffect(() => {
    if (!commentarySections || commentarySections.length === 0) {
      setActiveCommentaryTab(undefined);
      return;
    }
    setActiveCommentaryTab((previous) => {
      if (previous && commentarySections.some((section) => section.id === previous)) {
        return previous;
      }
      return commentarySections[0]?.id;
    });
  }, [commentarySections]);

  useEffect(() => {
    const handler = (event: CustomEvent<StrategicCommentaryTabEventDetail>) => {
      const tabId = event.detail?.tab;
      if (!tabId) {
        return;
      }
      setActiveCommentaryTab((previous) => {
        if (!commentarySections || commentarySections.length === 0) {
          return previous;
        }
        return commentarySections.some((section) => section.id === tabId) ? tabId : previous;
      });
    };

    const wrappedHandler = handler as EventListener;
    window.addEventListener(STRATEGIC_COMMENTARY_TAB_EVENT, wrappedHandler);
    return () => {
      window.removeEventListener(STRATEGIC_COMMENTARY_TAB_EVENT, wrappedHandler);
    };
  }, [commentarySections]);

  const salesData = dashboardData?.salesData ?? [];
  const productData = dashboardData?.productData ?? [];
  const categoryData = dashboardData?.categoryData ?? [];
  const regionalData = dashboardData?.regionalData ?? [];
  const demographicsData = dashboardData?.demographicsData ?? [];
  const metrics = dashboardData?.metrics ?? null;

  const keyMetrics = useMemo(() => {
    if (!metrics) {
      const placeholder = dashboardLoading ? "Loading..." : "N/A";
      return [
        { label: "Total Revenue", value: placeholder },
        { label: "Total Profit", value: placeholder },
        { label: "Customers", value: placeholder },
        { label: "Conversion Rate", value: placeholder },
        { label: "Avg Order Value", value: placeholder },
        { label: "Profit Margin", value: placeholder },
      ];
    }

    return [
      { label: "Total Revenue", value: `$${metrics.totalRevenue.toLocaleString()}` },
      { label: "Total Profit", value: `$${metrics.totalProfit.toLocaleString()}` },
      { label: "Customers", value: metrics.totalCustomers.toLocaleString() },
      { label: "Conversion Rate", value: metrics.conversionRate },
      { label: "Avg Order Value", value: `$${metrics.averageOrderValue}` },
      { label: "Profit Margin", value: metrics.profitMargin },
    ];
  }, [metrics, dashboardLoading]);

  // Color palettes for different charts
  const colors = {
    salesOverview: ["#3b82f6", "#10b981", "#ef4444"],  // Blue, Green, Red
    productPerformance: ["#8b5cf6", "#6366f1", "#4f46e5"],  // Purple spectrum
    categories: ["#3b82f6", "#64748b", "#10b981", "#f59e0b", "#94a3b8"],  // Mixed
    regional: ["#059669", "#10b981", "#34d399", "#6ee7b7", "#a7f3d0"],  // Green spectrum
    demographics: ["#f97316", "#f59e0b", "#eab308", "#facc15", "#fde047"]  // Orange to Yellow
  };
  
  return (
    <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-4 w-full">
      {dashboardError ? (
        <div className="col-span-1 md:col-span-2 lg:col-span-4">
          <div className="rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {dashboardError}
          </div>
        </div>
      ) : null}
      {/* Key Metrics */}
      <div className="col-span-1 md:col-span-2 lg:col-span-4">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {keyMetrics.map((metric) => (
            <Card key={metric.label} className="gap-2 py-4">
              <CardHeader className="px-4 py-0">
                <CardDescription className="text-xs text-muted-foreground">
                  {metric.label}
                </CardDescription>
              </CardHeader>
              <CardContent className="px-4 py-0">
                <CardTitle className="text-xl text-card-foreground">
                  {metric.value}
                </CardTitle>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Charts */}
      <Card className="col-span-1 md:col-span-2 lg:col-span-4" data-chart-id="sales-overview">
        <CardHeader className="pb-1 pt-3">
          <CardTitle className="text-base font-medium">Sales Overview</CardTitle>
          <CardDescription className="text-xs">Monthly sales and profit data</CardDescription>
        </CardHeader>
        <CardContent className="p-3">
          <div className="h-60">
            <AreaChart
              data={salesData}
              index="date"
              categories={["Sales", "Profit", "Expenses"]}
              chartId="sales-overview"
              colors={colors.salesOverview}
              valueFormatter={(value) => `$${value.toLocaleString()}`}
              showLegend={true}
              showGrid={true}
              showXAxis={true}
              showYAxis={true}
            />
          </div>
        </CardContent>
      </Card>

      <Card className="col-span-1 md:col-span-1 lg:col-span-2" data-chart-id="product-performance">
        <CardHeader className="pb-1 pt-3">
          <CardTitle className="text-base font-medium">Product Performance</CardTitle>
          <CardDescription className="text-xs">Top selling products</CardDescription>
        </CardHeader>
        <CardContent className="p-3">
          <div className="h-60">
            <BarChart
              data={productData}
              index="name"
              categories={["sales"]}
              chartId="product-performance"
              colors={colors.productPerformance}
              valueFormatter={(value) => `$${value.toLocaleString()}`}
              showLegend={false}
              showGrid={true}
              layout="horizontal"
            />
          </div>
        </CardContent>
      </Card>

      <Card className="col-span-1 md:col-span-1 lg:col-span-2" data-chart-id="sales-by-category">
        <CardHeader className="pb-1 pt-3">
          <CardTitle className="text-base font-medium">Sales by Category</CardTitle>
          <CardDescription className="text-xs">Distribution across categories</CardDescription>
        </CardHeader>
        <CardContent className="p-3">
          <div className="h-60">
            <DonutChart
              data={categoryData}
              category="value"
              index="name"
              chartId="sales-by-category"
              valueFormatter={(value) => `${value}%`}
              colors={colors.categories}
              centerText="Categories"
              paddingAngle={0}
              showLabel={false}
              showLegend={true}
              innerRadius={45}
              outerRadius="85%"
            />
          </div>
        </CardContent>
      </Card>

      <Card className="col-span-1 md:col-span-1 lg:col-span-2" data-chart-id="regional-sales">
        <CardHeader className="pb-1 pt-3">
          <CardTitle className="text-base font-medium">Regional Sales</CardTitle>
          <CardDescription className="text-xs">Sales by geographic region</CardDescription>
        </CardHeader>
        <CardContent className="p-3">
          <div className="h-60">
            <BarChart
              data={regionalData}
              index="region"
              categories={["sales"]}
              chartId="regional-sales"
              colors={colors.regional}
              valueFormatter={(value) => `$${value.toLocaleString()}`}
              showLegend={false}
              showGrid={true}
              layout="horizontal"
            />
          </div>
        </CardContent>
      </Card>

      <Card className="col-span-1 md:col-span-1 lg:col-span-2" data-chart-id="customer-demographics">
        <CardHeader className="pb-1 pt-3">
          <CardTitle className="text-base font-medium">Customer Demographics</CardTitle>
          <CardDescription className="text-xs">Spending by age group</CardDescription>
        </CardHeader>
        <CardContent className="p-3">
          <div className="h-60">
            <BarChart
              data={demographicsData}
              index="ageGroup"
              categories={["spending"]}
              chartId="customer-demographics"
              colors={colors.demographics}
              valueFormatter={(value) => `$${value}`}
              showLegend={false}
              showGrid={true}
              layout="horizontal"
            />
          </div>
        </CardContent>
      </Card>


      <Card className="col-span-1 md:col-span-2 lg:col-span-4" data-chart-id="strategic-commentary">
        <CardHeader className="pb-1 pt-3">
          <CardTitle className="text-base font-medium">Strategic Commentary</CardTitle>
          <CardDescription className="text-xs">Risks, opportunities, and recommendations</CardDescription>
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
            ) : commentarySections ? (
              <Tabs
                value={activeCommentaryTab ?? commentarySections[0]?.id}
                onValueChange={setActiveCommentaryTab}
                className="w-full"
              >
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
            ) : strategicCommentary ? (
              <div className="prose prose-sm text-muted-foreground dark:prose-invert">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{strategicCommentary}</ReactMarkdown>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                Strategic commentary is not available yet.
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 
