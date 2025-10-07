"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import {
  GitBranch,
  Database,
  TrendingUp,
  ArrowRight,
  ArrowDown,
  ArrowUp,
  Zap,
  Layers,
  AlertCircle
} from "lucide-react";

interface LineageNode {
  name: string;
  type: "entity" | "metric" | "dimension" | "table" | "view";
  description?: string;
  upstream_dependencies: LineageNode[];
  downstream_dependencies: LineageNode[];
  attributes?: string[];
  base_field?: string;
}

interface DataLineage {
  model_name: string;
  entities: LineageNode[];
  relationships: any[];
  data_flow: LineageNode[];
}

interface DataLineageViewProps {
  modelName: string;
  height?: number;
}

export function DataLineageView({ modelName, height = 600 }: DataLineageViewProps) {
  const [lineage, setLineage] = useState<DataLineage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<LineageNode | null>(null);
  const [viewMode, setViewMode] = useState<"graph" | "table">("graph");
  const svgRef = useRef<SVGSVGElement>(null);

  // Load data lineage
  const loadLineage = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`http://localhost:8004/semantic-model/${modelName}/lineage`);
      if (!response.ok) {
        throw new Error(`Failed to load lineage: ${response.statusText}`);
      }

      const lineageData = await response.json();
      setLineage(lineageData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data lineage');
    } finally {
      setLoading(false);
    }
  }, [modelName]);

  useEffect(() => {
    loadLineage();
  }, [loadLineage]);

  // Render graph visualization
  const renderGraphView = useCallback(() => {
    if (!lineage) return null;

    const allNodes = [...lineage.entities, ...lineage.data_flow];
    const nodeWidth = 180;
    const nodeHeight = 80;
    const horizontalSpacing = 220;
    const verticalSpacing = 120;

    // Calculate positions
    const entityNodes = lineage.entities.map((entity, index) => ({
      ...entity,
      x: 50 + (index % 3) * horizontalSpacing,
      y: 50 + Math.floor(index / 3) * verticalSpacing
    }));

    const metricNodes = lineage.data_flow.map((metric, index) => ({
      ...metric,
      x: 50 + (index % 3) * horizontalSpacing,
      y: 250 + Math.floor(index / 3) * verticalSpacing
    }));

    const allPositionedNodes = [...entityNodes, ...metricNodes];

    return (
      <div className="relative">
        <svg
          ref={svgRef}
          width="100%"
          height={height}
          className="border rounded-lg bg-muted/10"
        >
          {/* Background grid */}
          <defs>
            <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#e5e7eb" strokeWidth="1" opacity="0.3"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />

          {/* Render connections */}
          {allPositionedNodes.map((node, nodeIndex) => (
            <g key={`connections-${nodeIndex}`}>
              {node.downstream_dependencies.map((dep, depIndex) => {
                const targetNode = allPositionedNodes.find(n => n.name === dep.name);
                if (!targetNode) return null;

                return (
                  <line
                    key={`line-${nodeIndex}-${depIndex}`}
                    x1={node.x + nodeWidth / 2}
                    y1={node.y + nodeHeight}
                    x2={targetNode.x + nodeWidth / 2}
                    y2={targetNode.y}
                    stroke="#6366f1"
                    strokeWidth="2"
                    markerEnd="url(#arrowhead)"
                    opacity="0.7"
                  />
                );
              })}
            </g>
          ))}

          {/* Arrow marker */}
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="7"
              refX="9"
              refY="3.5"
              orient="auto"
            >
              <polygon
                points="0 0, 10 3.5, 0 7"
                fill="#6366f1"
              />
            </marker>
          </defs>

          {/* Render nodes */}
          {allPositionedNodes.map((node, index) => (
            <g
              key={`node-${index}`}
              transform={`translate(${node.x}, ${node.y})`}
              className="cursor-pointer"
              onClick={() => setSelectedNode(node)}
            >
              <rect
                width={nodeWidth}
                height={nodeHeight}
                rx="8"
                fill={selectedNode === node ? "#3b82f6" : getNodeColor(node.type)}
                stroke={selectedNode === node ? "#1d4ed8" : "#e5e7eb"}
                strokeWidth="2"
                className="transition-all hover:stroke-gray-400"
              />

              {/* Node icon */}
              <g transform="translate(10, 15)">
                {getNodeIcon(node.type)}
              </g>

              {/* Node text */}
              <text
                x="40"
                y="25"
                fill={selectedNode === node ? "white" : "#374151"}
                fontSize="14"
                fontWeight="500"
                className="pointer-events-none"
              >
                {truncateText(node.name, 18)}
              </text>

              <text
                x="40"
                y="45"
                fill={selectedNode === node ? "#e5e7eb" : "#6b7280"}
                fontSize="12"
                className="pointer-events-none"
              >
                {node.type}
              </text>

              {/* Additional info */}
              {node.type === "metric" && node.base_field && (
                <text
                  x="40"
                  y="60"
                  fill={selectedNode === node ? "#d1d5db" : "#9ca3af"}
                  fontSize="10"
                  className="pointer-events-none"
                >
                  {truncateText(node.base_field, 20)}
                </text>
              )}
            </g>
          ))}
        </svg>

        {/* Legend */}
        <div className="absolute top-4 right-4 bg-white p-3 rounded-lg shadow-sm border">
          <h4 className="text-sm font-medium mb-2">Legend</h4>
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 rounded bg-blue-100 border border-blue-300"></div>
              <span className="text-xs">Entity</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 rounded bg-green-100 border border-green-300"></div>
              <span className="text-xs">Metric</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 rounded bg-yellow-100 border border-yellow-300"></div>
              <span className="text-xs">Dimension</span>
            </div>
          </div>
        </div>
      </div>
    );
  }, [lineage, selectedNode, height]);

  // Render table view
  const renderTableView = useCallback(() => {
    if (!lineage) return null;

    const allNodes = [...lineage.entities, ...lineage.data_flow];

    return (
      <div className="space-y-6">
        {/* Entities Table */}
        <div>
          <h3 className="text-lg font-semibold mb-3 flex items-center">
            <Database className="h-5 w-5 mr-2" />
            Entities ({lineage.entities.length})
          </h3>
          <div className="border rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-muted">
                <tr>
                  <th className="text-left p-3 font-medium">Name</th>
                  <th className="text-left p-3 font-medium">Description</th>
                  <th className="text-left p-3 font-medium">Upstream</th>
                  <th className="text-left p-3 font-medium">Downstream</th>
                </tr>
              </thead>
              <tbody>
                {lineage.entities.map((entity, index) => (
                  <tr key={index} className="border-t hover:bg-muted/50">
                    <td className="p-3">
                      <div className="flex items-center">
                        <Database className="h-4 w-4 mr-2 text-blue-600" />
                        <span className="font-medium">{entity.name}</span>
                      </div>
                    </td>
                    <td className="p-3 text-sm text-muted-foreground">
                      {entity.description || "No description"}
                    </td>
                    <td className="p-3">
                      <div className="flex flex-wrap gap-1">
                        {entity.upstream_dependencies.map((dep, i) => (
                          <Badge key={i} variant="outline" className="text-xs">
                            {dep.name}
                          </Badge>
                        ))}
                      </div>
                    </td>
                    <td className="p-3">
                      <div className="flex flex-wrap gap-1">
                        {entity.downstream_dependencies.map((dep, i) => (
                          <Badge key={i} variant="secondary" className="text-xs">
                            {dep.name}
                          </Badge>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Metrics Table */}
        <div>
          <h3 className="text-lg font-semibold mb-3 flex items-center">
            <TrendingUp className="h-5 w-5 mr-2" />
            Metrics ({lineage.data_flow.length})
          </h3>
          <div className="border rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-muted">
                <tr>
                  <th className="text-left p-3 font-medium">Name</th>
                  <th className="text-left p-3 font-medium">Description</th>
                  <th className="text-left p-3 font-medium">Base Field</th>
                  <th className="text-left p-3 font-medium">Dependencies</th>
                </tr>
              </thead>
              <tbody>
                {lineage.data_flow.map((metric, index) => (
                  <tr key={index} className="border-t hover:bg-muted/50">
                    <td className="p-3">
                      <div className="flex items-center">
                        <TrendingUp className="h-4 w-4 mr-2 text-green-600" />
                        <span className="font-medium">{metric.name}</span>
                      </div>
                    </td>
                    <td className="p-3 text-sm text-muted-foreground">
                      {metric.description || "No description"}
                    </td>
                    <td className="p-3 text-sm">
                      <code className="bg-muted px-2 py-1 rounded text-xs">
                        {metric.base_field || "N/A"}
                      </code>
                    </td>
                    <td className="p-3">
                      <div className="flex flex-wrap gap-1">
                        {metric.upstream_dependencies.map((dep, i) => (
                          <Badge key={i} variant="outline" className="text-xs">
                            {dep.name}
                          </Badge>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }, [lineage]);

  // Helper functions
  const getNodeColor = (type: string) => {
    switch (type) {
      case "entity": return "#dbeafe";
      case "metric": return "#dcfce7";
      case "dimension": return "#fef3c7";
      case "table": return "#f3e8ff";
      case "view": return "#fce7f3";
      default: return "#f9fafb";
    }
  };

  const getNodeIcon = (type: string) => {
    const iconProps = { size: 16, color: "#374151" };
    switch (type) {
      case "entity": return <Database {...iconProps} />;
      case "metric": return <TrendingUp {...iconProps} />;
      case "dimension": return <Layers {...iconProps} />;
      case "table": return <Database {...iconProps} />;
      case "view": return <Zap {...iconProps} />;
      default: return <GitBranch {...iconProps} />;
    }
  };

  const truncateText = (text: string, maxLength: number) => {
    return text.length > maxLength ? text.substring(0, maxLength) + "..." : text;
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <span className="ml-2">Loading data lineage...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center text-red-600">
            <AlertCircle className="h-5 w-5 mr-2" />
            <span>{error}</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!lineage) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">
            No lineage information available
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center space-x-2">
                <GitBranch className="h-5 w-5" />
                <span>Data Lineage: {lineage.model_name}</span>
              </CardTitle>
              <CardDescription>
                Visual representation of data flow and dependencies
              </CardDescription>
            </div>
            <div className="flex space-x-2">
              <Button
                variant={viewMode === "graph" ? "default" : "outline"}
                size="sm"
                onClick={() => setViewMode("graph")}
              >
                Graph View
              </Button>
              <Button
                variant={viewMode === "table" ? "default" : "outline"}
                size="sm"
                onClick={() => setViewMode("table")}
              >
                Table View
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Main view */}
        <div className="lg:col-span-3">
          <Card>
            <CardContent className="p-4">
              {viewMode === "graph" ? renderGraphView() : renderTableView()}
            </CardContent>
          </Card>
        </div>

        {/* Details panel */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                {selectedNode ? "Node Details" : "Select a Node"}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {selectedNode ? (
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center space-x-2 mb-2">
                      {getNodeIcon(selectedNode.type)}
                      <span className="font-medium">{selectedNode.name}</span>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {selectedNode.type}
                    </Badge>
                  </div>

                  {selectedNode.description && (
                    <div>
                      <h4 className="text-sm font-medium mb-1">Description</h4>
                      <p className="text-sm text-muted-foreground">
                        {selectedNode.description}
                      </p>
                    </div>
                  )}

                  {selectedNode.base_field && (
                    <div>
                      <h4 className="text-sm font-medium mb-1">Base Field</h4>
                      <code className="text-xs bg-muted px-2 py-1 rounded">
                        {selectedNode.base_field}
                      </code>
                    </div>
                  )}

                  {selectedNode.attributes && selectedNode.attributes.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium mb-2">Attributes</h4>
                      <div className="flex flex-wrap gap-1">
                        {selectedNode.attributes.map((attr, i) => (
                          <Badge key={i} variant="secondary" className="text-xs">
                            {attr}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedNode.upstream_dependencies.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium mb-2 flex items-center">
                        <ArrowUp className="h-4 w-4 mr-1" />
                        Upstream
                      </h4>
                      <div className="space-y-1">
                        {selectedNode.upstream_dependencies.map((dep, i) => (
                          <div key={i} className="text-sm text-muted-foreground">
                            {dep.name}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedNode.downstream_dependencies.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium mb-2 flex items-center">
                        <ArrowDown className="h-4 w-4 mr-1" />
                        Downstream
                      </h4>
                      <div className="space-y-1">
                        {selectedNode.downstream_dependencies.map((dep, i) => (
                          <div key={i} className="text-sm text-muted-foreground">
                            {dep.name}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  Click on a node in the lineage graph to view its details
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}