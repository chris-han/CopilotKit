"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Plus,
  Settings,
  Trash2,
  BarChart3,
  PieChart,
  LineChart,
  Activity,
  FileText
} from "lucide-react";
import { DraggableResizableGrid } from "./DraggableResizableGrid";

interface DashboardItem {
  id: string;
  type: "chart" | "metric" | "text" | "commentary";
  chartType?: "area" | "bar" | "donut";
  title: string;
  description?: string;
  span: string;
  position: { row: number; col?: number };
  config?: Record<string, unknown>;
}

interface DashboardConfig {
  grid: { cols: number; rows: string };
  items: DashboardItem[];
}

interface DashboardEditorProps {
  config: DashboardConfig;
  onChange: (config: DashboardConfig) => void;
  dataLoading?: boolean;
}

const CHART_TYPES = [
  { value: "area", label: "Area Chart", icon: LineChart, description: "Time series data" },
  { value: "bar", label: "Bar Chart", icon: BarChart3, description: "Categorical comparisons" },
  { value: "donut", label: "Donut Chart", icon: PieChart, description: "Proportional data" },
];

const ITEM_TYPES = [
  { value: "chart", label: "Chart", icon: BarChart3, description: "Data visualization" },
  { value: "metric", label: "Metrics", icon: Activity, description: "Key performance indicators" },
  { value: "text", label: "Text", icon: FileText, description: "Custom content" },
  { value: "commentary", label: "Commentary", icon: FileText, description: "AI-generated insights" },
];

const SPAN_OPTIONS = [
  { value: "col-span-1", label: "1 Column" },
  { value: "col-span-2", label: "2 Columns" },
  { value: "col-span-3", label: "3 Columns" },
  { value: "col-span-4", label: "4 Columns" },
  { value: "col-span-1 md:col-span-2", label: "1-2 Columns (Responsive)" },
  { value: "col-span-1 md:col-span-2 lg:col-span-4", label: "1-2-4 Columns (Responsive)" },
];

