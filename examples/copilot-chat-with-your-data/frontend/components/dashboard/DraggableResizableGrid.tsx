"use client";

import React, { useState, useRef, useCallback, useEffect } from "react";
import { DashboardItem } from "@/types/dashboard";

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

interface DraggableResizableGridProps {
  items: DashboardItem[];
  onItemMove: (itemId: string, newPosition: GridPosition) => void;
  onItemResize: (itemId: string, newSize: { width: number; height: number }) => void;
  gridSize: number;
  cols: number;
  children: React.ReactNode;
  className?: string;
}

// Convert grid column spans to actual grid positions
function parseGridSpan(span: string): { width: number; height: number } {
  const colSpanMatch = span.match(/col-span-(\d+)/);
  const width = colSpanMatch ? parseInt(colSpanMatch[1]) : 1;
  const height = 1; // Default height, can be extended
  return { width, height };
}

// Convert grid position to CSS grid column/row values
function gridToCSS(position: GridPosition, cols: number) {
  return {
    gridColumnStart: Math.max(1, Math.min(position.x + 1, cols)),
    gridColumnEnd: Math.max(2, Math.min(position.x + position.width + 1, cols + 1)),
    gridRowStart: position.y + 1,
    gridRowEnd: position.y + position.height + 1,
  };
}

// Snap position to grid
function snapToGrid(x: number, y: number, gridSize: number): { x: number; y: number } {
  return {
    x: Math.round(x / gridSize) * gridSize,
    y: Math.round(y / gridSize) * gridSize,
  };
}

// Convert pixel position to grid coordinates
function pixelToGrid(pixelX: number, pixelY: number, containerWidth: number, cols: number): GridPosition {
  const cellWidth = containerWidth / cols;
  const gridX = Math.max(0, Math.min(Math.floor(pixelX / cellWidth), cols - 1));
  const gridY = Math.max(0, Math.floor(pixelY / 140)); // Approximate grid row height
  return { x: gridX, y: gridY, width: 1, height: 1 };
}

