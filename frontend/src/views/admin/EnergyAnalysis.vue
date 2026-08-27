<script setup>
import { onMounted, ref } from 'vue'
import KpiCard from '@/components/KpiCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import DataTable from '@/components/DataTable.vue'
import { api } from '@/api'
import { PALETTE, tooltipBase, axisLabelStyle, axisLineStyle, splitLineStyle } from '@/utils/charts'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const data = ref({})

const structureRef = ref(null)
const costRef = ref(null)
const effRef = ref(null)

const columns = [
  { prop: 'dimension', label: '维度', width: 110 },
  { prop: 'suggestion', label: '策略建议', minWidth: 320 },
  { prop: 'expected_effect', label: '预期效果', minWidth: 180 },
  { prop: 'priority', label: '优先级', width: 90, align: 'center', slot: true }
]

const PRIORITY_TYPE = { 高: 'danger', 中: 'warning', 低: 'info' }

function pieOption(items, unit) {
  return {
    color: PALETTE,
    tooltip: {
      ...tooltipBase,
      trigger: 'item',
      formatter: (p) => `${p.name}<br/><b>${Number(p.value).toLocaleString('zh-CN')} ${unit}</b> (${p.percent}%)`
    },
    legend: { bottom: 0, textStyle: { color: '#55655f', fontSize: 12 } },
    series: [
      {
        type: 'pie',
        radius: ['46%', '70%'],
        center: ['50%', '44%'],
        itemStyle: { borderColor: '#fff', borderWidth: 2, borderRadius: 6 },
        label: { formatter: '{b}\n{d}%', fontSize: 11, color: '#55655f' },
        emphasis: { scaleSize: 6 },
        data: items
      }
    ]
  }
}

function renderCharts() {
  const d = data.value
  if (d.structure?.length && structureRef.value) structureRef.value.setOption(pieOption(d.structure, 'tce'))
  if (d.cost?.length && costRef.value) costRef.value.setOption(pieOption(d.cost, '万元'))
  if (d.efficiency?.axis?.length && effRef.value) {
    effRef.value.setOption({
      color: [PALETTE[1]],
      tooltip: { ...tooltipBase, trigger: 'axis' },
      grid: { left: 12, right: 20, top: 30, bottom: 8, containLabel: true },
      xAxis: { type: 'category', data: d.efficiency.axis, axisLabel: axisLabelStyle, axisLine: axisLineStyle, axisTick: { show: false } },
      yAxis: { type: 'value', scale: true, axisLabel: axisLabelStyle, splitLine: splitLineStyle },
      series: d.efficiency.series.map((s) => ({
        name: s.name,
        type: 'line',
        smooth: true,
        symbolSize: 6,
        data: s.data,
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(47,111,237,0.25)' },
              { offset: 1, color: 'rgba(47,111,237,0)' }
            ]
          }
        }
      }))
    })
  }
}

async function load() {
  loading.value = true
  try {
    data.value = await api.energyAnalysis()
    renderCharts()
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

function applySuggestion(row) {
  ElMessage.success(`已采纳策略「${row.suggestion.slice(0, 20)}…」至优化任务队列`)
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h2>用能分析与策略推荐</h2>
        <p>用能结构、成本构成、能效趋势三维分析，输出可落地的节能优化策略</p>
      </div>
    </div>

    <div class="kpi-grid">
      <KpiCard label="电力占比" :value="data.structure?.find((s) => s.energy_code === 'electricity')?.share ?? '--'" unit="%" :decimals="2" accent="brand" sub="用能结构主力" />
      <KpiCard label="用能成本合计" :value="data.total_cost_wan ?? 0" unit="万元" accent="amber" sub="近 12 期累计" />
      <KpiCard
        label="当前单位产品能耗"
        :value="data.efficiency?.series?.[0]?.data?.slice(-1)[0] ?? '--'"
        unit="kgce/t"
        :decimals="2"
        accent="blue"
      />
      <KpiCard label="策略推荐数" :value="data.strategies?.length ?? 0" unit="项" :decimals="0" accent="violet" sub="按优先级排序" />
    </div>

    <div class="two-col">
      <ChartCard ref="structureRef" title="用能结构占比" desc="折标煤口径" :loading="loading" height="300px" />
      <ChartCard ref="costRef" title="用能成本构成" desc="本期累计" :loading="loading" height="300px" />
    </div>

    <ChartCard ref="effRef" title="能效趋势" desc="单位产品能耗逐月走势 · kgce/t" :loading="loading" height="300px" />

    <DataTable title="策略推荐列表" :columns="columns" :data="data.strategies || []" :loading="loading" show-index>
      <template #col-priority="{ row }">
        <el-tag :type="PRIORITY_TYPE[row.priority] || 'info'" size="small" effect="light">{{ row.priority }}</el-tag>
      </template>
      <template #extra>
        <el-button size="small" type="primary" plain @click="data.strategies?.[0] && applySuggestion(data.strategies[0])">
          采纳首选策略
        </el-button>
      </template>
    </DataTable>
  </div>
</template>
