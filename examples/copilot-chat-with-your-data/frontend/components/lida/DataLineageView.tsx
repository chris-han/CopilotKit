"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import {
  GitBranch,
  Database,
  TrendingUp,
  ArrowDown,
  ArrowUp,
  Zap,
  Layers,
  AlertCircle,
  Copy,
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

interface DbtModelMetadata {
  id?: string;
  slug?: string;
  name?: string;
  description?: string;
  path?: string;
  sql?: string;
  aliases?: string[];
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
  const [modelMetadata, setModelMetadata] = useState<DbtModelMetadata | null>(null);
  const [sqlCopied, setSqlCopied] = useState(false);
  const svgRef = useRef<SVGSVGElement>(null);

  const loadLineage = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const base =
        process.env.NEXT_PUBLIC_API_URL?.split(",").map((url) => url.trim()).filter(Boolean)[0] ??
        "http://localhost:8004";
      const encoded = encodeURIComponent(modelName);
      const [lineageResponse, metadataResponse] = await Promise.all([
        fetch(`${base}/lida/semantic-models/${encoded}/lineage`),
        fetch(`${base}/lida/dbt-models/${encoded}`),
      ]);

      if (!lineageResponse.ok) {
        throw new Error(
          `Failed to load lineage: ${lineageResponse.status} ${lineageResponse.statusText}`,
        );
      }

      const lineageData = await lineageResponse.json();
      setLineage(lineageData);
      setSelectedNode(null);