export function DashboardEditor({ config, onChange, dataLoading }: DashboardEditorProps) {
  const [selectedItem, setSelectedItem] = useState<string | null>(null);

  // Generate grid class based on column count
  const getGridClass = (cols: number) => {
    const colsMap: Record<number, string> = {
      2: "grid-cols-1 md:grid-cols-2",
      3: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
      4: "grid-cols-1 md:grid-cols-2 lg:grid-cols-4",
      6: "grid-cols-2 md:grid-cols-3 lg:grid-cols-6",
    };
    return `grid w-full gap-4 ${colsMap[cols] || "grid-cols-1 md:grid-cols-2 lg:grid-cols-4"}`;
  };

  const addItem = (type: DashboardItem["type"]) => {
    const newItem: DashboardItem = {
      id: `item-${Date.now()}`,
      type,
      title: `New ${type.charAt(0).toUpperCase() + type.slice(1)}`,
      span: type === "metric" ? "col-span-4" : "col-span-2",
      position: { row: (config.items.length || 0) + 1 },
      ...(type === "chart" && { chartType: "bar" }),
    };

    onChange({
      ...config,
      items: [...config.items, newItem],
    });
    setSelectedItem(newItem.id);
  };

  const removeItem = (itemId: string) => {
    onChange({
      ...config,
      items: config.items.filter(item => item.id !== itemId),
    });
    if (selectedItem === itemId) {
      setSelectedItem(null);
    }
  };

  const updateItem = (itemId: string, updates: Partial<DashboardItem>) => {
    onChange({
      ...config,
      items: config.items.map(item =>
        item.id === itemId ? { ...item, ...updates } : item
      ),
    });
  };


  const selectedItemData = selectedItem ? config.items.find(item => item.id === selectedItem) : null;

  // Handler for when items are moved via drag and drop
  const handleItemMove = (itemId: string, newPosition: { x: number; y: number; width: number; height: number }) => {
    const updatedItems = config.items.map(item => {
      if (item.id === itemId) {
        return {
          ...item,
          position: { row: newPosition.y + 1, col: newPosition.x },
          // Update span based on new width
          span: getSpanFromWidth(newPosition.width)
        };
      }
      return item;
    });

    onChange({ ...config, items: updatedItems });
  };

  // Handler for when items are resized
  const handleItemResize = (itemId: string, newSize: { width: number; height: number }) => {
    const updatedItems = config.items.map(item => {
      if (item.id === itemId) {
        return {
          ...item,
          span: getSpanFromWidth(newSize.width)
        };
      }
      return item;
    });

    onChange({ ...config, items: updatedItems });
  };

  // Helper function to convert grid width to span class
  const getSpanFromWidth = (width: number): string => {
    const spanMap: Record<number, string> = {
      1: "col-span-1",
      2: "col-span-2",
      3: "col-span-3",
      4: "col-span-4",
      5: "col-span-5",
      6: "col-span-6",
    };
    return spanMap[Math.min(width, 6)] || "col-span-1";
  };

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      {/* Dashboard Preview */}
      <div className="lg:col-span-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Dashboard Preview
            </CardTitle>
            <CardDescription>
              {dataLoading
                ? "Loading data..."
                : "Live preview of your dashboard. Drag items to move them, use resize handles to change size. All changes snap to grid."
              }
            </CardDescription>
          </CardHeader>
          <CardContent className="overflow-visible">
            <div className="min-h-[360px]">
              <DraggableResizableGrid
                items={config.items}
                onItemMove={handleItemMove}
                onItemResize={handleItemResize}
                cols={config.grid.cols}
                gridSize={120}
                className={getGridClass(config.grid.cols)}
              >
              {config.items.map((item) => (
                <div
                  key={item.id}
                  className={`cursor-pointer rounded-lg border-2 transition-all ${
                    selectedItem === item.id
                      ? "border-primary bg-primary/5"
                      : "border-dashed border-muted-foreground/30 hover:border-primary/50"
                  }`}
                  onClick={() => setSelectedItem(item.id)}
                >
                  <Card className="h-full">
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {item.type === "chart" && <BarChart3 className="h-4 w-4" />}
                          {item.type === "metric" && <Activity className="h-4 w-4" />}
                          {item.type === "text" && <FileText className="h-4 w-4" />}
                          {item.type === "commentary" && <FileText className="h-4 w-4" />}
                          <CardTitle className="text-sm">{item.title}</CardTitle>
                        </div>
                        <div className="flex items-center gap-1">
                          <Badge variant="secondary" className="text-xs">
                            {item.type}
                            {item.chartType && ` (${item.chartType})`}
                          </Badge>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0 opacity-60 hover:opacity-100"
                            onClick={(e) => {
                              e.stopPropagation();
                              removeItem(item.id);
                            }}
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                      {item.description && (
                        <CardDescription className="text-xs">{item.description}</CardDescription>
                      )}
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="flex h-32 items-center justify-center rounded bg-muted/50 text-xs text-muted-foreground">
                        {dataLoading ? (
                          <div className="animate-pulse">Loading...</div>
                        ) : (
                          <div className="text-center">
                            <div>{item.type} preview</div>
                            {item.chartType && <div className="mt-1">({item.chartType})</div>}
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              ))}
            </DraggableResizableGrid>
            </div>

            {/* Add item placeholder - outside the grid */}
            {config.items.length === 0 && (
              <div className="flex min-h-[200px] items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/30 mt-4">
                <div className="text-center">
                  <Plus className="mx-auto h-8 w-8 text-muted-foreground" />
                  <p className="mt-2 text-sm text-muted-foreground">Add new item to get started</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Editor Panel */}
      <div className="space-y-4">
        {/* Add Items */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Add Items</CardTitle>
            <CardDescription>Add new components to your dashboard</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-2">
              {ITEM_TYPES.map((itemType) => (
                <Button
                  key={itemType.value}
                  variant="outline"
                  size="sm"
                  className="flex flex-col gap-1 h-auto py-3"
                  onClick={() => addItem(itemType.value as DashboardItem["type"])}
                >
                  <itemType.icon className="h-4 w-4" />
                  <span className="text-xs">{itemType.label}</span>
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Item Properties */}
        {selectedItemData && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Item Properties</CardTitle>
              <CardDescription>Configure the selected item</CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="general">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="general">General</TabsTrigger>
                  <TabsTrigger value="layout">Layout</TabsTrigger>
                </TabsList>

                <TabsContent value="general" className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="item-title">Title</Label>
                    <Input
                      id="item-title"
                      value={selectedItemData.title}
                      onChange={(e) => updateItem(selectedItemData.id, { title: e.target.value })}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="item-description">Description</Label>
                    <Textarea
                      id="item-description"
                      value={selectedItemData.description || ""}
                      onChange={(e) => updateItem(selectedItemData.id, { description: e.target.value })}
                      rows={2}
                    />
                  </div>

                  {selectedItemData.type === "chart" && (
                    <div className="space-y-2">
                      <Label htmlFor="chart-type">Chart Type</Label>
                      <Select
                        value={selectedItemData.chartType}
                        onValueChange={(value) => updateItem(selectedItemData.id, { chartType: value as "area" | "bar" | "donut" })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {CHART_TYPES.map((type) => (
                            <SelectItem key={type.value} value={type.value}>
                              <div className="flex items-center gap-2">
                                <type.icon className="h-4 w-4" />
                                <div>
                                  <div className="font-medium">{type.label}</div>
                                  <div className="text-xs text-muted-foreground">{type.description}</div>
                                </div>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="layout" className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="item-span">Column Span</Label>
                    <Select
                      value={selectedItemData.span}
                      onValueChange={(value) => updateItem(selectedItemData.id, { span: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {SPAN_OPTIONS.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => removeItem(selectedItemData.id)}
                      className="flex-1"
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Remove Item
                    </Button>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        )}

        {/* Dashboard Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Dashboard Settings</CardTitle>
            <CardDescription>Configure dashboard layout</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="grid-cols">Grid Columns</Label>
                <Select
                  value={config.grid.cols.toString()}
                  onValueChange={(value) => onChange({
                    ...config,
                    grid: { ...config.grid, cols: parseInt(value) }
                  })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="2">2 Columns</SelectItem>
                    <SelectItem value="3">3 Columns</SelectItem>
                    <SelectItem value="4">4 Columns</SelectItem>
                    <SelectItem value="6">6 Columns</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}