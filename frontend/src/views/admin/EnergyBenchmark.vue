<script setup>
import { computed, onMounted, ref } from 'vue'
import KpiCard from '@/components/KpiCard.vue'
import ChartCard from '@/components/ChartCard.vue'
import DataTable from '@/components/DataTable.vue'
import { api } from '@/api'
import { PALETTE, tooltipBase, axisLabelStyle, axisLineStyle, splitLineStyle } from '@/utils/charts'

const loading = ref(false)
const data = ref({})
const activeTab = ref('process')

const TAB_META = {
  process: { label: '工序对标', unit: 'kgce/t' },
  product: { label: '产品对标', unit: 'kgce/t' },
  equipment: { label: '设备对标', unit: '比功率/效率' }
}

const chartRef = ref(null)

const rows = computed(() => data.value[activeTab.value] || [])
const passCount = computed(() => rows.value.filter((r) => r.pass).length)
const passRate = computed(() => (rows.value.length ? (passCount.value / rows.value.length) * 100 : 0))
const worst = computed(() => rows.value.filter((r) => !r.pass).sort((a, b) => Math.abs(b.gap) - Math.abs(a.gap))[0])

const columns = [
  { prop: 'name', label: '对标项', minWidth: 160 },
  { prop: 'actual', label: '实际值', width: 110, align: 'right', formatter: (r) => Number(r.actual || 0).toLocaleString('zh-CN') },
  { prop: 'limit', label: '限额值', width: 110, align: 'right', formatter: (r) => Number(r.limit || 0).toLocaleString('zh-CN') },
  { prop: 'unit', label: '单位', width: 100 },
  { prop: 'gap', label: '偏差', width: 110, align: 'right', slot: true },
  { prop: 'pass', label: '达标状态', width: 100, align: 'center', slot: true },
  { prop: 'advice', label: '处置建议', minWidth: 200 }
]

function renderChart() {
  const list = rows.value
  if (!list.length || !chartRef.value) return
  chartRef.value.setOption({
    color: [PALETTE[0], PALETTE[2]],
    tooltip: { ...tooltipBase, trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { top: 0, textStyle: { color: '#55655f', fontSize: 12 } },
    grid: { left: 12, right: 24, top: 36, bottom: 8, containLabel: true },
    xAxis: { type: 'value', axisLabel: axisLabelStyle, splitLine: splitLineStyle },
    yAxis: { type: 'category', data: list.map((r) => r.name), axisLabel: axisLabelStyle, axisLine: axisLineStyle, axisTick: { show: false } },
    series: [
      { name: '实际值', type: 'bar', barWidth: 10, itemStyle: { borderRadius: [0, 4, 4, 0] }, data: list.map((r) => r.actual) },
      { name: '限额值', type: 'bar', barWidth: 10, itemStyle: { borderRadius: [0, 4, 4, 0], opacity: 0.55 }, data: list.map((r) => r.limit) }
    ]
  })
}

async function load() {
  loading.value = true
  try {
    data.value = await api.energyBenchmark()
    renderChart()
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

function switchTab(tab) {
  activeTab.value = tab
  renderChart()
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h2>能效对标</h2>
        <p>工序、产品、设备三级对标 · 限额依据国家单位产品能耗限额标准与设备能效标准</p>
      </div>
      <el-radio-group :model-value="activeTab" @update:model-value="switchTab">
        <el-radio-button v-for="(m, k) in TAB_META" :key="k" :value="k">{{ m.label }}</el-radio-button>
      </el-radio-group>
    </div>

    <div class="kpi-grid">
      <KpiCard label="对标项总数" :value="rows.length" unit="项" :decimals="0" accent="blue" />
      <KpiCard label="达标项" :value="passCount" unit="项" :decimals="0" accent="brand" />
      <KpiCard label="达标率" :value="passRate.toFixed(1)" unit="%" accent="violet" :good-when-down="false" />
      <KpiCard
        label="最大超标项"
        :value="worst ? worst.name : '无'"
        :decimals="0"
        :sub="worst ? `偏差 ${worst.gap > 0 ? '+' : ''}${worst.gap}%` : '全部达标'"
        :accent="worst ? 'danger' : 'brand'"
      />
    </div>

    <ChartCard ref="chartRef" :title="`${TAB_META[activeTab].label} · 实际值与限额对比`" :desc="`单位：${TAB_META[activeTab].unit}`" :loading="loading" height="330px" />

    <DataTable :title="`${TAB_META[activeTab].label}明细`" :columns="columns" :data="rows" :loading="loading" show-index>
      <template #col-gap="{ row }">
        <span class="num" :style="{ color: row.pass ? 'var(--brand-deep)' : 'var(--danger)' }">
          {{ row.gap > 0 ? '+' : '' }}{{ row.gap }}%
        </span>
      </template>
      <template #col-pass="{ row }">
        <span class="tag-dot" :style="{ color: row.pass ? 'var(--brand-deep)' : 'var(--danger)' }">
          {{ row.pass ? '达标' : '超标' }}
        </span>
      </template>
    </DataTable>
  </div>
</template>
