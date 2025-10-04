"use client";

import { useState, useEffect, useCallback } from "react";
import { Database, Download, Shield, TrendingUp, AlertCircle, CheckCircle2 } from "lucide-react";

interface SampleDataset {
  name: string;
  description: string;
  rows: number;
  compliance_score: number;
  dataset_type: string;
  service_count: number;
  account_count: number;
  region_count: number;
  data_quality_score: number;
  optimization_opportunities_count: number;
  anomaly_candidates_count: number;
}

interface DatasetSelectorProps {
  onDatasetSelected: (datasetName: string, summary: any) => void;
  baseApiUrl: string;
}

export function DatasetSelector({ onDatasetSelected, baseApiUrl }: DatasetSelectorProps) {
  const [datasets, setDatasets] = useState<SampleDataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);
  const [processingDataset, setProcessingDataset] = useState<string | null>(null);

  useEffect(() => {
    loadSampleDatasets();
  }, []);

  const loadSampleDatasets = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${baseApiUrl}/finops-web/datasets`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to load datasets: ${response.statusText}`);
      }

      const result = await response.json();
      setDatasets(result.datasets || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load datasets");
    } finally {
      setLoading(false);
    }
  }, [baseApiUrl]);

  const handleDatasetSelect = useCallback(async (datasetName: string) => {
    try {
      setProcessingDataset(datasetName);
      setError(null);

      const response = await fetch(`${baseApiUrl}/finops-web/select-dataset`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: "web_user",
          dataset_name: datasetName,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to select dataset: ${response.statusText}`);
      }

      const result = await response.json();

      if (result.dataset && result.preview) {
        // Transform the backend response to match the expected summary format
        const summary = {
          name: result.dataset.name,
          file_name: datasetName,
          dataset_description: result.dataset.description,
          field_names: result.preview.columns || [],
          file_size: 0, // Not available from backend
          file_type: "focus_sample",
          num_rows: result.dataset.rows,
          num_columns: result.preview.columns?.length || 0,
          sample_data: result.preview.sample_records || [],
          statistical_summary: result.preview.statistics || {},
          data_quality_score: result.dataset.data_quality_score,
          focus_compliance: {
            compliance_level: result.dataset.compliance_score >= 0.8 ? "full_compliance" :
                              result.dataset.compliance_score >= 0.5 ? "partial_compliance" : "non_compliant",
            compliance_score: result.dataset.compliance_score,
            missing_fields: [],
          },
        };

        setSelectedDataset(datasetName);
        onDatasetSelected(datasetName, summary);
      } else {
        throw new Error("Invalid response from server");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to select dataset");
    } finally {
      setProcessingDataset(null);
    }
  }, [baseApiUrl, onDatasetSelected]);

  const getComplianceColor = (score: number) => {
    if (score >= 0.8) return "text-green-600";
    if (score >= 0.5) return "text-yellow-600";
    return "text-red-600";
  };

  const getQualityColor = (score: number) => {
    if (score >= 0.8) return "text-green-600";
    if (score >= 0.6) return "text-yellow-600";
    return "text-red-600";
  };

  const getDatasetTypeLabel = (type: string) => {
    const labels = {
      focus_sample: "FOCUS Sample",
      generated_sample: "Generated",
      uploaded_csv: "CSV Upload",
      production_data: "Production",
    };
    return labels[type as keyof typeof labels] || type;
  };

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="border rounded-lg p-4 animate-pulse">
            <div className="h-4 bg-muted rounded w-3/4 mb-2"></div>
            <div className="h-3 bg-muted rounded w-full mb-2"></div>
            <div className="flex space-x-4">
              <div className="h-3 bg-muted rounded w-16"></div>
              <div className="h-3 bg-muted rounded w-16"></div>
              <div className="h-3 bg-muted rounded w-16"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center space-x-2 text-destructive bg-destructive/10 border border-destructive/20 rounded-md p-3">
        <AlertCircle className="h-4 w-4 flex-shrink-0" />
        <div className="flex-1">
          <span className="text-sm">{error}</span>
          <button
            onClick={loadSampleDatasets}
            className="block text-xs underline mt-1 hover:no-underline"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  if (datasets.length === 0) {
    return (
      <div className="text-center py-8">
        <Database className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-medium mb-2">No sample datasets available</h3>
        <p className="text-sm text-muted-foreground">
          Check that the backend service is running and datasets are initialized.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {selectedDataset && (
        <div className="flex items-center space-x-2 text-green-600 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md p-3 mb-4">
          <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
          <span className="text-sm">
            Selected dataset: <strong>{selectedDataset}</strong>
          </span>
        </div>
      )}

      <div className="grid grid-cols-1 gap-3 max-h-96 overflow-y-auto">
        {datasets.map((dataset) => (
          <div
            key={dataset.name}
            className={`
              border rounded-lg p-4 cursor-pointer transition-colors hover:bg-secondary/50
              ${selectedDataset === dataset.name ? "border-primary bg-primary/5" : ""}
              ${processingDataset === dataset.name ? "opacity-50 pointer-events-none" : ""}
            `}
            onClick={() => handleDatasetSelect(dataset.name)}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <h4 className="font-medium text-sm mb-1">{dataset.name}</h4>
                <p className="text-xs text-muted-foreground line-clamp-2">
                  {dataset.description}
                </p>
              </div>
              <div className="flex items-center space-x-1 ml-2">
                {processingDataset === dataset.name ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                ) : (
                  <Download className="h-4 w-4 text-muted-foreground" />
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="flex items-center space-x-1">
                <Database className="h-3 w-3 text-muted-foreground" />
                <span className="text-muted-foreground">Rows:</span>
                <span className="font-medium">{dataset.rows.toLocaleString()}</span>
              </div>

              <div className="flex items-center space-x-1">
                <Shield className="h-3 w-3 text-muted-foreground" />
                <span className="text-muted-foreground">FOCUS:</span>
                <span className={`font-medium ${getComplianceColor(dataset.compliance_score)}`}>
                  {(dataset.compliance_score * 100).toFixed(0)}%
                </span>
              </div>

              <div className="flex items-center space-x-1">
                <TrendingUp className="h-3 w-3 text-muted-foreground" />
                <span className="text-muted-foreground">Quality:</span>
                <span className={`font-medium ${getQualityColor(dataset.data_quality_score)}`}>
                  {(dataset.data_quality_score * 100).toFixed(0)}%
                </span>
              </div>

              <div className="flex items-center space-x-1">
                <span className="text-muted-foreground">Type:</span>
                <span className="font-medium">{getDatasetTypeLabel(dataset.dataset_type)}</span>
              </div>
            </div>

            <div className="flex items-center justify-between mt-3 pt-2 border-t border-border/50">
              <div className="flex items-center space-x-3 text-xs text-muted-foreground">
                <span>{dataset.service_count} services</span>
                <span>{dataset.account_count} accounts</span>
                <span>{dataset.region_count} regions</span>
              </div>

              <div className="flex items-center space-x-3 text-xs">
                {dataset.optimization_opportunities_count > 0 && (
                  <span className="text-amber-600">
                    {dataset.optimization_opportunities_count} opportunities
                  </span>
                )}
                {dataset.anomaly_candidates_count > 0 && (
                  <span className="text-red-600">
                    {dataset.anomaly_candidates_count} anomalies
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="text-xs text-muted-foreground space-y-1 mt-4">
        <p>• All datasets are FOCUS v1.2 compliant or assessed for compliance</p>
        <p>• Quality scores indicate data completeness and consistency</p>
        <p>• Click on a dataset to load it for visualization</p>
      </div>
    </div>
  );
}