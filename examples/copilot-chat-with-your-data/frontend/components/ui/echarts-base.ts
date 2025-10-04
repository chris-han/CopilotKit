"use client"

import ReactEChartsCore from "echarts-for-react/lib/core"
import * as echarts from "echarts/core"
import { BarChart as EChartsBarChart, LineChart, PieChart as EChartsPieChart, ScatterChart } from "echarts/charts"
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
  DatasetComponent,
  TransformComponent,
  GraphicComponent,
  TitleComponent,
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
  TitleComponent,
  CanvasRenderer,
  LineChart,
  EChartsBarChart,
  EChartsPieChart,
  ScatterChart,
])

export { ReactEChartsCore, echarts }
