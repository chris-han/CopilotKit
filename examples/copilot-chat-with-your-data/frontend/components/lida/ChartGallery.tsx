"use client";

import { useState, useMemo, useEffect, useCallback } from "react";
import type { EChartsOption } from "echarts";
import { BarChart, LineChart, PieChart, Sparkles, Calendar, Download, Code, Eye, Lightbulb, Plus, CheckCircle, Trash2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { DynamicChart } from "../ui/dynamic-chart";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "../ui/dialog";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Textarea } from "../ui/textarea";
import { Label } from "../ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { Dashboard } from "@/types/dashboard";

interface DbtModelMetadata {
  id?: string;
  name?: string;
  description?: string;
  path?: string;
  sql?: string;
  aliases?: string[];
}

interface GeneratedVisualization {
  id: string;
  title: string;
  description: string;
  chart_type: string;
  chart_config: unknown;
  code: string;
  insights: string[];
  created_at: string;
  updated_at?: string;
  dataset_name?: string | null;
  dbt_metadata?: DbtModelMetadata | null;
  echar_code?: string | null;
  semantic_model_id?: string | null;
}

interface ChartGalleryProps {
  visualizations: GeneratedVisualization[];
  dashboards: Dashboard[];
  onVisualizationSelect: (visualization: GeneratedVisualization) => void;
  onAddToDashboard?: (visualization: GeneratedVisualization, dashboardId?: string) => void | Promise<void>;
  onCreateDashboard?: (name: string, description?: string) => Promise<Dashboard>;
  onDeleteVisualization?: (visualization: GeneratedVisualization) => Promise<void> | void;
  onUpdateVisualization?: (visualization: GeneratedVisualization) => Promise<GeneratedVisualization | void> | GeneratedVisualization | void;
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
  id?: string;
  name?: string;
  description?: string;
  path?: string;
  sql?: string;
  aliases?: string[];
};

type DetailTab = "preview" | "insights" | "code" | "config" | "dbt" | "edit";

const CHART_TYPE_OPTIONS = Object.keys(CHART_TYPE_ICONS);

type ChartTypeOption = "area" | "bar" | "donut";

type ChartTypePreset = {
  defaultDataset: string;
  buildConfig: (
    title: string,
    datasetKey: string,
    sampleData: Array<Record<string, unknown>>
  ) => EChartsOption;
  buildCode: (
    chartType: string,
    datasetKey: string,
    config: EChartsOption
  ) => string;
};

const SAMPLE_CHART_DATA: Record<string, Array<Record<string, unknown>>> = {
  salesData: [
    { date: "Jan 22", Sales: 2890, Profit: 2400, Expenses: 490 },
    { date: "Feb 22", Sales: 1890, Profit: 1398, Expenses: 492 },
    { date: "Mar 22", Sales: 3890, Profit: 2980, Expenses: 910 },
    { date: "Apr 22", Sales: 2890, Profit: 2300, Expenses: 590 },
    { date: "May 22", Sales: 4890, Profit: 3200, Expenses: 1690 },
    { date: "Jun 22", Sales: 3890, Profit: 2900, Expenses: 990 },
    { date: "Jul 22", Sales: 4200, Profit: 3100, Expenses: 1100 },
    { date: "Aug 22", Sales: 4500, Profit: 3400, Expenses: 1100 },
    { date: "Sep 22", Sales: 5100, Profit: 3800, Expenses: 1300 },
    { date: "Oct 22", Sales: 4800, Profit: 3600, Expenses: 1200 },
    { date: "Nov 22", Sales: 5500, Profit: 4100, Expenses: 1400 },
    { date: "Dec 22", Sales: 6800, Profit: 5200, Expenses: 1600 },
  ],
  productData: [
    { name: "Smartphone", sales: 9800, growth: 12.5 },
    { name: "Graphic Tee", sales: 4567, growth: 8.2 },
    { name: "Dishwasher", sales: 3908, growth: -2.4 },
    { name: "Blender", sales: 2400, growth: 5.6 },
    { name: "Smartwatch", sales: 1908, growth: -1.8 },
  ],
  categoryData: [
    { name: "Electronics", value: 35, growth: 8.2 },
    { name: "Clothing", value: 25, growth: 4.5 },
    { name: "Home & Kitchen", value: 20, growth: 12.1 },
    { name: "Other", value: 15, growth: -2.3 },
    { name: "Books", value: 5, growth: 1.5 },
  ],
};

