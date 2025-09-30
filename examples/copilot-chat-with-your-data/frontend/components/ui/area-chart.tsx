"use client"

import { useMemo } from "react"
import type { EChartsOption } from "echarts"

import { ReactEChartsCore, echarts } from "./echarts-base"

interface ChartDataItem {
  [key: string]: string | number
}

interface AreaChartProps {
  data: ChartDataItem[]
  index: string
  categories: string[]
  colors?: string[]
  valueFormatter?: (value: number) => string
  className?: string
  showLegend?: boolean
  showXAxis?: boolean
  showYAxis?: boolean
  showGrid?: boolean
  yAxisWidth?: number
}

export function AreaChart({
  data,
  index,
  categories,
  colors = ["#3b82f6", "#10b981", "#6366f1", "#f59e0b", "#ef4444"],
  valueFormatter = (value: number) => `${value}`,
  className,
  showLegend = true,
  showXAxis = true,
  showYAxis = true,
  showGrid = true,
  yAxisWidth = 55,
}: AreaChartProps) {
  const option = useMemo<EChartsOption>(() => {
    const xValues = data.map((item) => String(item[index]))
    const gridLeft = showYAxis ? Math.max(yAxisWidth, 45) : 20

    return {
      color: colors,
      tooltip: {
        trigger: "axis",
        valueFormatter: (value: number) => valueFormatter(value),
        backgroundColor: "#ffffff",
        borderColor: "#e5e7eb",
        borderWidth: 1,
        textStyle: { color: "#374151", fontSize: 12 },
        padding: 10,
      },
      legend: {
        show: showLegend,
        top: 0,
        icon: "circle",
        textStyle: { color: "#6b7280", fontSize: 14 },
      },
      grid: {
        top: showLegend ? 54 : 24,
        left: gridLeft,
        right: 24,
        bottom: showXAxis ? 36 : 16,
      },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: xValues,
        axisLine: { show: showXAxis, lineStyle: { color: "#d1d5db" } },
        axisTick: { show: false },
        axisLabel: {
          show: showXAxis,
          color: "#6b7280",
          fontSize: 12,
          margin: 12,
        },
      },
      yAxis: {
        type: "value",
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: showGrid, lineStyle: { color: "#e5e7eb", type: "dashed" } },
        axisLabel: {
          show: showYAxis,
          formatter: (value: number) => valueFormatter(value),
          color: "#6b7280",
          fontSize: 12,
          margin: 12,
        },
      },
      series: categories.map((category, idx) => ({
        name: category,
        type: "line",
        smooth: true,
        emphasis: { focus: "series" },
        symbolSize: 6,
        itemStyle: {
          color: colors[idx % colors.length],
        },
        lineStyle: {
          width: 2,
          color: colors[idx % colors.length],
        },
        areaStyle: {
          opacity: 0.15,
          color: colors[idx % colors.length],
        },
        data: data.map((item) => Number(item[category] ?? 0)),
      })),
    }
  }, [categories, colors, data, index, showGrid, showLegend, showXAxis, showYAxis, valueFormatter, yAxisWidth])

  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      className={className}
      style={{ width: "100%", height: "100%" }}
      notMerge
    />
  )
}
