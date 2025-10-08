"use client";

import { useState, useCallback, useMemo, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "../ui/dialog";
import { Button } from "../ui/button";
import { FileUpload } from "./FileUpload";
import { DataSummary } from "./DataSummary";
import { VisualizationChat } from "./VisualizationChat";
import { ChartGallery } from "./ChartGallery";
import { DatasetSelector } from "./DatasetSelector";
import { SemanticModelEditor, SemanticModel as SemanticModelDefinition } from "./SemanticModelEditor";
import { DataLineageView } from "./DataLineageView";
import { DashboardGrid } from "@/components/dashboard/DashboardGrid";
import { Dashboard } from "@/types/dashboard";
import { Plus, Sparkles, CheckCircle, AlertCircle } from "lucide-react";
import { useAgUiAgent } from "@/components/ag-ui/AgUiProvider";

interface DataSummaryData {
  name: string;
  file_name: string;
  dataset_description: string;
  field_names: string[];
  file_size: number;
  file_type: string;
  num_rows: number;
  num_columns: number;
  sample_data: Record<string, any>[];
  statistical_summary: Record<string, any>;
  data_quality_score: number;
  focus_compliance?: {
    compliance_level: string;
    compliance_score: number;
    missing_fields: string[];
  };
}

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
  dbt_metadata?: DbtModelMetadata | null;
  echar_code?: string | null;
  semantic_model_id?: string | null;
}

interface DbtModelMetadata {
  id?: string;
  name?: string;
  description?: string;
  path?: string;
  sql?: string;
  aliases?: string[];
}

type SemanticModel = SemanticModelDefinition;

function pickDatasetKey(...candidates: Array<string | null | undefined>): string | undefined {
  for (const candidate of candidates) {
    if (typeof candidate !== "string") {
      continue;
    }
    const trimmed = candidate.trim();
    if (trimmed.length > 0) {
      return trimmed;
    }
  }
  return undefined;
}

function normalizeDbtKey(value?: string | null): string | undefined {
  if (typeof value !== "string") {
    return undefined;
  }
  const trimmed = value.trim();
  if (!trimmed) {
    return undefined;
  }
  return trimmed.toLowerCase().replace(/[\s.-]+/g, "_").replace(/\.csv$/, "");
}

function normaliseChartConfigForDataset(chartConfig: any, datasetKey?: string | null) {
  const source =
    chartConfig && typeof chartConfig === "object" && !Array.isArray(chartConfig)
      ? chartConfig
      : {};
  const normalized: Record<string, unknown> = { ...source };
  if (typeof datasetKey === "string" && datasetKey.trim().length > 0) {
    const trimmed = datasetKey.trim();
    normalized.dbt_model = trimmed;
    delete normalized.dbtModel;
    normalized.dataset_name = trimmed;
    delete normalized.datasetName;
    delete normalized.dataSource;
    delete normalized.data_source;
  }
  return normalized;
}

function coerceChartConfig(raw: unknown): any {
  if (!raw) {
    return undefined;
  }
  if (typeof raw === "string") {
    try {
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === "object") {
        return parsed;
      }
    } catch {
      return undefined;
    }
  }
  if (typeof raw === "object") {
    return raw;
  }
  return undefined;
}


