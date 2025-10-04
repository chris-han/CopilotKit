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

  const baseApiUrl = useMemo(() => {
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8004";
  }, []);

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
  }) => {
    if (!currentDataset || !dataSummary) return;

    setIsLoading(true);
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
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to generate visualization: ${response.statusText}`);
      }

      const result = await response.json();

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
      }
    } catch (error) {
      console.error("Error generating visualization:", error);
    } finally {
      setIsLoading(false);
    }
  }, [baseApiUrl, currentDataset, dataSummary, handleVisualizationGenerated]);

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
              isLoading={isLoading}
              recentVisualizations={visualizations.slice(0, 3)}
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