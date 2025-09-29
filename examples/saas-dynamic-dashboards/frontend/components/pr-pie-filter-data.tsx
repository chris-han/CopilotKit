import { useEffect, useMemo, useState } from "react"
import { Cell, Pie, PieChart, Tooltip } from "recharts"
import { PRData } from "@/app/Interfaces/interface"
import { useSharedContext } from "@/lib/shared-context"
import { cn } from "@/lib/utils"
import { CustomPieTooltip, chunkArray } from "./pr-pie-all-data"
import { resolveChartHighlightIntent, useChartHighlight } from "@/lib/use-chart-highlight"
import { X } from "lucide-react"

export function PRPieFilterData({ args }: any) {
  const [userPRData, setUserPRData] = useState<{ name: string; value: number }[]>([])
  const { prData } = useSharedContext()
  const highlightRequested = resolveChartHighlightIntent("renderData_FilteredPie", args)
  const { isHighlighted, dismiss } = useChartHighlight("renderData_FilteredPie", highlightRequested)

  const status = useMemo(
    () => [
      { name: "approved", color: "bg-green-300", value: "rgb(134 239 172)" },
      { name: "needs_revision", color: "bg-yellow-300", value: "rgb(253 224 71)" },
      { name: "merged", color: "bg-purple-300", value: "rgb(216 180 254)" },
      { name: "in_review", color: "bg-blue-300", value: "rgb(147 197 253)" },
    ],
    []
  )

  useEffect(() => {
    const now = new Date()
    const pieData = Object.entries(
      getStatusCounts(
        prData.filter((pr: PRData) => {
          if (args?.userId && pr.userId !== args.userId) {
            return false
          }
          if (!pr.createdAt) {
            return false
          }
          const createdDate = new Date(pr.createdAt)
          const diffDays = (now.getTime() - createdDate.getTime()) / (1000 * 60 * 60 * 24)
          return diffDays <= args.dayCount
        })
      )
    ).map(([statusName, count]) => ({
      name: statusName,
      value: count as number,
    }))
    setUserPRData(pieData)
  }, [args, prData])

  const chartSize = useMemo(() => (isHighlighted ? { width: 320, height: 220 } : { width: 260, height: 180 }), [isHighlighted])

  function getStatusCounts(data: PRData[]) {
    return data.reduce<Record<string, number>>((acc, pr) => {
      acc[pr.status] = (acc[pr.status] || 0) + 1
      return acc
    }, {})
  }

  return (
    <div
      data-chart-id="renderData_FilteredPie"
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
          aria-label="Close focused PR status distribution chart"
          className="absolute right-4 top-4 rounded-full bg-background/80 p-1 text-muted-foreground transition hover:text-foreground"
          onClick={dismiss}
        >
          <X className="h-4 w-4" />
        </button>
      )}
      <h2 className="mb-2 text-center text-xl font-semibold text-gray-700">PR Status Distribution</h2>
      <div
        className="flex flex-col items-center justify-center"
        style={{ minHeight: isHighlighted ? chartSize.height + 40 : 180 }}
      >
        <PieChart width={chartSize.width} height={chartSize.height}>
          <Pie
            data={userPRData}
            cx={chartSize.width / 2}
            cy={chartSize.height / 2}
            innerRadius={isHighlighted ? 40 : 30}
            outerRadius={isHighlighted ? 90 : 70}
            paddingAngle={0}
            dataKey="value"
            labelLine={false}
            label={({ value }) => value}
          >
            {userPRData.map((entry, index: number) => (
              <Cell key={`cell-${index}`} fill={status.find((s) => s.name === entry.name)?.value} />
            ))}
          </Pie>
          <Tooltip content={<CustomPieTooltip />} />
        </PieChart>
      </div>
      <div className="mt-4 flex flex-col items-center">
        {chunkArray(status, 2).map((row, rowIdx) => (
          <div key={rowIdx} className="flex w-full flex-row items-center justify-center gap-x-6 gap-y-2">
            {row.map((entry) => (
              <div key={entry.name} className="flex min-w-[110px] items-center gap-1">
                <span className={`inline-block h-4 w-4 rounded-full ${entry.color}`} />
                <span className="text-sm text-black">{entry.name.split("_").join(" ")}</span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