      if (metadataResponse.ok) {
        const metadata = await metadataResponse.json();
        setModelMetadata(metadata);
      } else {
        setModelMetadata(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data lineage");
      setModelMetadata(null);
    } finally {
      setLoading(false);
    }
  }, [modelName]);

  useEffect(() => {
    loadLineage();
  }, [loadLineage]);

  const handleCopySql = useCallback(async () => {
    if (!modelMetadata?.sql || typeof navigator === "undefined" || !navigator.clipboard) {
      return;
    }
    try {
      await navigator.clipboard.writeText(modelMetadata.sql);
      setSqlCopied(true);
      setTimeout(() => setSqlCopied(false), 2000);
    } catch (copyError) {
      console.error("Failed to copy SQL", copyError);
    }
  }, [modelMetadata]);

  const renderGraphView = useCallback(() => {
    if (!lineage) return null;

    const nodeWidth = 180;
    const nodeHeight = 80;
    const horizontalSpacing = 220;
    const verticalSpacing = 120;

    const entityNodes = lineage.entities.map((entity, index) => ({
      ...entity,
      x: 50 + (index % 3) * horizontalSpacing,
      y: 50 + Math.floor(index / 3) * verticalSpacing,
    }));

    const metricNodes = lineage.data_flow.map((metric, index) => ({
      ...metric,
      x: 50 + (index % 3) * horizontalSpacing,
      y: 250 + Math.floor(index / 3) * verticalSpacing,
    }));

    const allPositionedNodes = [...entityNodes, ...metricNodes];

    return (
      <div className="relative">
        <svg ref={svgRef} width="100%" height={height} className="rounded-lg bg-muted/10">
          <rect width="100%" height="100%" fill="url(#grid)" />

          {allPositionedNodes.map((node, nodeIndex) => (
            <g key={`connections-${nodeIndex}`}>
              {node.downstream_dependencies.map((dep, depIndex) => {
                const targetNode = allPositionedNodes.find((n) => n.name === dep.name);
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

          <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="#6366f1" />
            </marker>
          </defs>

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

              <g transform="translate(10, 15)">{getNodeIcon(node.type)}</g>

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
      </div>
    );
  }, [height, lineage, selectedNode]);

  const renderTableView = useCallback(() => {
    if (!lineage) return null;

    return (
      <div className="space-y-6">
        <div>
          <h3 className="mb-3 flex items-center text-lg font-semibold">
            <Database className="mr-2 h-5 w-5" />
            Entities ({lineage.entities.length})
          </h3>
          <div className="overflow-hidden rounded-lg border">
            <table className="w-full">
              <thead className="bg-muted">
                <tr>
                  <th className="p-3 text-left font-medium">Name</th>
                  <th className="p-3 text-left font-medium">Description</th>
                  <th className="p-3 text-left font-medium">Upstream</th>
                  <th className="p-3 text-left font-medium">Downstream</th>
                </tr>
              </thead>
              <tbody>
                {lineage.entities.map((entity, index) => (
                  <tr key={index} className="border-t hover:bg-muted/50">
                    <td className="p-3">
                      <div className="flex items-center">
                        <Database className="mr-2 h-4 w-4 text-blue-600" />
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

        <div>
          <h3 className="mb-3 flex items-center text-lg font-semibold">
            <TrendingUp className="mr-2 h-5 w-5" />
            Metrics ({lineage.data_flow.length})
          </h3>
          <div className="overflow-hidden rounded-lg border">
            <table className="w-full">
              <thead className="bg-muted">
                <tr>
                  <th className="p-3 text-left font-medium">Name</th>
                  <th className="p-3 text-left font-medium">Description</th>
                  <th className="p-3 text-left font-medium">Base Field</th>
                  <th className="p-3 text-left font-medium">Dependencies</th>
                </tr>
              </thead>
              <tbody>
                {lineage.data_flow.map((metric, index) => (
                  <tr key={index} className="border-t hover:bg-muted/50">
                    <td className="p-3">
                      <div className="flex items-center">
                        <TrendingUp className="mr-2 h-4 w-4 text-green-600" />
                        <span className="font-medium">{metric.name}</span>
                      </div>
                    </td>
                    <td className="p-3 text-sm text-muted-foreground">
                      {metric.description || "No description"}
                    </td>
                    <td className="p-3 text-sm">
                      <code className="rounded bg-muted px-2 py-1 text-xs">
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

  const getNodeColor = (type: string) => {
    switch (type) {
      case "entity":
        return "#dbeafe";
      case "metric":
        return "#dcfce7";
      case "dimension":
        return "#fef3c7";
      case "table":
        return "#f3e8ff";
      case "view":
        return "#fce7f3";
      default:
        return "#f9fafb";
    }
  };

  const getNodeIcon = (type: string) => {
    const iconProps = { size: 16, color: "#374151" };
    switch (type) {
      case "entity":
        return <Database {...iconProps} />;
      case "metric":
        return <TrendingUp {...iconProps} />;
      case "dimension":
        return <Layers {...iconProps} />;
      case "table":
        return <Database {...iconProps} />;
      case "view":
        return <Zap {...iconProps} />;
      default:
        return <GitBranch {...iconProps} />;
    }
  };

  const truncateText = (text: string, maxLength: number) =>
    text.length > maxLength ? `${text.substring(0, maxLength)}...` : text;

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-primary"></div>
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
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center text-red-600">
              <AlertCircle className="mr-2 h-5 w-5" />
              <span>{error}</span>
            </div>
            <Button size="sm" onClick={loadLineage}>
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!lineage) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">No lineage information available</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center space-x-2">
                <GitBranch className="h-5 w-5" />
                <span>Data Lineage: {lineage.model_name}</span>
              </CardTitle>
              <CardDescription>
                {modelMetadata?.description ?? "Visual representation of data flow and dependencies"}
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
        <CardContent className="space-y-4">
          {modelMetadata && (
            <div className="rounded-lg border bg-muted/40 p-4">
              <div className="flex flex-wrap items-center gap-2">
                {modelMetadata.slug && (
                  <Badge variant="secondary" className="text-xs">
                    Slug: {modelMetadata.slug}
                  </Badge>
                )}
                {Array.isArray(modelMetadata.aliases) && modelMetadata.aliases.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1">
                    {modelMetadata.aliases.map((alias) => (
                      <Badge key={alias} variant="outline" className="text-xs">
                        {alias}
                      </Badge>
                    ))}
                  </div>
                )}
                {modelMetadata.path && (
                  <code className="rounded border bg-background/60 px-2 py-1 text-xs">
                    {modelMetadata.path}
                  </code>
                )}
              </div>
              {modelMetadata.sql && (
                <div className="mt-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-muted-foreground">Model SQL</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2 text-xs"
                      onClick={handleCopySql}
                    >
                      <Copy className="mr-1 h-3 w-3" />
                      {sqlCopied ? "Copied" : "Copy SQL"}
                    </Button>
                  </div>
                  <pre className="max-h-60 overflow-auto rounded border bg-background/60 p-3 text-xs">
                    {modelMetadata.sql}
                  </pre>
                </div>
              )}
            </div>
          )}

          {viewMode === "graph" ? (
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-4">
              <Card className="space-y-4 lg:col-span-3">
                <CardHeader>
                  <div className="flex flex-wrap gap-4">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-muted-foreground">Legend</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="h-4 w-4 rounded bg-blue-100 border border-blue-300"></div>
                      <span className="text-xs text-muted-foreground">Entity</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="h-4 w-4 rounded bg-green-100 border border-green-300"></div>
                      <span className="text-xs text-muted-foreground">Metric</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="h-4 w-4 rounded bg-yellow-100 border border-yellow-300"></div>
                      <span className="text-xs text-muted-foreground">Dimension</span>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">{renderGraphView()}</CardContent>
              </Card>

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
                        <div className="mb-2 flex items-center space-x-2">
                          {getNodeIcon(selectedNode.type)}
                          <span className="font-medium">{selectedNode.name}</span>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {selectedNode.type}
                        </Badge>
                      </div>

                      {selectedNode.description && (
                        <div>
                          <h4 className="mb-1 text-sm font-medium">Description</h4>
                          <p className="text-sm text-muted-foreground">{selectedNode.description}</p>
                        </div>
                      )}

                      {selectedNode.base_field && (
                        <div>
                          <h4 className="mb-1 text-sm font-medium">Base Field</h4>
                          <code className="rounded bg-muted px-2 py-1 text-xs">{selectedNode.base_field}</code>
                        </div>
                      )}

                      {selectedNode.attributes && selectedNode.attributes.length > 0 && (
                        <div>
                          <h4 className="mb-2 text-sm font-medium">Attributes</h4>
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
                          <h4 className="mb-2 flex items-center text-sm font-medium">
                            <ArrowUp className="mr-1 h-4 w-4" /> Upstream
                          </h4>
                          <div className="flex flex-wrap gap-1">
                            {selectedNode.upstream_dependencies.map((dep, i) => (
                              <Badge key={i} variant="outline" className="text-xs">
                                {dep.name}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {selectedNode.downstream_dependencies.length > 0 && (
                        <div>
                          <h4 className="mb-2 flex items-center text-sm font-medium">
                            <ArrowDown className="mr-1 h-4 w-4" /> Downstream
                          </h4>
                          <div className="flex flex-wrap gap-1">
                            {selectedNode.downstream_dependencies.map((dep, i) => (
                              <Badge key={i} variant="secondary" className="text-xs">
                                {dep.name}
                              </Badge>
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
          ) : (
            renderTableView()
          )}
        </CardContent>
      </Card>
    </div>
  );
}
