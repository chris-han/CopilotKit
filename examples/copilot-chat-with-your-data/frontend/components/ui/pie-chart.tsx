"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import type { EChartsOption } from "echarts"
import type { EChartsType } from "echarts/core"
import type { CallbackDataParams } from "echarts/types/dist/shared"

import {
  CHART_FOCUS_EVENT,
  type ChartFocusEventDetail,
} from "../../lib/chart-highlighting"
import { ReactEChartsCore, echarts } from "./echarts-base"

interface ChartDataItem {
  [key: string]: string | number
}

interface PieChartProps {
  data: ChartDataItem[]
  category: string
  index: string
  chartId?: string
  colors?: string[]
  valueFormatter?: (value: number) => string
  className?: string
  innerRadius?: number
  outerRadius?: string | number
  paddingAngle?: number
  showLabel?: boolean
  showLegend?: boolean
  centerText?: string
}

export function PieChart({
  data,
  category,
  index,
  chartId,
  colors = ["#3b82f6", "#64748b", "#10b981", "#f59e0b", "#94a3b8"],
  valueFormatter = (value: number) => `${value}`,
  className,
  innerRadius = 0,
  outerRadius = "80%",
  paddingAngle = 2,
  showLabel = true,
  showLegend = true,
  centerText,
}: PieChartProps) {
  const chartRef = useRef<EChartsType | null>(null)
  const lastFocusRef = useRef<ChartFocusEventDetail | null>(null)
  const centerPositionRef = useRef<{ left: number; top: number } | null>(null)
  const [isChartReady, setIsChartReady] = useState(false)
  const [centerOverride, setCenterOverride] = useState<[number, number] | null>(null)
  const [highlightTheme, setHighlightTheme] = useState({
    borderColor: "#111827",
    shadowColor: "rgba(17, 24, 39, 0.2)",
  })

  const centerGraphicId = useMemo(() => (chartId ? `${chartId}-center-text` : "pie-center-text"), [chartId])

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

  // Keep the optional center label aligned with the pie's computed center.
  const updateCenterGraphic = useCallback(() => {
    if (!centerText) {
      centerPositionRef.current = null
      return
    }

    const chart = chartRef.current
    if (!chart) {
      return
    }

    const model = chart.getModel()
    const seriesModel = model.getSeriesByIndex(0)
    if (!seriesModel) {
      return
    }

    const data = seriesModel.getData()
    if (!data || data.count() === 0) {
      return
    }

    const layout = data.getItemLayout(0) as { cx?: number; cy?: number }
    const cx = layout?.cx
    const cy = layout?.cy
    if (typeof cx !== "number" || typeof cy !== "number") {
      return
    }

    const previous = centerPositionRef.current
    if (previous && previous.left === cx && previous.top === cy) {
      return
    }

    centerPositionRef.current = { left: cx, top: cy }
    setCenterOverride([cx, cy])
  }, [centerText])

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

    const highlightPayload: Record<string, string | number | undefined> = {
      type: "highlight",
      ...descriptor,
    }
    const sliceNames = data.map((item) => String(item[index]))
    let resolvedIndex: number | undefined
    if (typeof target.dataIndex === "number") {
      highlightPayload.dataIndex = target.dataIndex
      resolvedIndex = target.dataIndex
    }
    if (typeof target.dataName === "string") {
      highlightPayload.name = target.dataName
      if (resolvedIndex === undefined) {
        const lookupIndex = sliceNames.indexOf(target.dataName)
        if (lookupIndex !== -1) {
          resolvedIndex = lookupIndex
        }
      }
    }
    if (resolvedIndex === undefined && typeof target.name === "string") {
      const lookupIndex = sliceNames.indexOf(target.name)
      if (lookupIndex !== -1) {
        resolvedIndex = lookupIndex
        highlightPayload.dataIndex = lookupIndex
        highlightPayload.name = sliceNames[lookupIndex]
      }
    }

    chart.dispatchAction(highlightPayload)

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

  useEffect(() => {
    if (!centerText || !isChartReady) {
      centerPositionRef.current = null
      setCenterOverride(null)
      return
    }

    updateCenterGraphic()
  }, [centerText, isChartReady, data, category, index, innerRadius, outerRadius, paddingAngle, showLegend, updateCenterGraphic])

  useEffect(() => {
    if (!isChartReady || !centerText) {
      return
    }

    const chart = chartRef.current
    if (!chart) {
      return
    }

    const handleUpdate = () => {
      updateCenterGraphic()
    }

    chart.on("rendered", handleUpdate)
    chart.on("legendselectchanged", handleUpdate)
    const zr = typeof chart.getZr === "function" ? chart.getZr() : null
    zr?.on?.("resize", handleUpdate)

    return () => {
      chart.off("rendered", handleUpdate)
      chart.off("legendselectchanged", handleUpdate)
      const cleanupZr = typeof chart.getZr === "function" ? chart.getZr() : null
      cleanupZr?.off?.("resize", handleUpdate)
    }
  }, [centerText, isChartReady, updateCenterGraphic])

  const option = useMemo<EChartsOption>(() => {
    const radius: [string | number, string | number] = [
      typeof innerRadius === "number" ? innerRadius : innerRadius,
      typeof outerRadius === "number" ? outerRadius : outerRadius,
    ]

    const chartData = data.map((item, idx) => ({
      value: Number(item[category] ?? 0),
      name: String(item[index]),
      itemStyle: {
        color: colors[idx % colors.length],
      },
    }))

    const pieCenter: [string | number, string | number] = showLegend
      ? ["60%", "50%"]
      : ["50%", "50%"]

    const effectiveCenter: [string | number, string | number] = centerOverride ?? pieCenter

    const centerGraphicElement = centerText
      ? centerOverride
        ? {
            id: centerGraphicId,
            type: "text" as const,
            silent: true,
            style: {
              text: centerText,
              fill: "#374151",
              fontSize: 16,
              fontWeight: 500,
              align: "center" as const,
              verticalAlign: "middle" as const,
              textAlign: "center" as const,
              textVerticalAlign: "middle" as const,
              x: centerOverride[0],
              y: centerOverride[1],
            },
          }
        : {
            id: centerGraphicId,
            type: "text" as const,
            silent: true,
            left: effectiveCenter[0],
            top: effectiveCenter[1],
            style: {
              text: centerText,
              fill: "#374151",
              fontSize: 16,
              fontWeight: 500,
              align: "center" as const,
              verticalAlign: "middle" as const,
              textAlign: "center" as const,
              textVerticalAlign: "middle" as const,
            },
          }
      : undefined

    return {
      color: colors,
      tooltip: {
        trigger: "item",
        backgroundColor: "#ffffff",
        borderColor: "#e5e7eb",
        borderWidth: 1,
        textStyle: { color: "#374151", fontSize: 12 },
        padding: 10,
        formatter: (params: CallbackDataParams) => {
          if (!params) {
            return ""
          }
          const value = Number(params.value ?? 0)
          const percent = Math.round(Number(params.percent ?? 0))
          const marker = typeof params.marker === "string" ? params.marker : ""
          const name = typeof params.name === "string" ? params.name : ""
          return `${marker}${name}: ${valueFormatter(value)} (${percent}%)`
        },
      },
      legend: {
        show: showLegend,
        orient: "vertical",
        left: 0,
        top: "middle",
        icon: "circle",
        textStyle: { color: "#6b7280", fontSize: 14 },
        itemGap: 12,
      },
      graphic: centerGraphicElement ? { elements: [centerGraphicElement] } : undefined,
      series: [
        {
          name: category,
          type: "pie",
          radius,
          center: effectiveCenter,
          padAngle: paddingAngle,
          avoidLabelOverlap: true,
          minAngle: 2,
          itemStyle: {
            borderRadius: 6,
            borderColor: "#ffffff",
            borderWidth: 2,
          },
          emphasis: {
            focus: "self",
            scale: true,
            scaleSize: 6,
            itemStyle: {
              borderColor: highlightTheme.borderColor,
              borderWidth: 3,
              shadowBlur: 24,
              shadowOffsetX: 0,
              shadowOffsetY: 8,
              shadowColor: highlightTheme.shadowColor,
            },
            label: showLabel
              ? {
                  color: highlightTheme.borderColor,
                  fontWeight: 600,
                }
              : undefined,
          },
          blur: {
            itemStyle: {
              opacity: 0.25,
            },
          },
          label: showLabel
            ? {
                show: true,
                formatter: (params: CallbackDataParams) => `${Math.round(Number(params.percent ?? 0))}%`,
                color: "#374151",
                fontSize: 12,
                fontWeight: 500,
                distance: 24,
              }
            : { show: false },
          labelLine: showLabel
            ? {
                show: true,
                length: 16,
                length2: 12,
                lineStyle: { width: 1, color: "#d1d5db" },
              }
            : { show: false },
          data: chartData,
        },
      ],
    }
  }, [
    centerText,
    centerOverride,
    centerGraphicId,
    colors,
    data,
    category,
    index,
    innerRadius,
    outerRadius,
    paddingAngle,
    highlightTheme,
    showLabel,
    showLegend,
    valueFormatter,
  ])

  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      onChartReady={(instance) => {
        chartRef.current = instance
        setIsChartReady(true)
        if (typeof window !== "undefined" && chartId) {
          ;(window as unknown as Record<string, EChartsType | undefined>)[`__chart_${chartId}`] = instance
        }
        const pendingFocus = lastFocusRef.current
        if (pendingFocus && pendingFocus.chartId === chartId) {
          applyFocus(instance, pendingFocus)
        }
        updateCenterGraphic()
      }}
      className={className}
      style={{ width: "100%", height: "100%" }}
      notMerge
    />
  )
}

export function DonutChart(props: PieChartProps) {
  return (
    <PieChart
      {...props}
      innerRadius={props.innerRadius ?? 40}
      outerRadius={props.outerRadius ?? "85%"}
      showLabel={props.showLabel ?? false}
      showLegend={props.showLegend ?? true}
    />
  )
}
