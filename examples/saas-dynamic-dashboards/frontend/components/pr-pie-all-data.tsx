import { useEffect, useMemo, useState } from "react"
import { Cell, Pie, PieChart, Tooltip } from "recharts"
import { cn } from "@/lib/utils"
import { resolveChartHighlightIntent, useChartHighlight } from "@/lib/use-chart-highlight"
import { X } from "lucide-react"

interface PieDataItem {
  name: string
  value: number
  color: string
  shortName: string
}

interface PieDataProps {
  args: {
    items: PieDataItem[]
    title?: string
  }
}

export function PRPieData({ args }: PieDataProps) {
  const [chartData, setChartData] = useState<PieDataItem[]>([])
  const highlightRequested = resolveChartHighlightIntent("renderData_PieChart", args)
  const { isHighlighted, dismiss } = useChartHighlight("renderData_PieChart", highlightRequested)

  useEffect(() => {
    if (args?.items) {
      setChartData(args.items)
    }
  }, [args?.items])

  const chartSize = useMemo(() => (isHighlighted ? { width: 320, height: 220 } : { width: 260, height: 180 }), [isHighlighted])

  return (
    <div
      data-chart-id="renderData_PieChart"
      className={cn(
        "relative flex min-w-[250px] max-w-[350px] flex-1 flex-col items-center rounded-2xl bg-background p-4 shadow-lg transition-all duration-300",
        isHighlighted
          ? "fixed left-1/2 top-1/2 z-50 w-[min(420px,calc(100vw-3rem))] max-h-[90vh] -translate-x-1/2 -translate-y-1/2 overflow-auto shadow-[0_25px_45px_-15px_rgba(15,23,42,0.6)] ring-2 ring-primary/70"
          : ""
      )}
    >
      {isHighlighted && (
        <button
          type="button"
          aria-label="Close focused pie chart"
          className="absolute right-4 top-4 rounded-full bg-background/80 p-1 text-muted-foreground transition hover:text-foreground"
          onClick={dismiss}
        >
          <X className="h-4 w-4" />
        </button>
      )}
      <h2 className="mb-2 text-center text-xl font-semibold text-gray-700">
        {args.title || "Data Distribution"}
      </h2>
      <div
        className="flex flex-col items-center justify-center"
        style={{ minHeight: isHighlighted ? chartSize.height + 40 : 180 }}
      >
        <PieChart width={chartSize.width} height={chartSize.height}>
          <Pie
            data={chartData}
            cx={chartSize.width / 2}
            cy={chartSize.height / 2}
            innerRadius={isHighlighted ? 40 : 30}
            outerRadius={isHighlighted ? 90 : 70}
            paddingAngle={0}
            dataKey="value"
            labelLine={false}
            label={({ value }) => value}
          >
            {chartData.map((entry, index: number) => (
              <Cell key={entry.name || `cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip content={<CustomPieTooltip />} />
        </PieChart>
      </div>
      <div className="mt-4 flex flex-col items-center">
        {chunkArray(chartData, 2).map((row, rowIdx) => (
          <div key={rowIdx} className="flex w-full flex-row items-center justify-center gap-x-6 gap-y-2">
            {row.map((entry: PieDataItem, colIdx) => (
              <div key={`${entry.name}-${rowIdx}-${colIdx}`} className="flex min-w-[110px] items-center gap-1">
                <span style={{ backgroundColor: entry.color }} className="inline-block h-4 w-4 rounded-full" />
                <span style={{ width: "94px" }} className="text-sm text-black">
                  {entry?.shortName}
                </span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

export const CustomPieTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const { name, value } = payload[0].payload
    return (
      <div className="rounded bg-white p-2 text-black shadow">
        <div>{name.split("_").join(" ")}</div>
        <div>Value: {value}</div>
      </div>
    )
  }
  return null
}

export function chunkArray<T>(array: T[], size: number): T[][] {
  const result: T[][] = []
  for (let i = 0; i < array.length; i += size) {
    result.push(array.slice(i, i + size))
  }
  return result
}
