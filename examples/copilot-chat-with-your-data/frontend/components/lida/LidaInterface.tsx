"use client";

import { useState, useCallback, useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { FileUpload } from "./FileUpload";
import { DataSummary } from "./DataSummary";
import { VisualizationChat } from "./VisualizationChat";
import { ChartGallery } from "./ChartGallery";
import { DatasetSelector } from "./DatasetSelector";

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
}

export function LidaInterface() {
  const [activeTab, setActiveTab] = useState("upload");
  const [currentDataset, setCurrentDataset] = useState<string | null>(null);
  const [dataSummary, setDataSummary] = useState<DataSummaryData | null>(null);
  const [visualizations, setVisualizations] = useState<GeneratedVisualization[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentBackendInsights, setCurrentBackendInsights] = useState<string[]>([]);
  const [lastCacheKey, setLastCacheKey] = useState<string | null>(null);

  // Cache for insights based on query key
  const [insightsCache, setInsightsCache] = useState<Map<string, {
    insights: string[];
    timestamp: number;
    suggestions?: any[];
  }>>(new Map());

  const baseApiUrl = useMemo(() => {
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8004";
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
  }, []);

  const handleFileUploaded = useCallback((fileName: string, summary: DataSummaryData) => {
    setCurrentDataset(fileName);
    setDataSummary(summary);
    setActiveTab("explore");
  }, []);

  const handleVisualizationGenerated = useCallback((visualization: GeneratedVisualization) => {
    setVisualizations(prev => [visualization, ...prev]);
  }, []);

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
      const response = await fetch(`${baseApiUrl}/lida/visualize`, {
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
        const newViz: GeneratedVisualization = {
          id: Date.now().toString(),
          title: request.goal,
          description: result.visualizations[0].explanation || "",
          chart_type: request.chart_type || "auto",
          chart_config: result.visualizations[0].chart_config,
          code: result.visualizations[0].code || "",
          insights: result.insights || [],
          created_at: new Date().toISOString(),
        };

        handleVisualizationGenerated(newViz);
        return { final_visualization: newViz };
      }

      return {};
    } catch (error) {
      console.error("Error generating visualization:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [baseApiUrl, currentDataset, dataSummary, handleVisualizationGenerated, generateCacheKey, insightsCache, CACHE_EXPIRY_MS]);

  const handleChartSelected = useCallback((suggestion: any, config: any) => {
    // Generate final visualization from selected chart
    const newViz: GeneratedVisualization = {
      id: Date.now().toString(),
      title: suggestion.title || "Generated Visualization",
      description: suggestion.reasoning || "",
      chart_type: suggestion.chart_type,
      chart_config: config,
      code: `// ECharts configuration\nconst chartConfig = ${JSON.stringify(config, null, 2)};`,
      insights: currentBackendInsights.length > 0
        ? currentBackendInsights
        : [`Selected ${suggestion.chart_type} chart`, suggestion.best_for],
      created_at: new Date().toISOString(),
    };

    handleVisualizationGenerated(newViz);
    setActiveTab("gallery"); // Switch to gallery to show the generated chart
  }, [handleVisualizationGenerated, currentBackendInsights]);

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
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="upload">Data</TabsTrigger>
          <TabsTrigger value="explore" disabled={!canExplore}>
            Explore
          </TabsTrigger>
          <TabsTrigger value="visualize" disabled={!canExplore}>
            Visualize
          </TabsTrigger>
          <TabsTrigger value="gallery" disabled={visualizations.length === 0}>
            Gallery ({visualizations.length})
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
                  baseApiUrl={baseApiUrl}
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
                  baseApiUrl={baseApiUrl}
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
                      disabled={visualizations.length === 0}
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

        <TabsContent value="visualize" className="space-y-6">
          {dataSummary && (
            <VisualizationChat
              dataSummary={dataSummary}
              onVisualizationRequest={handleVisualizationRequest}
              onChartSelected={handleChartSelected}
              isLoading={isLoading}
              recentVisualizations={visualizations.slice(0, 3)}
              baseApiUrl={baseApiUrl}
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
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}