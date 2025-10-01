"use client"

import { useEffect, useMemo, useRef, useState } from "react"
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
  const [highlightTheme, setHighlightTheme] = useState({
    borderColor: "#111827",
    shadowColor: "rgba(17, 24, 39, 0.2)",
  })

  useEffect(() => {
    if (typeof window === "undefined") {
      return
    }

    const parseToRgba = (input: string, alpha: number) => {
      const color = input.trim()
      if (!color) {
        return null
      }

      if (color.startsWith("#")) {
        const hex = color.replace("#", "")
        const normalized =
          hex.length === 3
            ? hex
                .split("")
                .map((char) => char + char)
                .join("")
            : hex
        if (normalized.length === 6) {
          const r = Number.parseInt(normalized.slice(0, 2), 16)
          const g = Number.parseInt(normalized.slice(2, 4), 16)
          const b = Number.parseInt(normalized.slice(4, 6), 16)
          return `rgba(${r}, ${g}, ${b}, ${alpha})`
        }
      }

      if (color.startsWith("rgb")) {
        const matches = color.match(/rgba?\(([^)]+)\)/i)
        if (!matches) {
          return null
        }
        const [r, g, b] = matches[1]
          .split(",")
          .map((part) => Number(part.trim()))
        if ([r, g, b].some((value) => Number.isNaN(value))) {
          return null
        }
        return `rgba(${r}, ${g}, ${b}, ${alpha})`
      }

      return null
    }

    const style = window.getComputedStyle(document.documentElement)
    const candidateVars = ["--ring", "--primary", "--copilot-kit-primary-color"]
    const candidateValues = candidateVars
      .map((variable) => style.getPropertyValue(variable).trim())
      .filter((value) => value.length > 0)

    const parsedBorder = candidateValues
      .map((value) => parseToRgba(value, 1))
      .find((converted) => converted !== null)

    const resolvedBorder = parsedBorder ?? candidateValues[0] ?? "#111827"

    const shadowColor =
      candidateValues
        .map((value) => parseToRgba(value, 0.35))
        .find((converted) => converted !== null) ?? "rgba(17, 24, 39, 0.2)"

    setHighlightTheme({
      borderColor: resolvedBorder,
      shadowColor,
    })
  }, [])

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
      chart.dispatchAction({ type: "hideTip" })
      return
    }

    const payload: Record<string, string | number | undefined> = {
      type: "highlight",
      ...descriptor,
    }
    const axisValues = data.map((item) => String(item[index]))
    let resolvedIndex: number | undefined
    if (typeof target.dataIndex === "number") {
      payload.dataIndex = target.dataIndex
      resolvedIndex = target.dataIndex
    }
    if (typeof target.dataName === "string") {
      payload.name = target.dataName
      if (resolvedIndex === undefined) {
        const lookupIndex = axisValues.indexOf(target.dataName)
        if (lookupIndex !== -1) {
          resolvedIndex = lookupIndex
        }
      }
    }
    if (resolvedIndex === undefined && typeof target.name === "string") {
      const lookupIndex = axisValues.indexOf(target.name)
      if (lookupIndex !== -1) {
        resolvedIndex = lookupIndex
        payload.dataIndex = lookupIndex
        payload.name = axisValues[lookupIndex]
      }
    }

    chart.dispatchAction(payload)

    if (resolvedIndex !== undefined) {
      chart.dispatchAction({
        type: "showTip",
        ...descriptor,
        dataIndex: resolvedIndex,
      })
    } else {
      chart.dispatchAction({ type: "hideTip" })
    }
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
        emphasis: {
          focus: "self",
          itemStyle: {
            opacity: 1,
            borderColor: highlightTheme.borderColor,
            borderWidth: 2,
            shadowBlur: 16,
            shadowColor: highlightTheme.shadowColor,
          },
        },
        blur: {
          itemStyle: {
            opacity: 0.2,
          },
        },
        barMaxWidth: isHorizontal ? 32 : 24,
        itemStyle: {
          color: colors[idx % colors.length],
          borderRadius: isHorizontal ? [4, 4, 0, 0] : [0, 4, 4, 0],
          opacity: 0.85,
        },
        data: data.map((item) => Number(item[category] ?? 0)),
      })),
    }
  }, [categories, colors, data, highlightTheme, index, layout, showGrid, showLegend, showXAxis, showYAxis, valueFormatter, yAxisWidth])

  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      onChartReady={(instance) => {
        chartRef.current = instance
        if (typeof window !== "undefined" && chartId) {
          ;(window as unknown as Record<string, EChartsType | undefined>)[`__chart_${chartId}`] = instance
        }
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
