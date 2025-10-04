"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { Send, Lightbulb, BarChart, PieChart, LineChart, Sparkles } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { ChartSuggestions } from "./ChartSuggestions";

interface ChartSuggestion {
  id: string;
  chart_type: string;
  config: any;
  title: string;
  reasoning: string;
  best_for: string;
  priority: number;
}

interface VisualizationChatProps {
  dataSummary: {
    name: string;
    field_names: string[];
    num_rows: number;
    sample_data: Record<string, any>[];
  };
  onVisualizationRequest: (request: {
    goal: string;
    chart_type?: string;
    persona?: string;
  }) => Promise<{
    suggestions?: ChartSuggestion[];
    final_visualization?: any;
  }>;
  onChartSelected: (suggestion: ChartSuggestion, config: any) => void;
  isLoading: boolean;
  recentVisualizations: Array<{
    id: string;
    title: string;
    chart_type: string;
  }>;
  baseApiUrl: string;
  userId?: string;
  datasetName?: string;
}

const CHART_TYPES = [
  { value: "bar", label: "Bar Chart", icon: BarChart },
  { value: "line", label: "Line Chart", icon: LineChart },
  { value: "pie", label: "Pie Chart", icon: PieChart },
  { value: "scatter", label: "Scatter Plot", icon: Sparkles },
  { value: "histogram", label: "Histogram", icon: BarChart },
  { value: "auto", label: "Let AI Choose", icon: Sparkles },
];

const PERSONAS = [
  { value: "default", label: "General Analyst" },
  { value: "executive", label: "Executive" },
  { value: "data-scientist", label: "Data Scientist" },
  { value: "finops", label: "FinOps Analyst" },
];

const SUGGESTED_GOALS = [
  "Show me the distribution of {field}",
  "What is the trend of {field} over time?",
  "Compare {field1} and {field2}",
  "Find outliers in {field}",
  "Show top 10 values in {field}",
  "Correlation between {field1} and {field2}",
];

