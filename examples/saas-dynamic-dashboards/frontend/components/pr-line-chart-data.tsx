import { useEffect, useMemo, useState } from "react"
import { CartesianGrid, Legend, Line, LineChart, Tooltip, XAxis, YAxis } from "recharts"
import { WeeklyCount } from "@/app/Interfaces/interface"
import { cn } from "@/lib/utils"
import { resolveChartHighlightIntent, useChartHighlight } from "@/lib/use-chart-highlight"
import { X } from "lucide-react"

export function PRLineChartData({ args }: any) {
  const [lineData, setLineData] = useState<WeeklyCount[]>([])
  const [xarr, setXarr] = useState<string[]>([])
  const highlightRequested = resolveChartHighlightIntent("renderData_LineChart", args)
  const { isHighlighted, dismiss } = useChartHighlight("renderData_LineChart", highlightRequested)

  useEffect(() => {
    if (args?.items) {
      const allKeys = new Set<string>()
      args?.items?.flat()?.forEach(({ accessorKey }: any) => allKeys.add(accessorKey))
      const merged: Record<string, Record<string, unknown>> = {}
      args?.items?.flat()?.forEach(({ name, value, accessorKey }: any) => {
        if (!merged[name]) {
          merged[name] = { name }
          allKeys.forEach((key) => {
            merged[name][key] = 0
          })
        }
        merged[name][accessorKey] = value
      })
      const result = Object.values(merged) as WeeklyCount[]
      setLineData(result)
      setXarr(args?.items?.map((item: any) => item[0]?.accessorKey))
    }
  }, [args?.items])

  const chartColors = useMemo(
    () => [
      "hsl(12, 76%, 61%)",
      "hsl(173, 58%, 39%)",
      "hsl(43, 74%, 66%)",
      "hsl(27, 87%, 67%)",
      "hsl(12, 76%, 61%)",
      "hsl(173, 58%, 39%)",
      "hsl(43, 74%, 66%)",
      "hsl(27, 87%, 67%)",
      "hsl(12, 76%, 61%)",
      "hsl(173, 58%, 39%)",
      "hsl(43, 74%, 66%)",
      "hsl(27, 87%, 67%)",
      "hsl(12, 76%, 61%)",
      "hsl(173, 58%, 39%)",
      "hsl(43, 74%, 66%)",
      "hsl(27, 87%, 67%)",
      "hsl(197, 37%, 24%)",
    ],
    []
  )

  const chartWidth = isHighlighted ? 640 : 520
  const chartHeight = isHighlighted ? 260 : 220

  return (
    <div
      data-chart-id="renderData_LineChart"
      className={cn(
        "relative flex w-full min-w-[250px] max-w-full flex-col items-center rounded-2xl bg-background p-4 shadow-lg transition-all duration-300",
        isHighlighted
          ? "fixed left-1/2 top-1/2 z-50 w-[min(720px,calc(100vw-3rem))] max-h-[90vh] -translate-x-1/2 -translate-y-1/2 overflow-auto shadow-[0_25px_45px_-15px_rgba(15,23,42,0.6)] ring-2 ring-primary/70"
          : ""
      )}
    >
      {isHighlighted && (
        <button
          type="button"
          aria-label="Close focused trend chart"
          className="absolute right-4 top-4 rounded-full bg-background/80 p-1 text-muted-foreground transition hover:text-foreground"
          onClick={dismiss}
        >
          <X className="h-4 w-4" />
        </button>
      )}
      <h2 className="mb-2 text-center text-xl font-semibold text-gray-700">Trend Distribution</h2>
      <div
        className="flex w-full items-center justify-center"
        style={{ minHeight: isHighlighted ? chartHeight + 40 : 200 }}
      >
        <LineChart width={chartWidth} height={chartHeight} data={lineData}>
          <CartesianGrid stroke="#B6C7DB" strokeDasharray="4 4" />
          <XAxis dataKey="name" stroke="#4F5A66" />
          <YAxis stroke="#4F5A66" />
          <Tooltip wrapperStyle={{ fontSize: 12, paddingLeft: 10 }} />
          <Legend align="center" verticalAlign="bottom" width={225} wrapperStyle={{ color: "black", fontSize: "12px", paddingLeft: 10 }} />
          {xarr.map((item: string, index: number) => (
            <Line
              key={`${item}-${index}`}
              type="monotone"
              dataKey={item}
              stroke={chartColors[index % chartColors.length]}
              strokeWidth={3}
              dot={{ r: 5 }}
            />
          ))}
        </LineChart>
      </div>
    </div>
  )
}
