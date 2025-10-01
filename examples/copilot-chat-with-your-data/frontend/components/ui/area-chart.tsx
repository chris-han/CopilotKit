"use client"

import { useCallback, useEffect, useMemo, useRef } from "react"
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

interface AreaChartProps {
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
}

export function AreaChart({
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
}: AreaChartProps) {
  const chartRef = useRef<EChartsType | null>(null)
  const lastFocusRef = useRef<ChartFocusEventDetail | null>(null)
  const xValues = useMemo(() => data.map((item) => String(item[index])), [data, index])

  const applyFocus = useCallback(
    (chart: EChartsType, detail: ChartFocusEventDetail) => {
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

      let resolvedIndex: number | undefined
      if (typeof target.dataIndex === "number") {
        resolvedIndex = target.dataIndex
      } else if (typeof target.dataName === "string") {
        const idx = xValues.indexOf(target.dataName)
        if (idx !== -1) {
          resolvedIndex = idx
        }
      }

      const payload: Record<string, string | number | undefined> = {
        type: "highlight",
        ...descriptor,
      }

      if (resolvedIndex !== undefined) {
        payload.dataIndex = resolvedIndex
        payload.name = xValues[resolvedIndex]
      } else if (typeof target.dataName === "string") {
        payload.name = target.dataName
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
    },
    [xValues],
  )

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
  }, [chartId, applyFocus])

  useEffect(() => {
    if (!chartId) {
      return
    }
    const pending = lastFocusRef.current
    const chart = chartRef.current
    if (!pending || !chart || pending.chartId !== chartId) {
      return
    }
    applyFocus(chart, pending)
  }, [applyFocus, chartId, data])

  const option = useMemo<EChartsOption>(() => {
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
  }, [categories, colors, data, index, showGrid, showLegend, showXAxis, showYAxis, valueFormatter, xValues, yAxisWidth])

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