const createCodeSnippet = (
  chartType: string,
  datasetKey: string,
  config: EChartsOption
) => {
  return [
    `// Auto-generated ${chartType} chart bound to ${datasetKey || "sample data"}`,
    `export const chartConfig = ${JSON.stringify(config, null, 2)};`,
  ].join("\n");
};

const attachDatasetMetadata = (
  config: EChartsOption,
  datasetKey: string
): EChartsOption => ({
  ...config,
  datasetName: datasetKey,
  dataset_name: datasetKey,
  dataSource: datasetKey,
  data_source: datasetKey,
  dbtModel: datasetKey,
  dbt_model: datasetKey,
});

const CHART_TYPE_PRESETS: Record<ChartTypeOption, ChartTypePreset> = {
  area: {
    defaultDataset: "salesData",
    buildConfig: (title, datasetKey, sampleData) => {
      const config: EChartsOption = {
        title: { text: title || "Sales Overview" },
        tooltip: { trigger: "axis" },
        legend: { show: true },
        dataset: { source: sampleData },
        xAxis: { type: "category", boundaryGap: false, name: "Period" },
        yAxis: { type: "value", name: "Amount" },
        grid: { left: "8%", right: "5%", bottom: "10%", containLabel: true },
        series: [
          {
            name: "Sales",
            type: "line",
            smooth: true,
            areaStyle: { opacity: 0.2 },
            encode: { x: "date", y: "Sales" },
          },
          {
            name: "Profit",
            type: "line",
            smooth: true,
            areaStyle: { opacity: 0.12 },
            encode: { x: "date", y: "Profit" },
          },
          {
            name: "Expenses",
            type: "line",
            smooth: true,
            areaStyle: { opacity: 0.12 },
            encode: { x: "date", y: "Expenses" },
          },
        ],
        color: ["#4f46e5", "#14b8a6", "#f97316"],
      };
      return attachDatasetMetadata(config, datasetKey);
    },
    buildCode: (chartType, datasetKey, config) =>
      createCodeSnippet(chartType, datasetKey, config),
  },
  bar: {
    defaultDataset: "productData",
    buildConfig: (title, datasetKey, sampleData) => {
      const config: EChartsOption = {
        title: { text: title || "Product Performance" },
        tooltip: { trigger: "axis" },
        dataset: { source: sampleData },
        grid: { left: 120, right: 40, bottom: 40, top: 60, containLabel: true },
        xAxis: { type: "value", name: "Sales" },
        yAxis: { type: "category", name: "Product", inverse: true },
        series: [
          {
            type: "bar",
            encode: { x: "sales", y: "name" },
            itemStyle: { borderRadius: [4, 4, 4, 4] },
            label: { show: true, position: "right", formatter: "{c}" },
          },
        ],
        color: ["#2563eb"],
      };
      return attachDatasetMetadata(config, datasetKey);
    },
    buildCode: (chartType, datasetKey, config) =>
      createCodeSnippet(chartType, datasetKey, config),
  },
  donut: {
    defaultDataset: "categoryData",
    buildConfig: (title, datasetKey, sampleData) => {
      const config: EChartsOption = {
        title: { text: title || "Sales by Category" },
        tooltip: { trigger: "item" },
        legend: { orient: "vertical", left: "left" },
        dataset: { source: sampleData },
        series: [
          {
            name: "Category Share",
            type: "pie",
            radius: ["45%", "70%"],
            center: ["55%", "55%"],
            avoidLabelOverlap: false,
            encode: { value: "value", itemName: "name" },
            label: { formatter: "{b}: {d}%" },
            emphasis: { scale: true, scaleSize: 8 },
          },
        ],
        color: ["#0ea5e9", "#f97316", "#22c55e", "#6366f1", "#a855f7"],
      };
      return attachDatasetMetadata(config, datasetKey);
    },
    buildCode: (chartType, datasetKey, config) =>
      createCodeSnippet(chartType, datasetKey, config),
  },
};

