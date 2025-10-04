"use client";

import { useState, useCallback } from "react";
import { BarChart3, PieChart, TrendingUp, ScatterChart, AlertCircle, CheckCircle2 } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface ChartSuggestion {
  id: string;
  chart_type: string;
  config: any;
  title: string;
  reasoning: string;
  best_for: string;
  priority: number;
}

interface ChartSuggestionsProps {
  suggestions: ChartSuggestion[];
  goal: string;
  onChartSelected: (suggestion: ChartSuggestion, config: any) => void;
  baseApiUrl: string;
  userId?: string;
  datasetName?: string;
  persona?: string;
  loading?: boolean;
}

const CHART_ICONS: Record<string, LucideIcon> = {
  bar: BarChart3,
  pie: PieChart,
  line: TrendingUp,
  scatter: ScatterChart,
  area: TrendingUp,
};

const CHART_COLORS: Record<string, string> = {
  bar: "bg-blue-50 border-blue-200 hover:bg-blue-100",
  pie: "bg-green-50 border-green-200 hover:bg-green-100",
  line: "bg-purple-50 border-purple-200 hover:bg-purple-100",
  scatter: "bg-orange-50 border-orange-200 hover:bg-orange-100",
  area: "bg-indigo-50 border-indigo-200 hover:bg-indigo-100",
};

export function ChartSuggestions({
  suggestions,
  goal,
  onChartSelected,
  baseApiUrl,
  userId = "default_user",
  datasetName,
  persona = "default",
  loading = false
}: ChartSuggestionsProps) {
  const [selectedSuggestion, setSelectedSuggestion] = useState<string | null>(null);
  const [processingSelection, setProcessingSelection] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSuggestionSelect = useCallback(async (suggestion: ChartSuggestion) => {
    try {
      setProcessingSelection(suggestion.id);
      setError(null);

      // Record the user's choice in the backend
      const response = await fetch(`${baseApiUrl}/lida/select-chart`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: userId,
          suggestion_id: suggestion.id,
          chart_type: suggestion.chart_type,
          goal: goal,
          dataset_name: datasetName,
          persona: persona,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to record selection: ${response.statusText}`);
      }

      const result = await response.json();
      console.log("Selection recorded:", result);

      // Update UI state
      setSelectedSuggestion(suggestion.id);

      // Notify parent component with the selected chart
      onChartSelected(suggestion, suggestion.config);

    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to record selection");
      console.error("Error recording chart selection:", err);
    } finally {
      setProcessingSelection(null);
    }
  }, [baseApiUrl, userId, goal, datasetName, persona, onChartSelected]);

  const getChartIcon = (chartType: string): LucideIcon => {
    return CHART_ICONS[chartType] || BarChart3;
  };

  const getChartColor = (chartType: string): string => {
    return CHART_COLORS[chartType] || "bg-gray-50 border-gray-200 hover:bg-gray-100";
  };

  if (loading) {
    return (
      <div className="space-y-3">
        <h3 className="text-lg font-semibold mb-4">Generating Chart Suggestions...</h3>
        {[1, 2, 3].map((i) => (
          <div key={i} className="border rounded-lg p-4 animate-pulse">
            <div className="flex items-start space-x-3">
              <div className="w-10 h-10 bg-muted rounded-lg"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-muted rounded w-3/4"></div>
                <div className="h-3 bg-muted rounded w-full"></div>
                <div className="h-3 bg-muted rounded w-5/6"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!suggestions || suggestions.length === 0) {
    return (
      <div className="text-center py-8">
        <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-medium mb-2">No suggestions available</h3>
        <p className="text-sm text-muted-foreground">
          Try entering a different visualization goal or check your dataset.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Chart Suggestions</h3>
        <span className="text-sm text-muted-foreground">
          {suggestions.length} suggestions for: "{goal}"
        </span>
      </div>

      {error && (
        <div className="flex items-center space-x-2 text-destructive bg-destructive/10 border border-destructive/20 rounded-md p-3">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {selectedSuggestion && (
        <div className="flex items-center space-x-2 text-green-600 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md p-3">
          <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
          <span className="text-sm">
            Chart selection recorded! This will improve future suggestions.
          </span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {suggestions.map((suggestion) => {
          const Icon = getChartIcon(suggestion.chart_type);
          const colorClass = getChartColor(suggestion.chart_type);
          const isSelected = selectedSuggestion === suggestion.id;
          const isProcessing = processingSelection === suggestion.id;

          return (
            <div
              key={suggestion.id}
              className={`
                border rounded-lg p-4 cursor-pointer transition-all duration-200
                ${colorClass}
                ${isSelected ? "ring-2 ring-primary shadow-lg" : ""}
                ${isProcessing ? "opacity-50 pointer-events-none" : ""}
              `}
              onClick={() => handleSuggestionSelect(suggestion)}
            >
              <div className="flex items-start space-x-3">
                <div className={`
                  flex items-center justify-center w-10 h-10 rounded-lg
                  ${isSelected ? "bg-primary text-primary-foreground" : "bg-background"}
                `}>
                  {isProcessing ? (
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
                  ) : (
                    <Icon className="h-5 w-5" />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-sm capitalize">
                      {suggestion.chart_type} Chart
                    </h4>
                    <span className="text-xs text-muted-foreground bg-background px-2 py-1 rounded">
                      #{suggestion.priority}
                    </span>
                  </div>

                  <p className="text-xs text-muted-foreground mb-3 line-clamp-2">
                    {suggestion.reasoning}
                  </p>

                  <div className="border-t pt-2">
                    <p className="text-xs font-medium text-muted-foreground mb-1">
                      Best for:
                    </p>
                    <p className="text-xs text-muted-foreground line-clamp-2">
                      {suggestion.best_for}
                    </p>
                  </div>

                  {isSelected && (
                    <div className="mt-3 pt-2 border-t">
                      <div className="flex items-center space-x-1">
                        <CheckCircle2 className="h-3 w-3 text-green-600" />
                        <span className="text-xs text-green-600 font-medium">
                          Selected
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="text-xs text-muted-foreground space-y-1 mt-4 p-3 bg-muted/50 rounded-lg">
        <p>• Click on a chart type to select it and generate the visualization</p>
        <p>• Your choice will be remembered to improve future suggestions</p>
        <p>• Charts are ranked by relevance to your goal and preferences</p>
      </div>
    </div>
  );
}