export function LidaInterface() {
  const router = useRouter();
  const { sendDirectDatabaseCrud } = useAgUiAgent();
  const [activeTab, setActiveTab] = useState("upload");
  const [currentDataset, setCurrentDataset] = useState<string | null>(null);
  const [dataSummary, setDataSummary] = useState<DataSummaryData | null>(null);
  const [visualizations, setVisualizations] = useState<GeneratedVisualization[]>([]);
  const [dbtModels, setDbtModels] = useState<Record<string, DbtModelMetadata>>({});
  const [semanticModel, setSemanticModel] = useState<SemanticModel | null>(null);
  const [semanticModelLoading, setSemanticModelLoading] = useState(false);
  const [semanticModelError, setSemanticModelError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [currentBackendInsights, setCurrentBackendInsights] = useState<string[]>([]);
  const [lastCacheKey, setLastCacheKey] = useState<string | null>(null);

  // Dashboard state management
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [selectedDashboard, setSelectedDashboard] = useState<Dashboard | null>(null);

  // Dialog state management
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogType, setDialogType] = useState<'success' | 'error'>('success');
  const [dialogMessage, setDialogMessage] = useState('');


  // Cache for insights based on query key
  const [insightsCache, setInsightsCache] = useState<Map<string, {
    insights: string[];
    timestamp: number;
    suggestions?: any[];
  }>>(new Map());

  const apiCandidates = useMemo(() => {
    const env = process.env.NEXT_PUBLIC_API_URL;
    if (env) {
      return env
        .split(",")
        .map((url) => url.trim())
        .filter(Boolean);
    }
    return ["http://localhost:8004", "http://127.0.0.1:8004"];
  }, []);

  const fetchWithFallback = useCallback(
    async (path: string, init?: RequestInit): Promise<Response | null> => {
      let lastError: unknown = new Error("No API base URL reachable");
      for (const base of apiCandidates) {
        try {
          const response = await fetch(`${base}${path}`, init);
          if (!response.ok) {
            lastError = new Error(await response.text());
            continue;
          }
          return response;
        } catch (error) {
          lastError = error;
        }
      }
      console.warn("fetchWithFallback failed:", lastError);
      return null;
    },
    [apiCandidates],
  );

  const primaryApiUrl = apiCandidates[0] ?? "";

  useEffect(() => {
    const loadDbtModels = async () => {
      try {
        const response = await fetchWithFallback("/lida/dbt-models");
        if (!response || !response.ok) {
          return;
        }
        const models = await response.json();
        if (!Array.isArray(models)) {
          return;
        }
        const next: Record<string, DbtModelMetadata> = {};
        const register = (key?: string | null, metadata?: DbtModelMetadata) => {
          const normalized = normalizeDbtKey(key);
          if (!normalized || !metadata) {
            return;
          }
          next[normalized] = metadata;
        };
        models.forEach((entry: any) => {
          if (!entry) {
            return;
          }
          const metadata: DbtModelMetadata = {
            id: entry.id,
            name: entry.name,
            description: entry.description,
            path: entry.path,
            sql: entry.sql,
            aliases: Array.isArray(entry.aliases) ? entry.aliases : [],
          };
          register(metadata.id, metadata);
          metadata.aliases?.forEach((alias) => register(alias, metadata));
        });
        setDbtModels(next);
      } catch (error) {
        console.error("Failed to load dbt models:", error);
      }
    };
    loadDbtModels();
  }, [fetchWithFallback]);

  const resolveDbtMetadata = useCallback(
    (datasetKey?: string | null, fallback?: DbtModelMetadata | null) => {
      if (fallback && (fallback.id || fallback.sql || fallback.name)) {
        return fallback;
      }
      const normalized = normalizeDbtKey(datasetKey);
      if (!normalized) {
        return undefined;
      }
      return dbtModels[normalized];
    },
    [dbtModels],
  );

  const ensureSemanticModel = useCallback(
    async (datasetName: string, summary?: DataSummaryData | null) => {
      if (!datasetName) {
        setSemanticModel(null);
        return;
      }
      setSemanticModelLoading(true);
      setSemanticModelError(null);
      try {
        const response = await fetchWithFallback("/lida/semantic-models", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            dataset_name: datasetName,
            summary: summary ?? undefined,
          }),
        });
        if (!response || !response.ok) {
          throw new Error(response ? await response.text() : "Unable to reach semantic model service");
        }
        const model = await response.json();
        setSemanticModel(model);
      } catch (error) {
        setSemanticModelError(error instanceof Error ? error.message : String(error));
        setSemanticModel(null);
      } finally {
        setSemanticModelLoading(false);
      }
    },
    [fetchWithFallback],
  );

  const handleSemanticModelChange = useCallback(
    async (model: SemanticModel) => {
      setSemanticModel(model);
      if (!model.id) {
        return;
      }
      try {
        await fetchWithFallback(`/lida/semantic-models/${model.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: model.name,
            description: model.description,
            definition: model.definition,
          }),
        });
      } catch (error) {
        console.error("Failed to update semantic model:", error);
      }
    },
    [fetchWithFallback],
  );

  useEffect(() => {
    const loadPersistedVisualizations = async () => {
      try {
        const data = await sendDirectDatabaseCrud({
          operation: 'read',
          resource: 'lida_visualizations',
          content: 'Load persisted visualizations',
        });
        if (Array.isArray(data)) {
          const normalized = (data as GeneratedVisualization[]).map((viz) => {
            const parsedConfig =
              coerceChartConfig(viz.chart_config) ??
              coerceChartConfig(viz.echar_code) ??
              coerceChartConfig((viz as Record<string, unknown>)?.["echarts_config"]);
            const datasetKey = pickDatasetKey(
              viz.dataset_name,
              parsedConfig?.dbtModel,
              parsedConfig?.dbt_model,
              parsedConfig?.datasetName,
              parsedConfig?.dataset_name,
              parsedConfig?.dataSource,
              parsedConfig?.data_source,
            );
            const metadata = resolveDbtMetadata(datasetKey, viz.dbt_metadata ?? null);
            const normalizedConfig = normaliseChartConfigForDataset(parsedConfig, datasetKey);
            return {
              ...viz,
              chart_config: normalizedConfig,
              dataset_name: datasetKey ?? viz.dataset_name ?? null,
              echar_code: viz.echar_code ?? (parsedConfig ? JSON.stringify(parsedConfig) : null),
              dbt_metadata: metadata ?? null,
            };
          });
          setVisualizations(normalized);
        }
      } catch (error) {
        console.error("Error loading persisted visualizations:", error);
      }
    };
    loadPersistedVisualizations();
  }, [sendDirectDatabaseCrud]);

  // Load dashboards from API on component mount
  useEffect(() => {
    const loadDashboards = async () => {
      try {
        const response = await fetch('/api/dashboards');
        if (response.ok) {
          const apiDashboards = await response.json();
          // Convert API dashboard format to unified Dashboard format
          const lidaDashboards = apiDashboards.map((apiDash: any) => ({
            id: apiDash.id,
            name: apiDash.name,
            description: apiDash.description,
            layout_config: apiDash.layout_config || {
              grid: { cols: 4, rows: 'auto' },
              items: []
            },
            metadata: apiDash.metadata,
            is_public: apiDash.is_public,
            created_by: apiDash.created_by,
            created_at: apiDash.created_at,
            updated_at: apiDash.updated_at
          }));
          setDashboards(lidaDashboards);
        }
      } catch (error) {
        console.error('Failed to load dashboards:', error);
      }
    };

    loadDashboards();
  }, []);

  // Generate cache key for insights
  const generateCacheKey = useCallback((dataset: string, goal: string, persona: string = "default") => {
    return `${dataset}:${goal.toLowerCase().trim()}:${persona}`;
  }, []);

  // Cache expiration time (10 minutes)
  const CACHE_EXPIRY_MS = 10 * 60 * 1000;

  const handleDatasetSelected = useCallback((datasetName: string, summary: DataSummaryData) => {
    setCurrentDataset(datasetName);
    setDataSummary(summary);
    setActiveTab("explore");
    ensureSemanticModel(datasetName, summary);
  }, [ensureSemanticModel]);

  const handleFileUploaded = useCallback((fileName: string, summary: DataSummaryData) => {
    setCurrentDataset(fileName);
    setDataSummary(summary);
    setActiveTab("explore");
    ensureSemanticModel(fileName, summary);
  }, [ensureSemanticModel]);

  const persistVisualization = useCallback(async (visualization: GeneratedVisualization): Promise<GeneratedVisualization> => {
    const resolvedDataset =
      visualization.dataset_name ??
      visualization.chart_config?.dbtModel ??
      visualization.chart_config?.dbt_model ??
      visualization.chart_config?.datasetName ??
      visualization.chart_config?.dataset_name ??
      visualization.chart_config?.dataSource ??
      visualization.chart_config?.data_source ??
      null;

    const datasetKey = pickDatasetKey(
      resolvedDataset,
      visualization.dataset_name,
      visualization.chart_config?.dbtModel,
      visualization.chart_config?.dbt_model,
      visualization.chart_config?.datasetName,
      visualization.chart_config?.dataset_name,
      visualization.chart_config?.dataSource,
      visualization.chart_config?.data_source,
    );
    const normalizedConfig = normaliseChartConfigForDataset(visualization.chart_config, datasetKey);
    const resolvedDbtMetadata = resolveDbtMetadata(datasetKey, visualization.dbt_metadata ?? null) ?? null;
    const echarCode =
      visualization.echar_code ??
      (typeof visualization.chart_config === "string"
        ? visualization.chart_config
        : JSON.stringify(normalizedConfig));
    const semanticModelId = visualization.semantic_model_id ?? semanticModel?.id ?? null;

    const fallbackVisualization: GeneratedVisualization = {
      ...visualization,
      chart_config: normalizedConfig,
      dataset_name: datasetKey ?? visualization.dataset_name ?? null,
      dbt_metadata: resolvedDbtMetadata,
      echar_code: echarCode,
      semantic_model_id: semanticModelId,
    };
    setVisualizations((prev) => [fallbackVisualization, ...prev.filter((viz) => viz.id !== visualization.id)]);

    try {
      const payload = {
        ...visualization,
        chart_config: normalizedConfig,
        dataset_name: datasetKey ?? visualization.dataset_name ?? null,
        dbt_metadata: resolvedDbtMetadata,
        echar_code: echarCode,
        semantic_model_id: semanticModelId,
      };
      const saved = await sendDirectDatabaseCrud({
        operation: 'create',
        resource: 'lida_visualizations',
        payload,
        content: `Persist visualization "${visualization.title}"`,
      });
      if (saved && typeof saved === 'object' && 'id' in saved) {
        const savedVisualization = saved as GeneratedVisualization;
        const savedDatasetKey = pickDatasetKey(
          savedVisualization.dataset_name,
          savedVisualization.chart_config?.dbtModel,
          savedVisualization.chart_config?.dbt_model,
          savedVisualization.chart_config?.datasetName,
          savedVisualization.chart_config?.dataset_name,
          savedVisualization.chart_config?.dataSource,
          savedVisualization.chart_config?.data_source,
          datasetKey,
          );
        const savedDbtMetadata = resolveDbtMetadata(savedDatasetKey, savedVisualization.dbt_metadata ?? resolvedDbtMetadata) ?? null;
        const savedChartConfig =
          coerceChartConfig(savedVisualization.chart_config) ??
          coerceChartConfig(savedVisualization.echar_code) ??
          normalizedConfig;
        const normalizedSaved: GeneratedVisualization = {
          ...savedVisualization,
          chart_config: normaliseChartConfigForDataset(savedChartConfig, savedDatasetKey),
          dataset_name: savedDatasetKey ?? savedVisualization.dataset_name ?? null,
          semantic_model_id: savedVisualization.semantic_model_id ?? semanticModelId,
          dbt_metadata: savedDbtMetadata,
          echar_code:
            savedVisualization.echar_code ??
            (typeof savedVisualization.chart_config === "string"
              ? savedVisualization.chart_config
              : JSON.stringify(savedChartConfig)),
        };
        setVisualizations((prev) => [normalizedSaved, ...prev.filter((viz) => viz.id !== normalizedSaved.id)]);
        return normalizedSaved;
      }
    } catch (error) {
      console.error("Error persisting visualization:", error);
    }
    return fallbackVisualization;
  }, [resolveDbtMetadata, semanticModel, sendDirectDatabaseCrud]);

  const handleVisualizationGenerated = useCallback(
    async (visualization: GeneratedVisualization) => {
      await persistVisualization(visualization);
    },
    [persistVisualization],
  );

  const handleDeleteVisualization = useCallback(
    async (visualization: GeneratedVisualization) => {
      if (!visualization.id) {
        return;
      }

      const previousVisualizations = visualizations;

      setVisualizations((prev) => prev.filter((item) => item.id !== visualization.id));

      const restoreVisualization = () => {
        setVisualizations((current) => {
          if (current.some((item) => item.id === visualization.id)) {
            return current;
          }
          const next = [...current];
          const originalIndex = previousVisualizations.findIndex((item) => item.id === visualization.id);
          const insertIndex = originalIndex >= 0 && originalIndex <= next.length ? originalIndex : next.length;
          next.splice(insertIndex, 0, visualization);
          return next;
        });
      };

      try {
        await sendDirectDatabaseCrud({
          operation: 'delete',
          resource: 'lida_visualizations',
          record_id: visualization.id,
          content: `Delete visualization "${visualization.title}"`,
        });
      } catch (error) {
        console.error("Error deleting visualization:", error);
        restoreVisualization();
      }
    },
    [sendDirectDatabaseCrud, visualizations],
  );

  const handleVisualizationRequest = useCallback(async (request: {
    goal: string;
    chart_type?: string;
    persona?: string;
  }): Promise<{ suggestions?: any[]; final_visualization?: any }> => {
    if (!currentDataset || !dataSummary) return {};

    const cacheKey = generateCacheKey(currentDataset, request.goal, request.persona || "default");
    const now = Date.now();

    // Check cache first
    const cached = insightsCache.get(cacheKey);
    if (cached && (now - cached.timestamp) < CACHE_EXPIRY_MS) {
      console.log(`Using cached insights for key: ${cacheKey}`);
      setCurrentBackendInsights(cached.insights);
      setLastCacheKey(cacheKey);
      setIsLoading(false);
      if (cached.suggestions) {
        return { suggestions: cached.suggestions };
      }
    }

    setIsLoading(true);
    // Reset previous insights only if not using cache
    if (!cached) {
      setCurrentBackendInsights([]);
    }

    try {
      const response = await fetchWithFallback("/lida/visualize", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          dataset_name: currentDataset,
          goal: request.goal,
          chart_type: request.chart_type,
          persona: request.persona || "default",
          summary: dataSummary,
          user_id: "web_user",
        }),
      });

      if (!response) {
        throw new Error("Unable to reach visualization service");
      }

      if (!response.ok) {
        throw new Error(`Failed to generate visualization: ${response.statusText}`);
      }

      const result = await response.json();

      // Store backend insights for use when chart is selected
      if (result.insights) {
        setCurrentBackendInsights(result.insights);

        // Cache the results
        const cacheEntry = {
          insights: result.insights,
          timestamp: now,
          suggestions: result.suggestions || undefined
        };

        setInsightsCache(prev => {
          const newCache = new Map(prev);
          newCache.set(cacheKey, cacheEntry);

          // Clean up expired entries to prevent memory leaks
          for (const [key, value] of newCache.entries()) {
            if (now - value.timestamp > CACHE_EXPIRY_MS) {
              newCache.delete(key);
            }
          }

          return newCache;
        });

        console.log(`Cached insights for key: ${cacheKey} (${result.insights.length} insights)`);
      }

      // Return suggestions for user selection
      if (result.suggestions && result.suggestions.length > 0) {
        return { suggestions: result.suggestions };
      }

      // Fallback: if no suggestions, handle as direct visualization
      if (result.visualizations && result.visualizations.length > 0) {
        const initialConfig = result.visualizations[0]?.chart_config;
        const datasetKey = pickDatasetKey(
          result.visualizations[0]?.dataset_name,
          initialConfig?.dbtModel,
          initialConfig?.dbt_model,
          initialConfig?.datasetName,
          initialConfig?.dataset_name,
          initialConfig?.dataSource,
          initialConfig?.data_source,
          currentDataset,
          dataSummary?.file_name,
          dataSummary?.name,
        );
        const normalizedConfig = normaliseChartConfigForDataset(initialConfig, datasetKey);
        const dbtMetadata = resolveDbtMetadata(datasetKey, result.visualizations[0]?.dbt_metadata ?? null) ?? null;
        const newViz: GeneratedVisualization = {
          id: `viz-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          title: request.goal,
          description: result.visualizations[0].explanation || "",
          chart_type: request.chart_type || "auto",
          chart_config: normalizedConfig,
          code: result.visualizations[0].code || "",
          insights: result.insights || [],
          created_at: new Date().toISOString(),
          dataset_name: datasetKey ?? null,
          dbt_metadata: dbtMetadata,
          echar_code: JSON.stringify(normalizedConfig),
        };

        const saved = await persistVisualization(newViz);
        return { final_visualization: saved };
      }

      return {};
    } catch (error) {
      console.error("Error generating visualization:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [currentDataset, dataSummary, generateCacheKey, insightsCache, CACHE_EXPIRY_MS, fetchWithFallback, persistVisualization, resolveDbtMetadata]);

  const handleChartSelected = useCallback((suggestion: any, config: any) => {
    // Generate final visualization from selected chart
    const datasetKey = pickDatasetKey(
      suggestion?.dataset_name,
      config?.dbtModel,
      config?.dbt_model,
      config?.datasetName,
      config?.dataset_name,
      config?.dataSource,
      config?.data_source,
      currentDataset,
      dataSummary?.file_name,
      dataSummary?.name,
    );
    const normalizedConfig = normaliseChartConfigForDataset(config, datasetKey);
    const dbtMetadata = resolveDbtMetadata(datasetKey, suggestion?.dbt_metadata ?? null) ?? null;
    const newViz: GeneratedVisualization = {
      id: `viz-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      title: suggestion.title || "Generated Visualization",
      description: suggestion.reasoning || "",
      chart_type: suggestion.chart_type,
      chart_config: normalizedConfig,
      code: `// ECharts configuration\nconst chartConfig = ${JSON.stringify(config, null, 2)};`,
      insights: currentBackendInsights.length > 0
        ? currentBackendInsights
        : [`Selected ${suggestion.chart_type} chart`, suggestion.best_for],
      created_at: new Date().toISOString(),
      dataset_name: datasetKey ?? null,
      dbt_metadata: dbtMetadata,
      echar_code: JSON.stringify(normalizedConfig),
    };

    persistVisualization(newViz).catch((error) => {
      console.error("Failed to persist visualization from suggestion:", error);
    });
    setActiveTab("gallery"); // Switch to gallery to show the generated chart
  }, [persistVisualization, currentBackendInsights, currentDataset, dataSummary, resolveDbtMetadata]);

  // Dashboard management handlers
  const handleCreateDashboard = useCallback(async (name: string, description?: string) => {
    try {
      const response = await fetch('/api/dashboards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          description: description || undefined,
          layout_config: {
            grid: { cols: 4, rows: 'auto' },
            items: []
          },
          metadata: { created_from: 'lida' }
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create dashboard');
      }

      const apiDashboard = await response.json();

      // Convert to LIDA dashboard format
      const newDashboard: Dashboard = {
        id: apiDashboard.id,
        name: apiDashboard.name,
        description: apiDashboard.description,
        layout_config: apiDashboard.layout_config || {
          grid: { cols: 4, rows: 'auto' },
          items: []
        },
        metadata: apiDashboard.metadata,
        created_at: apiDashboard.created_at,
        updated_at: apiDashboard.updated_at,
      };

      setDashboards(prev => [newDashboard, ...prev]);
      setSelectedDashboard(newDashboard);
      return newDashboard;
    } catch (error) {
      console.error('Failed to create dashboard:', error);
      // Fallback to local creation if API fails
      const newDashboard: Dashboard = {
        id: `dashboard-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        name,
        description,
        layout_config: {
          grid: { cols: 4, rows: 'auto' },
          items: []
        },
        metadata: { created_from: 'lida' },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      setDashboards(prev => [newDashboard, ...prev]);
      setSelectedDashboard(newDashboard);
      return newDashboard;
    }
  }, []);

  const handleAddToDashboard = useCallback(async (visualization: GeneratedVisualization, dashboardId?: string) => {
    console.log('handleAddToDashboard called with:', { visualization: visualization.title, dashboardId, selectedDashboard: selectedDashboard?.name });

    let targetDashboard = selectedDashboard;

    // If no dashboard is selected or specified, create a default one
    if (!targetDashboard && !dashboardId) {
      console.log('Creating new dashboard');
      try {
        targetDashboard = await handleCreateDashboard("My Dashboard", "Dashboard created from LIDA visualizations");
        console.log('New dashboard created:', targetDashboard);
      } catch (error) {
        console.error('Failed to create dashboard:', error);
        setDialogType('error');
        setDialogMessage('Failed to create dashboard. Please try again.');
        setDialogOpen(true);
        return;
      }
    } else if (dashboardId) {
      targetDashboard = dashboards.find(d => d.id === dashboardId) || null;
    }

    if (!targetDashboard) {
      console.error('No target dashboard available');
      setDialogType('error');
      setDialogMessage('No dashboard available. Please create a dashboard first.');
      setDialogOpen(true);
      return;
    }

    console.log('Target dashboard:', targetDashboard);

    // Check if visualization already exists in dashboard
    const vizExists = targetDashboard.layout_config?.items?.some((item: any) =>
      item.config?.lida_visualization_id === visualization.id
    ) || false;
    if (vizExists) {
      console.log("Visualization already exists in dashboard");
      setDialogType('error');
      setDialogMessage('This visualization is already in the dashboard!');
      setDialogOpen(true);
      return;
    }

    // Convert LIDA visualization to dashboard item format
    console.log('Converting LIDA visualization to dashboard item format');

    // Map LIDA chart types to dashboard chart types
    const mapChartType = (lidaChartType: string): "area" | "bar" | "donut" => {
      switch (lidaChartType.toLowerCase()) {
        case 'line':
        case 'area':
          return 'area';
        case 'pie':
        case 'donut':
          return 'donut';
        case 'bar':
        case 'column':
        default:
          return 'bar';
      }
    };

    const newDashboardItem = {
      id: `item-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type: "chart" as const,
      chartType: mapChartType(visualization.chart_type),
      title: visualization.title,
      description: visualization.description,
      span: "col-span-1 md:col-span-2",
      position: { row: (targetDashboard.layout_config?.items?.length || 0) + 1 },
      config: {
        echarts_config: visualization.chart_config,
        insights: visualization.insights,
        code: visualization.code,
        lida_visualization_id: visualization.id
      }
    };

    try {
      // Get current dashboard layout_config from database or create new one
      console.log('Fetching current dashboard from database');
      const dashboardResponse = await fetch(`/api/dashboards/${targetDashboard.id}`);
      if (!dashboardResponse.ok) {
        throw new Error('Failed to fetch current dashboard');
      }
      const currentDashboard = await dashboardResponse.json();

      // Update the layout_config with new item
      const updatedLayoutConfig = {
        grid: currentDashboard.layout_config?.grid || { cols: 4, rows: "auto" },
        items: [
          ...(currentDashboard.layout_config?.items || []),
          newDashboardItem
        ]
      };

      console.log('Updating dashboard in database with new visualization');
      // Update dashboard in database
      const updateResponse = await fetch(`/api/dashboards/${targetDashboard.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          layout_config: updatedLayoutConfig
        })
      });

      if (!updateResponse.ok) {
        throw new Error('Failed to update dashboard in database');
      }

      const updatedDashboard = await updateResponse.json();
      console.log('Dashboard updated successfully in database');

      // Update local state to reflect the database changes
      setDashboards(prev => prev.map(dashboard =>
        dashboard.id === targetDashboard.id
          ? {
              ...dashboard,
              layout_config: updatedLayoutConfig,
              updated_at: updatedDashboard.updated_at,
            }
          : dashboard
      ));

      // Update selected dashboard if it's the target
      if (selectedDashboard?.id === targetDashboard.id) {
        setSelectedDashboard(prev => prev ? {
          ...prev,
          layout_config: updatedLayoutConfig,
          updated_at: updatedDashboard.updated_at,
        } : null);
      }

      console.log(`Successfully added "${visualization.title}" to dashboard "${targetDashboard.name}"`);

      // Show success feedback and navigate to dashboard edit page
      setDialogType('success');
      setDialogMessage(`Successfully added "${visualization.title}" to dashboard "${targetDashboard.name}"!`);
      setDialogOpen(true);
      setTimeout(() => {
        // Navigate to the dashboard page in edit mode
        router.push(`/dashboard/${targetDashboard.id}?mode=edit`);
      }, 1500);

    } catch (error) {
      console.error('Failed to add visualization to dashboard:', error);
      setDialogType('error');
      setDialogMessage('Failed to add visualization to dashboard. Please try again.');
      setDialogOpen(true);
    }
  }, [selectedDashboard, dashboards, handleCreateDashboard]);

  // Wrapper function for button onClick handler
  const handleCreateNewDashboard = async () => {
    try {
      await handleCreateDashboard("New Dashboard", "Dashboard created manually");
    } catch (error) {
      console.error('Failed to create new dashboard:', error);
    }
  };

  // Dashboard deletion handler
  const handleDeleteDashboard = async (dashboard: Dashboard) => {
    try {
      const response = await fetch(`/api/dashboards/${dashboard.id}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Failed to delete dashboard");
      }

      setDashboards(dashboards.filter(d => d.id !== dashboard.id));

      // Clear selected dashboard if it was deleted
      if (selectedDashboard?.id === dashboard.id) {
        setSelectedDashboard(null);
      }
    } catch (err) {
      console.error("Failed to delete dashboard:", err);
      setDialogType('error');
      setDialogMessage('Failed to delete dashboard. Please try again.');
      setDialogOpen(true);
    }
  };

  const canExplore = currentDataset && dataSummary;

  return (
    <div className="container mx-auto px-4 py-6 max-w-7xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-foreground mb-2">
          LIDA - Automatic Visualization Generation
        </h1>
        <p className="text-muted-foreground">
          Upload your data and generate insightful visualizations using natural language
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="upload">Data</TabsTrigger>
          <TabsTrigger value="explore" disabled={!canExplore}>
            Explore
          </TabsTrigger>
          <TabsTrigger value="visualize" disabled={!canExplore}>
            Visualize
          </TabsTrigger>
          <TabsTrigger value="gallery">
            Gallery ({visualizations.length})
          </TabsTrigger>
          <TabsTrigger value="dashboard">
            Dashboards ({dashboards.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="upload" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Upload Dataset</CardTitle>
                <CardDescription>
                  Upload CSV, Excel, or JSON files for analysis
                </CardDescription>
              </CardHeader>
              <CardContent>
                <FileUpload
                  onFileUploaded={handleFileUploaded}
                  baseApiUrl={primaryApiUrl}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Sample Datasets</CardTitle>
                <CardDescription>
                  Choose from FOCUS-compliant sample datasets
                </CardDescription>
              </CardHeader>
              <CardContent>
                <DatasetSelector
                  onDatasetSelected={handleDatasetSelected}
                  baseApiUrl={primaryApiUrl}
                />
              </CardContent>
            </Card>
          </div>

          {dataSummary && (
            <Card>
              <CardHeader>
                <CardTitle>Dataset Summary</CardTitle>
                <CardDescription>
                  Overview of your selected dataset
                </CardDescription>
              </CardHeader>
              <CardContent>
                <DataSummary summary={dataSummary} />
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="explore" className="space-y-6">
          {currentDataset ? (
            <Tabs defaultValue="semantic-model" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="semantic-model">Semantic Model</TabsTrigger>
                <TabsTrigger value="lineage">Data Lineage</TabsTrigger>
                <TabsTrigger value="dataset-info">Dataset Info</TabsTrigger>
              </TabsList>

              <TabsContent value="semantic-model" className="space-y-4">
                <SemanticModelEditor
                  semanticModel={semanticModel}
                  loading={semanticModelLoading}
                  error={semanticModelError}
                  onRetry={
                    currentDataset
                      ? () => ensureSemanticModel(currentDataset, dataSummary)
                      : undefined
                  }
                  onModelChange={handleSemanticModelChange}
                />
              </TabsContent>

              <TabsContent value="lineage" className="space-y-4">
                <DataLineageView modelName={currentDataset} />
              </TabsContent>

              <TabsContent value="dataset-info" className="space-y-4">
                {dataSummary && (
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-2">
                      <Card>
                        <CardHeader>
                          <CardTitle>Dataset Overview</CardTitle>
                          <CardDescription>
                            Detailed information about {currentDataset}
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <DataSummary summary={dataSummary} detailed />
                        </CardContent>
                      </Card>
                    </div>

                    <div className="space-y-4">
                      <Card>
                        <CardHeader>
                          <CardTitle>Quick Actions</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2">
                          <button
                            onClick={() => setActiveTab("visualize")}
                            className="w-full bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md text-sm font-medium transition-colors"
                          >
                            Start Visualizing
                          </button>
                          <button
                            onClick={() => setActiveTab("gallery")}
                            className="w-full bg-secondary text-secondary-foreground hover:bg-secondary/80 px-4 py-2 rounded-md text-sm font-medium transition-colors"
                          >
                            View Gallery
                          </button>
                        </CardContent>
                      </Card>

                      {dataSummary.focus_compliance && (
                        <Card>
                          <CardHeader>
                            <CardTitle>FOCUS Compliance</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="space-y-2">
                              <div className="flex justify-between">
                                <span className="text-sm">Level:</span>
                                <span className="text-sm font-medium capitalize">
                                  {dataSummary.focus_compliance.compliance_level.replace("_", " ")}
                                </span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-sm">Score:</span>
                                <span className="text-sm font-medium">
                                  {(dataSummary.focus_compliance.compliance_score * 100).toFixed(1)}%
                                </span>
                              </div>
                              {dataSummary.focus_compliance.missing_fields.length > 0 && (
                                <div className="pt-2">
                                  <span className="text-sm text-muted-foreground">
                                    Missing fields: {dataSummary.focus_compliance.missing_fields.length}
                                  </span>
                                </div>
                              )}
                            </div>
                          </CardContent>
                        </Card>
                      )}
                    </div>
                  </div>
                )}
              </TabsContent>
            </Tabs>
          ) : (
            <Card>
              <CardContent className="p-6">
                <div className="text-center text-muted-foreground">
                  Please select a dataset to explore its semantic model
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="visualize" className="space-y-6">
          {dataSummary && (
            <VisualizationChat
              dataSummary={dataSummary}
              onVisualizationRequest={handleVisualizationRequest}
              onChartSelected={handleChartSelected}
              isLoading={isLoading}
              recentVisualizations={visualizations.slice(0, 3)}
              baseApiUrl={primaryApiUrl}
              userId="web_user"
              datasetName={currentDataset || undefined}
            />
          )}
        </TabsContent>

        <TabsContent value="gallery" className="space-y-6">
          <ChartGallery
            visualizations={visualizations}
            onVisualizationSelect={(viz) => {
              // Handle visualization selection for editing or viewing
              console.log("Selected visualization:", viz);
            }}
            onAddToDashboard={handleAddToDashboard}
            onDeleteVisualization={handleDeleteVisualization}
          />
        </TabsContent>

        <TabsContent value="dashboard" className="space-y-6">
          <DashboardGrid
            dashboards={dashboards}
            loading={false}
            error={null}
            onCreateDashboard={handleCreateNewDashboard}
            onDeleteDashboard={handleDeleteDashboard}
            showSearch={false}
            showBrowseTemplates={false}
          />
        </TabsContent>
      </Tabs>

      {/* Success/Error Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <div className="flex items-center space-x-2">
              {dialogType === 'success' ? (
                <CheckCircle className="h-6 w-6 text-green-600" />
              ) : (
                <AlertCircle className="h-6 w-6 text-red-600" />
              )}
              <DialogTitle className={dialogType === 'success' ? 'text-green-800' : 'text-red-800'}>
                {dialogType === 'success' ? 'Success!' : 'Already Added'}
              </DialogTitle>
            </div>
            <DialogDescription className="text-left pt-2">
              {dialogMessage}
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end pt-4">
            <Button
              onClick={() => setDialogOpen(false)}
              className={dialogType === 'success'
                ? 'bg-green-600 hover:bg-green-700 text-white'
                : 'bg-red-600 hover:bg-red-700 text-white'
              }
            >
              OK
            </Button>
          </div>
        </DialogContent>
      </Dialog>

    </div>
  );
}
