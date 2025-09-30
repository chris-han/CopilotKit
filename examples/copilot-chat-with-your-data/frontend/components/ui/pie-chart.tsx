"use client"

import { useMemo } from "react"
import type { EChartsOption } from "echarts"

import { ReactEChartsCore, echarts } from "./echarts-base"

interface ChartDataItem {
  [key: string]: string | number
}

interface PieChartProps {
  data: ChartDataItem[]
  category: string
  index: string
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

    return {
      color: colors,
      tooltip: {
        trigger: "item",
        backgroundColor: "#ffffff",
        borderColor: "#e5e7eb",
        borderWidth: 1,
        textStyle: { color: "#374151", fontSize: 12 },
        padding: 10,
        formatter: (params: any) => {
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
        bottom: 0,
        icon: "circle",
        textStyle: { color: "#6b7280", fontSize: 14 },
        itemGap: 12,
      },
      graphic: centerText
        ? [{
            type: "text",
            left: "center",
            top: "middle",
            style: {
              text: centerText,
              fill: "#374151",
              fontSize: 16,
              fontWeight: 500,
            },
          }]
        : undefined,
      series: [
        {
          name: category,
          type: "pie",
          radius,
          center: ["50%", showLegend ? "45%" : "50%"],
          padAngle: paddingAngle,
          avoidLabelOverlap: true,
          minAngle: 2,
          itemStyle: {
            borderRadius: 6,
            borderColor: "#ffffff",
            borderWidth: 2,
          },
          label: showLabel
            ? {
                show: true,
                formatter: (params: any) => `${Math.round(Number(params.percent ?? 0))}%`,
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
  }, [centerText, colors, data, category, index, innerRadius, outerRadius, paddingAngle, showLabel, showLegend, valueFormatter])

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