export function DraggableResizableGrid({
  items,
  onItemMove,
  onItemResize,
  gridSize = 120,
  cols = 4,
  children,
  className = "",
}: DraggableResizableGridProps) {
  const containerRef = useRef<HTMLDivElement>(null);
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

  // Initialize item positions from their span classes and position data
  useEffect(() => {
    const newPositions = new Map<string, GridPosition>();
    let currentRow = 0;
    let currentCol = 0;

    items.forEach((item) => {
      const { width, height } = parseGridSpan(item.span);

      // Use existing position if available, otherwise calculate based on order
      const position: GridPosition = {
        x: item.position.col !== undefined ? item.position.col : currentCol,
        y: item.position.row !== undefined ? item.position.row - 1 : currentRow,
        width,
        height,
      };

      // Ensure position fits within grid
      if (position.x + position.width > cols) {
        position.x = Math.max(0, cols - position.width);
      }

      newPositions.set(item.id, position);

      // Calculate next position for items without explicit position
      if (item.position.col === undefined) {
        currentCol = position.x + position.width;
        if (currentCol >= cols) {
          currentCol = 0;
          currentRow++;
        }
      }
    });

    setItemPositions(newPositions);
  }, [items, cols]);

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

      setDragState({
        isDragging: true,
        draggedItemId: itemId,
        startPosition: { x: startX, y: startY },
        currentPosition: { x: startX, y: startY },
        itemStartPosition: { x: itemPosition.x * gridSize, y: itemPosition.y * gridSize },
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
  }, [itemPositions, gridSize]);

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

      const snapped = snapToGrid(newPixelX, newPixelY, gridSize);

      setDragState(prev => ({
        ...prev,
        currentPosition: { x: snapped.x, y: snapped.y },
      }));
    }

    if (resizeState.isResizing && resizeState.resizedItemId) {
      const deltaX = currentX - resizeState.startPosition.x;
      const deltaY = currentY - resizeState.startPosition.y;

      const gridDeltaX = Math.round(deltaX / gridSize);
      const gridDeltaY = Math.round(deltaY / gridSize);

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
  }, [dragState, resizeState, itemPositions, gridSize]);

  const handleMouseUp = useCallback(() => {
    if (dragState.isDragging && dragState.draggedItemId) {
      const rect = containerRef.current?.getBoundingClientRect();
      if (rect) {
        const containerWidth = rect.width;
        const gridPos = pixelToGrid(dragState.currentPosition.x, dragState.currentPosition.y, containerWidth, cols);
        const currentItemPos = itemPositions.get(dragState.draggedItemId);

        if (currentItemPos) {
          const newPosition = { ...currentItemPos, x: gridPos.x, y: gridPos.y };
          onItemMove(dragState.draggedItemId, newPosition);

          const updatedPositions = new Map(itemPositions);
          updatedPositions.set(dragState.draggedItemId, newPosition);
          setItemPositions(updatedPositions);
        }
      }
    }

    if (resizeState.isResizing && resizeState.resizedItemId) {
      const currentItemPos = itemPositions.get(resizeState.resizedItemId);
      if (currentItemPos) {
        onItemResize(resizeState.resizedItemId, {
          width: currentItemPos.width,
          height: currentItemPos.height
        });
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
  }, [dragState, resizeState, itemPositions, onItemMove, onItemResize, cols]);

  // Calculate minimum grid height based on items
  const calculateMinHeight = () => {
    if (itemPositions.size === 0) return gridSize * 3; // Default minimum height

    let maxRow = 0;
    itemPositions.forEach((position) => {
      const bottomRow = position.y + position.height;
      maxRow = Math.max(maxRow, bottomRow);
    });

    return Math.max(maxRow * gridSize, gridSize * 3); // At least 3 rows minimum
  };

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
    <div
      ref={containerRef}
      className={`grid gap-4 ${className}`}
      style={{
        gridTemplateColumns: `repeat(${cols}, 1fr)`,
        gridAutoRows: `${gridSize}px`,
        minHeight: `${calculateMinHeight()}px`,
      }}
    >
      {React.Children.map(children, (child) => {
        if (!React.isValidElement(child) || !child.key) return child;

        const itemId = child.key.toString();
        const item = items.find(i => i.id === itemId);
        const position = itemPositions.get(itemId);

        if (!item || !position) return child;

        const isDragged = dragState.draggedItemId === itemId;
        const isResized = resizeState.resizedItemId === itemId;

        return (
          <div
            key={itemId}
            className={`relative group ${isDragged ? 'z-50' : 'z-10'} ${
              isDragged || isResized ? 'opacity-80' : ''
            }`}
            style={{
              ...gridToCSS(position, cols),
              transform: isDragged
                ? `translate(${dragState.currentPosition.x - dragState.itemStartPosition.x}px, ${dragState.currentPosition.y - dragState.itemStartPosition.y}px)`
                : undefined,
            }}
          >
            {/* Drag handle */}
            <div
              className="absolute -top-2 -left-2 w-6 h-6 bg-primary rounded cursor-move opacity-0 group-hover:opacity-100 transition-opacity z-20 flex items-center justify-center shadow-md"
              onMouseDown={(e) => handleMouseDown(e, itemId, 'drag')}
              title="Drag to move"
            >
              <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M7 2a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM7 8a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM7 14a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM13 2a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM13 8a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM13 14a2 2 0 1 0 0 4 2 2 0 0 0 0-4z"/>
              </svg>
            </div>

            {/* Resize handle */}
            <div
              className="absolute -bottom-2 -right-2 w-6 h-6 bg-primary rounded cursor-se-resize opacity-0 group-hover:opacity-100 transition-opacity z-20 flex items-center justify-center shadow-md"
              onMouseDown={(e) => handleMouseDown(e, itemId, 'resize', 'se')}
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
                className="absolute inset-0 border-2 border-primary border-dashed bg-primary/10 rounded"
                style={{
                  transform: `translate(${dragState.currentPosition.x - dragState.itemStartPosition.x}px, ${dragState.currentPosition.y - dragState.itemStartPosition.y}px)`,
                }}
              />
            )}

            {child}
          </div>
        );
      })}

      {/* Grid overlay for visual feedback */}
      {(dragState.isDragging || resizeState.isResizing) && (
        <div className="absolute inset-0 pointer-events-none z-0">
          <div
            className="grid gap-4 opacity-20"
            style={{
              gridTemplateColumns: `repeat(${cols}, 1fr)`,
              gridAutoRows: `${gridSize}px`,
              width: '100%',
              height: '100%',
            }}
          >
            {Array.from({ length: cols * 10 }).map((_, i) => (
              <div
                key={i}
                className="border border-primary/30 rounded"
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}