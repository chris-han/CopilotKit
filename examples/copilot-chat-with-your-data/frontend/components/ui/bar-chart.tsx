"use client"

import { useEffect, useMemo, useRef } from "react"
import type { EChartsOption } from "echarts"
import type { EChartsType } from "echarts/core"

import {
  CHART_FOCUS_EVENT,
  type ChartFocusEventDetail,
} from "../../lib/chart-highlighting"
import { ReactEChartsCore, echarts } from "./echarts-base"

interface ChartDataItem {
  [key: string]: string | number
}

interface BarChartProps {
  data: ChartDataItem[]
  index: string
  categories: string[]
  chartId?: string
  colors?: string[]
  valueFormatter?: (value: number) => string
  className?: string
  showLegend?: boolean
  showXAxis?: boolean
  showYAxis?: boolean
  showGrid?: boolean
  yAxisWidth?: number
  layout?: "horizontal" | "vertical"
}

export function BarChart({
  data,
  index,
  categories,
  chartId,
  colors = ["#3b82f6", "#10b981", "#6366f1", "#f59e0b", "#ef4444"],
  valueFormatter = (value: number) => `${value}`,
  className,
  showLegend = true,
  showXAxis = true,
  showYAxis = true,
  showGrid = true,
  yAxisWidth = 55,
  layout = "horizontal",
}: BarChartProps) {
  const chartRef = useRef<EChartsType | null>(null)
  const lastFocusRef = useRef<ChartFocusEventDetail | null>(null)

  const applyFocus = (chart: EChartsType, detail: ChartFocusEventDetail) => {
    lastFocusRef.current = detail

    const resolveSeriesDescriptor = () => {
      const target = detail.target
      if (!target) {
        return { seriesIndex: 0 }
      }
      if (typeof target.seriesId === "string") {
        return { seriesId: target.seriesId }
      }
      if (typeof target.seriesName === "string") {
        return { seriesName: target.seriesName }
      }
      if (typeof target.seriesIndex === "number") {
        return { seriesIndex: target.seriesIndex }
      }
      return { seriesIndex: 0 }
    }

    const descriptor = resolveSeriesDescriptor()

    chart.dispatchAction({ type: "downplay", ...descriptor })

    const target = detail.target
    if (!target) {
      return
    }

    const payload: Record<string, string | number | undefined> = {
      type: "highlight",
      ...descriptor,
    }
    if (typeof target.dataIndex === "number") {
      payload.dataIndex = target.dataIndex
    }
    if (typeof target.dataName === "string") {
      payload.name = target.dataName
    }

    chart.dispatchAction(payload)
  }

  useEffect(() => {
    if (!chartId) {
      return
    }

    const handler = (event: Event) => {
      const customEvent = event as CustomEvent<ChartFocusEventDetail | undefined>
      const detail = customEvent.detail
      if (!detail || detail.chartId !== chartId) {
        return
      }
      const chart = chartRef.current
      if (!chart) {
        lastFocusRef.current = detail
        return
      }
      applyFocus(chart, detail)
    }

    window.addEventListener(CHART_FOCUS_EVENT, handler as EventListener)
    return () => {
      window.removeEventListener(CHART_FOCUS_EVENT, handler as EventListener)
    }
  }, [chartId])

  const option = useMemo<EChartsOption>(() => {
    const axisValues = data.map((item) => String(item[index]))
    const isHorizontal = layout === "horizontal"

    const horizontalAxes = {
      xAxis: {
        type: "category" as const,
        data: axisValues,
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
        type: "value" as const,
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
    }

    const verticalAxes = {
      xAxis: {
        type: "value" as const,
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: showGrid, lineStyle: { color: "#e5e7eb", type: "dashed" } },
        axisLabel: {
          show: showXAxis,
          formatter: (value: number) => valueFormatter(value),
          color: "#6b7280",
          fontSize: 12,
          margin: 12,
        },
      },
      yAxis: {
        type: "category" as const,
        data: axisValues,
        axisLine: { show: showYAxis, lineStyle: { color: "#d1d5db" } },
        axisTick: { show: false },
        axisLabel: {
          show: showYAxis,
          color: "#6b7280",
          fontSize: 12,
          margin: 12,
        },
      },
    }

    const gridLeft = isHorizontal ? (showYAxis ? Math.max(yAxisWidth, 55) : 20) : showYAxis ? 100 : 20
    const gridBottom = showXAxis ? 40 : 20

    return {
      color: colors,
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
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
        bottom: gridBottom,
        containLabel: true,
      },
      ...(isHorizontal ? horizontalAxes : verticalAxes),
      series: categories.map((category, idx) => ({
        name: category,
        type: "bar",
        emphasis: { focus: "series" },
        barMaxWidth: isHorizontal ? 32 : 24,
        itemStyle: {
          color: colors[idx % colors.length],
          borderRadius: isHorizontal ? [4, 4, 0, 0] : [0, 4, 4, 0],
          opacity: 0.85,
        },
        data: data.map((item) => Number(item[category] ?? 0)),
      })),
    }
  }, [categories, colors, data, index, layout, showGrid, showLegend, showXAxis, showYAxis, valueFormatter, yAxisWidth])

  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      onChartReady={(instance) => {
        chartRef.current = instance
        const pending = lastFocusRef.current
        if (pending && pending.chartId === chartId) {
          applyFocus(instance, pending)
        }
      }}
      className={className}
      style={{ width: "100%", height: "100%" }}
      notMerge
    />
  )
}
