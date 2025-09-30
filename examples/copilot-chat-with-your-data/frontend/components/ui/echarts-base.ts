"use client"

import ReactEChartsCore from "echarts-for-react/lib/core"
import * as echarts from "echarts/core"
import { BarChart as EChartsBarChart, LineChart, PieChart as EChartsPieChart } from "echarts/charts"
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
  DatasetComponent,
  TransformComponent,
  GraphicComponent,
} from "echarts/components"
import { CanvasRenderer } from "echarts/renderers"

// Register the basic chart types and shared components once for the app.
echarts.use([
  GridComponent,
  LegendComponent,
  TooltipComponent,
  DatasetComponent,
  TransformComponent,
  GraphicComponent,
  CanvasRenderer,
  LineChart,
  EChartsBarChart,
  EChartsPieChart,
])

export { ReactEChartsCore, echarts }