export function VisualizationChat({
  dataSummary,
  onVisualizationRequest,
  onChartSelected,
  isLoading,
  recentVisualizations,
  baseApiUrl,
  userId = "default_user",
  datasetName,
}: VisualizationChatProps) {
  const [goal, setGoal] = useState("");
  const [selectedChartType, setSelectedChartType] = useState("auto");
  const [selectedPersona, setSelectedPersona] = useState("default");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [chartSuggestions, setChartSuggestions] = useState<ChartSuggestion[]>([]);
  const [currentGoal, setCurrentGoal] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Generate smart suggestions based on data fields
  useEffect(() => {
    if (dataSummary.field_names.length > 0) {
      const numericFields = dataSummary.field_names.filter(field => {
        const sampleValue = dataSummary.sample_data[0]?.[field];
        return typeof sampleValue === "number" || !isNaN(Number(sampleValue));
      });

      const categoricalFields = dataSummary.field_names.filter(field => {
        const sampleValue = dataSummary.sample_data[0]?.[field];
        return typeof sampleValue === "string";
      });

      const smartSuggestions = [];

      // Add field-specific suggestions
      if (numericFields.length > 0) {
        smartSuggestions.push(`Show me the distribution of ${numericFields[0]}`);
        if (numericFields.length > 1) {
          smartSuggestions.push(`Compare ${numericFields[0]} and ${numericFields[1]}`);
        }
      }

      if (categoricalFields.length > 0) {
        smartSuggestions.push(`Show top categories in ${categoricalFields[0]}`);
      }

      // Add time-based suggestions if we detect date fields
      const dateFields = dataSummary.field_names.filter(field =>
        field.toLowerCase().includes("date") ||
        field.toLowerCase().includes("time") ||
        field.toLowerCase().includes("period")
      );

      if (dateFields.length > 0 && numericFields.length > 0) {
        smartSuggestions.push(`Show ${numericFields[0]} trend over ${dateFields[0]}`);
      }

      // Add general suggestions
      smartSuggestions.push(`Create a summary visualization of the dataset`);
      smartSuggestions.push(`Find interesting patterns in the data`);

      setSuggestions(smartSuggestions.slice(0, 6));
    }
  }, [dataSummary]);

  const handleSubmit = useCallback(async () => {
    if (!goal.trim() || isLoading) return;

    try {
      // Clear previous suggestions
      setChartSuggestions([]);
      setCurrentGoal(goal.trim());

      const response = await onVisualizationRequest({
        goal: goal.trim(),
        chart_type: selectedChartType === "auto" ? undefined : selectedChartType,
        persona: selectedPersona,
      });

      // Handle chart suggestions response
      if (response?.suggestions && response.suggestions.length > 0) {
        setChartSuggestions(response.suggestions);
      }

      setGoal("");
    } catch (error) {
      console.error("Error generating visualization:", error);
      // Handle error (could show error state)
    }
  }, [goal, selectedChartType, selectedPersona, onVisualizationRequest, isLoading]);

  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }, [handleSubmit]);

  const handleSuggestionClick = useCallback((suggestion: string) => {
    setGoal(suggestion);
    textareaRef.current?.focus();
  }, []);

  const handleChartSelection = useCallback((suggestion: ChartSuggestion, config: any) => {
    // Clear chart suggestions after selection
    setChartSuggestions([]);
    setCurrentGoal("");

    // Notify parent component
    onChartSelected(suggestion, config);
  }, [onChartSelected]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Sparkles className="h-5 w-5" />
            <span>Natural Language Visualization</span>
          </CardTitle>
          <CardDescription>
            Describe what you want to visualize and I'll create the perfect chart for you
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Main input */}
          <div className="space-y-3">
            <textarea
              ref={textareaRef}
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="e.g., Show me the distribution of costs by service over time..."
              className="w-full min-h-[100px] p-3 border border-input rounded-md resize-y bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
              disabled={isLoading}
            />

            {/* Options */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Chart Type</label>
                <select
                  value={selectedChartType}
                  onChange={(e) => setSelectedChartType(e.target.value)}
                  className="w-full p-2 border border-input rounded-md bg-background text-foreground"
                  disabled={isLoading}
                >
                  {CHART_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Persona</label>
                <select
                  value={selectedPersona}
                  onChange={(e) => setSelectedPersona(e.target.value)}
                  className="w-full p-2 border border-input rounded-md bg-background text-foreground"
                  disabled={isLoading}
                >
                  {PERSONAS.map((persona) => (
                    <option key={persona.value} value={persona.value}>
                      {persona.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Submit button */}
            <button
              onClick={handleSubmit}
              disabled={!goal.trim() || isLoading}
              className="w-full bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed px-4 py-2 rounded-md font-medium flex items-center justify-center space-x-2 transition-colors"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-foreground"></div>
                  <span>Generating visualization...</span>
                </>
              ) : (
                <>
                  <Send className="h-4 w-4" />
                  <span>Create Visualization</span>
                </>
              )}
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Chart Suggestions */}
      {chartSuggestions.length > 0 && (
        <Card>
          <CardContent className="pt-6">
            <ChartSuggestions
              suggestions={chartSuggestions}
              goal={currentGoal}
              onChartSelected={handleChartSelection}
              baseApiUrl={baseApiUrl}
              userId={userId}
              datasetName={datasetName}
              persona={selectedPersona}
              loading={false}
            />
          </CardContent>
        </Card>
      )}

      {/* Suggestions */}
      {suggestions.length > 0 && !chartSuggestions.length && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Lightbulb className="h-5 w-5" />
              <span>Suggested Visualizations</span>
            </CardTitle>
            <CardDescription>
              Based on your data fields, here are some visualization ideas
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="text-left p-3 border border-input rounded-md hover:bg-secondary/50 transition-colors text-sm"
                  disabled={isLoading}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent visualizations */}
      {recentVisualizations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Visualizations</CardTitle>
            <CardDescription>
              Your recently generated charts for this dataset
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {recentVisualizations.map((viz) => (
                <div
                  key={viz.id}
                  className="flex items-center justify-between p-2 border border-input rounded-md"
                >
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-primary rounded-full"></div>
                    <span className="text-sm">{viz.title}</span>
                  </div>
                  <span className="text-xs text-muted-foreground capitalize">
                    {viz.chart_type}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Data context */}
      <Card>
        <CardHeader>
          <CardTitle>Data Context</CardTitle>
          <CardDescription>
            Available fields in your dataset
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="text-sm">
              <span className="font-medium">Dataset:</span> {dataSummary.name}
            </div>
            <div className="text-sm">
              <span className="font-medium">Rows:</span> {dataSummary.num_rows.toLocaleString()}
            </div>
            <div className="text-sm">
              <span className="font-medium">Fields:</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {dataSummary.field_names.map((field, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-secondary text-secondary-foreground text-xs rounded-md cursor-pointer hover:bg-secondary/80"
                  onClick={() => setGoal(prev => prev + (prev ? " " : "") + field)}
                >
                  {field}
                </span>
              ))}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Click on field names to add them to your request
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}