const NORMALIZE_CHART_TYPE: Record<string, ChartTypeOption> = {
  area: "area",
  line: "area",
  bar: "bar",
  column: "bar",
  auto: "bar",
  histogram: "bar",
  donut: "donut",
  pie: "donut",
  ring: "donut",
  scatter: "bar",
};

const getPresetType = (value: string): ChartTypeOption =>
  NORMALIZE_CHART_TYPE[value] ?? "bar";

export function ChartGallery({
  visualizations,
  dashboards,
  onVisualizationSelect,
  onAddToDashboard,
  onCreateDashboard,
  onDeleteVisualization,
  onUpdateVisualization,
}: ChartGalleryProps) {
  const [selectedViz, setSelectedViz] = useState<GeneratedVisualization | null>(null);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [detailsTab, setDetailsTab] = useState<DetailTab>("preview");
  const [editDraft, setEditDraft] = useState<GeneratedVisualization | null>(null);
  const [chartConfigText, setChartConfigText] = useState<string>("");
  const [chartConfigError, setChartConfigError] = useState<string | null>(null);
  const [codeText, setCodeText] = useState<string>("");
  const [datasetInput, setDatasetInput] = useState<string>("");
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [successDialogOpen, setSuccessDialogOpen] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [addMode, setAddMode] = useState<"existing" | "new">("existing");
  const [selectedDashboardId, setSelectedDashboardId] = useState<string>("");
  const [newDashboardName, setNewDashboardName] = useState<string>("");
  const [newDashboardDescription, setNewDashboardDescription] = useState<string>("");
  const [addError, setAddError] = useState<string | null>(null);
  const [addLoading, setAddLoading] = useState(false);

  const resetSaveState = useCallback(() => {
    setSaveSuccess(false);
    setSaveError(null);
  }, []);

  useEffect(() => {
    if (!selectedViz) return;
    const updated = visualizations.find((viz) => viz.id === selectedViz.id);
    if (updated && updated !== selectedViz) {
      setSelectedViz(updated);
    }
  }, [visualizations, selectedViz]);

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

  const selectedDbtModel = useMemo(() => {
    if (!selectedViz) return null;
    return selectedViz.dbt_metadata ?? null;
  }, [selectedViz]);

  const selectedDbtKey = useMemo(() => {
    if (selectedDbtModel?.id) {
      return selectedDbtModel.id;
    }
    if (!selectedViz) {
      return undefined;
    }
    const chartConfig = (selectedViz.chart_config ?? {}) as Record<string, unknown>;
    const candidates = [
      selectedViz.dataset_name,
      chartConfig["dbtModel"],
      chartConfig["dbt_model"],
      chartConfig["datasetName"],
      chartConfig["dataset_name"],
      chartConfig["dataSource"],
      chartConfig["data_source"],
    ];
    for (const candidate of candidates) {
      if (typeof candidate === "string" && candidate.trim().length > 0) {
        return candidate.trim();
      }
    }
    return undefined;
  }, [selectedViz, selectedDbtModel]);

  const selectedChartConfig = useMemo(() => {
    if (!selectedViz) return null;
    const candidates = [
      selectedViz.chart_config,
      selectedViz.echar_code,
      (selectedViz as Record<string, unknown>)?.["echarts_config"],
    ];
    for (const candidate of candidates) {
      if (!candidate) continue;
      if (typeof candidate === "string") {
        try {
          const parsed = JSON.parse(candidate);
          if (parsed && typeof parsed === "object") {
            return parsed as Record<string, unknown>;
          }
        } catch {
          continue;
        }
      } else if (typeof candidate === "object") {
        return candidate as Record<string, unknown>;
      }
    }
    return null;
  }, [selectedViz]);

  const originalConfigObject = useMemo<EChartsOption>(() => {
    if (!selectedViz) {
      return {};
    }
    if (selectedChartConfig && typeof selectedChartConfig === "object") {
      try {
        return JSON.parse(JSON.stringify(selectedChartConfig)) as EChartsOption;
      } catch {
        return selectedChartConfig as EChartsOption;
      }
    }
    if (selectedViz.chart_config) {
      if (typeof selectedViz.chart_config === "string") {
        try {
          const parsed = JSON.parse(selectedViz.chart_config);
          if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
            return parsed as EChartsOption;
          }
        } catch {
          return {};
        }
      } else if (typeof selectedViz.chart_config === "object") {
        try {
          return JSON.parse(JSON.stringify(selectedViz.chart_config)) as EChartsOption;
        } catch {
          return selectedViz.chart_config as EChartsOption;
        }
      }
    }
    return {};
  }, [selectedViz, selectedChartConfig]);

  useEffect(() => {
    if (!selectedViz) {
      setEditDraft(null);
      setChartConfigText("");
      setCodeText("");
      setDatasetInput("");
      setChartConfigError(null);
      setSaveError(null);
      setSaveSuccess(false);
      setDetailsTab("preview");
      return;
    }

    const normalizedConfig = JSON.parse(JSON.stringify(originalConfigObject ?? {})) as EChartsOption;

    let baselineConfigText = JSON.stringify(normalizedConfig, null, 2);
    if (typeof selectedViz.chart_config === "string") {
      const raw = selectedViz.chart_config;
      try {
        const parsed = JSON.parse(raw);
        if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
          baselineConfigText = JSON.stringify(parsed, null, 2);
        } else {
          baselineConfigText = raw;
        }
      } catch {
        baselineConfigText = raw;
      }
    }

    setEditDraft({
      ...selectedViz,
      chart_config: normalizedConfig,
    });
    setChartConfigText(baselineConfigText);
    setCodeText(selectedViz.code ?? "");
    setDatasetInput(selectedViz.dataset_name ?? "");
    setChartConfigError(null);
    setSaveError(null);
    setSaveSuccess(false);
    setDetailsTab("preview");
  }, [selectedViz, originalConfigObject]);

  const liveChartConfig = useMemo<EChartsOption>(() => {
    if (editDraft?.chart_config && typeof editDraft.chart_config === "object") {
      return editDraft.chart_config as EChartsOption;
    }
    return originalConfigObject;
  }, [editDraft, originalConfigObject]);

  const hasLiveConfig = useMemo(() => {
    return liveChartConfig && Object.keys(liveChartConfig).length > 0;
  }, [liveChartConfig]);

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
    setDetailsTab("preview");
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

  const handleAddToDashboardClick = (viz: GeneratedVisualization) => {
    console.log("ChartGallery: Add to Dashboard button clicked for:", viz.title);
    if (!onAddToDashboard) {
      setSuccessMessage("Dashboard functionality not connected. Please check the component setup.");
      setSuccessDialogOpen(true);
      return;
    }
    setSelectedViz(viz);
    setAddError(null);
    const hasDashboards = dashboards.length > 0;
    if (hasDashboards) {
      setAddMode("existing");
      setSelectedDashboardId(dashboards[0].id);
    } else {
      setAddMode("new");
      setSelectedDashboardId("");
    }
    setNewDashboardName(viz.title ? `${viz.title} Dashboard` : "New Dashboard");
    setNewDashboardDescription("");
    if (!hasDashboards && !onCreateDashboard) {
      setSuccessMessage("No dashboards available and dashboard creation is not configured.");
      setSuccessDialogOpen(true);
      return;
    }
    setAddDialogOpen(true);
  };

  const confirmAddToDashboard = async () => {
    if (!selectedViz) {
      setAddError("Select a visualization first.");
      return;
    }
    if (!onAddToDashboard) {
      setAddError("Dashboard functionality not connected.");
      return;
    }
    try {
      setAddLoading(true);
      setAddError(null);

      let dashboardId = selectedDashboardId;
      let dashboardName = "";

      if (addMode === "new") {
        if (!onCreateDashboard) {
          throw new Error("Creating dashboards is not supported in this environment.");
        }
        const name = (newDashboardName || `${selectedViz.title} Dashboard`).trim();
        const description = newDashboardDescription.trim() || undefined;
        const created = await onCreateDashboard(name, description);
        if (!created || !created.id) {
          throw new Error("Failed to create dashboard.");
        }
        dashboardId = created.id;
        dashboardName = created.name;
      } else {
        if (!dashboardId) {
          throw new Error("Please select a dashboard.");
        }
        const existing = dashboards.find((d) => d.id === dashboardId);
        dashboardName = existing?.name ?? "Dashboard";
      }

      await onAddToDashboard(selectedViz, dashboardId);
      setSuccessMessage(`Added "${selectedViz.title}" to "${dashboardName}".`);
      setSuccessDialogOpen(true);
      setAddDialogOpen(false);
    } catch (error) {
      console.error("ChartGallery: Failed to add visualization to dashboard:", error);
      setAddError(error instanceof Error ? error.message : "Failed to add visualization to dashboard.");
    } finally {
      setAddLoading(false);
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

  const handleTitleChange = useCallback((value: string) => {
    resetSaveState();
    setEditDraft((current) => (current ? { ...current, title: value } : current));
  }, [resetSaveState]);

  const handleDescriptionChange = useCallback((value: string) => {
    resetSaveState();
    setEditDraft((current) => (current ? { ...current, description: value } : current));
  }, [resetSaveState]);

  const handleChartTypeChange = useCallback((value: string) => {
    resetSaveState();
    const normalized = getPresetType(value);
    const preset = CHART_TYPE_PRESETS[normalized];
    const currentTitle = editDraft?.title ?? selectedViz?.title ?? value;

    const existingDataset =
      datasetInput.trim() ||
      (editDraft?.chart_config &&
        typeof editDraft.chart_config === "object" &&
        (editDraft.chart_config as Record<string, unknown>).datasetName &&
        typeof (editDraft.chart_config as Record<string, unknown>).datasetName === "string"
        ? String((editDraft.chart_config as Record<string, unknown>).datasetName)
        : "") ||
      selectedViz?.dataset_name ||
      "";

    const datasetKey =
      existingDataset.trim().length > 0 ? existingDataset.trim() : preset.defaultDataset;
    const sampleKey = SAMPLE_CHART_DATA[datasetKey] ? datasetKey : preset.defaultDataset;
    const sampleData = SAMPLE_CHART_DATA[sampleKey] ?? SAMPLE_CHART_DATA[preset.defaultDataset];
    const config = preset.buildConfig(currentTitle, datasetKey, sampleData);
    const code = preset.buildCode(value, datasetKey, config);

    setDatasetInput(datasetKey);
    setChartConfigText(JSON.stringify(config, null, 2));
    setCodeText(code);
    setChartConfigError(null);

    setEditDraft((current) => {
      const base = current ?? selectedViz;
      if (!base) return current;
      return {
        ...base,
        chart_type: value,
        dataset_name: datasetKey || null,
        chart_config: config,
      };
    });
  }, [datasetInput, editDraft, resetSaveState, selectedViz]);

  const handleDatasetChange = useCallback((value: string) => {
    resetSaveState();
    const trimmed = value.trim();
    setDatasetInput(value);
    const nextConfig: Record<string, unknown> =
      editDraft?.chart_config && typeof editDraft.chart_config === "object"
        ? { ...(editDraft.chart_config as Record<string, unknown>) }
        : {};

    if (trimmed) {
      nextConfig.datasetName = trimmed;
      nextConfig.dataset_name = trimmed;
      nextConfig.dataSource = trimmed;
      nextConfig.data_source = trimmed;
      nextConfig.dbtModel = nextConfig.dbtModel ?? trimmed;
      nextConfig.dbt_model = nextConfig.dbt_model ?? trimmed;
    } else {
      delete nextConfig.datasetName;
      delete nextConfig.dataset_name;
      delete nextConfig.dataSource;
      delete nextConfig.data_source;
    }

    setChartConfigText(JSON.stringify(nextConfig, null, 2));
    setChartConfigError(null);

    setEditDraft((current) => {
      if (!current) return current;
      return {
        ...current,
        dataset_name: trimmed || null,
        chart_config: nextConfig as EChartsOption,
      };
    });
  }, [editDraft, resetSaveState]);

  const handleChartConfigChange = useCallback((value: string) => {
    resetSaveState();
    setChartConfigText(value);
    if (!value.trim()) {
      setChartConfigError("Provide a valid JSON object to configure the chart.");
      return;
    }
    try {
      const parsed = JSON.parse(value);
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        setChartConfigError("Chart configuration must be a JSON object.");
        return;
      }
      const normalized = parsed as EChartsOption;
      setEditDraft((current) => (current ? { ...current, chart_config: normalized } : current));
      setChartConfigError(null);
    } catch (error) {
      setChartConfigError(error instanceof Error ? error.message : "Invalid JSON configuration.");
    }
  }, [resetSaveState]);

  const handleCodeChange = useCallback((value: string) => {
    resetSaveState();
    setCodeText(value);
    setEditDraft((current) => (current ? { ...current, code: value } : current));
  }, [resetSaveState]);

  const handleResetEdits = useCallback(() => {
    if (!selectedViz) return;
    resetSaveState();
    const baselineConfig = JSON.parse(JSON.stringify(originalConfigObject ?? {})) as EChartsOption;
    let baselineText = JSON.stringify(baselineConfig, null, 2);
    if (typeof selectedViz.chart_config === "string") {
      const raw = selectedViz.chart_config;
      try {
        const parsed = JSON.parse(raw);
        if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
          baselineText = JSON.stringify(parsed, null, 2);
        } else {
          baselineText = raw;
        }
      } catch {
        baselineText = raw;
      }
    }
    setEditDraft({
      ...selectedViz,
      chart_config: baselineConfig,
    });
    setChartConfigText(baselineText);
    setCodeText(selectedViz.code ?? "");
    setDatasetInput(selectedViz.dataset_name ?? "");
    setChartConfigError(null);
  }, [selectedViz, originalConfigObject, resetSaveState]);

  const handleSaveEdits = useCallback(async () => {
    if (!selectedViz || !editDraft) return;
    resetSaveState();

    let parsedConfig: Record<string, unknown>;
    try {
      parsedConfig = JSON.parse(chartConfigText || "{}");
      if (!parsedConfig || typeof parsedConfig !== "object" || Array.isArray(parsedConfig)) {
        throw new Error("Chart configuration must be a JSON object.");
      }
      setChartConfigError(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Invalid chart configuration.";
      setChartConfigError(message);
      setDetailsTab("edit");
      return;
    }

    const trimmedDataset = datasetInput.trim();
    const augmentedConfig: Record<string, unknown> = { ...(parsedConfig as Record<string, unknown>) };
    if (trimmedDataset) {
      augmentedConfig.datasetName = trimmedDataset;
      augmentedConfig.dataset_name = trimmedDataset;
      augmentedConfig.dataSource = trimmedDataset;
      augmentedConfig.data_source = trimmedDataset;
      if (augmentedConfig.dbtModel == null) {
        augmentedConfig.dbtModel = trimmedDataset;
      }
      if (augmentedConfig.dbt_model == null) {
        augmentedConfig.dbt_model = trimmedDataset;
      }
    } else {
      delete augmentedConfig.datasetName;
      delete augmentedConfig.dataset_name;
      delete augmentedConfig.dataSource;
      delete augmentedConfig.data_source;
    }

    const updatedVisualization: GeneratedVisualization = {
      ...selectedViz,
      ...editDraft,
      title: editDraft.title,
      description: editDraft.description,
      chart_type: editDraft.chart_type,
      chart_config: augmentedConfig as EChartsOption,
      code: codeText,
      dataset_name: trimmedDataset ? trimmedDataset : null,
    };

    setIsSaving(true);
    try {
      const result = onUpdateVisualization
        ? await onUpdateVisualization(updatedVisualization)
        : updatedVisualization;
      const resolved = result ?? updatedVisualization;
      setSelectedViz(resolved);
      setSaveSuccess(true);
      setDetailsTab("preview");
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : "Failed to save visualization.");
    } finally {
      setIsSaving(false);
    }
  }, [
    chartConfigText,
    codeText,
    datasetInput,
    editDraft,
    onUpdateVisualization,
    resetSaveState,
    selectedViz,
  ]);

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
                        <DialogTitle>{selectedDbtModel.name ?? selectedDbtKey ?? "dbt Model"}</DialogTitle>
                        <DialogDescription className="space-y-1">
                          {selectedDbtModel.description ? <p>{selectedDbtModel.description}</p> : null}
                          {selectedDbtModel.path ? (
                            <p className="text-xs text-muted-foreground">Path: {selectedDbtModel.path}</p>
                          ) : null}
                        </DialogDescription>
                      </DialogHeader>
                      <pre className="max-h-[360px] overflow-auto rounded-md bg-muted p-4 text-xs">
                        <code>{selectedDbtModel.sql ?? "// dbt SQL not provided"}</code>
                      </pre>
                    </DialogContent>
                  </Dialog>
                ) : null}
                <button
                  onClick={() => {
                    console.log('Button clicked, selectedViz:', selectedViz?.title);
                    if (selectedViz) {
                      handleAddToDashboardClick(selectedViz);
                    } else {
                      console.error('No selectedViz available');
                    }
                  }}
                  className="flex items-center space-x-2 bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md text-sm font-medium transition-colors"
                  title="Add to Dashboard"
                >
                  <Plus className="h-4 w-4" />
                  <span>Add to Dashboard</span>
                </button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Tabs
              value={detailsTab}
              onValueChange={(value) => setDetailsTab(value as DetailTab)}
              className="w-full"
            >
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
                      ? `View dbt model details for ${selectedDbtModel.name ?? selectedDbtKey ?? "dbt model"}`
                      : selectedDbtKey
                      ? `No dbt metadata registered for ${selectedDbtKey}`
                      : "Link a dbt model to this visualization to view details"
                  }
                >
                  dbt Model
                </TabsTrigger>
                <TabsTrigger value="edit">Edit</TabsTrigger>
              </TabsList>

              <TabsContent value="preview" className="space-y-4">
                <div className="aspect-video bg-muted rounded-md overflow-hidden">
                  {hasLiveConfig ? (
                    <DynamicChart
                      config={liveChartConfig}
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
                  <code>
                    {codeText && codeText.trim().length > 0
                      ? codeText
                      : selectedViz?.code ?? "# Code not available"}
                  </code>
                </pre>
              </TabsContent>

              <TabsContent value="config">
                <pre className="bg-muted p-4 rounded-md text-sm overflow-x-auto">
                  <code>
                    {chartConfigText && chartConfigText.trim().length > 0
                      ? chartConfigText
                      : "# Chart configuration not available"}
                  </code>
                </pre>
              </TabsContent>

              <TabsContent value="dbt">
                {selectedDbtModel ? (
                  <div className="space-y-3">
                    <div>
                      <h4 className="text-sm font-semibold">
                        {selectedDbtModel.name ?? selectedDbtKey ?? "dbt Model"}
                      </h4>
                      {selectedDbtModel.description ? (
                        <p className="text-xs text-muted-foreground">
                          {selectedDbtModel.description}
                        </p>
                      ) : null}
                      {selectedDbtModel.path ? (
                        <p className="text-xs text-muted-foreground">
                          Path: {selectedDbtModel.path}
                        </p>
                      ) : null}
                    </div>
                    <pre className="bg-muted p-4 rounded-md text-xs overflow-auto max-h-[360px]">
                      <code>{selectedDbtModel.sql ?? "// dbt SQL not provided"}</code>
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

              <TabsContent value="edit">
                {editDraft ? (
                  <div className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="viz-title">Title</Label>
                        <Input
                          id="viz-title"
                          value={editDraft.title}
                          onChange={(event) => handleTitleChange(event.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="viz-type">Chart Type</Label>
                        <Select
                          value={editDraft.chart_type || "auto"}
                          onValueChange={handleChartTypeChange}
                        >
                          <SelectTrigger id="viz-type">
                            <SelectValue placeholder="Select chart type" />
                          </SelectTrigger>
                          <SelectContent>
                            {CHART_TYPE_OPTIONS.map((option) => (
                              <SelectItem key={option} value={option}>
                                {option}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="viz-description">Description</Label>
                      <Textarea
                        id="viz-description"
                        value={editDraft.description ?? ""}
                        onChange={(event) => handleDescriptionChange(event.target.value)}
                        rows={3}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="viz-dataset">Dataset / dbt Model</Label>
                      <Input
                        id="viz-dataset"
                        placeholder="e.g. salesData"
                        value={datasetInput}
                        onChange={(event) => handleDatasetChange(event.target.value)}
                      />
                      <p className="text-xs text-muted-foreground">
                        Used for dataset selection, dbt model linking, and dashboard integration.
                      </p>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label htmlFor="viz-config">Chart Configuration (JSON)</Label>
                        {chartConfigError ? (
                          <span className="text-xs text-destructive">{chartConfigError}</span>
                        ) : null}
                      </div>
                      <Textarea
                        id="viz-config"
                        value={chartConfigText}
                        onChange={(event) => handleChartConfigChange(event.target.value)}
                        rows={14}
                        className="font-mono text-xs"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="viz-code">Generated Code</Label>
                      <Textarea
                        id="viz-code"
                        value={codeText}
                        onChange={(event) => handleCodeChange(event.target.value)}
                        rows={10}
                        className="font-mono text-xs"
                      />
                    </div>

                    <div className="flex flex-wrap items-center gap-3">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={handleResetEdits}
                        disabled={isSaving}
                      >
                        Reset
                      </Button>
                      <Button
                        type="button"
                        onClick={handleSaveEdits}
                        disabled={isSaving || Boolean(chartConfigError)}
                      >
                        {isSaving ? "Saving..." : "Save Changes"}
                      </Button>
                      {saveSuccess && (
                        <span className="text-xs text-green-600">Visualization updated.</span>
                      )}
                      {saveError && (
                        <span className="text-xs text-destructive">{saveError}</span>
                      )}
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Select a visualization to edit its configuration.
                  </p>
                )}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}

      {/* Add to Dashboard Dialog */}
      <Dialog open={addDialogOpen} onOpenChange={(open) => {
        setAddDialogOpen(open);
        if (!open) {
          setAddLoading(false);
          setAddError(null);
        }
      }}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Add to Dashboard</DialogTitle>
            <DialogDescription>
              Choose a dashboard to add <strong>{selectedViz?.title}</strong> or create a new one.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-sm font-medium">Destination</Label>
              <div className="mt-2 flex flex-col gap-2">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name="dashboard-mode"
                    value="existing"
                    checked={addMode === "existing"}
                    onChange={() => setAddMode("existing")}
                    disabled={!dashboards.length}
                  />
                  <span>Existing dashboard</span>
                  {!dashboards.length && <span className="text-xs text-muted-foreground">(none available)</span>}
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name="dashboard-mode"
                    value="new"
                    checked={addMode === "new"}
                    onChange={() => setAddMode("new")}
                    disabled={!onCreateDashboard}
                  />
                  <span>Create new dashboard</span>
                  {!onCreateDashboard && <span className="text-xs text-muted-foreground">(disabled)</span>}
                </label>
              </div>
            </div>

            {addMode === "existing" ? (
              <div className="space-y-2">
                <Label htmlFor="dashboard-select">Select dashboard</Label>
                <select
                  id="dashboard-select"
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  value={selectedDashboardId}
                  onChange={(event) => setSelectedDashboardId(event.target.value)}
                  disabled={!dashboards.length}
                >
                  {dashboards.map((dashboard) => (
                    <option key={dashboard.id} value={dashboard.id}>
                      {dashboard.name}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="space-y-1">
                  <Label htmlFor="new-dashboard-name">Dashboard name</Label>
                  <Input
                    id="new-dashboard-name"
                    value={newDashboardName}
                    onChange={(event) => setNewDashboardName(event.target.value)}
                    placeholder="FinOps Executive Dashboard"
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="new-dashboard-description">Description (optional)</Label>
                  <Textarea
                    id="new-dashboard-description"
                    value={newDashboardDescription}
                    onChange={(event) => setNewDashboardDescription(event.target.value)}
                    placeholder="Explain the purpose of this dashboard"
                    rows={3}
                  />
                </div>
              </div>
            )}

            {addError ? (
              <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {addError}
              </div>
            ) : null}
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <Button variant="outline" onClick={() => setAddDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={confirmAddToDashboard} disabled={addLoading || (addMode === "existing" && !selectedDashboardId && dashboards.length > 0)}>
              {addLoading ? "Adding..." : "Add to dashboard"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

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
