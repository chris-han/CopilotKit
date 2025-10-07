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
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
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
import { useRef, useCallback, useEffect, useMemo } from "react";
import type { MouseEvent } from "react";
import { useAgUiAgent } from "../ag-ui/AgUiProvider";

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

interface GridPosition {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface DragState {
  isDragging: boolean;
  draggedItemId: string | null;
  startPosition: { x: number; y: number };
  currentPosition: { x: number; y: number };
  itemStartPosition: { x: number; y: number };
}

interface ResizeState {
  isResizing: boolean;
  resizedItemId: string | null;
  startSize: { width: number; height: number };
  startPosition: { x: number; y: number };
  resizeHandle: string | null;
}

interface DashboardConfig {
  grid: { cols: number; rows: string };
  items: DashboardItem[];
}

interface DashboardEditorProps {
  config: DashboardConfig;
  onChange: (config: DashboardConfig) => void;
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

const DATA_CONFIG_MAP = {
  dataSource: ["dataSource", "data_source"],
  metricField: ["metricField", "metric_field"],
  dimensionField: ["dimensionField", "dimension_field"],
  filters: ["filters"],
  dbtModel: ["dbtModel", "dbt_model"],
} as const;

type DataConfigKey = keyof typeof DATA_CONFIG_MAP;

function normalizeDataConfigUpdates(updates: Record<string, unknown>): Record<string, unknown> {
  const normalized: Record<string, unknown> = { ...updates };
  for (const key of Object.keys(updates)) {
    if (key in DATA_CONFIG_MAP) {
      const aliases = DATA_CONFIG_MAP[key as DataConfigKey];
      for (const alias of aliases) {
        normalized[alias] = updates[key];
      }
    }
  }
  return normalized;
}

function getConfigValue(item: DashboardItem, key: DataConfigKey) {
  const config = item.config ?? {};
  const aliases = DATA_CONFIG_MAP[key] ?? [key];
  for (const alias of aliases) {
    if (alias in config) {
      return (config as Record<string, unknown>)[alias];
    }
  }
  return undefined;
}

const DBT_MODEL_MAP: Record<
  string,
  { name: string; path: string; description: string; sql: string }
> = {
  salesData: {
    name: "Sales Performance Model",
    path: "models/marts/finance/sales_performance.sql",
    description: "Aggregates revenue, profit, and expense metrics by month for executive dashboards.",
    sql: `with source as (
  select * from {{ ref('fct_sales_transactions') }}
),
calendar as (
  select * from {{ ref('dim_calendar') }}
)
select
  c.month_start as billing_period_start,
  sum(s.revenue) as revenue,
  sum(s.profit) as profit,
  sum(s.expense) as expense,
  sum(s.customer_count) as customers
from source s
left join calendar c
  on s.date_id = c.date_id
group by 1
order by 1;`,
  },
  productData: {
    name: "Product Performance Model",
    path: "models/marts/finance/product_performance.sql",
    description: "Computes sales, units, and growth percentages by product for ranking visualizations.",
    sql: `select
  p.product_id,
  p.product_name,
  sum(f.revenue) as sales,
  sum(f.units) as units,
  avg(f.growth_pct) as growth_percentage
from {{ ref('dim_product') }} p
join {{ ref('fct_product_revenue') }} f
  on p.product_id = f.product_id
group by 1,2
order by sales desc;`,
  },
  categoryData: {
    name: "Category Mix Model",
    path: "models/marts/finance/category_mix.sql",
    description: "Provides revenue share and growth metrics across product categories.",
    sql: `select
  c.category_name,
  sum(f.revenue) as revenue,
  sum(f.revenue) / sum(sum(f.revenue)) over () as revenue_share,
  avg(f.growth_pct) as growth_percentage
from {{ ref('dim_category') }} c
join {{ ref('fct_category_revenue') }} f
  on c.category_id = f.category_id
group by 1
order by revenue desc;`,
  },
  regionalData: {
    name: "Regional Sales Model",
    path: "models/marts/finance/regional_sales.sql",
    description: "Summarizes sales and market share by region for geographic comparisons.",
    sql: `select
  r.region_name,
  sum(f.revenue) as revenue,
  sum(f.revenue) / sum(sum(f.revenue)) over () as market_share
from {{ ref('dim_region') }} r
join {{ ref('fct_regional_revenue') }} f
  on r.region_id = f.region_id
group by 1
order by revenue desc;`,
  },
  demographicsData: {
    name: "Customer Demographics Model",
    path: "models/marts/finance/customer_demographics.sql",
    description: "Tracks spend distribution by age cohort for demographic analysis.",
    sql: `select
  d.age_group,
  sum(f.spend) as total_spend,
  sum(f.customers) as customers
from {{ ref('dim_demographic') }} d
join {{ ref('fct_customer_spend') }} f
  on d.demographic_id = f.demographic_id
group by 1
order by total_spend desc;`,
  },
};

function truncateTitle(title: string, maxLength = 18): string {
  if (title.length <= maxLength) return title;
  return `${title.slice(0, maxLength - 3)}...`;
}


// Grid utility functions
function parseGridSpan(span: string): { width: number; height: number } {
  const colSpanMatch = span.match(/col-span-(\d+)/);
  const width = colSpanMatch ? parseInt(colSpanMatch[1]) : 1;
  const height = 1; // Default height, can be extended
  return { width, height };
}

function gridToCSS(position: GridPosition, cols: number) {
  return {
    gridColumnStart: Math.max(1, Math.min(position.x + 1, cols)),
    gridColumnEnd: Math.max(2, Math.min(position.x + position.width + 1, cols + 1)),
    gridRowStart: position.y + 1,
    gridRowEnd: position.y + position.height + 1,
  };
}

function pixelToGrid(pixelX: number, pixelY: number, containerWidth: number, cols: number, gridSize: number, gridGap: number): GridPosition {
  const totalGapWidth = gridGap * (cols - 1);
  const availableWidth = containerWidth - totalGapWidth;
  const cellWidth = cols > 0 ? Math.max(availableWidth, 0) / cols : 0;
  const effectiveCellWidth = cellWidth + gridGap;
  const rowHeight = gridSize + gridGap;
  const gridX = Math.max(0, Math.min(Math.floor(pixelX / effectiveCellWidth), cols - 1));
  const gridY = Math.max(0, Math.floor(pixelY / rowHeight));
  return { x: gridX, y: gridY, width: 1, height: 1 };
}

function gridToPixel(gridX: number, gridY: number, containerWidth: number, cols: number, gridSize: number, gridGap: number): { x: number; y: number } {
  const totalGapWidth = gridGap * (cols - 1);
  const availableWidth = containerWidth - totalGapWidth;
  const cellWidth = cols > 0 ? Math.max(availableWidth, 0) / cols : 0;
  const effectiveCellWidth = cellWidth + gridGap;
  const rowHeight = gridSize + gridGap;
  return {
    x: gridX * effectiveCellWidth,
    y: gridY * rowHeight,
  };
}

function isOverlapping(pos1: GridPosition, pos2: GridPosition): boolean {
  const pos1Right = pos1.x + pos1.width;
  const pos1Bottom = pos1.y + pos1.height;
  const pos2Right = pos2.x + pos2.width;
  const pos2Bottom = pos2.y + pos2.height;
  return !(pos1Right <= pos2.x || pos1.x >= pos2Right || pos1Bottom <= pos2.y || pos1.y >= pos2Bottom);
}

function findNextAvailablePosition(
  desiredPosition: GridPosition,
  existingPositions: Map<string, GridPosition>,
  excludeItemId: string,
  cols: number
): GridPosition {
  const { width, height } = desiredPosition;
  let testPosition = { ...desiredPosition };

  const hasCollision = (pos: GridPosition): boolean => {
    for (const [itemId, existingPos] of existingPositions) {
      if (itemId !== excludeItemId && isOverlapping(pos, existingPos)) {
        return true;
      }
    }
    return false;
  };

  if (!hasCollision(testPosition)) {
    return testPosition;
  }

  for (let radius = 1; radius <= 10; radius++) {
    for (let dy = -radius; dy <= radius; dy++) {
      for (let dx = -radius; dx <= radius; dx++) {
        if (Math.abs(dx) !== radius && Math.abs(dy) !== radius) continue;

        testPosition = {
          x: Math.max(0, Math.min(desiredPosition.x + dx, cols - width)),
          y: Math.max(0, desiredPosition.y + dy),
          width,
          height
        };

        if (testPosition.x + width <= cols && testPosition.x >= 0 && testPosition.y >= 0) {
          if (!hasCollision(testPosition)) {
            return testPosition;
          }
        }
      }
    }
  }

  return desiredPosition;
}

export function DashboardEditor({ config, onChange }: DashboardEditorProps) {
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  const { sendDirectUIUpdate } = useAgUiAgent();

  // Grid system state
  const containerRef = useRef<HTMLDivElement>(null);
  const gridSize = 120;
  const gridGap = 16;
  const effectiveGridSize = gridSize + gridGap;

  const [dragState, setDragState] = useState<DragState>({
    isDragging: false,
    draggedItemId: null,
    startPosition: { x: 0, y: 0 },
    currentPosition: { x: 0, y: 0 },
    itemStartPosition: { x: 0, y: 0 },
  });

  const [resizeState, setResizeState] = useState<ResizeState>({
    isResizing: false,
    resizedItemId: null,
    startSize: { width: 0, height: 0 },
    startPosition: { x: 0, y: 0 },
    resizeHandle: null,
  });

  const [itemPositions, setItemPositions] = useState<Map<string, GridPosition>>(new Map());
  const [hasCollision, setHasCollision] = useState<boolean>(false);

  // Initialize item positions from their span classes and position data
  useEffect(() => {
    const newPositions = new Map<string, GridPosition>();
    let currentRow = 0;
    let currentCol = 0;

    console.log('DashboardEditor: Updating item positions for', config.items.length, 'items');

    config.items.forEach((item, index) => {
      const { width, height } = parseGridSpan(item.span);

      const position: GridPosition = {
        x: item.position.col !== undefined ? item.position.col : currentCol,
        y: item.position.row !== undefined ? item.position.row - 1 : currentRow,
        width,
        height,
      };

      if (position.x + position.width > config.grid.cols) {
        position.x = Math.max(0, config.grid.cols - position.width);
      }

      console.log(`Item ${index} (${item.id}):`, {
        title: item.title,
        span: item.span,
        itemPosition: item.position,
        gridPosition: position
      });

      newPositions.set(item.id, position);

      if (item.position.col === undefined) {
        currentCol = position.x + position.width;
        if (currentCol >= config.grid.cols) {
          currentCol = 0;
          currentRow++;
        }
      }
    });

    console.log('DashboardEditor: Final item positions map:', newPositions);
    setItemPositions(newPositions);
  }, [config.items, config.grid.cols]);

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


  const removeItem = (itemId: string) => {
    onChange({
      ...config,
      items: config.items.filter(item => item.id !== itemId),
    });
    if (selectedItem === itemId) {
      setSelectedItem(null);
    }
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

  // Handler for when items are moved via drag and drop
  const handleItemMove = (itemId: string, newPosition: GridPosition) => {
    const updatedItems = config.items.map(item => {
      if (item.id === itemId) {
        return {
          ...item,
          position: { row: newPosition.y + 1, col: newPosition.x },
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

  const handleSelectItem = useCallback((event: MouseEvent, item: DashboardItem) => {
    event.stopPropagation();
    if (dragState.isDragging || resizeState.isResizing) {
      return;
    }
    setSelectedItem(item.id);
    sendDirectUIUpdate(`Show item properties for "${item.title}" (${item.id}) in Data Assistant panel`);
  }, [dragState.isDragging, resizeState.isResizing, sendDirectUIUpdate]);

  // Mouse event handlers for drag and resize
  const handleMouseDown = useCallback((e: React.MouseEvent, itemId: string, type: 'drag' | 'resize', handle?: string) => {
    e.preventDefault();
    e.stopPropagation();

    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;

    const startX = e.clientX - rect.left;
    const startY = e.clientY - rect.top;

    if (type === 'drag') {
      const itemPosition = itemPositions.get(itemId);
      if (!itemPosition) return;

      const containerWidth = rect.width;
      const startPixelPosition = gridToPixel(
        itemPosition.x,
        itemPosition.y,
        containerWidth,
        config.grid.cols,
        gridSize,
        gridGap
      );

      setDragState({
        isDragging: true,
        draggedItemId: itemId,
        startPosition: { x: startX, y: startY },
        currentPosition: startPixelPosition,
        itemStartPosition: startPixelPosition,
      });
    } else if (type === 'resize') {
      const itemPosition = itemPositions.get(itemId);
      if (!itemPosition) return;

      setResizeState({
        isResizing: true,
        resizedItemId: itemId,
        startSize: { width: itemPosition.width, height: itemPosition.height },
        startPosition: { x: startX, y: startY },
        resizeHandle: handle || 'se',
      });
    }
  }, [itemPositions, effectiveGridSize]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;

    const currentX = e.clientX - rect.left;
    const currentY = e.clientY - rect.top;

    if (dragState.isDragging && dragState.draggedItemId) {
      const deltaX = currentX - dragState.startPosition.x;
      const deltaY = currentY - dragState.startPosition.y;

      const newPixelX = dragState.itemStartPosition.x + deltaX;
      const newPixelY = dragState.itemStartPosition.y + deltaY;

      // Check for potential collision at current drag position
      const containerWidth = rect.width;
      const gridPos = pixelToGrid(newPixelX, newPixelY, containerWidth, config.grid.cols, gridSize, gridGap);
      const snappedPixel = gridToPixel(gridPos.x, gridPos.y, containerWidth, config.grid.cols, gridSize, gridGap);
      const currentItemPos = itemPositions.get(dragState.draggedItemId);

      if (currentItemPos) {
        const testPosition = { ...currentItemPos, x: gridPos.x, y: gridPos.y };

        // Check if this position would cause a collision
        let wouldCollide = false;
        for (const [itemId, existingPos] of itemPositions) {
          if (itemId !== dragState.draggedItemId && isOverlapping(testPosition, existingPos)) {
            wouldCollide = true;
            break;
          }
        }

        setHasCollision(wouldCollide);
      }

      setDragState(prev => ({
        ...prev,
        currentPosition: snappedPixel,
      }));
    }

    if (resizeState.isResizing && resizeState.resizedItemId) {
      const deltaX = currentX - resizeState.startPosition.x;
      const deltaY = currentY - resizeState.startPosition.y;

      const gridDeltaX = Math.round(deltaX / effectiveGridSize);
      const gridDeltaY = Math.round(deltaY / effectiveGridSize);

      const newWidth = Math.max(1, resizeState.startSize.width + gridDeltaX);
      const newHeight = Math.max(1, resizeState.startSize.height + gridDeltaY);

      // Update item position temporarily
      const currentPosition = itemPositions.get(resizeState.resizedItemId);
      if (currentPosition) {
        const newPosition = { ...currentPosition, width: newWidth, height: newHeight };
        const updatedPositions = new Map(itemPositions);
        updatedPositions.set(resizeState.resizedItemId, newPosition);
        setItemPositions(updatedPositions);
      }
    }
  }, [dragState, resizeState, itemPositions, gridSize, gridGap, effectiveGridSize, config.grid.cols]);

  const handleMouseUp = useCallback(() => {
    if (dragState.isDragging && dragState.draggedItemId) {
      const rect = containerRef.current?.getBoundingClientRect();
      if (rect) {
        const containerWidth = rect.width;
        const gridPos = pixelToGrid(dragState.currentPosition.x, dragState.currentPosition.y, containerWidth, config.grid.cols, gridSize, gridGap);
        const currentItemPos = itemPositions.get(dragState.draggedItemId);

        if (currentItemPos) {
          const desiredPosition = { ...currentItemPos, x: gridPos.x, y: gridPos.y };

          // Use collision detection to find the best available position
          const finalPosition = findNextAvailablePosition(
            desiredPosition,
            itemPositions,
            dragState.draggedItemId,
            config.grid.cols
          );

          handleItemMove(dragState.draggedItemId, finalPosition);

          const updatedPositions = new Map(itemPositions);
          updatedPositions.set(dragState.draggedItemId, finalPosition);
          setItemPositions(updatedPositions);
        }
      }
    }

    if (resizeState.isResizing && resizeState.resizedItemId) {
      const currentItemPos = itemPositions.get(resizeState.resizedItemId);
      if (currentItemPos) {
        // Check for collisions after resize
        const resizedPosition = { ...currentItemPos };
        const finalPosition = findNextAvailablePosition(
          resizedPosition,
          itemPositions,
          resizeState.resizedItemId,
          config.grid.cols
        );

        // If collision found, adjust the size to fit
        if (finalPosition.x !== resizedPosition.x || finalPosition.y !== resizedPosition.y) {
          // Position changed due to collision, keep original size and position
          handleItemResize(resizeState.resizedItemId, {
            width: resizeState.startSize.width,
            height: resizeState.startSize.height
          });
        } else {
          // No collision, use the resized dimensions
          handleItemResize(resizeState.resizedItemId, {
            width: currentItemPos.width,
            height: currentItemPos.height
          });
        }
      }
    }

    setDragState({
      isDragging: false,
      draggedItemId: null,
      startPosition: { x: 0, y: 0 },
      currentPosition: { x: 0, y: 0 },
      itemStartPosition: { x: 0, y: 0 },
    });

    setResizeState({
      isResizing: false,
      resizedItemId: null,
      startSize: { width: 0, height: 0 },
      startPosition: { x: 0, y: 0 },
      resizeHandle: null,
    });

    // Clear collision state
    setHasCollision(false);
  }, [dragState, resizeState, itemPositions, handleItemMove, handleItemResize, config.grid.cols, gridSize, gridGap]);

  // Calculate minimum grid height based on items (memoized for performance and real-time updates)
  const minHeight = useMemo(() => {
    if (itemPositions.size === 0) return effectiveGridSize * 3; // Default minimum height

    let maxRow = 0;
    itemPositions.forEach((position) => {
      const bottomRow = position.y + position.height;
      maxRow = Math.max(maxRow, bottomRow);
    });

    // Account for dragged items that might be at different positions
    if (dragState.isDragging && dragState.draggedItemId) {
      const draggedItem = itemPositions.get(dragState.draggedItemId);
      if (draggedItem) {
        // Convert pixel position to grid coordinates for dragged item
        const draggedGridY = Math.floor(dragState.currentPosition.y / effectiveGridSize);
        const draggedBottomRow = draggedGridY + draggedItem.height;
        maxRow = Math.max(maxRow, draggedBottomRow);
      }
    }

    // Calculate exact height without buffer - use pure grid multiples
    const calculatedHeight = maxRow * gridSize + (maxRow - 1) * gridGap;

    return Math.max(calculatedHeight, effectiveGridSize * 3); // At least 3 rows minimum
  }, [itemPositions, dragState.isDragging, dragState.draggedItemId, dragState.currentPosition, gridSize, effectiveGridSize, gridGap, config.grid.cols]);

  // Add global mouse event listeners
  useEffect(() => {
    if (dragState.isDragging || resizeState.isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [dragState.isDragging, resizeState.isResizing, handleMouseMove, handleMouseUp]);

  return (
    <div className="">
      {/* Dashboard Preview */}
      <div className="lg:col-span-6 overflow-visible">
        <Card className="overflow-visible">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Dashboard Preview
            </CardTitle>
            <CardDescription>
              Dashboard layout editor. Drag items to move them, use resize handles to change size. All changes snap to grid.
            </CardDescription>
          </CardHeader>
          <CardContent className="overflow-visible">
            <div className="min-h-[360px] overflow-visible">
              <div
                ref={containerRef}
                className={`relative ${getGridClass(config.grid.cols)}`}
                style={{
                  gridTemplateColumns: `repeat(${config.grid.cols}, 1fr)`,
                  gridAutoRows: `${gridSize}px`,
                  minHeight: `${minHeight}px`,
                  alignItems: 'stretch',
                }}
              >
              {config.items.map((item) => {
                const position = itemPositions.get(item.id);
                console.log(`Rendering item ${item.id} (${item.title}):`, {
                  hasPosition: !!position,
                  position: position,
                  itemPositionsSize: itemPositions.size
                });
                if (!position) {
                  console.warn(`No position found for item ${item.id}, skipping render`);
                  return null;
                }

                const isDragged = dragState.draggedItemId === item.id;
                const isResized = resizeState.resizedItemId === item.id;
                const isCompact = position.width === 1 && position.height === 1;
                const displayTitle = isCompact ? truncateTitle(item.title, 16) : item.title;

                return (
                <div
                  key={item.id}
                  className={`relative group ${isDragged ? 'z-50' : 'z-10'} ${
                    isDragged || isResized ? 'opacity-80' : ''
                  } ${isDragged && hasCollision ? 'cursor-not-allowed' : ''} h-full cursor-pointer rounded-lg border-2 transition-all ${
                    selectedItem === item.id
                      ? "border-primary bg-primary/5"
                      : "border-dashed border-muted-foreground/30 hover:border-primary/50"
                  }`}
                  style={{
                    ...gridToCSS(position, config.grid.cols),
                    minHeight: `${position.height * gridSize + (position.height - 1) * gridGap}px`,
                    transform: isDragged
                      ? `translate(${dragState.currentPosition.x - dragState.itemStartPosition.x}px, ${dragState.currentPosition.y - dragState.itemStartPosition.y}px)`
                      : undefined,
                  }}
                  onClick={(event) => handleSelectItem(event, item)}
                >
                  {/* Drag handle */}
                  <div
                    className="absolute -top-2 -left-2 w-6 h-6 bg-primary rounded cursor-move opacity-0 group-hover:opacity-100 transition-opacity z-20 flex items-center justify-center shadow-md"
                    onMouseDown={(e) => handleMouseDown(e, item.id, 'drag')}
                    title="Drag to move"
                  >
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M7 2a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM7 8a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM7 14a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM13 2a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM13 8a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM13 14a2 2 0 1 0 0 4 2 2 0 0 0 0-4z"/>
                    </svg>
                  </div>

                  {/* Resize handle */}
                  <div
                    className="absolute -bottom-2 -right-2 w-6 h-6 bg-primary rounded cursor-se-resize opacity-0 group-hover:opacity-100 transition-opacity z-20 flex items-center justify-center shadow-md"
                    onMouseDown={(e) => handleMouseDown(e, item.id, 'resize', 'se')}
                    title="Drag to resize"
                  >
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M4 4v12h12V4H4zm10 10H6V6h8v8z"/>
                      <path d="M14 14l-4-4M14 10l-2-2"/>
                    </svg>
                  </div>

                  {/* Grid overlay during drag */}
                  {isDragged && (
                    <div
                      className={`absolute inset-0 border-2 border-dashed rounded ${
                        hasCollision
                          ? "border-red-500 bg-red-500/20"
                          : "border-primary bg-primary/10"
                      }`}
                    />
                  )}
                  <Card className={`h-full flex flex-col ${isCompact ? "text-xs" : ""}`}>
                    <CardHeader className={`flex-shrink-0 ${isCompact ? "px-2 py-2" : "pb-2"}`}>
                      <div className="flex items-center justify-between gap-2">
                        <div className={`flex items-center ${isCompact ? "gap-1" : "gap-2"}`}>
                          {item.type === "chart" && (
                            <BarChart3 className={isCompact ? "h-3 w-3" : "h-4 w-4"} />
                          )}
                          {item.type === "metric" && (
                            <Activity className={isCompact ? "h-3 w-3" : "h-4 w-4"} />
                          )}
                          {item.type === "text" && (
                            <FileText className={isCompact ? "h-3 w-3" : "h-4 w-4"} />
                          )}
                          {item.type === "commentary" && (
                            <FileText className={isCompact ? "h-3 w-3" : "h-4 w-4"} />
                          )}
                          <CardTitle
                            className={`${isCompact ? "max-w-[5.5rem] truncate font-medium" : "text-sm"}`}
                          >
                            {displayTitle}
                          </CardTitle>
                        </div>
                        <div className="flex items-center gap-1">
                          {!isCompact && (
                            <Badge variant="secondary" className="text-xs">
                              {item.type}
                              {item.chartType && ` (${item.chartType})`}
                            </Badge>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            className={`${isCompact ? "h-5 w-5" : "h-6 w-6"} p-0 opacity-60 hover:opacity-100`}
                            onClick={(e) => {
                              e.stopPropagation();
                              removeItem(item.id);
                            }}
                          >
                            <Trash2 className={isCompact ? "h-3 w-3" : "h-3 w-3"} />
                          </Button>
                        </div>
                      </div>
                      {item.description && !isCompact && (
                        <CardDescription className="text-xs">{item.description}</CardDescription>
                      )}
                    </CardHeader>
                    <CardContent
                      className={`${isCompact ? "flex-1 flex flex-col px-2 pb-2 pt-0" : "pt-0 flex-1 flex flex-col p-0"}`}
                    >
                      
                    </CardContent>
                  </Card>
                </div>
                );
              })}

              {/* Grid overlay for visual feedback */}
              {(dragState.isDragging || resizeState.isResizing) && (
                <div className="absolute inset-0 pointer-events-none z-0">
                  <div
                    className="grid gap-4 opacity-30"
                    style={{
                      gridTemplateColumns: `repeat(${config.grid.cols}, 1fr)`,
                      gridAutoRows: `${gridSize}px`,
                      width: '100%',
                      height: '100%',
                    }}
                  >
                    {Array.from({ length: config.grid.cols * 10 }).map((_, i) => (
                      <div
                        key={i}
                        className="border border-primary/30 rounded"
                      />
                    ))}
                  </div>
                </div>
              )}

              </div>
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


    </div>
  );
}

// Data Assistant Panel Components for context-aware display
export interface DataAssistantProps {
  config: DashboardConfig;
  onChange: (config: DashboardConfig) => void;
  selectedItem?: string;
  onItemSelect?: (itemId: string) => void;
}

// Add Items Component for Data Assistant
export function AddItemsCard({ config, onChange, onItemSelect }: DataAssistantProps) {
  // No AgUI messaging needed for direct UI updates

  const addItem = (type: DashboardItem["type"]) => {
    console.log('AddItemsCard: Starting to add item of type:', type);
    console.log('AddItemsCard: Current config.items length:', config.items.length);

    // Direct UI update - no LLM involved
    // Generate new item with unique ID
    const newItemId = `item-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;

    const itemTypeNames = {
      chart: "Chart",
      metric: "Metrics",
      text: "Text",
      commentary: "Commentary"
    };

    const itemName = itemTypeNames[type] || type;

    // Create new dashboard item
    const newItem: DashboardItem = {
      id: newItemId,
      type: type,
      chartType: type === "chart" ? "bar" : undefined,
      title: `New ${itemName}`,
      description: `${itemName} component`,
      span: "col-span-1 md:col-span-2",
      position: { row: config.items.length + 1, col: 0 },
      config: {}
    };

    console.log('AddItemsCard: Created new item:', newItem);

    // Add item directly to configuration without LLM
    const updatedConfig = {
      ...config,
      items: [...config.items, newItem]
    };

    console.log('AddItemsCard: Updated config items length:', updatedConfig.items.length);
    console.log('AddItemsCard: Calling onChange with updated config');

    onChange(updatedConfig);

    // Optionally select the new item for immediate editing
    if (onItemSelect) {
      onItemSelect(newItemId);
    }

    console.log(`Added new ${itemName} item to dashboard preview canvas - Direct UI update`);
  };

  return (
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
  );
}

// Dashboard Settings Component for Data Assistant
export function DashboardSettingsCard({ config, onChange }: DataAssistantProps) {
  const { sendDirectUIUpdate } = useAgUiAgent();

  const handleGridChange = (value: string) => {
    const cols = parseInt(value);
    // Send direct UI update for protocol compliance (no LLM)
    sendDirectUIUpdate(`Change dashboard grid to ${value} columns`);
    onChange({
      ...config,
      grid: { ...config.grid, cols }
    });
  };

  return (
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
              onValueChange={handleGridChange}
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
  );
}

// Item Properties Component for Data Assistant (when clicking dashboard item)
export function ItemPropertiesCard({ config, onChange, selectedItemId }: DataAssistantProps & {
  selectedItemId?: string | null;
}) {
  const { sendDirectUIUpdate, sendAIMessage, isRunning } = useAgUiAgent();

  const selectedItemData = selectedItemId ? config.items.find(item => item.id === selectedItemId) : null;

  if (!selectedItemData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Item Properties</CardTitle>
          <CardDescription>No item selected</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Click on a dashboard item to edit its properties.</p>
        </CardContent>
      </Card>
    );
  }

  const updateItem = (itemId: string, updates: Partial<DashboardItem>) => {
    const newConfig = {
      ...config,
      items: config.items.map(item =>
        item.id === itemId ? { ...item, ...updates } : item
      ),
    };

    // Send direct UI update for protocol compliance (no LLM)
    sendDirectUIUpdate(`Update ${selectedItemData.type} item "${selectedItemData.title}"`);
    onChange(newConfig);
  };

  const updateItemConfig = (itemId: string, updates: Record<string, unknown>) => {
    const currentItem = config.items.find(item => item.id === itemId);
    const mergedConfig = { ...(currentItem?.config ?? {}), ...normalizeDataConfigUpdates(updates) };
    updateItem(itemId, { config: mergedConfig });
  };

  const removeItem = (itemId: string) => {
    const newConfig = {
      ...config,
      items: config.items.filter(item => item.id !== itemId),
    };
    // Send direct UI update for protocol compliance (no LLM)
    sendDirectUIUpdate(`Remove ${selectedItemData.type} item "${selectedItemData.title}"`);
    onChange(newConfig);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Item Properties</CardTitle>
        <CardDescription>Configure the selected item</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="general">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="general">General</TabsTrigger>
            <TabsTrigger value="layout">Layout</TabsTrigger>
            <TabsTrigger value="data">Data</TabsTrigger>
          </TabsList>

          <TabsContent value="general" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="item-title">Title</Label>
              <Input
                id="item-title"
                value={selectedItemData.title}
                onChange={(e) => updateItem(selectedItemData.id, { title: e.target.value })}
                disabled={isRunning}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="item-description">Description</Label>
              <Textarea
                id="item-description"
                value={selectedItemData.description || ""}
                onChange={(e) => updateItem(selectedItemData.id, { description: e.target.value })}
                rows={2}
                disabled={isRunning}
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
                value={(() => {
                  const match = selectedItemData.span?.match(/col-span-(\d+)/);
                  const current = match ? parseInt(match[1], 10) : 1;
                  const clamped = Math.min(Math.max(current, 1), config.grid.cols);
                  return `col-span-${clamped}`;
                })()}
                onValueChange={(value) => updateItem(selectedItemData.id, { span: value })}
                disabled={isRunning}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Array.from({ length: config.grid.cols }, (_, i) => {
                    const spanValue = `col-span-${i + 1}`;
                    return (
                      <SelectItem key={spanValue} value={spanValue}>
                        {i + 1} Column{i === 0 ? "" : "s"}
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => removeItem(selectedItemData.id)}
                className="flex-1"
                disabled={isRunning}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Remove Item
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="data" className="space-y-4">
            {selectedItemData.type === "chart" ? (
              <>
                {!(getConfigValue(selectedItemData, "dataSource") && getConfigValue(selectedItemData, "metricField") && getConfigValue(selectedItemData, "dimensionField")) && (
                  <div className="space-y-3 rounded-md border border-primary/20 bg-primary/5 p-4">
                    <p className="text-sm text-muted-foreground">
                      This visualization doesn&apos;t have data configured yet. Launch the LIDA data exploration workflow to map fields automatically.
                    </p>
                    <Button
                      size="sm"
                      onClick={() => {
                        sendAIMessage(`Launch LIDA data exploration for "${selectedItemData.title}" (${selectedItemData.id})`);
                      }}
                      disabled={isRunning}
                    >
                      Launch LIDA Data Explore
                    </Button>
                  </div>
                )}
                <div className="space-y-2">
                  <Label htmlFor="data-source">Data Source</Label>
                  <Input
                    id="data-source"
                    placeholder="e.g., salesData"
                    value={(getConfigValue(selectedItemData, "dataSource") as string) ?? ""}
                    onChange={(e) => updateItemConfig(selectedItemData.id, { dataSource: e.target.value })}
                    disabled={isRunning}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="metric-field">Metric Field</Label>
                  <Input
                    id="metric-field"
                    placeholder="e.g., revenue"
                    value={(getConfigValue(selectedItemData, "metricField") as string) ?? ""}
                    onChange={(e) => updateItemConfig(selectedItemData.id, { metricField: e.target.value })}
                    disabled={isRunning}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="dimension-field">Dimension Field</Label>
                  <Input
                    id="dimension-field"
                    placeholder="e.g., month"
                    value={(getConfigValue(selectedItemData, "dimensionField") as string) ?? ""}
                    onChange={(e) => updateItemConfig(selectedItemData.id, { dimensionField: e.target.value })}
                    disabled={isRunning}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="filters">Filters (JSON)</Label>
                  <Textarea
                    id="filters"
                    placeholder='e.g., {"region": "EMEA"}'
                    value={
                      typeof getConfigValue(selectedItemData, "filters") === "string"
                        ? (getConfigValue(selectedItemData, "filters") as string)
                        : getConfigValue(selectedItemData, "filters")
                        ? JSON.stringify(getConfigValue(selectedItemData, "filters"), null, 2)
                        : ""
                    }
                    onChange={(e) => {
                      const value = e.target.value;
                      let parsed: string | Record<string, unknown> = value;
                      try {
                        parsed = value ? JSON.parse(value) : "";
                      } catch {
                        parsed = value;
                      }
                      updateItemConfig(selectedItemData.id, { filters: parsed });
                    }}
                    rows={4}
                    disabled={isRunning}
                  />
                  <p className="text-xs text-muted-foreground">
                    Provide filters as JSON (stored as-is if parsing fails).
                  </p>
                </div>
                {(() => {
                  const dataSource = ((getConfigValue(selectedItemData, "dbtModel") ||
                    getConfigValue(selectedItemData, "dataSource")) as string) ?? "";
                  const dbtModel = DBT_MODEL_MAP[dataSource];
                  if (!dbtModel) return null;
                  return (
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button variant="outline" size="sm">
                          View dbt Model
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-3xl">
                        <DialogHeader>
                          <DialogTitle>{dbtModel.name}</DialogTitle>
                          <DialogDescription className="space-y-1">
                            <p>{dbtModel.description}</p>
                            <p className="text-xs text-muted-foreground">Path: {dbtModel.path}</p>
                          </DialogDescription>
                        </DialogHeader>
                        <pre className="max-h-[360px] overflow-auto rounded-md bg-muted p-4 text-xs">
                          <code>{dbtModel.sql}</code>
                        </pre>
                      </DialogContent>
                    </Dialog>
                  );
                })()}
              </>
            ) : (
              <p className="text-sm text-muted-foreground">
                Data configuration is available for chart items.
              </p>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

// Dashboard Properties Component for Data Assistant (when clicking dashboard title)
export function DashboardPropertiesCard({ dashboard, saving, onDashboardUpdate }: {
  dashboard?: any;
  saving?: boolean;
  onDashboardUpdate?: (updates: any) => void;
}) {
  const { sendDirectUIUpdate } = useAgUiAgent();

  // Use local state for immediate UI responsiveness
  const [localName, setLocalName] = useState(dashboard?.name || "");
  const [localDescription, setLocalDescription] = useState(dashboard?.description || "");

  // Sync with dashboard prop when it changes from outside
  useEffect(() => {
    setLocalName(dashboard?.name || "");
    setLocalDescription(dashboard?.description || "");
  }, [dashboard?.name, dashboard?.description]);

  // Only disable when saving, not when running (to allow continuous typing)
  const isDisabled = saving;

  const handleNameChange = (newName: string) => {
    // Update local state immediately for responsive UI
    setLocalName(newName);
    // Send direct UI update for protocol compliance (no LLM)
    sendDirectUIUpdate(`Change dashboard name to "${newName}"`);
    // Update dashboard state
    if (onDashboardUpdate) {
      onDashboardUpdate({ name: newName });
    }
  };

  const handleDescriptionChange = (newDescription: string) => {
    // Update local state immediately for responsive UI
    setLocalDescription(newDescription);
    // Send direct UI update for protocol compliance (no LLM)
    sendDirectUIUpdate(`Change dashboard description to "${newDescription}"`);
    // Update dashboard state
    if (onDashboardUpdate) {
      onDashboardUpdate({ description: newDescription });
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Dashboard Properties</CardTitle>
        <CardDescription>Configure dashboard metadata and settings</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="dashboard-name-props">Dashboard Name</Label>
            <Input
              id="dashboard-name-props"
              value={localName}
              onChange={(e) => handleNameChange(e.target.value)}
              placeholder="Enter dashboard name"
              disabled={isDisabled}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="dashboard-description-props">Description (Optional)</Label>
            <Textarea
              id="dashboard-description-props"
              value={localDescription}
              onChange={(e) => handleDescriptionChange(e.target.value)}
              placeholder="Enter dashboard description"
              rows={3}
              disabled={isDisabled}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
