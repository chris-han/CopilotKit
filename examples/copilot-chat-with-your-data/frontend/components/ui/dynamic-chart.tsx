"use client";

import { useEffect, useRef } from "react";
import type { EChartsOption } from "echarts";
import type { EChartsType } from "echarts/core";
import { ReactEChartsCore, echarts } from "./echarts-base";

interface DynamicChartProps {
  config: EChartsOption;
  className?: string;
  style?: React.CSSProperties;
}

export function DynamicChart({ config, className, style }: DynamicChartProps) {
  const chartRef = useRef<EChartsType | null>(null);

  const defaultStyle = {
    width: "100%",
    height: "400px",
    ...style,
  };

  useEffect(() => {
    // Ensure chart resizes properly when window size changes
    const handleResize = () => {
      if (chartRef.current) {
        chartRef.current.resize();
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Enhanced chart configuration with better defaults
  const enhancedConfig: EChartsOption = {
    // Default styling
    backgroundColor: "transparent",
    textStyle: {
      fontFamily: "system-ui, -apple-system, sans-serif",
    },
    // Merge with provided config
    ...config,
    // Enhanced tooltip
    tooltip: {
      backgroundColor: "#ffffff",
      borderColor: "#e5e7eb",
      borderWidth: 1,
      textStyle: {
        color: "#374151",
        fontSize: 12
      },
      padding: 10,
      trigger: "item",
      ...config.tooltip,
    },
    // Enhanced legend
    legend: {
      textStyle: {
        color: "#6b7280",
        fontSize: 12
      },
      ...config.legend,
    },
    // Ensure grid has proper padding
    grid: {
      left: "10%",
      right: "10%",
      top: "15%",
      bottom: "15%",
      containLabel: true,
      ...config.grid,
    },
  };

  return (
    <ReactEChartsCore
      ref={(instance) => {
        chartRef.current = instance?.getEchartsInstance() || null;
      }}
      echarts={echarts}
      option={enhancedConfig}
      className={className}
      style={defaultStyle}
      notMerge={true}
      lazyUpdate={true}
      onChartReady={(instance) => {
        chartRef.current = instance;
        // Trigger initial resize to ensure proper rendering
        setTimeout(() => {
          instance.resize();
        }, 100);
      }}
    />
  );
}