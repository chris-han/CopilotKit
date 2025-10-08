"use client";

import { useState, useMemo } from "react";
import { BarChart, LineChart, PieChart, Sparkles, Calendar, Download, Code, Eye, Lightbulb, Plus, CheckCircle, Trash2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { DynamicChart } from "../ui/dynamic-chart";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from "../ui/dialog";
import { Button } from "../ui/button";

interface GeneratedVisualization {
  id: string;
  title: string;
  description: string;
  chart_type: string;
  chart_config: any;
  code: string;
  insights: string[];
  created_at: string;
  updated_at?: string;
  dataset_name?: string | null;
}

interface ChartGalleryProps {
  visualizations: GeneratedVisualization[];
  onVisualizationSelect: (visualization: GeneratedVisualization) => void;
  onAddToDashboard?: (visualization: GeneratedVisualization) => void;
  onDeleteVisualization?: (visualization: GeneratedVisualization) => Promise<void> | void;
}

const CHART_TYPE_ICONS = {
  bar: BarChart,
  line: LineChart,
  pie: PieChart,
  scatter: Sparkles,
  histogram: BarChart,
  area: LineChart,
  auto: Sparkles,
};

type DbtModelMetadata = {
  name: string;
  path: string;
  description: string;
  sql: string;
};

const DBT_MODEL_MAP: Record<string, DbtModelMetadata> = {
  salesData: {
    name: "Sales Performance Model",
    path: "models/marts/finance/sales_performance.sql",
    description: "Aggregates revenue, profit, and expense metrics by month for executive dashboards.",
    sql: `with source as (
  select * from {{ ref('fct_sales_transactions') }}
),
calendar as (
  select * from {{ ref('dim_calendar') }}
)
select
  c.month_start as billing_period_start,
  sum(s.revenue) as revenue,
  sum(s.profit) as profit,
  sum(s.expense) as expense,
  sum(s.customer_count) as customers
from source s
left join calendar c
  on s.date_id = c.date_id
group by 1
order by 1;`,
  },
  productData: {
    name: "Product Performance Model",
    path: "models/marts/finance/product_performance.sql",
    description: "Computes sales, units, and growth percentages by product for ranking visualizations.",
    sql: `select
  p.product_id,
  p.product_name,
  sum(f.revenue) as sales,
  sum(f.units) as units,
  avg(f.growth_pct) as growth_percentage
from {{ ref('dim_product') }} p
join {{ ref('fct_product_revenue') }} f
  on p.product_id = f.product_id
group by 1,2
order by sales desc;`,
  },
  categoryData: {
    name: "Category Mix Model",
    path: "models/marts/finance/category_mix.sql",
    description: "Provides revenue share and growth metrics across product categories.",
    sql: `select
  c.category_name,
  sum(f.revenue) as revenue,
  sum(f.revenue) / sum(sum(f.revenue)) over () as revenue_share,
  avg(f.growth_pct) as growth_percentage
from {{ ref('dim_category') }} c
join {{ ref('fct_category_revenue') }} f
  on c.category_id = f.category_id
group by 1
order by revenue desc;`,
  },
  regionalData: {
    name: "Regional Sales Model",
    path: "models/marts/finance/regional_sales.sql",
    description: "Summarizes sales and market share by region for geographic comparisons.",
    sql: `select
  r.region_name,
  sum(f.revenue) as revenue,
  sum(f.revenue) / sum(sum(f.revenue)) over () as market_share
from {{ ref('dim_region') }} r
join {{ ref('fct_regional_revenue') }} f
  on r.region_id = f.region_id
group by 1
order by revenue desc;`,
  },
  demographicsData: {
    name: "Customer Demographics Model",
    path: "models/marts/finance/customer_demographics.sql",
    description: "Tracks spend distribution by age cohort for demographic analysis.",
    sql: `select
  d.age_group,
  sum(f.spend) as total_spend,
  sum(f.customers) as customers
from {{ ref('dim_demographic') }} d
join {{ ref('fct_customer_spend') }} f
  on d.demographic_id = f.demographic_id
group by 1
order by total_spend desc;`,
  },
  enterprise_multi_cloud: {
    name: "Enterprise Multi-Cloud Spend",
    path: "models/marts/finops/enterprise_multi_cloud.sql",
    description: "Normalised cloud cost data across AWS, Azure, and GCP with provider, service, and environment dimensions.",
    sql: `with source as (
  select * from {{ ref('fct_enterprise_cloud_costs') }}
),
aggregated as (
  select
    billing_period_start,
    provider,
    service,
    environment,
    sum(cost) as total_cost,
    sum(usage_quantity) as usage_quantity,
    sum(credits) as credits,
    sum(reserved_savings) as reserved_savings,
    sum(spot_savings) as spot_savings
  from source
  group by 1, 2, 3, 4
)
select *
from aggregated
order by billing_period_start desc, provider asc, service asc;`,
  },
};

function resolveDbtModelInfo(
  visualization: GeneratedVisualization | null,
): { key?: string; metadata?: DbtModelMetadata } {
  if (!visualization) {
    return {};
  }

  const chartConfig = (visualization.chart_config ?? {}) as Record<string, unknown>;
  const datasetNameRaw = visualization.dataset_name;
  const datasetName =
    typeof datasetNameRaw === "string" && datasetNameRaw.trim().length > 0
      ? datasetNameRaw.trim()
      : undefined;

  const candidateValues: unknown[] = [
    chartConfig["dbtModel"],
    chartConfig["dbt_model"],
    datasetName,
    chartConfig["datasetName"],
    chartConfig["dataset_name"],
    chartConfig["dataSource"],
    chartConfig["data_source"],
  ];

  let resolvedKey: string | undefined;
  for (const candidate of candidateValues) {
    if (typeof candidate === "string") {
      const trimmed = candidate.trim();
      if (trimmed.length > 0) {
        resolvedKey = trimmed;
        break;
      }
    }
  }

  if (!resolvedKey && datasetName) {
    resolvedKey = datasetName;
  }

  if (!resolvedKey) {
    return {};
  }

  const lookupCandidates = new Set<string>();
  lookupCandidates.add(resolvedKey);
  lookupCandidates.add(resolvedKey.toLowerCase());
  lookupCandidates.add(resolvedKey.replace(/[\s-]+/g, "_"));
  lookupCandidates.add(resolvedKey.toLowerCase().replace(/[\s-]+/g, "_"));
  lookupCandidates.add(resolvedKey.replace(/\.[^.]+$/, ""));
  lookupCandidates.add(resolvedKey.toLowerCase().replace(/\.[^.]+$/, "").replace(/[\s-]+/g, "_"));

  for (const candidate of Array.from(lookupCandidates)) {
    if (candidate && candidate !== resolvedKey) {
      lookupCandidates.add(candidate.toLowerCase());
    }
  }

  let resolvedMetadata: DbtModelMetadata | undefined;
  let resolvedLookupKey: string | undefined;
  for (const candidate of lookupCandidates) {
    if (!candidate) continue;
    const metadata = DBT_MODEL_MAP[candidate];
    if (metadata) {
      resolvedMetadata = metadata;
      resolvedLookupKey = candidate;
      break;
    }
  }

  return {
    key: resolvedLookupKey ?? resolvedKey,
    metadata: resolvedMetadata,
  };
}

export function ChartGallery({ visualizations, onVisualizationSelect, onAddToDashboard, onDeleteVisualization }: ChartGalleryProps) {
  const [selectedViz, setSelectedViz] = useState<GeneratedVisualization | null>(null);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [successDialogOpen, setSuccessDialogOpen] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");

  const normalizedSelectedInsights = useMemo(() => {
    if (!selectedViz) return [];
    const raw = selectedViz.insights;
    if (Array.isArray(raw)) {
      return raw as string[];
    }
    if (typeof raw === "string" && raw.trim().length > 0) {
      return [raw];
    }
    return [];
  }, [selectedViz]);

  const sortedVisualizations = useMemo(() => {
    return [...visualizations].sort((a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
  }, [visualizations]);

  const { key: selectedDbtKey, metadata: selectedDbtModel } = useMemo(
    () => resolveDbtModelInfo(selectedViz),
    [selectedViz],
  );

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getChartIcon = (chartType: string) => {
    const IconComponent = CHART_TYPE_ICONS[chartType as keyof typeof CHART_TYPE_ICONS] || Sparkles;
    return IconComponent;
  };

  const handleVisualizationClick = (viz: GeneratedVisualization) => {
    setSelectedViz(viz);
    onVisualizationSelect(viz);
  };

  const handleDownload = (viz: GeneratedVisualization, format: "png" | "svg" | "json") => {
    // Implementation would depend on the chart library used
    console.log(`Downloading ${viz.title} as ${format}`);
  };

  const handleCodeView = (viz: GeneratedVisualization) => {
    // Show code in a modal or expand in place
    console.log("Viewing code for:", viz.title);
  };

  const handleAddToDashboard = async (viz: GeneratedVisualization) => {
    console.log("ChartGallery: Add to Dashboard button clicked for:", viz.title);
    console.log("ChartGallery: onAddToDashboard handler available:", !!onAddToDashboard);

    if (onAddToDashboard) {
      try {
        console.log("ChartGallery: Calling onAddToDashboard handler");
        await onAddToDashboard(viz);
        console.log("ChartGallery: onAddToDashboard completed successfully");
        // Don't show success message here since parent will handle it
      } catch (error) {
        console.error("ChartGallery: Failed to add to dashboard:", error);
        setSuccessMessage(`Failed to add "${viz.title}" to dashboard. Error: ${error.message || 'Unknown error'}`);
        setSuccessDialogOpen(true);
      }
    } else {
      // Default behavior if no handler provided
      console.log("ChartGallery: No onAddToDashboard handler provided");
      setSuccessMessage("Dashboard functionality not connected. Please check the component setup.");
      setSuccessDialogOpen(true);
    }
  };

  const handleDeleteVisualization = async (viz: GeneratedVisualization) => {
    console.log("ChartGallery: Delete button clicked for:", viz.title);

    if (onDeleteVisualization) {
      try {
        await onDeleteVisualization(viz);
        console.log("ChartGallery: Visualization deleted successfully");
      } catch (error) {
        console.error("ChartGallery: Failed to delete visualization:", error);
      }
    } else {
      console.log("ChartGallery: No onDeleteVisualization handler provided");
    }
  };

  const renderVisualizationCard = (viz: GeneratedVisualization) => {
    const insightsRaw = viz.insights;
    let insights: string[] = [];
    if (Array.isArray(insightsRaw)) {
      insights = insightsRaw as string[];
    } else if (typeof insightsRaw === "string" && insightsRaw.trim().length > 0) {
      insights = [insightsRaw];
    }

    const IconComponent = getChartIcon(viz.chart_type);

    return (
      <Card
        key={viz.id}
        className="cursor-pointer hover:shadow-md transition-shadow"
        onClick={() => handleVisualizationClick(viz)}
      >
        <CardHeader className="pb-2 space-y-2">
          <div className="flex min-w-0 items-start gap-2">
            <IconComponent className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
            <CardTitle className="text-sm font-medium leading-tight line-clamp-2">{viz.title}</CardTitle>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
            <div className="flex flex-wrap items-center gap-2">
              <Calendar className="h-3 w-3" />
              <span>{formatDate(viz.created_at)}</span>
              <span>•</span>
              <span className="capitalize">{viz.chart_type}</span>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteVisualization(viz);
                }}
                className="p-1 hover:bg-destructive/10 text-destructive rounded-md"
                title="Delete visualization"
                aria-label={`Delete ${viz.title}`}
              >
                <Trash2 className="h-3 w-3" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleCodeView(viz);
                }}
                className="p-1 hover:bg-secondary rounded-md"
                title="View code"
              >
                <Code className="h-3 w-3" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDownload(viz, "png");
                }}
                className="p-1 hover:bg-secondary rounded-md"
                title="Download"
              >
                <Download className="h-3 w-3" />
              </button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          {/* Chart Preview */}
          <div className="aspect-video bg-muted rounded-md flex items-center justify-center mb-3">
            <div className="text-center">
              <IconComponent className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
              <p className="text-xs text-muted-foreground">Chart Preview</p>
            </div>
          </div>

          {/* Description */}
          {viz.description && (
            <p className="text-xs text-muted-foreground mb-2 line-clamp-2">
              {viz.description}
            </p>
          )}

          {/* Insights */}
          {insights.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs font-medium">Key Insights:</p>
              <ul className="text-xs text-muted-foreground space-y-1">
                {insights.slice(0, 2).map((insight, index) => (
                  <li key={index} className="flex items-start space-x-1">
                    <span className="w-1 h-1 bg-muted-foreground rounded-full mt-1.5 flex-shrink-0"></span>
                    <span className="line-clamp-1">{insight}</span>
                  </li>
                ))}
              </ul>
              {insights.length > 2 && (
                <p className="text-xs text-muted-foreground">
                  +{insights.length - 2} more insights
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  const renderVisualizationList = (viz: GeneratedVisualization) => {
    const insightsRaw = viz.insights;
    let insights: string[] = [];
    if (Array.isArray(insightsRaw)) {
      insights = insightsRaw as string[];
    } else if (typeof insightsRaw === "string" && insightsRaw.trim().length > 0) {
      insights = [insightsRaw];
    }

    const IconComponent = getChartIcon(viz.chart_type);

    return (
      <Card
        key={viz.id}
        className="cursor-pointer hover:shadow-md transition-shadow"
        onClick={() => handleVisualizationClick(viz)}
      >
        <CardContent className="p-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:space-x-4">
            {/* Chart Preview */}
            <div className="w-20 h-16 bg-muted rounded-md flex items-center justify-center flex-shrink-0">
              <IconComponent className="h-6 w-6 text-muted-foreground" />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0 flex flex-col gap-2">
              <h3 className="text-sm font-medium leading-tight line-clamp-2 pr-2">{viz.title}</h3>

              <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
                <div className="flex flex-wrap items-center gap-2">
                  <Calendar className="h-3 w-3" />
                  <span>{formatDate(viz.created_at)}</span>
                  <span>•</span>
                  <span className="capitalize">{viz.chart_type}</span>
                </div>
                <div className="flex flex-wrap items-center gap-1 sm:flex-shrink-0">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteVisualization(viz);
                    }}
                    className="p-1 hover:bg-destructive/10 text-destructive rounded-md"
                    title="Delete visualization"
                    aria-label={`Delete ${viz.title}`}
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCodeView(viz);
                    }}
                    className="p-1 hover:bg-secondary rounded-md"
                    title="View code"
                  >
                    <Code className="h-3 w-3" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDownload(viz, "png");
                    }}
                    className="p-1 hover:bg-secondary rounded-md"
                    title="Download"
                  >
                    <Download className="h-3 w-3" />
                  </button>
                </div>
              </div>

              {viz.description && (
                <p className="text-xs text-muted-foreground mb-2 line-clamp-2">
                  {viz.description}
                </p>
              )}

              {insights.length > 0 && (
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-medium">Insights:</span>
                  <span className="text-xs text-muted-foreground truncate">
                    {insights[0]}
                  </span>
                  {insights.length > 1 && (
                    <span className="text-xs text-muted-foreground">
                      +{insights.length - 1} more
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  if (visualizations.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Sparkles className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">No visualizations yet</h3>
          <p className="text-sm text-muted-foreground text-center">
            Generate your first visualization by going to the Visualize tab and describing what you want to see.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Visualization Gallery</h2>
          <p className="text-sm text-muted-foreground">
            {visualizations.length} visualization{visualizations.length !== 1 ? "s" : ""} generated
          </p>
        </div>

        {/* View mode toggle */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setViewMode("grid")}
            className={`p-2 rounded-md transition-colors ${
              viewMode === "grid"
                ? "bg-primary text-primary-foreground"
                : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
            }`}
          >
            <div className="grid grid-cols-2 gap-0.5 w-3 h-3">
              <div className="bg-current rounded-sm"></div>
              <div className="bg-current rounded-sm"></div>
              <div className="bg-current rounded-sm"></div>
              <div className="bg-current rounded-sm"></div>
            </div>
          </button>
          <button
            onClick={() => setViewMode("list")}
            className={`p-2 rounded-md transition-colors ${
              viewMode === "list"
                ? "bg-primary text-primary-foreground"
                : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
            }`}
          >
            <div className="space-y-0.5 w-3 h-3">
              <div className="bg-current h-0.5 rounded-sm"></div>
              <div className="bg-current h-0.5 rounded-sm"></div>
              <div className="bg-current h-0.5 rounded-sm"></div>
            </div>
          </button>
        </div>
      </div>

      {/* Gallery */}
      {viewMode === "grid" ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sortedVisualizations.map(renderVisualizationCard)}
        </div>
      ) : (
        <div className="space-y-3">
          {sortedVisualizations.map(renderVisualizationList)}
        </div>
      )}

      {/* Selected visualization details */}
      {selectedViz && (
        <Card className="border-primary">
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <div>
                <CardTitle className="flex items-center space-x-2">
                  <Eye className="h-5 w-5" />
                  <span>Selected Visualization</span>
                </CardTitle>
                <CardDescription>{selectedViz.title}</CardDescription>
              </div>
              <div className="flex items-center gap-2">
                {selectedDbtModel ? (
                  <Dialog>
                    <DialogContent className="max-w-3xl">
                      <DialogHeader>
                        <DialogTitle>{selectedDbtModel.name}</DialogTitle>
                        <DialogDescription className="space-y-1">
                          <p>{selectedDbtModel.description}</p>
                          <p className="text-xs text-muted-foreground">Path: {selectedDbtModel.path}</p>
                        </DialogDescription>
                      </DialogHeader>
                      <pre className="max-h-[360px] overflow-auto rounded-md bg-muted p-4 text-xs">
                        <code>{selectedDbtModel.sql}</code>
                      </pre>
                    </DialogContent>
                  </Dialog>
                ) : null}
                <button
                  onClick={() => {
                    console.log('Button clicked, selectedViz:', selectedViz?.title);
                    if (selectedViz) {
                      handleAddToDashboard(selectedViz);
                    } else {
                      console.error('No selectedViz available');
                    }
                  }}
                  className="flex items-center space-x-2 bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md text-sm font-medium transition-colors"
                  title="Add to Dashboard"
                  disabled={!selectedViz}
                >
                  <Plus className="h-4 w-4" />
                  <span>Add to Dashboard</span>
                </button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="preview" className="w-full">
              <TabsList>
                <TabsTrigger value="preview">Preview</TabsTrigger>
                <TabsTrigger value="insights">
                  Insights {normalizedSelectedInsights.length > 0 && (
                    <span className="ml-1 text-xs bg-primary text-primary-foreground rounded-full px-1.5 py-0.5">
                      {normalizedSelectedInsights.length}
                    </span>
                  )}
                </TabsTrigger>
                <TabsTrigger value="code">Code</TabsTrigger>
                <TabsTrigger value="config">Config</TabsTrigger>
                <TabsTrigger
                  value="dbt"
                  title={
                    selectedDbtModel
                      ? `View dbt model details for ${selectedDbtModel.name}`
                      : selectedDbtKey
                      ? `No dbt metadata registered for ${selectedDbtKey}`
                      : "Link a dbt model to this visualization to view details"
                  }
                >
                  dbt Model
                </TabsTrigger>
              </TabsList>

              <TabsContent value="preview" className="space-y-4">
                <div className="aspect-video bg-muted rounded-md overflow-hidden">
                  {selectedViz.chart_config ? (
                    <DynamicChart
                      config={selectedViz.chart_config}
                      style={{ width: "100%", height: "100%" }}
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <div className="text-center">
                        {(() => {
                          const IconComponent = getChartIcon(selectedViz.chart_type);
                          return <IconComponent className="h-16 w-16 text-muted-foreground mx-auto mb-4" />;
                        })()}
                        <p className="text-muted-foreground">No chart configuration available</p>
                      </div>
                    </div>
                  )}
                </div>
                {selectedViz.description && (
                  <p className="text-sm text-muted-foreground">{selectedViz.description}</p>
                )}
              </TabsContent>

              <TabsContent value="insights" className="space-y-3">
                {normalizedSelectedInsights.length > 0 ? (
                  <div className="space-y-4">
                    <div className="text-sm text-muted-foreground">
                      {normalizedSelectedInsights.length} AI-generated insights about your data:
                    </div>
                    <ul className="space-y-3">
                      {normalizedSelectedInsights.map((insight, index) => (
                        <li key={index} className="flex items-start space-x-3">
                          <span className="w-2 h-2 bg-primary rounded-full mt-2 flex-shrink-0"></span>
                          <div className="text-sm leading-relaxed">
                            {insight.split('**').map((part, i) =>
                              i % 2 === 1 ? (
                                <strong key={i} className="font-semibold text-foreground">{part}</strong>
                              ) : (
                                <span key={i} className="text-muted-foreground">{part}</span>
                              )
                            )}
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Lightbulb className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-sm text-muted-foreground">No insights available for this visualization.</p>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="code">
                <pre className="bg-muted p-4 rounded-md text-sm overflow-x-auto">
                  <code>{selectedViz.code || "# Code not available"}</code>
                </pre>
              </TabsContent>

              <TabsContent value="config">
                <pre className="bg-muted p-4 rounded-md text-sm overflow-x-auto">
                  <code>{JSON.stringify(selectedViz.chart_config, null, 2)}</code>
                </pre>
              </TabsContent>

              <TabsContent value="dbt">
                {selectedDbtModel ? (
                  <div className="space-y-3">
                    <div>
                      <h4 className="text-sm font-semibold">{selectedDbtModel.name}</h4>
                      <p className="text-xs text-muted-foreground">
                        {selectedDbtModel.description}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Path: {selectedDbtModel.path}
                      </p>
                    </div>
                    <pre className="bg-muted p-4 rounded-md text-xs overflow-auto max-h-[360px]">
                      <code>{selectedDbtModel.sql}</code>
                    </pre>
                  </div>
                ) : selectedDbtKey ? (
                  <div className="space-y-4">
                    <div className="rounded-md border border-dashed border-muted-foreground/40 bg-muted/40 p-4">
                      <p className="text-sm font-medium text-foreground">
                        No dbt metadata registered for{" "}
                        <code className="font-mono text-xs">{selectedDbtKey}</code>.
                      </p>
                      <p className="text-xs text-muted-foreground mt-2">
                        Add this model to the gallery&#39;s dbt catalogue or persist metadata with the visualization to surface SQL lineage here.
                      </p>
                    </div>
                    {selectedViz?.dataset_name ? (
                      <p className="text-xs text-muted-foreground">
                        Linked dataset:{" "}
                        <code className="font-mono text-xs">{selectedViz.dataset_name}</code>
                      </p>
                    ) : null}
                  </div>
                ) : (
                  <div className="text-center py-8 text-sm text-muted-foreground">
                    Connect this visualization to a dbt model by including a `dbtModel` or `dataset_name` property in the chart configuration.
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}

      {/* Success Dialog */}
      <Dialog open={successDialogOpen} onOpenChange={setSuccessDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-6 w-6 text-green-600" />
              <DialogTitle className="text-green-800">Success!</DialogTitle>
            </div>
            <DialogDescription className="text-left pt-2">
              {successMessage}
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end pt-4">
            <Button
              onClick={() => setSuccessDialogOpen(false)}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              OK
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
