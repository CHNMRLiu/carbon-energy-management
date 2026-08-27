<script setup>
import { onMounted, ref } from 'vue'
import KpiCard from '@/components/KpiCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import DataTable from '@/components/DataTable.vue'
import { api } from '@/api'
import { PALETTE, tooltipBase, axisLabelStyle, axisLineStyle, splitLineStyle } from '@/utils/charts'

const loading = ref(false)
const data = ref({})
const chartRef = ref(null)

const columns = [
  { prop: 'level', label: '预警级别', width: 110, align: 'center', slot: true },
  { prop: 'content', label: '预警内容', minWidth: 320 }
]

const LEVEL_TYPE = { 红色: 'danger', 橙色: 'warning', 黄色: 'warning', 蓝色: 'info' }

/** 预算执行率与时间进度对比（后端无月度趋势，改用执行进度对比图） */
function renderChart() {
  const d = data.value
  if (!d.energy || !chartRef.value) return
  chartRef.value.setOption({
    color: [PALETTE[0], PALETTE[2]],
    tooltip: { ...tooltipBase, trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: (v) => `${v}%` },
    legend: { top: 0, textStyle: { color: '#55655f', fontSize: 12 } },
    grid: { left: 12, right: 20, top: 36, bottom: 8, containLabel: true },
    xAxis: { type: 'category', data: ['用能预算', '碳预算'], axisLabel: axisLabelStyle, axisLine: axisLineStyle, axisTick: { show: false } },
    yAxis: { type: 'value', name: '%', nameTextStyle: { color: '#8b988f' }, axisLabel: axisLabelStyle, splitLine: splitLineStyle },
    series: [
      { name: '预算执行率', type: 'bar', barWidth: 26, itemStyle: { borderRadius: [5, 5, 0, 0] }, label: { show: true, position: 'top', formatter: '{c}%', color: '#55655f', fontSize: 12 }, data: [d.energy.rate, d.carbon.rate] },
      { name: '时间进度', type: 'bar', barWidth: 26, itemStyle: { borderRadius: [5, 5, 0, 0], opacity: 0.55 }, label: { show: true, position: 'top', formatter: '{c}%', color: '#55655f', fontSize: 12 }, data: [d.energy.time_progress, d.carbon.time_progress] }
    ]
  })
}

async function load() {
  loading.value = true
  try {
    data.value = await api.carbonBudget()
    renderChart()
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h2>碳预算管理</h2>
        <p>{{ data.year || '--' }} 年度用能与碳排放预算执行率、年末预测与预警 · 统计区间 {{ data.period_label || '--' }}</p>
      </div>
    </div>

    <div class="kpi-grid">
      <KpiCard label="用能预算执行率" :value="data.energy?.rate ?? '--'" unit="%" accent="brand" :sub="`时间进度 ${data.energy?.time_progress ?? '--'}% · ${data.energy?.status || ''}`" />
      <KpiCard label="碳预算执行率" :value="data.carbon?.rate ?? '--'" unit="%" accent="blue" :sub="`时间进度 ${data.carbon?.time_progress ?? '--'}% · ${data.carbon?.status || ''}`" />
      <KpiCard label="用能年末预测" :value="data.energy?.forecast ?? '--'" unit="tce" accent="amber" />
      <KpiCard label="碳排放年末预测" :value="data.carbon?.forecast ?? '--'" unit="tCO₂e" accent="violet" />
    </div>

    <div class="two-col">
      <div class="card budget-card">
        <h3 class="budget-title">用能预算 <span class="num">{{ Number(data.energy?.budget || 0).toLocaleString('zh-CN') }} {{ data.energy?.unit }}</span></h3>
        <el-progress :percentage="data.energy?.rate || 0" :stroke-width="14" :color="(data.energy?.rate || 0) > 90 ? '#d64545' : '#0c8f7a'" />
        <div class="budget-meta">
          <span>已用 <b class="num">{{ Number(data.energy?.used || 0).toLocaleString('zh-CN') }}</b></span>
          <span>年末预测 <b class="num">{{ Number(data.energy?.forecast || 0).toLocaleString('zh-CN') }}</b></span>
        </div>
      </div>
      <div class="card budget-card">
        <h3 class="budget-title">碳排放预算 <span class="num">{{ Number(data.carbon?.budget || 0).toLocaleString('zh-CN') }} {{ data.carbon?.unit }}</span></h3>
        <el-progress :percentage="data.carbon?.rate || 0" :stroke-width="14" :color="(data.carbon?.rate || 0) > 90 ? '#d64545' : '#2f6fed'" />
        <div class="budget-meta">
          <span>已排放 <b class="num">{{ Number(data.carbon?.used || 0).toLocaleString('zh-CN') }}</b></span>
          <span>年末预测 <b class="num">{{ Number(data.carbon?.forecast || 0).toLocaleString('zh-CN') }}</b></span>
        </div>
      </div>
    </div>

    <ChartCard ref="chartRef" title="预算执行进度对比" desc="预算执行率 vs 时间进度" :loading="loading" height="320px" />

    <DataTable title="预算预警记录" :columns="columns" :data="data.warnings || []" :loading="loading" show-index>
      <template #col-level="{ row }">
        <el-tag :type="LEVEL_TYPE[row.level] || 'info'" size="small" effect="dark">{{ row.level }}</el-tag>
      </template>
    </DataTable>
  </div>
</template>

<style scoped>
.budget-card { padding: 18px 20px; }
.budget-title {
  margin: 0 0 14px; font-size: 14px; color: var(--ink-2);
  display: flex; align-items: baseline; gap: 8px;
}
.budget-title .num { font-size: 18px; font-weight: 700; color: var(--ink); }
.budget-meta {
  margin-top: 12px; display: flex; gap: 24px;
  font-size: 12.5px; color: var(--ink-2);
}
.budget-meta b { font-size: 14px; color: var(--ink); margin-left: 4px; }
</style>
