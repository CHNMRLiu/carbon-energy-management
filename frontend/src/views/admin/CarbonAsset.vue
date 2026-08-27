<script setup>
import { onMounted, ref } from 'vue'
import KpiCard from '@/components/KpiCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import DataTable from '@/components/DataTable.vue'
import { api } from '@/api'
import { PALETTE, tooltipBase, axisLabelStyle, axisLineStyle, splitLineStyle } from '@/utils/charts'

const loading = ref(false)
const data = ref({})

const gaugeRef = ref(null)
const trendRef = ref(null)

const columns = [
  { prop: 'level', label: '级别', width: 100, align: 'center', slot: true },
  { prop: 'content', label: '预警内容', minWidth: 360 }
]

const LEVEL_TYPE = { 红色: 'danger', 橙色: 'warning', 黄色: 'warning', 蓝色: 'info' }

function renderGauge(rate) {
  if (!gaugeRef.value || rate === undefined) return
  gaugeRef.value.setOption({
    series: [
      {
        type: 'gauge',
        startAngle: 210,
        endAngle: -30,
        min: 0,
        max: 100,
        radius: '92%',
        progress: { show: true, width: 16, roundCap: true, itemStyle: { color: rate > 90 ? '#d64545' : '#0c8f7a' } },
        axisLine: { lineStyle: { width: 16, color: [[1, '#eef2f0']] } },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        pointer: { show: false },
        anchor: { show: false },
        title: { show: true, offsetCenter: [0, '34%'], fontSize: 13, color: '#55655f' },
        detail: {
          valueAnimation: true,
          offsetCenter: [0, '2%'],
          fontSize: 30,
          fontWeight: 700,
          fontFamily: 'Bahnschrift, "DIN Alternate", sans-serif',
          color: '#16241f',
          formatter: '{value}%'
        },
        data: [{ value: rate, name: '配额使用率' }]
      }
    ]
  })
}

function renderHistory(history) {
  if (!history?.length || !trendRef.value) return
  trendRef.value.setOption({
    color: [PALETTE[3], PALETTE[0]],
    tooltip: { ...tooltipBase, trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { top: 0, textStyle: { color: '#55655f', fontSize: 12 } },
    grid: { left: 12, right: 20, top: 36, bottom: 8, containLabel: true },
    xAxis: { type: 'category', data: history.map((h) => `${h.year}年`), axisLabel: axisLabelStyle, axisLine: axisLineStyle, axisTick: { show: false } },
    yAxis: { type: 'value', name: 'tCO₂e', nameTextStyle: { color: '#8b988f' }, axisLabel: axisLabelStyle, splitLine: splitLineStyle },
    series: [
      { name: '年度配额', type: 'bar', barWidth: 26, itemStyle: { borderRadius: [6, 6, 0, 0] }, data: history.map((h) => h.quota) },
      { name: '实际排放', type: 'bar', barWidth: 26, itemStyle: { borderRadius: [6, 6, 0, 0] }, data: history.map((h) => h.actual_emission) }
    ]
  })
}

async function load() {
  loading.value = true
  try {
    data.value = await api.carbonAsset()
    renderGauge(data.value.usage_rate)
    renderHistory(data.value.history)
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
        <h2>碳资产管理</h2>
        <p>配额管理、履约测算、预测预警 · {{ data.year || '--' }} 年度履约周期，截止 {{ data.compliance_deadline || '--' }}</p>
      </div>
    </div>

    <div class="kpi-grid">
      <KpiCard label="年度配额" :value="data.quota ?? '--'" unit="tCO₂e" :decimals="0" accent="brand" />
      <KpiCard label="已排放" :value="data.emitted ?? '--'" unit="tCO₂e" :decimals="0" accent="danger" />
      <KpiCard label="配额盈余" :value="data.surplus ?? '--'" unit="tCO₂e" :decimals="0" accent="blue" sub="盈余可参与交易" />
      <KpiCard label="年底排放预测" :value="data.forecast_year_end ?? '--'" unit="tCO₂e" :decimals="0" accent="amber" :sub="`预计年底盈余 ${(data.forecast_surplus ?? 0).toLocaleString('zh-CN', { maximumFractionDigits: 0 })} tCO₂e`" />
    </div>

    <div class="two-col">
      <ChartCard ref="gaugeRef" title="配额履约测算" desc="履约截止日（含清缴）" :loading="loading" height="300px">
        <template #extra>
          <el-tag type="info" size="small" effect="plain">截止 {{ data.compliance_deadline || '--' }}</el-tag>
        </template>
      </ChartCard>
      <ChartCard ref="trendRef" title="配额与实际排放对比" desc="年度口径 · tCO₂e" :loading="loading" height="300px" />
    </div>

    <DataTable title="碳资产预警" :columns="columns" :data="data.alerts || []" :loading="loading" show-index empty-text="当前无预警，配额盈余充足，系统持续监控中">
      <template #col-level="{ row }">
        <el-tag :type="LEVEL_TYPE[row.level] || 'info'" size="small" effect="dark">{{ row.level }}</el-tag>
      </template>
    </DataTable>
  </div>
</template>
