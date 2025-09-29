import { useMemo, useEffect, useState } from "react"
import { BarChart, CartesianGrid, Legend, Tooltip, XAxis, YAxis, Bar } from "recharts"
import { cn } from "@/lib/utils"
import { resolveChartHighlightIntent, useChartHighlight } from "@/lib/use-chart-highlight"
import { X } from "lucide-react"

interface BarChartData {
  name: string
  value: number
}

export function PRReviewBarData({ args }: any) {
  const [data, setData] = useState<BarChartData[]>([])
  const highlightRequested = resolveChartHighlightIntent("renderData_BarChart", args)
  const { isHighlighted, dismiss } = useChartHighlight("renderData_BarChart", highlightRequested)
  const chartColors = useMemo(
    () => [
      "hsl(12, 76%, 61%)",
      "hsl(173, 58%, 39%)",
      "hsl(197, 37%, 24%)",
      "hsl(43, 74%, 66%)",
      "hsl(27, 87%, 67%)",
    ],
    []
  )

  useEffect(() => {
    if (args?.items) {
      setData(args.items)
    }
  }, [args?.items])

  const chartSize = useMemo(() => (isHighlighted ? { width: 320, height: 220 } : { width: 260, height: 180 }), [isHighlighted])

  return (
    <div
      data-chart-id="renderData_BarChart"
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
          aria-label="Close focused bar chart"
          className="absolute right-4 top-4 rounded-full bg-background/80 p-1 text-muted-foreground transition hover:text-foreground"
          onClick={dismiss}
        >
          <X className="h-4 w-4" />
        </button>
      )}
      <h2 className="mb-2 text-center text-xl font-semibold text-gray-700">Data Distribution</h2>
      <div
        className="flex items-center justify-center"
        style={{ minHeight: isHighlighted ? chartSize.height + 40 : 180 }}
      >
        <BarChart width={chartSize.width} height={chartSize.height} data={data}>
          <CartesianGrid stroke="#94a3b855" strokeDasharray="3 3" />
          <XAxis
            dataKey="name"
            stroke="#cbd5e1"
            tickFormatter={(value: string) => value?.[0]?.toUpperCase() ?? value}
          />
          <YAxis stroke="#cbd5e1" />
          <Tooltip contentStyle={{ background: "#1f2937", border: "none", color: "white" }} />
          <Legend wrapperStyle={{ color: "white" }} />
          <Bar dataKey="value" fill={chartColors[3]} />
        </BarChart>
      </div>
    </div>
  )
}
