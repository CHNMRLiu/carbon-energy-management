/**
 * ECharts 按需注册：仅注册 line / bar / pie / sankey / gauge
 * 以及渲染所需的必要组件与 Canvas 渲染器。
 */
import * as echarts from 'echarts/core'
import { LineChart, BarChart, PieChart, SankeyChart, GaugeChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  DataZoomComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  LineChart,
  BarChart,
  PieChart,
  SankeyChart,
  GaugeChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  DataZoomComponent,
  CanvasRenderer
])

/** 统一图表色板（与全局设计令牌一致） */
export const PALETTE = ['#0c8f7a', '#2f6fed', '#d9912b', '#d64545', '#7c5cff', '#37b26a', '#0e7490', '#b45309']

/** 通用 tooltip 配置 */
export const tooltipBase = {
  backgroundColor: 'rgba(22, 36, 31, 0.92)',
  borderColor: 'transparent',
  textStyle: { color: '#f2f7f5', fontSize: 12 },
  padding: [8, 12]
}

/** 通用网格配置（管理端浅色主题） */
export const gridBase = {
  left: 12,
  right: 20,
  top: 36,
  bottom: 8,
  containLabel: true
}

export const axisLabelStyle = { color: '#55655f', fontSize: 12 }
export const axisLineStyle = { lineStyle: { color: '#ccd6d0' } }
export const splitLineStyle = { lineStyle: { color: '#e9eeeb', type: 'dashed' } }

export default echarts
